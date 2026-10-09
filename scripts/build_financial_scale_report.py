"""Export measured 50-symbol assessment and scale costs without calculating features."""
import csv,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory

def load(path):return json.loads((ROOT/path).read_bytes())
if __name__=='__main__':
    output=ROOT/'artifacts/reports/financial-scale-validation50-v1';output.mkdir(parents=True,exist_ok=True)
    probe='data/financial/scale_probe50_20261008_v1';analysis='data/financial/scale_analysis50_20261008_v1'
    ocr='data/financial/scale_ocr4_20261008_v1';review='data/financial/scale_review4_20261008_v1'
    supplement='data/financial/issuer_supplement_v1/run-2026-10-08T093755.974487-0000-f3dbdc60'
    plc='data/financial/issuer_supplement_v1/run-2026-10-08T101058.771561-0000-7684a622'
    runs=[probe,analysis,ocr,review,supplement,plc]
    for run in runs:verify_inventory(ROOT/run)
    p=load(probe+'/results.json');a=load(analysis+'/results.json');o=load(ocr+'/index.json');r=load(review+'/results.json')
    refs=load(review+'/references.json');qa=load(review+'/qa.json');extra=load(supplement+'/inventory.json')
    rows=load(analysis+'/per-symbol.json');reference_by_symbol={x['symbol']:x for x in refs}
    for row in rows:
        sym=row['symbol'];x=reference_by_symbol.get(sym)
        row.update(new_ocr_pages=sum(len(d['pages']) for d in o['documents'] if d['symbol']==sym),
            new_reviewed_reference_cells=2 if x else 0,new_reviewed_annual_pe_arithmetic=1 if x else 0,
            reviewed_z_reference=x['z_reference']['em_z_double_prime_reference'] if x and x['z_reference'] else None,
            reviewed_basic_eps=x['disclosed_basic_eps_reference']['value'] if x and x['disclosed_basic_eps_reference'] else None,
            usable_from_date=x['usable_from_date'] if x else None,
            date_pit_status=x['date_pit_status'] if x else 'NOT_REVIEWED_IN_THIS_WAVE',
            prior_reviewed_symbol=sym in ['FPT','ACV'],production_ready=False,
            scope_fiscal_exception='FY_END_2025_06_30_NOT_CALENDAR_ANNUAL' if sym=='SLS' else
                'STANDALONE_DISCLOSURE_CHECKBOX_VERIFIED_SECTOR_TEMPLATE_REQUIRED' if sym=='SHS' else
                'ANNUAL_TITLE_UNLABELED_SCOPE_REVIEW_PENDING' if sym in ['HCM','VND'] else
                'UNLABELED_ANNUAL_PDF_404' if sym=='SCS' else
                'CAFEF_ANNUAL_LISTING_GAP_ISSUER_CHALLENGE_STOP' if sym=='PLC' else None)
    immutable_write(output/'per-symbol.json',encoded(rows))
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    immutable_write(output/'per-symbol.csv',stream.getvalue().encode('utf-8-sig'))
    immutable_write(output/'new-references.json',encoded(refs));immutable_write(output/'field-qa.json',encoded(qa))
    recovery=extra['requests']+load(plc+'/inventory.json')['requests']
    immutable_write(output/'source-exceptions.json',encoded(recovery))
    costs=dict(probe_physical_attempts=p['transport_state']['transport_attempts'],
        probe_logical_network_requests=p['transport_state']['logical_requests'],
        probe_downloaded_bytes=p['transport_state']['downloaded_bytes'],probe_pdf_attempts=p['transport_state']['pdf_download_attempts'],
        cache_records=p['acquisition_counts']['CACHED'],text_pages=a['text_pages_used'],ocr_pages=o['ocr_pages'],ocr_seconds=o['seconds'],
        ocr_statement_attempts=r['ocr_statement_attempts'],ocr_matches=r['ocr_matching_cells'],
        review_method='AUTOMATED_RENDER_OCR_AND_CANDIDATE_PARSER_PLUS_HUMAN_VISUAL_TRANSCRIPTION; NOT_FULL_AUTO',
        manual_review_seconds=None,manual_review_cost='NOT_INSTRUMENTED; DO_NOT_EXTRAPOLATE_TO_1000_SYMBOLS',
        run_storage=[dict(run=run,files=len([p for p in (ROOT/run).rglob('*') if p.is_file()]),
            bytes=sum(p.stat().st_size for p in (ROOT/run).rglob('*') if p.is_file())) for run in runs])
    immutable_write(output/'operating-cost.json',encoded(costs))
    immutable_write(output/'lineage.json',encoded(dict(manifests={run+'/manifest.json':digest((ROOT/run/'manifest.json').read_bytes()) for run in runs},
        configs=['configs/data/financial_scale_probe_v1.json','configs/data/financial_scale_ocr_v1.json','configs/data/financial_scale_review_v1.json',
                 'configs/data/financial_scale_exception_sources_v1.json','configs/data/financial_scale_plc_recovery_v1.json'],
        report_builder_sha256=digest(Path(__file__).read_bytes()))))
    # Keep only eight inspected exception headers, not copies of the OCR corpus.
    evidence=output/'header-evidence';evidence.mkdir(exist_ok=False)
    for p in sorted((ROOT/'.tmp/financial-source-review').glob('recovery-*.png')):
        immutable_write(evidence/p.name,p.read_bytes())
    semantic=[]
    for sym,pages in [('PHP',[18]),('VCS',[15]),('VEA',[17]),('PAN',[7])]:
        d=next(d for d in o['documents'] if d['symbol']==sym and d['year']==2025)
        semantic.append(dict(symbol=sym,pdf_sha256=d['pdf_sha256'],review='VAS/consolidated scope and annual period visual context',
                             pages=[x for x in d['pages'] if x['pdf_page'] in pages]))
    immutable_write(output/'semantic-context.json',encoded(semantic))
    print(json.dumps(dict(symbols=len(rows),new_reference_cells=r['numeric_reference_cells'],date_covered_symbols=r['date_covered_symbols'],costs=costs),ensure_ascii=False))
