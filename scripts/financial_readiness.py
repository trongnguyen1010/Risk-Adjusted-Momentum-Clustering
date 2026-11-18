"""User-operated frozen50 acquisition, OCR, readiness and reference review."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments import financial_user_workflow as flow


def doctor(config):
    c = flow.load(ROOT / config)
    branch = subprocess.run(['git', 'branch', '--show-current'], cwd=ROOT, text=True,
                            capture_output=True, check=True).stdout.strip()
    members = flow.load(ROOT / c['trial_run'] / 'plan.json')['members']
    flow.validate(c, members)
    for name, sha in c['input_pins'].items():
        flow.pin(ROOT, name, sha)
    ocr_check = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
        'Add-Type -AssemblyName System.Runtime.WindowsRuntime; '
        '[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] > $null; '
        '[Windows.Globalization.Language,Windows.Foundation,ContentType=WindowsRuntime] > $null; '
        'if ($null -eq [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))) {exit 2}'],
        capture_output=True, timeout=30) if shutil.which('powershell.exe') else None
    checks = dict(cafef_branch=branch == c['expected_branch'], pypdf=importlib.util.find_spec('pypdf') is not None,
                  pdftoppm=bool(shutil.which('pdftoppm')), windows_ocr=bool(ocr_check and ocr_check.returncode == 0),
                  free_disk=shutil.disk_usage(ROOT).free >= c['min_free_disk_bytes'])
    return dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks, branch=branch,
                python=sys.executable, **flow.CLOSED)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['doctor', 'plan', 'audit', 'acquire', 'extract', 'run', 'template', 'review', 'verify'])
    p.add_argument('--config', default='configs/data/financial_user_workflow50_v1.json')
    p.add_argument('--run', default='data/financial/user_workflow50_v1')
    p.add_argument('--execute-network', action='store_true')
    p.add_argument('--limit', type=int)
    p.add_argument('--full-ocr', action='store_true'); p.add_argument('--retry-failed', action='store_true')
    p.add_argument('--symbols'); p.add_argument('--symbol'); p.add_argument('--pdf-sha'); p.add_argument('--review-file')
    a = p.parse_args(); worker = ROOT / 'scripts/analyze_financial_scale.py'
    if a.action == 'doctor':
        r = doctor(a.config)
    elif a.action == 'plan':
        r = flow.make_plan(ROOT, a.config, a.run)
        r['assessment'] = flow.report(ROOT, a.run)
    elif a.action == 'audit':
        r = flow.report(ROOT, a.run)
    elif a.action == 'acquire':
        r = flow.acquire(ROOT, a.run, a.execute_network, a.limit or 10)
        r['assessment'] = flow.report(ROOT, a.run)
    elif a.action == 'extract':
        r = flow.extract(ROOT, a.run, a.limit or 8, a.full_ocr, worker,
                         a.symbols.split(',') if a.symbols else None, a.retry_failed)
        r['assessment'] = flow.report(ROOT, a.run)
    elif a.action == 'run':
        r = {}
        try:
            r['acquisition'] = flow.acquire(ROOT, a.run, a.execute_network, 300)
            r['extraction'] = (dict(status='SKIPPED_GLOBAL_STOP') if r['acquisition']['status'] == 'GLOBAL_STOP' else
                flow.extract(ROOT, a.run, a.limit or 8, a.full_ocr, worker,
                a.symbols.split(',') if a.symbols else None, a.retry_failed))
        finally:
            r['assessment'] = flow.report(ROOT, a.run)
            print(json.dumps(r, ensure_ascii=False, indent=2), flush=True)
        return 3 if r['acquisition']['status'] == 'GLOBAL_STOP' else 0
    elif a.action == 'template':
        if not a.symbol:
            p.error('--symbol required')
        r = flow.template(ROOT, a.run, a.symbol, pdf_sha=a.pdf_sha)
    elif a.action == 'review':
        if not a.review_file:
            p.error('--review-file required')
        r = flow.review(ROOT, a.run, a.review_file)
        r['assessment'] = flow.report(ROOT, a.run)
    else:
        r = flow.verify(ROOT, a.run)
    print(json.dumps(r, ensure_ascii=False, indent=2), flush=True)
    return 2 if r.get('status') == 'FAIL' else 3 if r.get('status') == 'GLOBAL_STOP' else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='ERROR', error=str(exc)), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
