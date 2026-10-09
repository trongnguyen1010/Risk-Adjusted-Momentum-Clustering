"""Bounded PDF text + explicitly selected scan pages; preserve source coordinates."""
import json
import shutil
import subprocess
import time
from pathlib import Path

from .cafef_financial import digest, encoded, immutable_write
from .financial_batch_evidence import VERSION, inside, task_key
from .financial_table_parser import extract_cell, compare_candidate


def extract(checkpoints, document, script, command=subprocess.run):
    acquired, c = document['acquisition'], checkpoints.c
    if acquired['status'] != 'COMPLETE':
        return dict(status=acquired['status'], payload={})
    raw = acquired['payload']
    pdf = inside(checkpoints.root, raw['path'], 'data')
    if digest(pdf.read_bytes()) != raw['sha256'] or not pdf.read_bytes().startswith(b'%PDF'):
        raise ValueError('PDF source integrity mismatch')
    try:
        import pypdf
    except ImportError:
        return dict(status='DEFERRED_DEPENDENCY', payload={}, error='Install pinned pypdf dependency')
    selected = document.get('ocr_pages', [])
    templates = document.get('cell_templates', [])
    renderer = shutil.which('pdftoppm')
    request = dict(version=VERSION, operation='USER_PDF_TEXT_SELECTED_OCR', pdf_sha256=raw['sha256'],
                   ocr_pages=selected, cell_templates=templates, pypdf=pypdf.__version__,
                   max_pdf_pages=c['max_pdf_pages'], extractor_sha256=digest(Path(__file__).read_bytes()),
                   script_sha256=digest(Path(script).read_bytes()),
                   renderer_sha256=digest(Path(renderer).read_bytes()) if renderer else 'UNAVAILABLE')
    cached = checkpoints.cached_result(request)
    if cached:
        return cached
    folder = checkpoints.output / 'tasks' / task_key(request)
    pages, ocr_pages, deferred, cell_candidates = [], [], [], []
    try:
        reader = pypdf.PdfReader(pdf)
        if reader.is_encrypted:
            raise ValueError('encrypted PDF requires explicit review')
        count = len(reader.pages)
        if any(n > count for n in selected):
            raise ValueError('selected OCR page exceeds actual PDF length')
        if count > c['max_pdf_pages'] or checkpoints.metrics['text_pages'] + count > c['max_text_pages']:
            return checkpoints.commit(request, 'DEFERRED_TEXT_PAGE_BUDGET', dict(total_pdf_pages=count))
        if time.monotonic() - checkpoints.started >= c['max_seconds']:
            return checkpoints.commit(request, 'DEFERRED_TIME_BUDGET', {})
        folder.mkdir(parents=True, exist_ok=False)
        for n, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ''
            file = folder / 'text' / f'page-{n:03d}.txt'
            immutable_write(file, text.encode('utf8'))
            pages.append(dict(pdf_page=n, text_path=file.relative_to(checkpoints.root).as_posix(),
                              text_sha256=digest(file.read_bytes()), text_characters=len(text), low_text=len(text.strip()) < 80))
        checkpoints.metrics['text_pages'] += count
        for n in selected:
            if (not renderer or not shutil.which('powershell.exe')
                    or checkpoints.metrics['ocr_pages'] >= c['max_ocr_pages']
                    or time.monotonic() - checkpoints.started >= c['max_seconds']):
                deferred.append(n)
                continue
            images = folder / f'ocr-{n:03d}'
            images.mkdir()
            checkpoints.metrics['ocr_pages'] += 1
            command([renderer, '-f', str(n), '-l', str(n), '-scale-to', '2200', '-png', str(pdf), str(images/'page')],
                    check=True, timeout=90, capture_output=True)
            command(['powershell.exe', '-NoProfile', '-File', str(script), '-ImageDirectory', str(images)],
                    check=True, timeout=90, capture_output=True)
            records = list(images.glob('*.ocr.json'))
            if len(records) != 1:
                raise ValueError('OCR must produce exactly one page record')
            record = json.loads(records[0].read_bytes())
            image = records[0].with_name(records[0].name.replace('.ocr.json', '.png'))
            if digest(image.read_bytes()) != record['image_sha256']:
                raise ValueError('OCR image checksum mismatch')
            ocr_pages.append(dict(pdf_page=n, image_path=image.relative_to(checkpoints.root).as_posix(),
                image_sha256=record['image_sha256'], ocr_path=records[0].relative_to(checkpoints.root).as_posix(),
                ocr_sha256=digest(records[0].read_bytes())))
            for spec in templates:
                if spec['pdf_page'] == n:
                    value = extract_cell(record, spec, spec['year'])
                    cell_candidates.append(dict(spec=spec, candidate=value, pdf_sha256=raw['sha256'],
                        image_sha256=record['image_sha256'], pdf_page=n,
                        reference_qa=compare_candidate(value,spec['reference_value']) if 'reference_value' in spec else None,
                        reference_policy='USER_SUPPLIED_REFERENCE_NOT_PRODUCTION_ACCEPTANCE'))
        payload = dict(pdf_sha256=raw['sha256'], total_pdf_pages=count, pages=pages, ocr_pages=ocr_pages,
            deferred_ocr_pages=deferred, low_text_pages=[p['pdf_page'] for p in pages if p['low_text']],
            cell_candidates=cell_candidates, extraction_scope='ALL_TEXT_AND_EXPLICIT_SELECTED_OCR',
            acceptance='CANDIDATE_REQUIRES_SEMANTIC_AND_PUBLICATION_REVIEW')
        return checkpoints.commit(request, 'PARTIAL_OCR_DEFERRED' if deferred else 'COMPLETE', payload, folder)
    except (ValueError, OSError, subprocess.SubprocessError, pypdf.errors.PyPdfError) as exc:
        detail = dict(error_type=type(exc).__name__, message=str(exc))
        if isinstance(exc, subprocess.CalledProcessError):
            detail.update(stdout=(exc.stdout or b'').decode('utf8', errors='replace')[-4000:],
                          stderr=(exc.stderr or b'').decode('utf8', errors='replace')[-4000:])
        return checkpoints.commit(request, 'FAILED_PDF_EXTRACTION', dict(pages=pages, ocr_pages=ocr_pages,
            deferred_ocr_pages=deferred, diagnostic=detail), folder, str(exc))
