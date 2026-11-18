"""Explicit bounded PDF page ranges, including interim statements; never infer period."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.financial_pdf_evidence import validate_pdf

def grouped_ranges(documents):
    """Group disjoint ranges without rendering employee-list pages in between."""
    groups = {}
    for d in documents:
        key = Path(d['pdf_path']).stem
        identity = (str(Path(d['pdf_path']).resolve()), d['pdf_sha256'])
        if key in groups and groups[key]['identity'] != identity:
            raise ValueError('PDF filename collision')
        group = groups.setdefault(key, {'identity': identity, 'ranges': [], 'pages': set()})
        pages = set(range(d['first_page'], d['last_page'] + 1))
        if group['pages'] & pages:
            raise ValueError('overlapping page ranges')
        group['pages'].update(pages)
        group['ranges'].append(d)
    return groups

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();c=json.loads((ROOT/a.config).read_bytes());out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data') or c.get('financial_features_allowed') is not False:
        raise ValueError('bounded raw evidence only')
    verify_inventory(ROOT/c['source_run'])
    if not 1<=len(c['documents'])<=4 or sum(d['last_page']-d['first_page']+1 for d in c['documents'])>120:
        raise ValueError('OCR budget exceeded')
    for d in c['documents']:
        if not 1<=d['first_page']<=d['last_page']<=120:raise ValueError('invalid page range')
        validate_pdf(ROOT/d['pdf_path'],d['pdf_sha256'])
    groups = grouped_ranges(c['documents'])
    out.mkdir(parents=True,exist_ok=False)
    for name, group in groups.items():
        folder=out/name;folder.mkdir()
        for d in group['ranges']:
            pdf=ROOT/d['pdf_path']
            subprocess.run(['pdftoppm','-f',str(d['first_page']),'-l',str(d['last_page']),'-scale-to','2200','-png',str(pdf),str(folder/'page')],check=True,timeout=300)
        subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'scripts/ocr_financial_pages.ps1'),'-ImageDirectory',str(folder)],check=True,timeout=600)
        records=list(folder.glob('*.ocr.json'))
        if len(records)!=len(group['pages']):raise ValueError('incomplete OCR')
        for record in records:
            data=json.loads(record.read_bytes())
            if digest(record.with_name(record.name.replace('.ocr.json','.png')).read_bytes())!=data['image_sha256']:
                raise ValueError('image mismatch')
        print(pdf.name,len(records),flush=True)
    immutable_write(out/'index.json',encoded(c));immutable_write(out/'extractor.py',Path(__file__).read_bytes())
    immutable_write(out/'ocr_script.ps1',(ROOT/'scripts/ocr_financial_pages.ps1').read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.relative_to(out).as_posix():digest(p.read_bytes()) for p in out.rglob('*') if p.is_file()}}))
