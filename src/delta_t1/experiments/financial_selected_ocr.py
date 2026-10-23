"""Offline Tesseract CPU on explicit, pinned pages. OCR never accepts facts."""
import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import put, read
from .financial_user_workflow import exclusive


def validate_jobs(jobs, cap):
    if not 1 <= cap <= 40 or len(jobs) > cap:
        raise ValueError('selected-page cap exceeded')
    if len({j['id'] for j in jobs}) != len(jobs):
        raise ValueError('duplicate OCR task')
    if any(n > 40 for n in Counter(j['pdf_sha256'] for j in jobs).values()):
        raise ValueError('per-PDF OCR cap exceeded')
    if any(type(j['pdf_page']) is not int or j['pdf_page'] < 1 for j in jobs):
        raise ValueError('explicit 1-based PDF page required')


def prepare(root, config_path):
    config = read(inside(root, config_path))
    if config.get('version') != 'financial-selected-ocr-v1' or config.get('language') != 'vie+eng':
        raise ValueError('pinned CPU OCR language contract required')
    validate_jobs(config['jobs'], config['max_ocr_pages'])
    if datetime.now(timezone.utc).timestamp() > config['campaign_anchor'] + 259200:
        raise ValueError('inherited 72h deadline expired')
    pins = {}
    for relative in [config_path, config['runtime_lock'], 'src/delta_t1/experiments/financial_selected_ocr.py',
                     'scripts/financial_selected_ocr.py']:
        pins[relative] = digest(inside(root, relative).read_bytes())
    lock = read(inside(root, config['runtime_lock']))
    for relative, sha in lock['files'].items():
        if digest(inside(root, relative).read_bytes()) != sha:
            raise ValueError('OCR runtime/model hash mismatch')
    for job in config['jobs']:
        for name in ['pdf', 'image']:
            path = inside(root, job[name + '_path'])
            sha = digest(path.read_bytes())
            if sha != job[name + '_sha256']:
                raise ValueError('selected OCR source changed: ' + str(path))
            pins[job[name + '_path']] = sha
    out = inside(root, config['output_root']);out.mkdir(parents=True, exist_ok=True)
    put(out / 'contract.json', dict(pins=pins, max_ocr_pages=config['max_ocr_pages'],
        accepted=False, pit_ready=False, engine='TESSERACT_CPU_TESSEROCR', language='vie+eng'))
    return config, out


def run(root, config, out):
    for job in config['jobs']:
        target = out / 'pages' / (job['id'] + '.json')
        if target.exists():
            continue
        reservation = out / 'reservations' / (job['id'] + '.json')
        if reservation.exists():
            raise ValueError('interrupted OCR reservation requires review; no automatic repeat')
        if len(list((out / 'reservations').glob('*.json'))) >= config['max_ocr_pages']:
            raise ValueError('cumulative OCR cap reached')
        put(reservation, dict(job=job, charged_pages=1))
        command = [sys.executable, str(root / 'scripts/financial_selected_ocr.py'), 'worker',
                   '--image', str(inside(root, job['image_path'])), '--runtime', config['runtime_folder']]
        try:
            proc = subprocess.run(command, cwd=root, capture_output=True, timeout=60)
            if proc.returncode:
                raise ValueError(proc.stderr.decode('utf-8', errors='replace')[-1000:])
            put(target, dict(job=job, result=json.loads(proc.stdout), status='OCR_CANDIDATE_ONLY', accepted=False, pit_ready=False))
        except Exception as error:
            put(out / 'errors' / (job['id'] + '.json'), dict(reason=str(error), reservation_retained=True))


def snapshot(root, out, verify):
    paths = [out / 'contract.json']
    for folder in ['pages', 'reservations', 'errors']:
        paths += sorted((out / folder).glob('*.json'))
    inventory = {p.relative_to(out).as_posix(): digest(p.read_bytes()) for p in paths}
    result = out / 'results' / digest(encoded(inventory))[:20]
    summary = dict(status='PARTIAL', successful_ocr_pages=len(list((out / 'pages').glob('*.json'))),
        charged_pages=len(list((out / 'reservations').glob('*.json'))),errors=len(list((out / 'errors').glob('*.json'))),
        new_accepted_facts=0,pit_ready=False,financial_features_allowed=False)
    if verify:
        if read(result / 'manifest.json') != inventory or read(result / 'summary.json') != summary:
            raise ValueError('OCR result changed')
    else:
        put(result / 'manifest.json', inventory);put(result / 'summary.json', summary)
    return dict(summary, status='VERIFIED' if verify else 'PARTIAL', output=result.relative_to(root).as_posix())


def cli(root):
    p=argparse.ArgumentParser();p.add_argument('action',choices=['doctor','run','verify','worker'])
    p.add_argument('--config',default='configs/data/financial_selected_ocr_v1.json')
    p.add_argument('--image');p.add_argument('--runtime');args=p.parse_args()
    try:
        if args.action=='worker':
            runtime=inside(root,args.runtime);sys.path.insert(0,str(runtime/'runtime'))
            import tesserocr
            from PIL import Image
            with tesserocr.PyTessBaseAPI(path=str(runtime),lang='vie+eng') as api:
                api.SetImage(Image.open(args.image));text=api.GetUTF8Text()
                print(json.dumps(dict(text=text,tsv=api.GetTSVText(0),confidence=api.MeanTextConf(),
                    engine_version=tesserocr.tesseract_version()),ensure_ascii=True))
            return
        config,out=prepare(root,args.config)
        with exclusive(out):
            if args.action=='run':run(root,config,out)
            print(json.dumps(snapshot(root,out,args.action=='verify'),ensure_ascii=False,indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED',reason=str(error)),ensure_ascii=False));raise SystemExit(2)
