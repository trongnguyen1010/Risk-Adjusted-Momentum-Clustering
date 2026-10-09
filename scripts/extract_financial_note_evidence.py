"""OCR remaining FPT annual note pages from a verified existing PDF index."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_note_evidence import extract
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index-run',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data'):raise ValueError('output must be under data')
    r=extract(ROOT/a.index_run,out,ROOT/'scripts/ocr_financial_pages.ps1')
    print(json.dumps({'new_ocr_pages':r['new_ocr_pages']}))
