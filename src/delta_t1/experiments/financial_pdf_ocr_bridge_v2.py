"""Versioned controller: prepare/run coexist; reuse registered OCR pages by hash."""
import argparse
import json
from pathlib import Path

from .financial_history_documents import put, read
from .financial_pdf_pipeline import file_hash
from .financial_pdf_ocr_bridge import validate_selection, run as render_prepare
from .financial_ocr_campaign import coordinate
from .financial_user_workflow import exclusive
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside


def registered_pages(root, campaign_root, pdf_sha256):
    found={}
    for path in sorted(inside(root,campaign_root).joinpath('registrations').glob('*.json')):
        record=read(path)
        child=inside(root,record['config_path'])
        if file_hash(child)!=record['config_sha256']:
            raise ValueError('registered OCR config changed')
        for job in record['jobs']:
            if job['pdf_sha256']!=pdf_sha256:continue
            page=job['pdf_page']
            if page in found:raise ValueError('duplicate registered PDF page')
            found[page]=dict(job=job,registration=path.relative_to(root).as_posix(),registration_sha256=file_hash(path))
    return found


def run(root, selection_path, execute=False):
    from pypdf import PdfReader
    c=read(inside(root,selection_path));out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
    if c['version']!='financial-pdf-ocr-bridge-v1' or c['selection_method']!='VISUAL_PAGE_SELECTION_REQUIRES_REVIEW':
        raise ValueError('explicit page-selection receipt required')
    if file_hash(inside(root,c['pdf_path']))!=c['pdf_sha256'] or file_hash(inside(root,c['parent_ocr_config']))!=c['parent_ocr_config_sha256']:
        raise ValueError('PDF/campaign source changed')
    validate_selection(c['pages'],len(PdfReader(inside(root,c['pdf_path'])).pages))
    pins={p:file_hash(inside(root,p)) for p in [selection_path,c['pdf_path'],c['parent_ocr_config'],c['selection_evidence'],
        'src/delta_t1/experiments/financial_pdf_ocr_bridge_v2.py','scripts/financial_pdf_ocr_bridge_v2.py',
        'src/delta_t1/experiments/financial_pdf_ocr_bridge.py']}
    # Rendering helper has its own lock; never acquire the same lock recursively.
    planpath=out/'controller-plan.json'
    if not planpath.exists():
        parent=read(inside(root,c['parent_ocr_config']))
        existing=registered_pages(root,parent['output_root'],c['pdf_sha256'])
        reused=[existing[p] for p in c['pages'] if p in existing]
        if reused and len(reused)!=len(c['pages']):
            raise ValueError('partial OCR reuse requires separate explicit selection of new pages')
        if reused:
            for item in reused:
                job=item['job']
                for kind in ['pdf','image']:
                    if file_hash(inside(root,job[kind+'_path']))!=job[kind+'_sha256']:
                        raise ValueError('registered OCR source changed')
            plan=dict(mode='REUSE_REGISTERED_SELECTION',campaign_config=c['parent_ocr_config'],campaign_config_sha256=c['parent_ocr_config_sha256'],reused_pages=reused,new_pages=0)
        else:
            render_prepare(root,selection_path,False)
            campaign=(out/'campaign-config.json').relative_to(root).as_posix()
            plan=dict(mode='NEW_EXPLICIT_SELECTION',campaign_config=campaign,campaign_config_sha256=file_hash(inside(root,campaign)),reused_pages=[],new_pages=len(c['pages']))
        put(planpath,dict(pins=pins,plan=plan))
    stored=read(planpath)
    if stored['pins']!=pins:raise ValueError('OCR controller inputs changed')
    plan=stored['plan']
    if file_hash(inside(root,plan['campaign_config']))!=plan['campaign_config_sha256']:
        raise ValueError('prepared campaign config changed')
    for item in plan['reused_pages']:
        if file_hash(inside(root,item['registration']))!=item['registration_sha256']:
            raise ValueError('reused registration changed')
        for kind in ['pdf','image']:
            job=item['job']
            if file_hash(inside(root,job[kind+'_path']))!=job[kind+'_sha256']:
                raise ValueError('reused source changed')
    with exclusive(out):
        result=coordinate(root,plan['campaign_config'],'run') if execute else dict(status='PREPARED',selected_pages=len(c['pages']),reused_pages=len(plan['reused_pages']),new_planned_pages=plan['new_pages'])
        folder=out/'controller-results'/digest(encoded(result))[:20]
        put(folder/'result.json',result)
    return result


def cli(root):
    p=argparse.ArgumentParser();p.add_argument('--selection',required=True);p.add_argument('--run',action='store_true')
    args=p.parse_args();print(json.dumps(run(root,args.selection,args.run),ensure_ascii=False))
