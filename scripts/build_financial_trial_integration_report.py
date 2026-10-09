"""Render the reviewed integration handoff from sealed results and test logs."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_batch_evidence import seal


def build():
    run='data/financial/cafef_trial50_reviewed_20261008_v1'
    report=ROOT/'artifacts/reports/cafef-financial-reviewed-integration-v1'
    folder=ROOT/run
    result=json.loads((folder/'results.json').read_bytes())
    ledger=json.loads((folder/'reference-ledger.json').read_bytes())
    rows=json.loads((folder/'assessment.json').read_bytes())
    symbols=json.loads((folder/'per-symbol.json').read_bytes())
    full=(report/'full-tests.log').read_text(encoding='utf-8-sig')
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s',full)
    if not match:raise ValueError('full gate must finish before report sealing')
    tests=dict(total=int(match[1]),seconds=float(match[2]),
        errors=len(re.findall(r'^ERROR: ',full,re.M)),failures=len(re.findall(r'^FAIL: ',full,re.M)))
    targeted=(report/'targeted-tests.log').read_text(encoding='utf-8-sig')
    if not re.search(r'^OK\s*$',targeted,re.M):raise ValueError('targeted tests not passing')
    verification=json.loads((report/'verification.log').read_text(encoding='utf-8-sig'))
    if verification['status']!='PASS':raise ValueError('integration verification failed')
    manifest_pin=digest((folder/'manifest.json').read_bytes())
    controls=[r for r in ledger if r['symbol'] not in {s['symbol'] for s in symbols}]
    priorities=['PHP','VCS','VEA','PAN']
    queue=[]
    for s in symbols:
        tasks=[r for r in rows if r['symbol']==s['symbol']]
        missing=sorted({v for r in tasks for v in r['missing_candidate_inputs']})
        queue.append(dict(symbol=s['symbol'], proposed_company_type=s['proposed_company_type'],
            priority='REGULAR_WIRE_COMPLETE_REVIEW_PILOT' if s['symbol'] in priorities else
                'EXISTING_REVIEW_ACCEPTANCE_AND_HISTORY' if s['symbol'] in ['FPT','ACV'] else
                'SECTOR_TEMPLATE_FIRST' if s['proposed_company_type']!='Regular' else 'REGULAR_DOCUMENT_REVIEW',
            missing_exact_candidate_inputs=missing, annual_reference_cells=s['annual_reference_cells'],
            actions=['VERIFY_CONSOLIDATED_VAS_UNITS_AND_EXACT_REPORT_VINTAGE',
                     'REVIEW_NOTES_EPS_SHARES_DEBT_PPE_AND_EBIT',
                     'ATTACH_PUBLICATION_TO_EXACT_DOCUMENT_AND_APPLY_DATE_ONLY_POLICY',
                     'RECONCILE_REVISIONS_AND_EFFECTIVE_SHARE_EVENTS',
                     'CALCULATE_EACH_SUPPORTED_VARIANT_WITH_UNKNOWN_PRESERVED'],
            execution_authorized_by_this_artifact=False, financial_cluster_allowed=False))
    analysis=dict(result,full_tests=tests,targeted_tests=57,
        source_manifest_sha256=manifest_pin, controls_reference_values=sum(r['value'] is not None for r in controls),
        assessment_status_counts=dict(Counter(r['reference_status'] for r in rows)),
        in_cohort_pit_status_counts=dict(Counter(r['pit_status'] for r in ledger if r['symbol'] in ['FPT','ACV'] and r['value'] is not None)))
    immutable_write(report/'analysis.json',encoded(analysis))
    immutable_write(report/'next-review-plan.json',encoded(queue))
    for name in ['per-symbol.csv','assessment.csv','reference-ledger.json']:
        immutable_write(report/name,(folder/name).read_bytes())
    table='\n'.join('| '+ ' | '.join([r['symbol'],str(r['year']) if r['year'] else r['period'],r['task'],str(r['value']),r['basis']])+' |'
                    for r in ledger if r['symbol'] in ['FPT','ACV'] and r['value'] is not None)
    text=f'''# Report nối CafeF trial50 với financial reference — 08/10/2026

Stage integration offline đã hoàn thành; financial acceptance còn PARTIAL. **15/900 ô annual có giá trị reference**, trên **2/50 mã**: FPT có9 ô qua2023–2025, ACV có6 ô năm2025. Thêm3 giá trị FPT theo cơ sở khác annual: EPS TTM, P/E TTM và P/B gross ESOP capital bridge. Tổng18 giá trị trong cohort; không có accepted HTML fact mới. Đây không phải tỷ lệ hoàn thành dự án hoặc tỷ lệ chỉ số production-ready.

Lượt trước0/900 là checklist strict của candidates-only runner, chưa gọi calculator với facts đã review. Kết quả mới sửa cách đánh giá coverage bằng cách nối evidence/calculators đã có, không sửa artifact cũ và không bỏ điều kiện strict. VNM/PVS là controls ngoài frozen50; không đưa vào mẫu số50 hoặc900.

Run: `{run}`; manifest SHA256 `{manifest_pin}`. Nhánh thực thi `m1-cafef-primary-experiment`. Decision của reference adapters là28/08/2026; không dùng ngày crawl08/10 như ngày dữ liệu đã biết trong lịch sử. Plan financial năm giai đoạn và market-only protocol giữ nguyên.

Flow triển khai: sealed CafeF HTML candidates → kiểm raw/cache/reference pins → kiểm reviewed PDF/image/derivation proofs → replay annual calculators và hai reviewed adapters → ledger có kỳ/basis/publication status → assessment từng task-year và per-symbol → verify/review queue. Flow này nối các reference đã có; chưa tự động review facts của48 mã còn lại.

FPT annual F/M được tính lại từ exact reviewed inputs của các snapshot đã lưu; EPS/Z được tính lại và đối chiếu arithmetic/QA. Replay FPT adapter tái kiểm annual upstream, TTM/equity review và tính gross capital bridge; adapter VNM/PVS/ACV dựng lại reviewed facts và tính annual/TTM theo contract hiện có. Không tạo công thức, đổi variants, mở feature registry hoặc chuyển HTML candidates thành accepted numeric facts.

| Mã | Kỳ | Nhóm | Giá trị reference | Basis |
| --- | --- | --- | --- | --- |
{table}

FPT: F VAS2023=6,2024=7,2025=3; M2024/2025 sensitivity, Z EM double-prime và EPS annual2024/2025 có exact DATE_ONLY input evidence. Các snapshot F lịch sử giữ decision date gốc ở ledger; không tuyên bố đã kiểm đầy đủ mọi revision mới đến28/08/2026. EPS2025 annual≈5216,07 khác EPS TTM≈5570,36. P/E≈13,141 dùng TTM; P/B≈3,14038 dùng gross ESOP bridge, khác latest-reported-equity reference≈3,14891. Không trộn các basis vào900 ô annual.

ACV: có6 annual arithmetic references, **chưa đủ PIT cho toàn bộ auxiliary inputs**; trường thiếu được giữ trong `references/THREE_SYMBOL_2025/facts.json` và blocker `AUXILIARY_PUBLICATION_UNVERIFIED`. EPS annual2025≈3018,84; P/E≈14,04515 dùng annual EPS, P/B≈2,17465 dùng book/common-shares2025 snapshot. Đây chưa phải current TTM/event-adjusted valuation; EPS/P/E TTM vẫn null. Không coi6 arithmetic values là6 PIT/production-ready metrics.

DATE_ONLY đã được sử dụng, không yêu cầu thêm giờ công bố: dùng phiên exchange quan sát được đầu tiên **sau** publication date, rồi kiểm decision date≥usable date. FPT FY2025 công bố19/03/2026, usable20/03/2026. `available_at=null` với DATE_ONLY không làm mất date-PIT. Ngày chỉ gắn exact PDF/vintage; không copy sang HTML theo ticker/year hoặc audit/signature date. Calendar vẫn là observed-session union, không tự nhận authoritative exchange calendar.

Đối với48 mã còn lại, đã có raw/candidate mapping nhưng chưa có reviewed adapter cho exact notes, unit/scope/vintage và publication/revisions.10 mã proposed Bank/Securities/Insurance cần template riêng trước generic F/M/Z. Không thể suy numeric accuracy toàn50 từ29/30 reference comparisons của FPT/ACV; difference ACV2024 vendor EPS giữ nguyên, không ghi đè để đạt QA.

Handoff tiếp theo ở `next-review-plan.json`: ưu tiên kiểm4 Regular có wire13/13 kỳ đủ3 statements là PHP/VCS/VEA/PAN; ACV là control đã review một phần. Wave này cần chọn exact consolidated reports, review thuyết minh shares/numerator/debt/PPE/EBIT, publication DATE_ONLY và revisions. FPT cần chốt strict variants, reserve/event/effective-share basis và historical identity; ACV cần auxiliary dates, annual2023/2024 và TTM bridge có thể dùng tại decision. Chỉ khi evidence mới được review mới thêm adapter; crawler vẫn CafeF chính, không tự fallback KBS. Chưa chạy wave này trong stage hiện tại.

Đã tạo một integration root nhỏ,37 files/{sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()):,} bytes, không copy raw HTML/PDF/images. Manifest/pointers giữ lineage;130 external evidence files được pin và verify. Retention đọc thêm `financial_active_integration_v1.json` để giữ integration và transitive parents. Không cleanup/delete thêm.

Validation:57 targeted tests PASS; compileall và synthetic smoke PASS; offline verification/replay PASS. Full repository snapshot: {tests['total']} tests, {tests['total']-tests['errors']-tests['failures']} PASS, {tests['errors']} ERROR, {tests['failures']} FAIL ({tests['seconds']}s). Lỗi frozen M2-PREP `docs/DECISIONS.md` checksum đã tồn tại trước stage này; không sửa frozen artifact/assertion để làm gate xanh. Xem `full-tests.log` cho exact diagnostics.

Strict ready vẫn0/900, financial features/cluster/research/full-universe/unattended acceptance/next100 vẫnfalse. Engineering stage integration PASS, toàn repository gate có lỗi cũ và financial acceptance PARTIAL. Chỉ báo các metric/reference có evidence, không kết luận0 dòng dùng được hoặc toàn50 đã đủ financial clustering.
'''
    immutable_write(report/'report.md',text.encode('utf8'))
    immutable_write(report/'worklog.md',('''# Work log — reviewed integration

- Xác nhận nhánh CafeF và frozen50; đọc active plan/date policy/reference flows. Phát hiện0/900 cũ là candidate checklist, không phải900 calculator failures.
- Xác nhận FPT/ACV thuộc50, VNM/PVS ngoài cohort. Chọn orchestration offline và existing variants, không crawl/PDF/OCR mới.
- Viết integration/CLI, tách annual và TTM/book-share bridge; preserve raw và sealed runs. Thử replay lần đầu dừng vì M-score note aliases khác tên calculator; chưa tạo output. Đối chiếu source_completion và dùng đúng hai aliases đã có, không đổi định nghĩa.
- Replay thành công:9 FPT annual+6 ACV annual+3 FPT nonannual values; auxiliary ACV PIT giữ pending. Kiểm130 external pins và regression tests chống future/unreviewed facts, basis collision, unit/scope/vintage, source tamper và controls ngoài cohort.
- Bổ sung active retention pointer; chạy targeted/full/compile/synthetic/verify. Xuất report, per-symbol/assessment/ledger và next-review-plan; không tự chạy wave review/100 mã hoặc mở cluster.
''').encode('utf8'))
    immutable_write(report/'self-review.md',('''# Self-review

- PASS: exact frozen50 và900 annual tasks; controls riêng; annual/TTM/book bases không trộn; unknown giữnull, không magnitude scaling/source priority.
- PASS: DATE_ONLY dùng policy đã duyệt; PDF/vintage evidence nguyên vẹn, không truyền publication sang HTML; FPT input dates kiểm tại source snapshot và ACV auxiliary gaps không bị che.
- PASS: dùng existing reference calculators/adapters; gate strict/production/research/cluster false; không đổi market-only hoặc five-stage methodology.
- PASS: immutable output,130 external evidence pins, assessment replay,57 targeted tests, compile/synthetic, active retention closure.
- PARTIAL:48 mã chưa reviewed inputs; ACV dates/history/TTM chưa đủ; strict variants/identity/revisions/events chưa accepted. Full gate còn frozen M2-PREP checksum error cũ.
- STOP: stage nối reference đã hoàn thành; wave notes/publication review là stage tiếp theo, chưa chạy tự động.
''').encode('utf8'))
    immutable_write(report/'source-pins.json',encoded(dict(run_manifest=manifest_pin,
        input_config_sha256=digest((ROOT/'configs/data/financial_trial_integration_v1.json').read_bytes()),
        report_builder_sha256=digest(Path(__file__).read_bytes()))))
    seal(report)
    print(json.dumps(dict(status='SEALED',annual_reference_cells=result['annual_reference_cells'],full_tests=tests)))


if __name__=='__main__':build()
