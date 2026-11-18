"""One bounded entry point; stage accounting and financial acceptance stay separate."""
import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path

from .financial_history_documents import put,read
from .financial_pdf_pipeline import prepare,execute,snapshot,file_hash
from .financial_pdf_ocr_bridge_v2 import run as selected_ocr
from .financial_ocr_campaign import coordinate
from .financial_pdf_reference_import import run as import_review
from .financial_user_workflow import exclusive
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside


def checked_result(root,spec):
    path=inside(root,spec['path']);raw=(path/'manifest.json').read_bytes()
    if digest(raw)!=spec['manifest_sha256']:raise ValueError('workflow dataset manifest changed')
    for name,sha in json.loads(raw).items():
        if file_hash(path/name)!=sha:raise ValueError('workflow dataset file changed: '+name)
    return path


def status(root,c):
    p=read(inside(root,c['acquisition_config']))
    states=[read(x) for x in inside(root,p['output_root']).joinpath('targets').glob('*.json')]
    ref=read(inside(root,c['dataset_result_ref']));dataset=checked_result(root,ref)
    summary=read(dataset/'summary.json')
    rows=list(csv.DictReader(io.StringIO((dataset/'recovered-rows.csv').read_text(encoding='utf-8-sig'))))
    recovered={(r['registry_id'],int(r['year'])) for r in rows}
    targets=[]
    for t in p['targets']:
        old=next((r['status'] for r in states if r['target']['registry_id']==t['registry_id'] and r['target']['year']==t['year']), 'PENDING')
        restored=(t['registry_id'],t['year']) in recovered
        targets.append(dict(symbol=t['symbol'],year=t['year'],acquisition_state=old,reference_state='RESTORED_REVIEWED_CORE_REFERENCE' if restored else 'UNRESOLVED',strict_pit_ready=False))
    n=sum(r['reference_state']=='RESTORED_REVIEWED_CORE_REFERENCE' for r in targets)
    return dict(status='PARTIAL_PILOT',targets_total=len(targets),targets_visited=len(states),
        reference_targets_completed=n,reference_progress_percent=100*n/len(targets),
        current_feature_rows=summary['rows_after'],current_full10=summary['full10_after'],
        new_reference_rows=summary['new_rows'],acquisition_state_counts=dict(Counter(r['status'] for r in states)),
        next50_allowed=False,strict_pit_ready=False,research_ready=False,targets=targets,
        current_dataset=ref['path'])


def run(root,config_path,action,network=False):
    c=read(inside(root,config_path))
    if c['version']!='financial-pdf-workflow-v1':raise ValueError('workflow contract required')
    for path,sha in c['input_pins'].items():
        if file_hash(inside(root,path))!=sha:raise ValueError('workflow input changed: '+path)
    if action=='status':return status(root,c)
    out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
    pins={p:file_hash(inside(root,p)) for p in [config_path,'src/delta_t1/experiments/financial_pdf_workflow.py','scripts/financial_pdf_workflow.py','scripts/financial_pdf_workflow.ps1']}
    with exclusive(out):
        put(out/'contract.json',dict(pins=pins,scope='APPROVED_PILOT10_ONLY',automatic_fact_acceptance=False))
        pc,po,contract=prepare(root,c['acquisition_config'])
        if action=='run':
            execute(root,pc,po,contract,network)
            snapshot(root,pc,po)
            if c.get('ocr_selection'):selected_ocr(root,c['ocr_selection'],True)
            if c.get('review_import_config'):import_review(root,c['review_import_config'])
        elif action=='verify':
            snapshot(root,pc,po,True)
            ref=read(inside(root,c['dataset_result_ref']));dataset=checked_result(root,ref)
            for path,sha in read(dataset/'input-pins.json').items():
                if file_hash(inside(root,path))!=sha:raise ValueError('reviewed dataset source changed: '+path)
            if c.get('ocr_selection'):
                selection=read(inside(root,c['ocr_selection']))
                plan=read(inside(root,selection['output_root']+'/controller-plan.json'))['plan']
                coordinate(root,plan['campaign_config'],'verify')
        result=status(root,c)
        folder=out/'results'/digest(encoded(result))[:20]
        put(folder/'status.json',result)
        return dict(result,status='VERIFIED_PARTIAL_PILOT' if action=='verify' else result['status'],workflow_result=folder.relative_to(root).as_posix())


def cli(root):
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','status','verify'],default='status',nargs='?')
    p.add_argument('--config',default='configs/data/financial_pdf_workflow_v1.json');p.add_argument('--network',action='store_true')
    args=p.parse_args();print(json.dumps(run(root,args.config,args.action,args.network),ensure_ascii=False))
