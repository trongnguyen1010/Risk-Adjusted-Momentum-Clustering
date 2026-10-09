"""Bounded offline note-page OCR; reuse the verified main-page index."""
import json
import subprocess
from pathlib import Path
from .cafef_financial import digest, encoded, immutable_write
from .financial_documents import verify_inventory
from .financial_pdf_evidence import validate_pdf

def selections(index, start_page=19, max_total_pages=400):
    if type(start_page) is not int or start_page < 1:
        raise ValueError('invalid starting page')
    if type(max_total_pages) is not int or not 1 <= max_total_pages <= 400:
        raise ValueError('invalid total page cap')
    docs = index['documents']
    if not 1 <= len(docs) <= 8 or index.get('financial_features_allowed') is not False:
        raise ValueError('bounded evidence input required')
    result = []
    for d in docs:
        total = d['total_pages']
        if type(total) is not int or not start_page <= total <= 120 or d['symbol'] != 'FPT' or d['quarter'] != 0:
            raise ValueError('outside FPT annual note scope')
        result.append(dict(d, first_page=start_page, last_page=total, pages_selected=total-start_page+1))
    if sum(d['pages_selected'] for d in result) > max_total_pages:
        raise ValueError('page budget exceeded')
    return result

def extract(index_run, output, ocr_script):
    run = Path(index_run).resolve(); verify_inventory(run)
    docs = selections(json.loads((run/'index.json').read_bytes()))
    for d in docs:
        validate_pdf(d['path'], d['sha256'])
    out = Path(output).resolve(); out.mkdir(parents=True, exist_ok=False)
    for d in docs:
        pdf = Path(d['path']); folder = out/pdf.stem; folder.mkdir()
        subprocess.run(['pdftoppm','-f',str(d['first_page']),'-l',str(d['last_page']),
                        '-scale-to','2200','-png',str(pdf),str(folder/'page')],check=True,timeout=300)
        subprocess.run(['powershell.exe','-NoProfile','-File',str(Path(ocr_script).resolve()),
                        '-ImageDirectory',str(folder)],check=True,timeout=600)
        records=list(folder.glob('*.ocr.json'))
        if len(records) != d['pages_selected']:
            raise ValueError('incomplete OCR page inventory')
        for record in records:
            r=json.loads(record.read_bytes())
            if digest(record.with_name(record.name.replace('.ocr.json','.png')).read_bytes()) != r['image_sha256']:
                raise ValueError('OCR image hash mismatch')
        print(f"{d['symbol']} {d['year']}: {len(records)} new note pages",flush=True)
    result=dict(documents=docs,new_ocr_pages=sum(d['pages_selected'] for d in docs),
                input_manifest_sha256=digest((run/'manifest.json').read_bytes()),
                financial_features_allowed=False,financial_pit_gate='NOT_READY',
                validation_status='OCR_REQUIRES_VISUAL_VERIFICATION')
    immutable_write(out/'index.json',encoded(result))
    immutable_write(out/'extractor.py',Path(__file__).read_bytes())
    immutable_write(out/'ocr_script.ps1',Path(ocr_script).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.relative_to(out).as_posix():digest(p.read_bytes())
                      for p in sorted(out.rglob('*')) if p.is_file()}}))
    return result
