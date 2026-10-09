"""Seal reference continuation evidence and the Vietnamese owner handoff."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import encoded,digest,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
OUT=ROOT/'artifacts/reports/financial-revision-fscore-v1'
if (OUT/'manifest.json').exists():raise FileExistsError('report already sealed')
runs=['fpt_revision_fscore_review_v1','pilot_readiness_v11','task_readiness_v7',
      'date_pit_v5','workflow_v7','reference_flow_v8','reference_flow_v9']
for name in runs:verify_inventory(ROOT/'data/financial'/name)
flow=json.loads((ROOT/'data/financial/reference_flow_v9/flow.json').read_bytes())
assert (ROOT/'data/financial/reference_flow_v8/flow.json').read_bytes()==(ROOT/'data/financial/reference_flow_v9/flow.json').read_bytes()
assert not flow['review_queue']
assert sum(c['candidate'].get('value') is not None for c in flow['parsed_cells'])==25
assert all(c['passed'] for c in flow['parsed_cells'])
latest={ (r['year'],r['task']):r for r in flow['results'] if r['decision_date']=='2026-08-28'}
for year in [2024,2025]:
    assert latest[year,'F_SCORE']['known_signals']==6
    assert latest[year,'F_SCORE']['value'] is None
eps={r['decision_date']:r for r in flow['results'] if r['task']=='EPS_RECOMPUTE' and r['year']==2024}
assert eps['2026-03-19']['rounded']['annual_basic_eps_reference']=='4944'
assert eps['2026-03-20']['rounded']['annual_basic_eps_reference']=='4292'
assert eps['2025-03-14']['value'] is None
assert latest[2025,'EPS_RECOMPUTE']['rounded']['annual_basic_eps_reference']=='5216'
assert all(not r['financial_features_allowed'] and not r['research_ready'] for r in flow['results'])
assert all(ref['usable_from_date'] <= r['decision_date'] for r in flow['results']
           for item in r['inputs'] for ref in item['references'])
for r in flow['results']:
    if r['task']=='F_SCORE' and r['decision_date']<'2025-03-17':
        assert r['known_signals']==0 and r['value'] is None
full_log=(OUT/'full-suite.log').read_text(encoding='utf8')
assert 'Ran 233 tests' in full_log and 'FAILED (errors=1)' in full_log
assert 'M2-PREP input hash mismatch: docs/DECISIONS.md' in full_log
summary=dict(stage='FIN-D2_REFERENCE_CONTINUATION',status='PARTIAL',eps_revision_reference='PASS',
    f_score_known_signals={str(y):latest[y,'F_SCORE']['signals'] for y in [2024,2025]},
    original_vs_revised_eps2024=dict(original=4944,revised=4292,usable_from_date='2026-03-20'),
    numeric_cells_passed=25,accounting_bridges_passed=4,review_queue=0,deterministic_replay=True,
    flow_counts=flow['counts'],financial_features_allowed=False,research_ready=False,full_universe_allowed=False,
    input_manifest_sha256={name:digest((ROOT/'data/financial'/name/'manifest.json').read_bytes()) for name in runs})
immutable_write(OUT/'summary.json',encoded(summary))
text='''# Report — FPT EPS revision và F-score reference, 03/10/2026

Nhánh `m1-cafef-primary-experiment`. Kết quả stage **PARTIAL**: EPS revision
reference PASS; F-score có 6/9 signals, total vẫn null. Không thay nhóm market
clustering, production financial gate hoặc mở full-universe crawl.

## Đã thực hiện

1. Reuse original audited consolidated VAS PDFs/OCR FPT 2019–2025. Không tải PDF
mới hoặc gọi OCR mới. Đối chiếu ảnh notes: debt2020–25, parent issuance2021–25,
EPS2024 restated trong original2025 page55. OCR chỉ cung cấp candidates;
ground truth/semantic mapping còn visual review.
2. Tạo `fpt_revision_fscore_review_v1`: 15 observations và 12 mapping/arithmetic
checks. Nợ gồm loans + finance leases theo kỳ hạn gốc, đã chứa current portion;
không cộng thêm toàn bộ vay ngắn hạn. Parent ESOP khác stock dividend/NCI funding.
FPT2024 note56 ghi 10.621.177 ESOP shares; FPT2025 note54 ghi 10.260.939.
Indicator1 là có phát hành được xác minh, vì vậy no-issuance signal0.
3. Giữ hai vintages EPS2024. Numerator 7.231.780.632.599 VND không đổi;
basic denominator original 1.462.653.544, restated 1.684.830.543 shares, tăng
222.176.999 do stock dividend. Revised diluted denominator derive từ original
FY2024 explicit no-dilution note và cùng adjustment, lưu hai-source lineage.
4. Config v2 thêm exact revision template; as-of selection chọn bằng ngày và
PDF hash. Reference calculator dùng Decimal, strict denominators/comparisons.
F-score xuất từng signal/reason, total chỉ khi cả9 known; không proxy net profit.
5. Rebuild readiness v11, task matrix v7, date-PIT v5, workflow v7. Flow v8/v9
replay cùng output bytes. Initial v7 giữ nguyên làm evidence; hai EPS-only
balance/EBIT checks không áp dụng đã được sửa bằng conditional template checks,
không sửa artifact v7. Final review queue zero chỉ áp cho25 numeric calibration
cells và4 balance/EBIT bridges, không phải accuracy trên unseen PDFs.

## Kết quả theo ngày quyết định

| Task | Trước ngày khả dụng | Từ ngày khả dụng | Reference result |
|---|---|---|---|
| EPS2024 original | 14/03/2025: null | 17/03/2025 | 4.944 VND/share |
| EPS2024 revision | 19/03/2026: giữ original | 20/03/2026 | 4.292 VND/share |
| EPS2025 | 19/03/2026: null | 20/03/2026 | 5.216 VND/share |

Basic/diluted reference EPS bằng nhau theo note/derivation ở trên. Các số trong
bảng là rounded; raw Decimal values/provenance có trong flow.json.
EM Z2024/25 vẫn 6,843186/7,106292. Đây là annual EPS reference, chưa EPS TTM/P-E.

| F-score signal | FPT2024 | FPT2025 |
|---|---:|---:|
| CFO > 0 | 1 | 1 |
| Leverage giảm, dùng average assets | 1 | 0 |
| Current ratio tăng | 1 | 1 |
| Không phát hành cổ phiếu mẹ | 0 | 0 |
| Gross margin tăng | 0 | 0 |
| Asset turnover tăng, dùng average assets | 1 | 0 |
| ROA > 0 | null | null |
| ROA tăng | null | null |
| CFO > ROA | null | null |
| **F-score total** | **null** | **null** |

Sáu signals trên là binary điều kiện đạt/không đạt, không phải sáu điểm.
ROA/CFO dùng beginning assets; leverage/turnover dùng average assets theo frozen
Piotroski contract. Multi-year inputs chỉ nhận reviewed original PDF mỗi năm,
cùng VAS/consolidated scope và đã khả dụng. Cross-year reference vẫn chưa là
production vintage/reclassification acceptance trên toàn bộ lịch sử.

Readiness tăng 139→150/1.176 verified field-year cells; FPT150/294=51,0% value
coverage, không phải % dự án hoàn thành. Date references124→135. Task matrix v7
vẫn0/120 production-ready vì semantic/external gates khác vẫn thiếu.
60 task-date executions:12 EPS/Z QA-pass,10 partial F-score,8 EPS/Z unavailable,
30 M/P-E/P-B ngoài reference calculators. Snapshot dùng28/08/2026 theo C8.

## Phần chưa đóng và workflow tiếp theo

Blocker chung ba F-score signals: `income_before_extraordinary_items`. VAS
reported net profit và other income không tự chứng minh ordinary earnings theo
strict contract. Trừ toàn bộ other income cũng không có reconciliation về tax
và loại giao dịch. Giữ null; chưa đổi variant. Muốn thay bằng VAS reported-profit
adaptation cần đề xuất definition/impact rõ và review methodology riêng.

Tiếp theo: đóng earnings reconciliation của FPT trước, sau đó M-score net
receivables/PPE depreciation/debt scope; quarterly/YTD-compatible TTM và
historical shares/common equity cho P-E/P-B. Khi FPT đủ task-level acceptance,
áp vào PVS/ACV/VNM và đo parser coverage/exception cost trước batch expansion.
VNM full-VAS2019/20/21/25 và historical identity/sector vẫn là gaps riêng.

Flow áp dụng cho mã khác: discover exact PDF và publication → acquire/hash/cache
→ render/OCR → extract candidates → review unit/scope/period/semantic notes
→ accounting QA → preserve revision/DATE_ONLY next-session overlay → select
inputs as-of → calculate per-task hoặc null+reason → export manifest/report.
Code hỗ trợ replay những template đã review; chưa unattended unseen-template
extraction. PDF/date/values đều cần matching evidence trước khi scale.

## Kiểm chứng và tái lập

26 targeted tests PASS; compile và synthetic smoke PASS. Full suite233 tests:
232 PASS,1 ERROR tại frozen M2-PREP `DECISIONS.md` checksum cũ. Không sửa frozen
snapshot hoặc giảm assertion để làm gate xanh. Logs trong thư mục report này.

Config: `configs/data/financial_reference_flow_v2.json`. Ví dụ replay sang
directory mới chưa tồn tại:

```powershell
.venv/Scripts/python.exe scripts/run_financial_reference_flow.py --config configs/data/financial_reference_flow_v2.json --output data/financial/reference_flow_owner_replay_v1
```

Evidence runs: `data/financial/fpt_revision_fscore_review_v1`,
`pilot_readiness_v11`, `task_readiness_v7`, `date_pit_v5`, `workflow_v7`,
`reference_flow_v8`, `reference_flow_v9`. Report summary.json pin input manifests;
manifest.json pin exact report inventory. Artifacts cũ giữ nguyên.

Self-review: không missing→zero, future selection, latest-vintage backfill,
blind ordinary-profit alias, partial total hoặc mở scale/research gates.
**Stage tổng PARTIAL; EPS revision reference slice PASS.**
'''
immutable_write(OUT/'report.md',text.encode('utf8'))
immutable_write(OUT/'generator.py',Path(__file__).read_bytes())
immutable_write(OUT/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}}))
verify_inventory(OUT)
print(json.dumps(summary,ensure_ascii=True))
