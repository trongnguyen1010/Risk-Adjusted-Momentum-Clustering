"""Verify/seal research, acquisition and calculation handoff; never claim full readiness."""
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import encoded,digest,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
OUT=ROOT/'artifacts/reports/financial-source-research-v1'
if (OUT/'manifest.json').exists():raise FileExistsError('sealed report')
runs=['provider_probe_v1','provider_probe_v2','provider_probe_v3','fpt_extended_review_v2',
      'fpt_interim_ocr_v1','fpt_interim_review_v1','fpt_review_corrections_v1',
      'pilot_readiness_v12','date_pit_v6','task_readiness_v8','workflow_v8','source_completion_v4','source_completion_v5']
for run in runs:verify_inventory(ROOT/'data/financial'/run)
left=ROOT/'data/financial/source_completion_v4/result.json';right=ROOT/'data/financial/source_completion_v5/result.json'
assert left.read_bytes()==right.read_bytes()
for name in ['runner.py','features.py','provider_normalizer.py','corrections.py','provider_candidates.json','config.json']:
    assert (left.parent/name).read_bytes()==(right.parent/name).read_bytes()
r=json.loads(right.read_bytes());validation=json.loads((OUT/'final-validation/validation.json').read_bytes())
assert all(x['status'] in ['PASS','KNOWN_FROZEN_M2_CHECKSUM_FAILURE'] for x in validation)
assert len(validation)==6
assert not r['financial_features_allowed'] and not r['research_ready']
f=[x for x in r['f_score'] if x['vas_reference']['value'] is not None]
assert [(x['year'],x['vas_reference']['value']) for x in f]==[(2021,4),(2022,6),(2023,6),(2024,7),(2025,3)]
assert all(x['vas_reference']['known_signals']==9 and x['strict']['value'] is None for x in f)
assert all(x['vas_reference']['value'] is None for x in r['f_score'] if x not in f)
assert all(i['usable_from_date']<=x['decision_date'] for x in r['f_score']+r['m_score'] for i in x['inputs'])
assert len(r['m_score'])==2 and all(len(x['gross_trade_reference']['ratios'])==8 and x['conditional_range'] for x in r['m_score'])
assert r['interim_review']['eps_reference']['rounded']['basic']=='2967'
assert r['interim_review']['usable_from_date']=='2026-08-24'
assert r['interim_review']['latest_ttm']['value'] is None
assert any(x['comparison'].get('revision_conflict') for x in r['provider_comparisons'])
assert not any(x['comparison']['status']=='VALUE_CONFLICT' for x in r['provider_comparisons'])
assert all(c['passed'] for c in r['review_corrections']['checks'])
status=Counter(x['status'] for x in r['provider_requests'])
summary=dict(stage=r['stage'],status='PARTIAL',provider_requests=dict(status),provider_cells=r['provider_cells'],
    provider_comparisons=dict(Counter(x['comparison']['status'] for x in r['provider_comparisons'])),
    f_score_vas={str(x['year']):x['vas_reference']['value'] for x in f},
    m_score_sensitivity={str(x['year']):dict(gross=x['gross_trade_reference']['value'],conditional_range=x['conditional_range']) for x in r['m_score']},
    valuation={k:r['reported_valuation'][k] for k in ['pe','pb','bvps']},interim_eps=2967,
    deterministic_replay=True,financial_features_allowed=False,research_ready=False,full_universe_allowed=False,
    production_review_status='MANUAL_REVIEW_REQUIRED',validation=validation,
    input_manifest_sha256={name:digest((ROOT/'data/financial'/name/'manifest.json').read_bytes()) for name in runs})
