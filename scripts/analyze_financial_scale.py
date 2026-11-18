"""Offline scale diagnostics and isolated bounded PDF text workers."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
sys.stdout.reconfigure(encoding='utf8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--collection');p.add_argument('--output')
    p.add_argument('--price-config',default='configs/data/financial_three_symbol_pilot_v3.json')
    p.add_argument('--worker-pdf');p.add_argument('--worker-output');p.add_argument('--max-pages',type=int)
    a=p.parse_args()
    if a.worker_pdf:
        import pypdf
        from delta_t1.ingestion.cafef_financial import encoded,immutable_write
        reader=pypdf.PdfReader(a.worker_pdf)
        if reader.is_encrypted:raise ValueError('encrypted document requires review')
        if not a.max_pages or a.max_pages>250:raise ValueError('bounded pages required')
        pages=[dict(pdf_page=i+1,text=reader.pages[i].extract_text() or '') for i in range(min(len(reader.pages),a.max_pages))]
        immutable_write(Path(a.worker_output),encoded(dict(status='COMPLETE' if len(pages)==len(reader.pages) else 'PARTIAL_PAGE_BUDGET',
            total_pages=len(reader.pages),pages=pages,pypdf_version=pypdf.__version__)))
    else:
        if not a.collection or not a.output:p.error('--collection and --output required')
        from delta_t1.experiments.financial_scale_analysis import analyze
        r=analyze(ROOT,a.collection,a.output,a.price_config,Path(__file__).resolve())
        print(json.dumps(r,ensure_ascii=False,indent=2))
