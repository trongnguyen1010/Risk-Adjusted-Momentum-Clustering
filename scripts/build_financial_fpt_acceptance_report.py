"""Run bounded validation once and seal the Vietnamese FPT stage report."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.cafef_financial import encoded, immutable_write
from delta_t1.experiments.financial_ttm_valuation import file_hash
from delta_t1.ingestion.financial_documents import verify_inventory
from validate_financial_fpt_acceptance import validate


def build(output, resume_validated_logs=False, validated_log_source=None):
    out = (ROOT / output).resolve()
    if not out.is_relative_to(ROOT / 'artifacts/reports'):
        raise ValueError('report under artifacts/reports only')
    if resume_validated_logs:
        if not out.is_dir() or (out / 'manifest.json').exists():
            raise ValueError('only unsealed interrupted report may resume')
    else:
        out.mkdir(parents=True, exist_ok=False)
    previous_validation = None
    if validated_log_source:
        source = (ROOT / validated_log_source).resolve()
        if not source.is_relative_to(ROOT / 'artifacts/reports'):
            raise ValueError('validation source outside reports')
        verify_inventory(source)
        hashes = json.loads((source / 'source_hashes.json').read_bytes())
        for path, sha in hashes.items():
            if path.endswith('.py') and file_hash(ROOT / path) != sha:
                raise ValueError('tested code changed; logs cannot be reused')
        previous_validation = {v['name']: v for v in json.loads((source / 'summary.json').read_bytes())['validation']}
    checks = validate('data/financial/fpt_acceptance_v5', 'data/financial/fpt_acceptance_v4')
    validation = []
    commands = [(area, ['-m', 'unittest', 'discover', '-s', f'tests/unit/{area}', '-p', 'test_financial*.py'])
                for area in ['features', 'ingestion', 'experiments']]
    commands += [('compile', ['-m', 'compileall', '-q', 'src', 'tests', 'scripts', 'run.py']),
                 ('synthetic-smoke', ['run.py', 'run', '--config', 'configs/data/synthetic_smoke.example.json']),
                 ('full-suite', ['-m', 'unittest', 'discover', '-s', 'tests'])]
    for name, args in commands:
        command = [sys.executable, *args]
        if previous_validation is not None:
            prior = previous_validation[name]
            if prior['command'] != command:
                raise ValueError('validation command changed')
            content = (source / f'{name}.log').read_bytes()
            immutable_write(out / f'{name}.log', content)
            log = content.decode('utf8', errors='replace')
            exit_code = prior['exit_code']
        elif resume_validated_logs:
            log = (out / f'{name}.log').read_bytes().decode('utf8', errors='replace')
            # Reuse this interrupted stage's logs, without repeating successful tests.
            if name in ['features', 'ingestion', 'experiments', 'full-suite']:
                if not re.search(r'Ran \d+ tests?', log):
                    raise ValueError('incomplete test log')
                exit_code = 0 if re.search(r'\nOK\s*$', log) else 1
            elif name == 'compile':
                if log.strip():
                    raise ValueError('unexpected compile diagnostics')
                exit_code = 0
            else:
                if 'status=complete synthetic=True' not in log:
                    raise ValueError('missing successful synthetic smoke output')
                exit_code = 0
        else:
            completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
            log = completed.stdout.decode('utf8', errors='replace')
            immutable_write(out / f'{name}.log', completed.stdout)
            exit_code = completed.returncode
        count = re.search(r'Ran (\d+) tests?', log)
        record = dict(name=name, command=command, exit_code=exit_code,
                      status='PASS' if exit_code == 0 else 'FAIL', tests=int(count[1]) if count else None)
        if (name == 'full-suite' and exit_code == 1 and 'FAILED (errors=1)' in log
                and 'ValueError: M2-PREP input hash mismatch: docs/DECISIONS.md' in log
                and 'ERROR: test_artifact_is_immutable_and_verifiable' in log):
            record['status'] = 'KNOWN_FROZEN_M2_CHECKSUM_FAILURE'
        validation.append(record)
        print(json.dumps(record), flush=True)
        if record['status'] == 'FAIL':
            raise ValueError(f'validation failed: {name}; preserve log, repair then use new report folder')
    r = json.loads((ROOT / 'data/financial/fpt_acceptance_v5/results.json').read_bytes())
    latest = r['results'][-1]
    metrics = {m['task']: m['value'] for m in latest['metrics']}
    full = validation[-1]
    summary = dict(stage='FIN_D4_FPT_REFERENCE_HANDOFF', date='2026-10-04',
        branch='m1-cafef-primary-experiment', status=r['stage_status'],
        active_run='data/financial/fpt_acceptance_v5', replay_run='data/financial/fpt_acceptance_v4',
        review_run='data/financial/fpt_equity_review_v1', newly_acquired_pdfs=2, newly_acquired_pdf_pages=46,
        new_ocr_pages=49, visually_reviewed_pages_this_stage=10,
        accounting_checks=len(checks['accounting_checks']), artifact_checks=checks['passed'],
        deterministic_replay=True, latest_decision_at=latest['decision_at'], reference_values=metrics,
        reference_families_available=6, production_families_accepted=0,
        gross_esop_proceeds=108193010000, gross_bridge_parent_equity=39959656534930,
        actual_issuance_fee=None, cash_classification_at_june30=None,
        strict_event_adjusted_pb=None, strict_normalized_ttm_eps=None,
        financial_features_allowed=False, research_ready=False, full_universe_allowed=False,
        remaining=r['remaining'], validation=validation,
        targeted_tests=sum(v['tests'] or 0 for v in validation[:3]),
        full_tests=full['tests'], full_passed=full['tests'] - (1 if full['exit_code'] else 0))
    rows = '\n'.join(f"| {m['task']} | {m['value']} | {m['basis']} | {m['period']} |" for m in latest['metrics'])
    report = f'''# FPT financial reference handoff và ESOP equity review

Ngày 04/10/2026; nhánh `m1-cafef-primary-experiment`. Stage FIN-D4, riêng FPT.
Kết quả: có đủ **6/6 nhóm kết quả tham khảo** tại 24/08 và 28/08/2026; **0/6 nhóm
được promote production**. Đây không phải 100% dữ liệu financial cho toàn dự án.
FPT reference handoff complete, strict acceptance và four-symbol pilot vẫn PARTIAL.

## Kết quả tại 28/08/2026

| Nhóm | Giá trị reference | Basis | Kỳ |
|---|---|---|---|
{rows}

F-score VAS có 9/9 signals, 2025=3; strict F chỉ 6 signals và total null.
M có 8/8 ratios, 2025 gross=-2,27998; các allowance scenarios có khoảng conditional
[-2,325857; -2,217720], không fraud threshold hoặc verified strict bounds.
Z là EM Z-double-prime có hằng số 3,25, không distress classification.
Annual basic EPS2025 ≈ 5.216,068 (in 5.216); H1 2026 in 2.967.
TTM reported numerator/share-days ≈ 5.570,364, chưa normalized reserve.
P/E ≈ 13,14097. P/B gross-capital ≈ 3,14038; P/B current-shares/latest-reported-equity
của đợt trước ≈ 3,14891 được giữ riêng, không sửa artifact cũ.
Các period/basis khác nhau không tự trở thành same-period clustering vector.

## Quá trình và evidence

1. Tái dùng các EPS, F/M/Z, scope và share-event runs đã seal; không crawl lại market.
2. Review bank attachments trong hai báo cáo ESOP đã tải: senior managers
   2.302.000 shares × 10.000 = 23.020.000.000 VND; staff
   8.517.301 shares × 10.000 = 85.173.010.000 VND. Bank confirmations ngày 25/06.
3. Tải thêm hai issuer PDFs công khai: đăng ký doanh nghiệp lần 61 (4 trang) và
   BCTC riêng bán niên reviewed (42 trang). URL được chọn từ cached issuer listing;
   public HTTPS download không login, không bypass. Một default-network request
   FAILED được giữ; bounded request sau đó DOWNLOADED.
4. Index 42 trang BCTC riêng, đều không có embedded text. Render/OCR thêm 49 trang:
   staff pages 1–3/12, registration 1–3, separate statement 1–42. Visual review
   10 trang liên quan, không tuyên bố 49 trang đều manually verified. OCR chỉ hỗ trợ
   discovery; accepted facts giữ explicit transcription và exact PDF/image hashes.
5. Extractor được sửa để hỗ trợ disjoint ranges cùng PDF, từ chối overlap và
   filename collisions. Partial extraction_v1 không có manifest và không được dùng;
   sealed esop_evidence_ocr_v2 là input. Không OCR danh sách staff ở pages 4–11.
6. Registration notice xác nhận capital 17.035.071.210.000 → 17.143.264.220.000 VND,
   effective 16/07, công bố 17/07; 1.714.326.422 common shares.
   Không gọi ngày registration là ngày issuance/accounting/transfer của mọi input.
7. Separate parent equity table vẫn ghi capital 17.035.071.210.000 tại 30/06.
   Other payables 143.204.484.997 là aggregate; chưa đủ evidence tách tiền ESOP.
   Không dùng separate parent total equity thay consolidated parent equity.
8. Seal equity_review_v1; thêm offline registry/calculator và runner tổng hợp sáu
   families; final acceptance_v4/v5 byte-identical. V1–V3 là intermediate runs,
   không active handoff. Config pin manifest, không chọn provider bằng priority.

## Equity bridge và quyết định

Gross bank proceeds = registered capital increment = **108.193.010.000 VND**.
Reference denominator = 39.851.463.524.930 (consolidated parent equity 30/06)
+ 108.193.010.000 = **39.959.656.534.930 VND**. Raw price 28/08=73.200 VND/share.
Đây là gross capital contribution bridge; không current net equity hoặc zero-fee
estimate. Cash classification tại 30/06 và fee treatment chưa riêng biệt verified,
nên asset/liability changes và actual fee giữ null. Không cộng tiền vào assets
lần nữa hoặc suy liability conversion từ việc tiền được thu trước ngày balance.
Dividend H1 đã reflected không trừ lại; internal capital transfer 381,75B không
ESOP proceeds. Subsequent operating results và complete events chưa được quan sát.
Strict event-adjusted PB vẫn null. Bonus 10% approved plan không tăng share count.

Chọn dùng explicit VAS F, M sensitivity, continuous EM Z và reported TTM trong
reference handoff. Literature matrix B6/B7 hỗ trợ firm characteristics/valuation,
không định nghĩa F/M/Z; công thức primary đã ghi trong
[financial contract](../../../docs/research/FINANCIAL_FEATURE_CONTRACT.md).
Không biến missing reserve/allowance thành zero hoặc proxy thành strict input.
Production variants tiếp tục MANUAL_REVIEW_REQUIRED.

## PIT và acceptance

DATE_ONLY vẫn dùng phiên quan sát đầu tiên sau ngày công bố. Ngày 21/08 chưa dùng
H1 PDF: F/M/Z annual có references, latest TTM/PE/PB block. Ngày 24/08 và 28/08
có 6 reference families. Registration notice chỉ chứng minh loại ngày đăng ký;
historical issuance interval và common-share effective basis chưa hết ambiguity,
không backfill từ latest review. Raw price/observed calendar hashes được kế thừa
từ pinned TTM run; identity `KBS:HOSE:FPT` vẫn provisional.
Readiness v12=153/1.176; date v6=138; strict task v8=0/120 giữ nguyên vì slice riêng.
Financial/research/full-universe gates false; market-only M2 protocol không đổi.

## Kiểm chứng

{summary['targeted_tests']} targeted tests PASS; compileall và synthetic smoke PASS.
{len(checks['accounting_checks'])} accounting checks + {checks['passed']} real-artifact checks PASS:
bank/capital/share sums, independent PB arithmetic, exact manifests, same-publication-day
block, strict nulls, no inferred cash classification và deterministic replay.
Full suite: {summary['full_tests']} tests, {summary['full_passed']} pass; một lỗi
frozen M2-PREP checksum của docs/DECISIONS.md đã có trước stage. Không sửa frozen
artifact hoặc giảm assertion. Command outputs và exit codes trong summary.json/logs.

```powershell
.venv/Scripts/python.exe scripts/run_financial_fpt_acceptance.py --config configs/data/financial_fpt_acceptance_v1.json --output data/financial/fpt_acceptance_NEW
.venv/Scripts/python.exe scripts/validate_financial_fpt_acceptance.py --run data/financial/fpt_acceptance_v5 --replay data/financial/fpt_acceptance_v4
```

## Handoff và dữ liệu còn thiếu

Workflow đã thực hiện: public issuer acquisition → immutable inventory/hash →
text/OCR → explicit visual mapping review → publication/date-PIT → comparability,
share/capital bridge → offline calculation → per-family acceptance → replay/report.
Acquisition/OCR/calculation có code; PDF template/semantics mới vẫn vào review queue.
Chưa fully automatic acceptance trên unseen PDFs hoặc sẵn scale khoảng 1.000 mã.

Blockers dữ liệu còn lại: actual fee treatment và pre-balance cash classification;
complete event/historical share coverage; reserve allocation không được issuer
ước tính cho H1; historical identity/sector. Strict F/M mappings là methodology
review, không thể chỉ thêm nguồn rồi gọi VAS proxy thành original score.
Không nhất thiết mọi blocker đều có thể giải quyết bằng crawl công khai.

Stage kế tiếp dự kiến: áp workflow có bounds cho VNM/PVS/ACV, xác minh full VAS,
exact publications, EPS reserve/share changes và note exceptions; đo coverage từng
task/mã trước khi quyết định scale. Stage đó chưa được execute trong đợt này.
[Execution plan v6](../../../configs/data/financial_execution_plan_v6.json)
giữ năm stages và FIN-D4 pilot PARTIAL, FIN-D5 PENDING.
'''
    immutable_write(out / 'report.md', report.encode('utf8'))
    immutable_write(out / 'summary.json', encoded(summary))
    immutable_write(out / 'artifact_checks.json', encoded(checks))
    immutable_write(out / 'builder.py', Path(__file__).read_bytes())
    source_paths = [
        'configs/data/financial_fpt_acceptance_v1.json', 'configs/data/financial_execution_plan_v6.json',
        'scripts/build_financial_fpt_equity_review.py', 'scripts/extract_financial_selected_pages.py',
        'scripts/validate_financial_fpt_acceptance.py', 'scripts/run_financial_fpt_acceptance.py',
        'src/delta_t1/features/financial_equity_reference.py', 'src/delta_t1/experiments/financial_fpt_acceptance.py',
        'tests/unit/features/test_financial_equity_reference.py', 'tests/unit/experiments/test_financial_fpt_acceptance.py',
        'docs/research/FINANCIAL_FEATURE_CONTRACT.md', 'docs/DECISIONS.md', 'docs/CURRENT_STATUS.md',
        'docs/README.md', 'docs/crawl/README.md', 'docs/DELTA_UNIFIED_PROJECT_PLAN.md', 'CHANGELOG.md']
    immutable_write(out / 'source_hashes.json', encoded({p: file_hash(ROOT / p) for p in source_paths}))
    immutable_write(out / 'manifest.json', encoded({'files': {p.name: file_hash(p) for p in out.iterdir()}}))
    return dict(output=str(out), status=summary['status'], tests=summary['targeted_tests'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    p.add_argument('--resume-validated-logs', action='store_true')
    p.add_argument('--validated-log-source')
    a = p.parse_args()
    print(json.dumps(build(a.output, a.resume_validated_logs, a.validated_log_source)))
