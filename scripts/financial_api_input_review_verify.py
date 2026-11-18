"""Verify completed offline review, then publish its documentation handoff."""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'artifacts/reports/financial-api-input-review1522-v1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def verify():
    ref=json.loads((REPORT/'result-ref.json').read_bytes())
    result=(ROOT/ref['path']).resolve()
    if not result.is_relative_to(ROOT/'data/financial/history_api_input_review1522_v1/jobs'):
        raise ValueError('result outside expected job')
    assert sha(result/'manifest.json')==ref['manifest_sha256']
    manifest=json.loads((result/'manifest.json').read_bytes())
    for name,expected in manifest.items():
        assert sha(result/name)==expected,name
    for name,expected in json.loads((result/'input-pins.json').read_bytes()).items():
        assert sha(ROOT/name)==expected,name
    summary=json.loads((result/'summary.json').read_bytes())
    assert summary['symbols']==1522 and summary['annual_tasks']==118716
    assert summary['new_accepted_metric_rows']==summary['verified_full10y_symbols']==0
    assert summary['network_requests']==summary['pdf_downloads']==summary['ocr_pages']==0
    assert not summary['pdf_download_plan_created'] and not summary['accepted']
    rows=list(csv.DictReader((result/'symbols-readiness.csv').open(encoding='utf-8',newline='')))
    assert len(rows)==len({r['symbol'] for r in rows})==1522
    with (result/'metric-tasks.csv').open(encoding='utf-8',newline='') as stream:
        count=0
        for row in csv.DictReader(stream):
            assert not row['value'] and row['accepted']=='False'
            count+=1
        assert count==118716
    zrows=zsymbols=0;symbols=set()
    with (result/'api-arithmetic-diagnostics.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            assert row['accepted']==row['strict_pit_ready']==row['financial_features_allowed']=='False'
            if row['family']=='Z_SCORE' and row['value']:
                zrows+=1;symbols.add(row['symbol'])
            elif row['family']=='F_SCORE':
                assert not row['value']
    assert zrows==summary['conditional_z_arithmetic_rows'] and len(symbols)==summary['conditional_z_symbols']
    for item in json.loads((result/'symbol-manifests.json').read_bytes()).values():
        path=ROOT/item['path'];assert sha(path)==item['sha256']
        for name,expected in json.loads(path.read_bytes()).items():
            assert sha(path.parent/name)==expected
    for target in re.findall(r'\]\(([^)]+)\)',(REPORT/'report.md').read_text(encoding='utf-8')):
        if '://' not in target:
            assert (REPORT/target.split('#')[0]).exists(),target
    verification=dict(status='PASS_OFFLINE_OUTPUT_VERIFICATION',at=datetime.now(timezone.utc).isoformat(),
        result=ref,symbols=1522,tasks=118716,network_requests=0,pdf_downloads=0,ocr_pages=0,
        accepted_metric_rows_added=0,reference_results_preserved=True)
    (REPORT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return summary


def update_docs(summary):
    status=(f"Đã hoàn tất review raw annual cho 1.522 mã / 118.716 tasks; mapping "
            f"{summary['old_alias_fields']}→{summary['expanded_alias_fields']} fields. "
            f"Có {summary['conditional_z_arithmetic_rows']:,} dòng Z có điều kiện cho {summary['conditional_z_symbols']} mã, "
            "chỉ là arithmetic diagnostics, chưa được chấp nhận thành reference. "
            "Giữ 11 mã có reference reviewed / 5 mã đủ6 tại một cohort / 0 mã đủ bộ2016–2025. "
            "Không PDF/OCR mới; financial/PIT/M3 vẫn PARTIAL.")
    for filename,prefix in [('README.md','docs/'),('docs/README.md',''),('docs/CURRENT_STATUS.md',''),('docs/PROJECT_MAP.md','')]:
        path=ROOT/filename;lines=path.read_text(encoding='utf-8').splitlines()
        for i,line in enumerate(lines):
            if line.startswith('**Ưu tiên hiện tại'):
                lines[i]=f'**Ưu tiên hiện tại — API input review (22/10/2026):** [Execution34]({prefix}crawl/FINANCIAL_HISTORY_PIT_PLAN.md#34-expanded-api-input-review1522-22102026). '+status
                break
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    plan=ROOT/'docs/crawl/FINANCIAL_HISTORY_PIT_PLAN.md'
    text=plan.read_text(encoding='utf-8')
    marker='<!-- API_INPUT_REVIEW34_RESULT -->'
    final='\n'+marker+'\n\nKết quả cuối: '+status+'\n\nOutput hash/manifest, 1.522 mã unique, 118.716 tasks, no-acceptance/no-PDF guards và report links đã kiểm PASS. Xem `artifacts/reports/financial-api-input-review1522-v1/verification.json`.\n'
    if marker in text:text=text.split(marker)[0].rstrip()+'\n'
    plan.write_text(text+final,encoding='utf-8')
    return status


if __name__=='__main__':
    summary=verify()
    print(update_docs(summary))
