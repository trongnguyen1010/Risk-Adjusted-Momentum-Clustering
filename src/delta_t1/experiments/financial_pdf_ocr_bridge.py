"""Explicit page-selection bridge into the existing durable OCR campaign."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from .financial_history_documents import put, read
from .financial_user_workflow import exclusive
from .financial_ocr_campaign import coordinate
from ..ingestion.cafef_financial import digest
from ..ingestion.financial_batch_evidence import inside
from .financial_pdf_pipeline import file_hash


def validate_selection(pages, count):
    if not pages or len(pages) > 40 or len(set(pages)) != len(pages):
        raise ValueError('explicit unique selection of at most40 pages required')
    if any(type(p) is not int or not 1 <= p <= count for p in pages):
        raise ValueError('selected physical page outside PDF')


def run(root, selection_path, execute=False):
    from pypdf import PdfReader
    c = read(inside(root, selection_path)); out = inside(root, c['output_root'])
    if c['version'] != 'financial-pdf-ocr-bridge-v1' or c['selection_method'] != 'VISUAL_PAGE_SELECTION_REQUIRES_REVIEW':
        raise ValueError('explicit reviewed page selection required')
    source = inside(root, c['pdf_path'])
    if file_hash(source) != c['pdf_sha256']:
        raise ValueError('selected PDF changed')
    validate_selection(c['pages'], len(PdfReader(source).pages))
    parent = inside(root, c['parent_ocr_config'])
    if file_hash(parent) != c['parent_ocr_config_sha256']:
        raise ValueError('OCR campaign parent changed')
    renderer = shutil.which('pdftoppm')
    if not renderer:
        raise ValueError('pinned renderer unavailable')
    pins = {p:file_hash(inside(root,p)) for p in [selection_path, c['pdf_path'], c['parent_ocr_config'], 'src/delta_t1/experiments/financial_pdf_ocr_bridge.py', 'scripts/financial_pdf_ocr_bridge.py']}
    pins[c['selection_evidence']] = file_hash(inside(root,c['selection_evidence']))
    out.mkdir(parents=True, exist_ok=True)
    with exclusive(out):
        put(out/'contract.json', dict(pins=pins, renderer_sha256=file_hash(Path(renderer)), selected_pages=c['pages'], automatic_acceptance=False))
        jobs=[]
        for page in c['pages']:
            name=c['symbol']+str(c['year'])+'-p'+str(page).zfill(2)
            terminal=out/'rendered'/(name+'.json')
            if terminal.exists():
                image=read(terminal)
                if file_hash(inside(root,image['path'])) != image['sha256']:
                    raise ValueError('rendered image changed')
            else:
                reserve=out/'render-reservations'/(name+'.json')
                if reserve.exists():
                    raise ValueError('interrupted render requires review')
                put(reserve, dict(pdf_sha256=c['pdf_sha256'], pdf_page=page))
                folder=out/'images';folder.mkdir(exist_ok=True)
                prefix=folder/name
                subprocess.run([renderer,'-f',str(page),'-l',str(page),'-scale-to','2200','-singlefile','-png',str(source),str(prefix)],check=True,capture_output=True,timeout=90)
                path=prefix.with_suffix('.png')
                image=dict(path=path.relative_to(root).as_posix(),sha256=file_hash(path))
                put(terminal,image)
            jobs.append(dict(id=name,pdf_path=c['pdf_path'],pdf_sha256=c['pdf_sha256'],pdf_page=page,image_path=image['path'],image_sha256=image['sha256']))
        child=dict(version='financial-selected-ocr-v1',output_root=c['ocr_output_root'],runtime_folder='.tools/financial-ocr',runtime_lock='.tools/financial-ocr/runtime-lock.json',language='vie+eng',max_ocr_pages=40,campaign_anchor=c['batch_created_at'],jobs=jobs)
        child_path=out/'selected-ocr-config.json';put(child_path,child)
        campaign=read(parent)
        campaign['batches'][c['batch_id']]=dict(created_at=c['batch_created_at'],page_cap=1000)
        campaign['runs'].append(dict(config_path=child_path.relative_to(root).as_posix(),config_sha256=file_hash(child_path),batch_id=c['batch_id']))
        campaign_path=out/'campaign-config.json';put(campaign_path,campaign)
        result=coordinate(root,campaign_path.relative_to(root).as_posix(),'run') if execute else dict(status='PREPARED_NOT_EXECUTED',pages=len(jobs))
        put(out/'result.json',result)
        return result


def cli(root):
    p=argparse.ArgumentParser();p.add_argument('--selection',required=True);p.add_argument('--run',action='store_true')
    args=p.parse_args();print(json.dumps(run(root,args.selection,args.run),ensure_ascii=False))
