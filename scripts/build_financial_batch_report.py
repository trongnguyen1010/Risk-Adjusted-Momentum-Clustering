"""Seal Vietnamese process/report evidence for the bounded batch flow."""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_batch_evidence import seal
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.experiments.financial_batch_flow import verify_flow

OUT=ROOT/'artifacts/reports/financial-batch-flow-v1'
ACTIVE='data/financial/batch_flow_v9_final'
REPLAY='data/financial/batch_flow_v10_replay'


def build():
    if (OUT/'manifest.json').exists():raise ValueError('report already sealed')
    for run in [ACTIVE,REPLAY]:verify_flow(ROOT,run)
    active=json.loads((ROOT/ACTIVE/'results.json').read_bytes())
    replay=json.loads((ROOT/REPLAY/'results.json').read_bytes())
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!='m1-cafef-primary-experiment':raise ValueError('wrong branch')
    if active['engineering_status']!='COMPLETE' or replay['engineering_status']!='COMPLETE':raise ValueError('batch incomplete')
    if any(replay['metrics'][k] for k in ['logical_requests','pdf_download_attempts','downloaded_bytes','new_checkpoints','text_pages','ocr_pages']):
        raise ValueError('replay did not fully reuse evidence')
    compared=[]
    for adapter in active['reference_runs']:
        a=ROOT/adapter['output'];b=ROOT/REPLAY/'references'/adapter['adapter']
        names={p.name for p in a.iterdir() if p.is_file()}
        if names!={p.name for p in b.iterdir() if p.is_file()} or any((a/n).read_bytes()!=(b/n).read_bytes() for n in names):
            raise ValueError('reference replay differs')
        compared.append(dict(adapter=adapter['adapter'],files=len(names),byte_identical=True))
    if (ROOT/ACTIVE/'review-queue.json').read_bytes()!=(ROOT/REPLAY/'review-queue.json').read_bytes():raise ValueError('review queue replay differs')
    logs=OUT/'logs'
    tests=(logs/'financial-tests-accepted.txt').read_text(encoding='utf8')
    full=(logs/'full-tests-accepted.txt').read_text(encoding='utf8')
    if not re.search(r'\nOK\s*$',tests):raise ValueError('financial tests not passed')
    failures=re.findall(r'^(?:ERROR|FAIL): (.+)$',full,re.MULTILINE)
    if failures and (len(failures)!=1 or 'test_artifact_is_immutable_and_verifiable' not in failures[0] or 'M2-PREP input hash mismatch: docs/DECISIONS.md' not in full):
        raise ValueError('unexpected full-suite regression')
    for name in ['compile-accepted','smoke-accepted','financial-tests-accepted','accepted-engineering','accepted-replay']:
        if int((logs/(name+'-exit.txt')).read_text(encoding='utf-8-sig').strip()):raise ValueError('failed log '+name)
    runs=['data/financial/batch_flow_v1_acquire','data/financial/batch_flow_v2_acquire',
          'data/financial/batch_flow_v3_extract','data/financial/batch_flow_v4_complete',
          'data/financial/batch_flow_v5_verified','data/financial/batch_flow_v6_replay',
          'data/financial/batch_flow_v7_final','data/financial/batch_flow_v8_replay',ACTIVE,REPLAY]
    lineage=[]
    for run in runs:
        verify_inventory(ROOT/run)
        r=json.loads((ROOT/run/'results.json').read_bytes())
        events=[json.loads(l) for l in (ROOT/run/'work-log.jsonl').read_text(encoding='utf8').splitlines()]
        seconds=(datetime.fromisoformat(events[-1]['at'])-datetime.fromisoformat(events[0]['at'])).total_seconds()
        lineage.append(dict(run=run,status=r['engineering_status'],metrics=r['metrics'],
                            elapsed_seconds=round(seconds,3),manifest_sha256=digest((ROOT/run/'manifest.json').read_bytes())))
    docs=[]
    for d in active['documents']:
        x=d['extraction']['payload']
        docs.append(dict(symbol=d['symbol'],pdf_sha256=d['acquisition']['payload']['sha256'],
            pages=x['total_pdf_pages'],text_pages_with_80_chars=sum(not p['low_text'] for p in x['pages']),
            ocr_pages=len(x['ocr_pages']),source_url=d['url'],scope_framework_publication='REQUIRES_REVIEW'))
    acceptance=json.loads((ROOT/ACTIVE/'reference-metrics.json').read_bytes())
    queue=json.loads((ROOT/ACTIVE/'review-queue.json').read_bytes())
    self_review=[dict(check=name,passed=ok) for name,ok in [
        ('Đúng nhánh CafeF',branch=='m1-cafef-primary-experiment'),
        ('10 mã có PDF/text candidate',len(docs)==10 and all(d['extraction']['status']=='COMPLETE' for d in active['documents'])),
        ('Manifest và dependency ngoài run được kiểm chứng',True),
        ('Replay không gọi network/OCR/trích text lại',all(replay['metrics'][k]==0 for k in ['logical_requests','ocr_pages','text_pages','new_checkpoints'])),
        ('Hai adapter tính lại byte-identical',all(c['byte_identical'] for c in compared)),
        ('Không promote reference sang clustering',all(r['financial_cluster_eligible'] is False and r['production_accepted'] is False for r in acceptance)),
        ('Không giả publication/missing thành số',all(d['publication_date'] is None for d in active['documents'])),
        ('VNM F và PVS/ACV TTM còn null',all(r['value'] is None for r in acceptance if
            (r['symbol']=='VNM' and r['task']=='F_SCORE') or (r['symbol'] in ['PVS','ACV'] and r['task']=='EPS_TTM'))),
        ('Full-suite chỉ lỗi frozen M2 đã biết',len(failures)==1),
    ]]
    if not all(x['passed'] for x in self_review):raise ValueError('self-review failed')
    result=dict(date='2026-10-05',branch=branch,stage='BOUNDED_FINANCIAL_AUTOMATION_ENGINEERING',
        engineering_status='COMPLETE_10_SYMBOL_BATCH_AND_OFFLINE_RESUME_VERIFIED',
        financial_acceptance='PARTIAL_REFERENCE_ONLY',active_run=ACTIVE,replay_run=REPLAY,
        documents=docs,lineage=lineage,reference_replay=compared,
        current_unique_pdf_pages=sum(d['pages'] for d in docs),current_unique_ocr_prefix_pages=sum(d['ocr_pages'] for d in docs),
        reference_rows=len(acceptance),reference_values=sum(r['value'] is not None for r in acceptance),
        production_accepted=0,cluster_eligible=0,review_queue_items=len(queue),
        tests=dict(financial=int(re.search(r'Ran (\d+) tests',tests).group(1)),
                   full=int(re.search(r'Ran (\d+) tests',full).group(1)),full_known_errors=failures),
        self_review=self_review,source_resolution=json.loads((ROOT/ACTIVE/'config.json').read_bytes())['source_resolutions'],
        operational_limits=['10 symbols, FY2025 discovery only; not complete 2019-2025 history',
            'Six new symbols have candidates only; no accepted new numeric facts',
            'WinRT en-US OCR and bounded first four scan pages; notes/manual mapping remain',
            'Separate reviewed adapters still bounded to four pilot symbols',
            'No measured unattended 1000-symbol throughput or financial clustering gate'],
        next=['Close pilot semantics/PIT/TTM/event blockers per feature',
              'Validate new template parsers against visually reviewed ground truth',
              'Freeze independent acceptance thresholds before 20-30-symbol batch',
              'Historical snapshot/identity and separate financial protocol review'])
    result['changed_files']=[
        'src/delta_t1/ingestion/financial_batch_evidence.py','src/delta_t1/experiments/financial_batch_flow.py',
        'tests/unit/ingestion/test_financial_batch_evidence.py','tests/unit/experiments/test_financial_batch_flow.py',
        *['scripts/'+n+'.py' for n in ['run_financial_batch_flow','verify_financial_batch_flow','prepare_financial_batch_config',
            'prepare_financial_batch_source_resolution','freeze_financial_batch_config',
            'prepare_financial_execution_batch_handoff','build_financial_batch_report']],
        *['configs/data/financial_batch_flow_v'+str(n)+'.json' for n in range(1,7)],
        'configs/data/financial_dgc_source_resolution_v1.json','configs/data/financial_execution_plan_v8.json',
        'docs/crawl/README.md','docs/README.md','docs/CURRENT_STATUS.md','docs/DECISIONS.md',
        'docs/DELTA_UNIFIED_PROJECT_PLAN.md','CHANGELOG.md']
    for f in result['changed_files']:
        if not (ROOT/f).is_file():raise ValueError('missing handoff file '+f)
    rows='\n'.join(f"| {d['symbol']} | {d['pages']} | {d['text_pages_with_80_chars']} | {d['ocr_pages']} | Candidate, cần review |" for d in docs)
    processes='\n'.join(f"| {Path(r['run']).name} | {r['status']} | {r['metrics']['logical_requests']} | {r['metrics']['text_pages']} | {r['metrics']['ocr_pages']} | {r['elapsed_seconds']:.1f} |" for r in lineage)
    md=f'''# Report xây dựng financial batch flow — 05/10/2026

Đã chạy xuyên suốt batch **10 mã** và kiểm chứng resume/replay offline trên nhánh
`{branch}`. Trạng thái kỹ thuật: COMPLETE ở phạm vi thử nghiệm này.
Financial acceptance vẫn **PARTIAL_REFERENCE_ONLY**; production/cluster eligible = **0**.
Chưa nghiệm thu tự động toàn bộ dữ liệu và chỉ số của ~1.000 mã.

## Flow đã triển khai

```mermaid
flowchart LR
  A[Config nguồn và ngân sách] --> B[Discovery hoặc cache có hash]
  B --> C[PDF gốc và checkpoint]
  C --> D[Embedded text mọi trang]
  D --> E[OCR prefix trang scan theo cap]
  E --> F[Hàng đợi review và ngoại lệ]
  F --> G[Mapping và bằng chứng được review]
  G --> H[Adapter tính reference offline]
  H --> I[Gate theo chỉ số và snapshot]
```

Runner `scripts/run_financial_batch_flow.py` mặc định offline; network cần flag rõ.
Checkpoint có manifest riêng sau mỗi acquisition/extraction; resume chỉ dùng checkpoint
đã sealed, bỏ qua tác vụ chưa sealed của run bị ngắt. Không ghi đè raw/run cũ.
Verifier kiểm cả file/manifest ngoài run mà cache tham chiếu, không chỉ outer manifest.
Transport giữ giới hạn 2 attempts/logical call, interval 2 giây, timeout20 giây;
401/403/429/challenge dừng network cho batch và lineage resume. Không redirect/bypass.
Cache theo frozen epoch và exact request; epoch mới giữ vintage, không suy latest/PIT.

## Quá trình thực hiện và xử lý lỗi

| Lượt chạy | Engineering | Logical calls | Text pages mới | OCR attempts mới | Giây |
|---|---|---:|---:|---:|---:|
{processes}

Lượt đầu cả6 discovery lỗi transport trong sandbox; chạy có quyền network lấy được6
listing và5 PDF, một PDF DGC lỗi404. Không retry/bẻ URL404. Tìm độc lập trang
[công bố DGC](https://ducgiangchem.vn/cbtt-bao-cao-tai-chinh-kiem-toan-nam-2025/),
lưu HTML và đúng attachment ở một supplemental run riêng (2 responses thành công).
Config source-resolution mới thay task URL hỏng bằng official candidate; listing/lỗi cũ
giữ ở lineage và được pin. Đây chưa là reconciliation giá trị hoặc PIT acceptance.

Sau extraction/resume ban đầu, bổ sung transitive verifier và pin code mới. Replay v6
phát hiện resume-from-newest chưa nạp external acquisition checkpoints; sửa truy hồi
exact receipt/manifest từ results của run gần nhất và thêm regression test chuỗi A→B→C.
Lượt v7/v8 nghiệm thu fix này; bổ sung test và giữ boundary latch qua nhiều resume
(403/429→deferred→resume vẫn chặn network). Lượt v9/v10 là final. Lượt intermediate giữ để audit; code hardening đổi extraction fingerprint
nên có trích/OCR lại. Không cộng các lần chạy lặp thành coverage mới.
Các cảnh báo Poppler về font được lưu trong log; không dùng OCR token làm accepted fact.
Đọc lại VNM borrowing notes trang vật lý47–48: reclassification flow không chứng minh
current portion stock tại hai ngày, nên không lấy20.750.493.750 thay input F-score.

## Coverage của artifact hiện hành

| Mã | PDF pages | Trang embedded text ≥80 chars | Trang prefix OCR | Acceptance |
|---|---:|---:|---:|---|
{rows}

Tổng **{result['current_unique_pdf_pages']} PDF/text pages**; **{result['current_unique_ocr_prefix_pages']} unique prefix OCR pages**.
Trong6 mã mới HPG/DGC/MWG/REE/GMD/VHC, acquisition/extraction candidate đã có;
chưa visual-review/mapping toàn bộ bảng/thuyết minh hoặc tính chỉ số mới cho các mã này.
19 queue items =10 document review items +9 blocker items đã biết (khác với số input thiếu).
OCR bốn trang đầu chưa bao phủ thuyết minh; scan còn lại cần chọn trang/OCR riêng.

Hai adapter pilot tính **{result['reference_values']}/{result['reference_rows']} rows có giá trị tham chiếu**,
gồm nhiều decision dates và basis annual/TTM/book snapshot khác nhau; không phải số
chỉ số độc lập hoặc tỷ lệ hoàn thành dự án. Giá trị financial đã nghiệm thu không tăng
so với pilot trước. Không ghép các rows thành một vector clustering.

## Verification và giới hạn scale

- {result['tests']['financial']} financial targeted tests PASS; compile và synthetic smoke PASS.
- Full suite {result['tests']['full']-1}/{result['tests']['full']} PASS, một frozen M2-PREP
  `docs/DECISIONS.md` checksum error đã biết. Không sửa assertion/immutable M2 evidence.
- Hai adapter replay byte-identical; review queue byte-identical.
- Replay v10:0 network calls,0 download,0 text/OCR mới,0 checkpoint mới.
- Corrupt cache, external dependency tampering, interruption resume, budget/offline miss,
  403/429, multiple report vintages, wrong-PDF/host và null/missing có tests.

Có thể dùng runner này cho acquisition/extraction có giới hạn và tiếp tục review.
Điều kiện mở scale cho accepted facts: parser mới qua ground truth theo template,
giới hạn tỷ lệ sai được khóa trước khi test, source completeness/PIT/revisions và
chi phí review đo trên batch20–30 trước khi tăng số mã. Không tự đặt tỷ lệ accuracy
hoặc coverage đã nghiệm thu khi chưa có mẫu review độc lập.

Để mở financial clustering: khép mapping F/M, chọn variant được review; hoàn thiện
TTM/event basis cho valuation đã chọn; publication từng exact vintage; historical
security/sector identity; ít nhất3 năm history dùng được; snapshot theo decision date;
feature registry và protocol financial riêng được freeze/review. Có thể nghiệm thu
feature subset trước, nhưng không impute phần thiếu hoặc sửa protocol M2 market-only.

## Chạy và kiểm chứng

Xem [runbook](../../../docs/crawl/README.md) và
[config active](../../../configs/data/financial_batch_flow_v6.json).
Artifacts: [results](../../../{ACTIVE}/results.json),
[review queue](../../../{ACTIVE}/review-queue.json),
[reference metrics](../../../{ACTIVE}/reference-metrics.json).
Log quá trình nằm trong `logs/` và work-log JSONL từng run.
Danh sách file thay đổi của workstream này nằm trong `report.json.changed_files`;
working tree còn các thay đổi từ những giai đoạn trước, không reset/commit chúng.
Report này sealed bằng manifest; sửa tạo report version mới.
'''
    immutable_write(OUT/'report.md',md.encode('utf8'))
    immutable_write(OUT/'report.json',encoded(result))
    immutable_write(OUT/'self-review.json',encoded(self_review))
    immutable_write(OUT/'builder.py',Path(__file__).read_bytes())
    seal(OUT);verify_inventory(OUT)
    print(json.dumps(dict(report=str(OUT/'report.md'),documents=len(docs),pages=result['current_unique_pdf_pages'],replay='PASS')))

if __name__=='__main__':build()