immutable_write(OUT/'summary.json',encoded(summary))
text='''# Report — Bổ sung nguồn financial và tính reference VAS, 03/10/2026

Nhánh `m1-cafef-primary-experiment`. Stage FIN-D4 source research/reference
**PARTIAL**. Đã mở được nguồn bảng tài chính có cấu trúc trên cả bốn mã pilot,
bổ sung hai PDF 2026 và chạy các phép tính mới. Chưa đủ dữ liệu/acceptance để
gọi là full financial production hoặc scale toàn bộ khoảng 1.000 mã. Market-only
protocol, clustering và frozen M2 snapshot giữ nguyên.

## Research và quyết định

| Project/tài liệu nguồn | Điều học được | Quyết định áp dụng |
|---|---|---|
| [Vnstock Finance](https://www.vnstocks.com/docs/vnstock-data/bao-cao-tai-chinh), [community VCI source](https://raw.githubusercontent.com/thinh-vu/vnstock/main/vnstock/explorer/vci/financial.py) | Có adapters KBS/VCI/MAS, bảng tài chính và mapping | Probe public endpoints trực tiếp, pin raw JSON; không import SDK có side effects hoặc giả định mọi package miễn phí |
| [Intrinio Piotroski example](https://gist.github.com/intrinio-gists/37806a997366786697f5ea89cb49ca25) | Dùng net income cho profitability/accrual signals; shares proxy có hạn chế | Tạo biến thể VAS reported net profit riêng; giữ original-maturity debt, verified actual issuance. Không dùng share-count delta thay issuance vì stock dividend |
| [Vietnam Stock Screener](https://github.com/preutbao/vss_v1.1) | Workflow financial screener và chín tín hiệu | Tham khảo cách tổ chức acquisition/caching; README không chứng minh financial PIT/vintage đúng |
| [Valinvest](https://github.com/astro30/valinvest) | Tự mô tả alternate score, gồm growth/beta | Không dùng alternate/fractional score làm Piotroski gốc |

Hệ số M-score tiếp tục model 2013 trong literature contract của project. Giữ
strict ordinary-income definition; không alias net profit vào canonical strict
field. VAS adaptation và owned-PPE sensitivity có tên/registry riêng,
`strict_original_score=false`, `cluster_eligible=false`. Đây là research reference
theo phạm vi owner cho phép quyết định hợp lý; production methodology acceptance
vẫn `MANUAL_REVIEW_REQUIRED`. Không áp threshold để kết luận gian lận/phá sản.

## Thu thập và xử lý thực tế

1. `provider_probe_v1`: môi trường network mặc định lỗi transport; giữ evidence.
`provider_probe_v2`: KBS FPT trả sáu JSON (annual/quarter × CDKT/KQKD/LCTT).
VCI trả 403 ở request đầu; hai request còn lại không gửi, không workaround.
`provider_probe_v3`: VNM/PVS/ACV trả đủ chín annual JSON. Tổng 15 KBS responses;
không cần nhiều nguồn cho từng bảng core. Nguồn notes/publication vẫn là PDF gốc.
2. Tải từ [FPT disclosure listing](https://fpt.com/vi/nha-dau-tu/thong-tin-cong-bo):
PDF hợp nhất Q1 2026 và bán niên reviewed 2026. Q3 2025 URL cũ trả 404, giữ lỗi.
Hai PDF đều scanned: 112 physical pages; đã render/OCR 80 trang (H1 toàn66,
Q1 đầu14). WinRT en-US tạo candidates; visual review vẫn quyết định semantics.
Q1 chưa review/accept toàn bộ notes, không gọi là quarter flow đã hoàn chỉnh.
3. Offline KBS normalizer xuất 4.796 wire cells, bao gồm null/unmapped values,
không phải 4.796 accepted facts. Content là dict các lists; Head dài14/57 nhưng
response thực tế chỉ Value1–4. Không sinh thêm năm từ pageSize12. Monetary mapping
dùng queryunit1000 như candidate và so exact PDF trong tolerance500 VND cho
rounding; EPS không nhân1000. Null khác verified zero. Raw header/dates giữ nguyên,
không dùng provider ReportDate/LastUpdate/DatePubDepartment làm ngày công bố PIT.
4. `fpt_extended_review_v2`: 17 reviewed annual observations riêng, gồm SG&A2023,
gross trade/allowance2023–25, noncurrent loan/lease2023–25, owned depreciation
2023–25, owned PPE2025, common shares và parent common equity2025. Hai arithmetic
bridges PASS. Không cộng17 vào150 baseline cells vì có overlaps/field scopes mới.
5. `fpt_interim_review_v1`: 13 H1 facts/comparatives cùng exact hash/ảnh/period.
H1 publication21/08/2026 nối exact issuer attachment; first observed HOSE session
24/08/2026. Không giả giờ. EPS note có weighted basic1.703.507.121, explicit
no dilution ở trang57. Reserve chưa được issuer ước tính, không gán missing=0.

## Kết quả đã tính

| Chỉ số | FPT2024 | FPT2025 | Ý nghĩa |
|---|---:|---:|---|
| F-score VAS reported-profit | 7/9 | 3/9 | Đủ chín binary signals theo biến thể đã khai báo |
| Strict F-score | null | null | Sáu known signals; ordinary-income reconciliation chưa đóng |
| M-score gross-trade/owned-PPE sensitivity | -2,446702 | -2,279981 | Đủ tám ratios theo giả định riêng; chưa strict M-score |
| M conditional allowance scenarios | [-2,499385; -2,346361] | [-2,325857; -2,217720] | Bốn corner scenarios về phân bổ allowance; không phải bounds của strict model |
| EM Z reference (giữ kết quả flow v9) | 6,843186 | 7,106292 | Continuous diagnostic theo variant contract |
| Annual EPS sau latest reviewed revision tại20/03/2026 | 4.292 | 5.216 | VND/share; EPS2024 trước revision release là4.944 |

F-score VAS đầy đủ thêm2021=4,2022=6,2023=6. Mọi year đều null trên ngày công bố
original và có reference từ phiên kế tiếp. Dùng reviewed original current-year
PDF từng năm; chưa tuyên bố latest-restatement joint comparability đã nghiệm thu.
Gross trade receivables chưa trừ trade-specific allowance; scenario chỉ giả định
trade allocation từ0 đến toàn short-term allowance. M-score dùng cùng owned PPE
và owned depreciation, loại leases/intangibles/goodwill; earnings dùng reported
consolidated net profit. Strict M-score còn null; không áp threshold.

Tại decision20/03/2026 17:00+07, raw_close FPT74.600 VND/share từ C8. EPS exact
FY2025 window01/01–31/12 recompute5216,068... cho **reported P/E14,301961**.
Parent common equity36.480.193.944.772 VND và outstanding common1.703.507.121
cùng31/12/2025 cho **BVPS21.414,758703**, **reported P/B3,483579**. Không dùng
adj_close73.585,4 hoặc weighted EPS denominator cho BVPS. P/B là reported basis;
intervening share-event coverage và historical identity còn pending, không gọi
là event-complete PIT valuation. H1/TTM chưa thay annual window lúc March20.

H1 2026 EPS recompute **2.967 VND/share**, basic=diluted, đúng printed note.
Không annualize ×2 hoặc cộng EPS các quý. Từ01/01/2026, FTEL chuyển từ công ty
con sang liên kết; H1PDF trang18 công bố pro-forma H1 2025 nhưng chưa review
full-year2025 cùng scope. Trang19 còn nêu adoption chế độ biểu mẫu mới. H1EPS
chưa trích reserve chưa ước tính, khác FY2025. Vì vậy latest TTM/P-E ghép
FY2025+H12026−H12025 còn **SCOPE_AND_EPS_BASIS_BRIDGE_REQUIRED**.

## Reconciliation và kiểm chứng

KBS EPS2024 raw4.944 chưa phản ánh revised4.292 trong original2025PDF. Cả hai
vintages giữ lại và có revision conflict output. Diluted EPS raw5/5/5/4 có scale
exception, không tự chọn magnitude. Matching monetary values không chứng minh
revision history/PIT hoặc semantic mapping cho các mã khác.

Final `source_completion_v4` và replayv5 có result/candidates/config/code snapshots
byte-identical. v1 exploratory giữ nguyên, M-score còn thiếu depreciation vì
readiness chỉ giữ target fields; đã sửa bằng exact original note facts trong
extended reviewv2. v1 không dùng làm reproducibility claim do code có iteration
khi run hoàn tất. v2/v3 superseded sau correction review. Không sửa artifacts cũ.

Provider reconciliation phát hiện hai transcription errors trong review: CFO2024
11.703.377.718.868 → **11.703.777.188.868**, noncurrent loan/lease2024
501.111.537.075 → **501.115.537.075**. Đọc lại exact original PDF pages14/11,
giữ bad observations như excluded evidence bằng identity/hash/value, không
source-priority overwrite hoặc đổi publication date. CFO+CFI+CFF=netcashchange
và noncurrent-liability component sum đều PASS. F-score không đổi; M reference
được tính lại. Final56 comparisons:48 monetary matches,4 per-share exceptions,
4 not-comparable (diluted unit); không còn monetary conflict trong covered set.
EPS revision conflict vẫn giữ. Các mã khác chưa PDF QA.

Rebuild pilot_readiness_v12: **153/1.176 value-verified**,697 raw-unverified,
272 note-review,54 missing,302 accepted observations; không có verified new facts
cho ba mã còn lại. Date overlayv6:138 date-reference cells; strict taskv8 vẫn
0/120 ready. Workflowv8 giữ queue scope annual; H1 review là artifact riêng.

Validation logs ở report folder: targeted financial features/ingestion/experiments,
compile, synthetic smoke PASS. Full-suite còn đúng một lỗi frozen M2-PREP checksum
`docs/DECISIONS.md`; không bỏ assertion hoặc rewrite frozen snapshot để làm pass.
Số tests/exits chính xác nằm trong validation.json và summary.json.

## Phần còn thiếu và workflow để scale

Không phải tất cả gaps đều do chưa có data core. Với FPT annual đã đủ cho F-score
VAS reference; strict definitions, source revisions, valuation event coverage và
TTM comparability cần xử lý riêng. Với VNM/PVS/ACV, mới có structured candidates:
chưa đủ verified financial tasks. Workflow áp dụng tiếp:

1. Bounded structured acquisition → cache/normalize theo report/row/period/unit.
2. Match exact issuer PDFs, framework/scope, year/quarter/YTD, accounting bridges.
3. Notes queue chỉ cho depreciation/receivables/equity/EPS/issuance chưa có evidence.
4. Publication exact hash → date-only next-session rule → keep all revisions.
5. Joint comparability và corporate actions/shares → calculate strict hoặc named
VAS variant; missing/conflicts xuất lý do, không biến thành zero.
6. Acceptance pilot trên các nhóm ngành/formats → checkpoint/retry/cache khi scale.

Cần tiếp tục: trade allowance/leased depreciation/ordinary-income reconciliation
nếu giữ strict M/F; full-year2025 FTEL bridge và EPS reserve/share-weight bridge
cho latest TTM; dated issuance/bonus/treasury register cho P/B; map/QA các pilot
còn lại và bổ sung VNM full-VAS years thiếu. Chưa mở FIN-D5 full-universe crawl.
Registry/provenance/temporal checks có code; semantic review trên unseen PDFs vẫn
chưa unattended, không thể hứa OCR80trang là scale1000mã đã PASS.

## Chạy lại offline

```powershell
.venv/Scripts/python.exe scripts/run_financial_source_completion.py --config configs/data/financial_source_completion_v3.json --output data/financial/source_completion_NEW
```

Output phải là folder mới. acquisition/OCR CLI và configs nằm trong configs/data,
evidence SHA256 nằm ở input inventories/manifest. Full result chứa từng signal,
tám ratios, four scenarios, raw price, EPS/equity/share evidence và exception.
'''
immutable_write(OUT/'report.md',text.encode('utf8'))
immutable_write(OUT/'builder.py',Path(__file__).read_bytes())
immutable_write(OUT/'validator.py',(ROOT/'scripts/validate_financial_source_completion.py').read_bytes())
immutable_write(OUT/'manifest.json',encoded({'files':{p.relative_to(OUT).as_posix():digest(p.read_bytes()) for p in OUT.rglob('*') if p.is_file()}}))
print(json.dumps(dict(report=str(OUT/'report.md'),provider_cells=r['provider_cells'],f_scores=summary['f_score_vas'],validation=validation)))
