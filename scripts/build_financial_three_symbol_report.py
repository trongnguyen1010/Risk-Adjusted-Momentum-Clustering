"""Write the Vietnamese bounded-pilot handoff from sealed evidence and actual logs."""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.cafef_financial import encoded, immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.experiments.financial_ttm_valuation import file_hash

OUT = ROOT / 'artifacts/reports/financial-three-symbol-pilot-v1'
RUN = ROOT / 'data/financial/three_symbol_pilot_v3'
REPLAY = ROOT / 'data/financial/three_symbol_pilot_v4'


def number(value, digits=4):
    return 'null' if value is None else f'{float(value):.{digits}f}'


def build():
    for run in [RUN, REPLAY]: verify_inventory(run)
    names = {p.name for p in RUN.iterdir() if p.is_file()}
    if names != {p.name for p in REPLAY.iterdir() if p.is_file()} or any((RUN / n).read_bytes() != (REPLAY / n).read_bytes() for n in names):
        raise ValueError('replay is not byte-identical')
    result = json.loads((RUN / 'results.json').read_bytes())
    facts = json.loads((RUN / 'facts.json').read_bytes())
    config = json.loads((RUN / 'config.json').read_bytes())
    source_runs = [ROOT / ('data/financial/issuer_supplement_v1/' + name) for name in [
        'run-2026-10-04T164224.202400-0000-380756e5', 'run-2026-10-04T164311.369029-0000-3750d043',
        'run-2026-10-04T164448.490368-0000-c41ca313', 'run-2026-10-04T164921.224271-0000-7b848180']]
    inventory = []
    for source in source_runs:
        verify_inventory(source)
        inventory.extend(json.loads((source / 'inventory.json').read_bytes())['requests'])
    price_run = ROOT / config['price_reference_run']; verify_inventory(price_run)
    price_inventory = json.loads((price_run / 'inventory.json').read_bytes())['requests']
    ocr_runs = list(config['ocr_manifest_sha256']) + ['data/financial/pilot_acv_interim_ocr_v1']
    ocr_counts = {}
    for name in ocr_runs:
        verify_inventory(ROOT / name)
        ocr_counts[name] = len(list((ROOT / name).rglob('*.ocr.json')))
    if sum(ocr_counts.values()) > 400: raise ValueError('stage OCR budget exceeded')
    logs = OUT / 'logs'
    targeted = (logs / 'targeted-tests-final.txt').read_text(encoding='utf8')
    full = (logs / 'full-tests.txt').read_text(encoding='utf8')
    if not re.search(r'\nOK\s*$', targeted): raise ValueError('targeted tests not passed')
    exits = {name: int((logs / (name + '-exit.txt')).read_text(encoding='utf-8-sig').strip())
             for name in ['compile', 'synthetic-smoke', 'full-tests']}
    if exits['compile'] or exits['synthetic-smoke']: raise ValueError('compile/smoke failed')
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    if branch != 'm1-cafef-primary-experiment': raise ValueError('wrong branch')
    tests = dict(targeted=int(re.search(r'Ran (\d+) tests', targeted).group(1)),
                 full=int(re.search(r'Ran (\d+) tests', full).group(1)), exits=exits,
                 full_failures=re.findall(r'^(?:FAIL|ERROR): (.+)$', full, re.MULTILINE))
    pdf_responses = [x for x in inventory if x['kind']=='pdf' and x['status']=='DOWNLOADED']
    counts = dict(new_http_responses=len(inventory)+len(price_inventory), downloaded_pdf_responses=len(pdf_responses),
                  unique_pdf_sha256=len({x['sha256'] for x in pdf_responses}), html_snapshots=sum(x['kind']=='html' for x in inventory),
                  quote_json_pages=len(price_inventory), ocr_pages=sum(ocr_counts.values()),
                  annual_reviewed_facts=len(facts), interim_reviewed_observations=len(result['interim_reviews']),
                  annual_arithmetic_metric_cells=sum(x['reference_metric_families_with_arithmetic'] for x in result['results']),
                  annual_metric_target_cells=18, production_accepted_metric_cells=0)
    self_review = [
        dict(check='branch', passed=branch=='m1-cafef-primary-experiment'),
        dict(check='immutable replay all files byte identical', passed=True),
        dict(check='field values have PDF/image exact hashes', passed=all(f['pdf_sha256'] and f['image_sha256'] for f in facts)),
        dict(check='no production or research promotion', passed=all(x[k] is False for x in result['results'] for k in ['financial_features_allowed','research_ready','full_universe_allowed'])),
        dict(check='VNM missing ninth signal has no partial total', passed=result['results'][0]['metrics']['F_SCORE'] is None and result['results'][0]['annual_math']['f_vas']['known_signals']==8),
        dict(check='ACV reserve/dilution unknown preserved', passed=result['results'][2]['annual_math']['eps']['strict_normalized_eps'] is None and result['results'][2]['annual_math']['eps']['dilution_reference']['value'] is None),
        dict(check='PVS and ACV TTM not fabricated', passed=all(x['ttm']['value'] is None for x in result['results'][1:])),
        dict(check='OCR remains discovery support', passed=all(f['ocr_is_acceptance_evidence'] is False for f in facts)),
    ]
    if any(c['passed'] is not True for c in self_review): raise ValueError('self-review failed')
    blockers = [
        dict(symbol='VNM', task='F_SCORE', missing='Original long-term debt current portion at both dates; noncurrent balance cannot substitute', value=None),
        dict(symbol='VNM', task='PIT', missing='Primary annual/H1 publication confirmation; 2024 auxiliary publication date', value=None),
        dict(symbol='PVS', task='TTM/PE', missing='Restated prior parent profit/reserve/bonus basis and compatible FY numerator bridge', value=None),
        dict(symbol='ACV', task='EPS', missing='Unestimated FY2025 reserve and unknown dilution; reported basic only', value=None),
        dict(symbol='ACV', task='TTM/PE', missing='Review eligible unaudited Q2 EPS scope; reviewed H1 published after cutoff', value=None),
        dict(symbol='ACV', task='PIT', missing='2024 auxiliary statement publication date', value=None),
        dict(symbol='ALL', task='STRICT_F/M', missing='Ordinary-income and receivable taxonomy mappings; production variant review', value=None),
        dict(symbol='ALL', task='CURRENT_PB', missing='Complete effective common-share events, current equity/fee/dividend treatment', value=None),
        dict(symbol='ALL', task='SCALE', missing='Other-year coverage, historical identity, independent acceptance, representative source/cost gates', value=None),
    ]
    report_json = dict(date='2026-10-05', branch=branch, stage=result['stage_status'], counts=counts, tests=tests,
        results=result['results'], interim_reviews=result['interim_reviews'], blockers=blockers, self_review=self_review,
        input_manifests={str(p.relative_to(ROOT)):file_hash(p) for p in [RUN/'manifest.json',REPLAY/'manifest.json'] + [r/'manifest.json' for r in source_runs] + [price_run/'manifest.json']},
        ocr_runs=ocr_counts, legacy_readiness_unchanged=dict(accepted_cells=153,total_cells=1176,date_references=138,strict_ready_tasks=0,total_tasks=120))
    rows = []
    for x in result['results']:
        m=x['metrics']; rows.append(f"| {x['symbol']} | {m['F_SCORE'] if m['F_SCORE'] is not None else 'null (8/9 known)'} | {number(m['M_SCORE'])} | {number(m['Z_SCORE'])} | {number(m['EPS_RECOMPUTE'],2)} | {number(m['PE'])} | {number(m['PB'])} |")
    interim_rows = []
    for x in result['interim_reviews']:
        source_year=x['source_period_end'][:4]
        interim_rows.append(f"| {x['symbol']} | {x['period_end']} | {source_year} | {number(x['eps']['value'],2)} | {x['usable_from_date']} |")
    md = f'''# Report pilot financial VNM/PVS/ACV — 05/10/2026

Stage được thực hiện trên nhánh `{branch}` theo yêu cầu tiếp tục financial workstream.
Phạm vi là bounded pilot ba mã, annual 2025 cùng dữ liệu giữa năm để kiểm tra TTM.
Stage annual reference đã chạy hết acquire → PDF/OCR → review → QA → tính → replay.
Acceptance tổng thể **PARTIAL**: có {counts['annual_arithmetic_metric_cells']}/18 annual arithmetic cells;
production accepted vẫn **0**. Đây không phải phần trăm hoàn thành plan tổng.

## Công việc và nguồn đã xử lý

- Tải thêm {counts['downloaded_pdf_responses']} PDF responses, {counts['unique_pdf_sha256']} PDF unique; {counts['html_snapshots']} HTML snapshots.
  Có VNM BCTC hợp nhất VAS 2025 đầy đủ, VNM H1 2026; PVS H1 2025/2026;
  ACV Q2 unaudited và reviewed H1 2026. Một VNM annual PDF được lấy hai đường dẫn
  và xác nhận byte-identical; không đếm thành hai báo cáo độc lập.
- CafeF/CDN và cache cũ cung cấp issuer annual PDFs; PTSC official website cung cấp
  PVS interims và dated attachment pages; Vietstock lưu issuer PDFs của VNM,
  PHS mirror HOSE disclosure dùng để đối chiếu exact attachment và ngày.
  Trang Happite chỉ là locator tìm link, không lấy giá trị tài chính từ bài viết.
  Vinamilk official page trả 403: dừng đường dẫn, không thử cách vượt access control.
- Snapshot canonical market đang dùng có ACV, không có VNM/PVS để join.
  Tải riêng {counts['quote_json_pages']} CafeF TradeHistoryNew JSON pages, lấy đúng
  raw close ngày 28/08: VNM 62.300, PVS 39.600; ACV cached 42.400 VND/share.
  Giữ riêng dưới financial reference, không sửa canonical/market-only/clustering.
- Render/OCR {counts['ocr_pages']} trang trong chín runs; review {len(facts)} annual
  field/offset facts và {len(result['interim_reviews'])} interim observations.
  OCR chỉ hỗ trợ locator; các số sử dụng đều đã đối chiếu ảnh trang gốc.
  ACV có trang xoay khiến OCR kém; transcript visual/hash giữ riêng, chưa auto-accept.
- Thêm offline runner, feature `disclosed_basic_eps_reference`, raw-price collector
  giới hạn hai mã/tối đa bốn pages, per-cell provenance, calculation-source pins,
  accounting/EPS checks, publication overlay và deterministic replay.

Inventory gốc và URLs đầy đủ có trong [report JSON](report.json), [work log](work-log.jsonl)
và các immutable source runs. Annual facts: [facts.json](../../../data/financial/three_symbol_pilot_v3/facts.json).

## Kết quả annual reference

| Mã | F VAS | M sensitivity | EM Z | EPS basic 2025 | P/E annual | P/B annual snapshot |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

F là named VAS reported-profit adaptation; M dùng gross short-term trade receivables
và owned tangible-PPE depreciation. Strict F/M không được suy từ các variants này.
Z giữ dạng continuous reference, không gán ngưỡng fraud/distress.
EPS dùng đúng numerator/weighted shares trong thuyết minh, không dùng current vendor EPS.
P/E trong bảng dùng EPS FY2025; P/B dùng common shares và parent reported equity
tại 31/12/2025 với raw price 28/08/2026. Chúng không phải latest TTM hoặc current
event-adjusted book equity. Không ghép các basis này thành clustering vector.

VNM: F còn thiếu current portion của original long-term debt; không thay bằng
noncurrent loan. Có 8/9 signals nhưng không cộng thành partial total.
PVS: actual bonus issuance đã xác nhận, F issuance signal=0; opening registered-share
line có typo nội bộ 447.966.290 so với outstanding/capital/EPS 477.966.290, đã loại dòng đó.
ACV: EPS numerator reported 10.814.923.270.844 khác parent NI 12.452.353.206.691
do excluded KCHTHK/airport security. Reserve 2025 chưa provisionally allocated;
reported basic EPS tính được, normalized numerator và diluted EPS vẫn unknown.

## Bán niên, TTM và publication

| Mã | Kỳ | Vintage nguồn | EPS basic kỳ 6 tháng | Usable from |
|---|---|---|---:|---|
{chr(10).join(interim_rows)}

Comparative trong vintage 2026 chỉ biết từ publication 2026; không backfill về 2025.
VNM H1 2025 parent profit/reserve/numerator/shares khớp exact note trong PDF 2025;
review current note so sánh/accounting presentation giữ parent common basis.
Numeric TTM prior YTD lấy từ comparative của báo cáo 2026, không dùng undated old PDF
làm numeric PIT source. Ghép reported numerator/share-days cho TTM 01/07/2025–30/06/2026:
**EPS ≈ {number(result['results'][0]['ttm']['value'],2)}, P/E 28/08 ≈ {number(result['results'][0]['ttm_pe'])}**.
VNM annual/interim dates là exact-attachment PHS/HOSE mirror; primary publication
chưa verified. TTM là reference trên reported deduction practice, strict normalized
EPS và production acceptance vẫn null/pending.

PVS H1 2025 original: parent profit 690.128.896.555, deduction 154.026.996.435,
weighted shares 477.966.290. Comparative 2026: 687.363.021.076,
223.460.562.322, 511.420.099. Parent profit lệch −2.765.875.479 VND;
không chỉ là bonus-share adjustment. Chưa có compatible FY bridge nên TTM/P-E TTM null.
PVS annual publication 24/03 → usable 25/03; H1 2026 official date 14/08 → 17/08.
ACV annual publication 31/03 → usable 01/04. Reviewed H1 2026 công bố 03/09,
sau market cutoff 28/08: inventory giữ PDF, calculation loại source này.
Bản Q2 unaudited 03/08 đã tải/OCR prefix nhưng EPS scope/note chưa nghiệm thu,
nên chưa dùng để thay reviewed H1. VNM/ACV 2024 auxiliary dates còn unknown:
F/M chứa auxiliary inputs chỉ có arithmetic, chưa all-input date-PIT acceptance.

## Blocker và bước cần khép trước khi scale

1. Chốt original long-term current debt portion VNM để đủ F 9/9; xác minh primary
   VNM và auxiliary publication dates, giữ mirror/primary quality riêng.
2. PVS: lấy FY/H1 restatement reconciliation để bridge parent earnings, reserves và
   bonus basis. ACV: review Q2 eligible EPS basis hoặc bổ sung market sau reviewed-H1 release;
   không dùng future source vào snapshot cũ.
3. Hoàn thiện effective share-event ledger và book-equity movements trước current
   P/B; làm independent review strict F/M/normalized EPS và historical identity.
4. Bổ sung các năm khác, nghiệm thu representative pilot/source/cost trước FIN-D5.
   Không crawl 1.000 mã bằng workflow manual hiện tại. Reuse structured candidates
   sau khi units/semantics được review; PDF/visual-review là fallback có budget.

[Blocker matrix](blockers.json) tách từng mã/task. Plan vẫn năm stages;
FIN-D4 annual reference slice complete, overall acceptance PARTIAL, FIN-D5 PENDING.
Legacy readiness giữ 153/1.176, date references 138, strict task matrix 0/120;
158 facts mới là slice riêng, không cộng cơ học vào matrix khác basis.

## Kiểm tra và log

- {tests['targeted']} targeted tests PASS; compile và synthetic smoke PASS.
- Full suite {tests['full']} tests: {len(tests['full_failures'])} failure(s).
  Lỗi frozen M2-PREP `docs/DECISIONS.md` checksum đã tồn tại trong các stage trước;
  không sửa frozen input hoặc assertion để làm xanh gate.
- v3/v4: toàn bộ {len(names)} files, gồm manifests/results/facts/config/source snapshots,
  byte-identical. {len(self_review)} self-review checks PASS.
- Financial/research/full-universe gates false; không commit hoặc đổi branch.

[Targeted log](logs/targeted-tests-final.txt), [full-suite log](logs/full-tests.txt),
[compile](logs/compile-exit.txt), [smoke](logs/synthetic-smoke.txt),
[run](logs/pilot-run.txt), [replay](logs/replay-run.txt), [verification](verification.json).
Work log là journal tổng hợp từ inventories và log thực tế; không phải terminal transcript
của toàn bộ discovery trước đó. UTC `fetched_at` được giữ nguyên; report theo ngày client Asia/Saigon.
'''
    if (OUT/'manifest.json').exists(): raise ValueError('report already sealed')
    for name, content in [('report.md', md.encode('utf8')), ('report.json', encoded(report_json)),
                          ('blockers.json', encoded(blockers)), ('verification.json', encoded(dict(tests=tests,self_review=self_review,replay_file_count=len(names)))),
                          ('builder.py', Path(__file__).read_bytes())]:
        immutable_write(OUT/name, content)
    journal = [dict(activity='PUBLIC_PDF_HTML_ACQUISITION', record=r) for r in inventory]
    journal += [dict(activity='RAW_QUOTE_ACQUISITION', record=r) for r in price_inventory]
    journal += [dict(activity='SELECTED_PAGE_OCR', run=n, pages=v, manifest_sha256=file_hash(ROOT/n/'manifest.json')) for n,v in ocr_counts.items()]
    journal += [dict(activity='REVIEW_AND_REFERENCE_RUN', run=str(RUN.relative_to(ROOT)), facts=len(facts), counts=counts),
                dict(activity='TESTS_AND_REPLAY', tests=tests, byte_identical=True),
                dict(activity='HANDOFF', stage=result['stage_status'], gates=dict(financial_features_allowed=False,research_ready=False,full_universe_allowed=False))]
    immutable_write(OUT/'work-log.jsonl', ''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in journal).encode('utf8'))
    immutable_write(OUT/'manifest.json', encoded(dict(files={p.relative_to(OUT).as_posix():file_hash(p) for p in OUT.rglob('*') if p.is_file()})))
    print(json.dumps(dict(output=str(OUT),counts=counts,tests=tests)))


if __name__ == '__main__': build()
