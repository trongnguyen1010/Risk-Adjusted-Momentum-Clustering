"""Create a NEW pinned bounded batch config from reviewed pilot raw evidence."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_batch_evidence import GATES, VERSION, validate
from delta_t1.ingestion.financial_documents import verify_inventory


def build(output):
    source=ROOT/'data/financial/document_vintages_v1/run-2026-10-02T191138.893586-0000-af898b2f'
    runs=[ROOT/'data/financial/issuer_supplement_v1'/n for n in [
        'run-2026-10-03T045409.716988-0000-516cea03',
        'run-2026-10-04T164224.202400-0000-380756e5']]
    seeds, docs=[] , []
    for run in runs+[source]:
        verify_inventory(run)
        inv=json.loads((run/'inventory.json').read_bytes())
        rows=inv.get('requests',inv.get('documents',[]))
        for r in rows:
            if r.get('status') != 'DOWNLOADED' or r.get('year') != 2025 or r.get('symbol') not in ['FPT','VNM','PVS','ACV']:
                continue
            if r.get('kind','pdf')!='pdf' or r.get('quarter',0)!=0:
                continue
            url=r.get('url',r.get('provider_report',{}).get('Link'))
            pdf=Path(r['path']); pdf=pdf if pdf.is_absolute() else run/pdf
            relative=str(pdf.relative_to(ROOT)).replace('\\','/')
            seeds.append(dict(url=url,kind='pdf',run=run.relative_to(ROOT).as_posix(),
                manifest_sha256=digest((run/'manifest.json').read_bytes()),path=relative,sha256=r['sha256']))
            docs.append(dict(symbol=r['symbol'],year=2025,quarter=0,url=url))
    if sorted(d['symbol'] for d in docs)!=['ACV','FPT','PVS','VNM']:
        raise ValueError('exact four annual seed PDFs required')
    candidates=['HPG','DGC','MWG','REE','GMD','VHC']
    blockers=ROOT/'artifacts/reports/financial-three-symbol-pilot-v1/blockers.json'
    c=dict(version=VERSION, cache_epoch='2026-10-05-engineering-candidates-v1',
        symbols=['FPT','VNM','PVS','ACV']+candidates,years=[2025],
        approved_hosts=['cafef.vn','cafefnew.mediacdn.vn','fpt.com','static2.vietstock.vn'],
        discovery=[dict(symbol=s,year=2025) for s in candidates],documents=docs,cache_records=seeds,
        max_logical_requests=18,max_pdf_downloads=12,max_documents=20,max_bytes=50_000_000,
        max_total_bytes=200_000_000,max_pdf_pages=250,max_text_pages=1500,
        max_ocr_pages=32,ocr_first_pages=4,max_seconds=1800,
        note_search_terms=dict(EPS=['lãi cơ bản','earnings per share','weighted average'],
            DEBT=['vay','borrowings','current portion'],PPE=['khấu hao','depreciation'],
            EQUITY=['vốn chủ sở hữu','equity','cổ phiếu'],PUBLICATION=['công bố','publication']),
        known_blockers=dict(path=blockers.relative_to(ROOT).as_posix(),sha256=digest(blockers.read_bytes())),
        reference_jobs=[dict(adapter=adapter,config=name,config_sha256=digest((ROOT/name).read_bytes()))
            for adapter,name in [('THREE_SYMBOL_2025','configs/data/financial_three_symbol_pilot_v3.json'),
                                 ('FPT_2025','configs/data/financial_fpt_acceptance_v1.json')]],
        **GATES)
    names=['src/delta_t1/ingestion/financial_batch_evidence.py','src/delta_t1/experiments/financial_batch_flow.py',
           'src/delta_t1/ingestion/cafef_financial_detail.py','src/delta_t1/ingestion/financial_documents.py',
           'src/delta_t1/ingestion/cafef_financial.py','scripts/ocr_financial_pages.ps1',
           'src/delta_t1/experiments/financial_fpt_acceptance.py','src/delta_t1/features/financial_equity_reference.py']
    pilot=json.loads((ROOT/'configs/data/financial_three_symbol_pilot_v3.json').read_bytes())
    c['code_sha256']={n:digest((ROOT/n).read_bytes()) for n in names}
    c['code_sha256'].update(pilot['calculation_source_sha256'])
    c['evidence_pins']={blockers.relative_to(ROOT).as_posix():digest(blockers.read_bytes())}
    acceptance=json.loads((ROOT/'configs/data/financial_fpt_acceptance_v1.json').read_bytes())
    c['evidence_pins'].update({acceptance[k]+'/manifest.json':v for k,v in acceptance['input_manifest_sha256'].items()})
    validate(c)
    immutable_write(ROOT/output,encoded(c))
    print(json.dumps(dict(config=output,symbols=len(c['symbols']),seed_documents=len(docs))))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    build(p.parse_args().output)
