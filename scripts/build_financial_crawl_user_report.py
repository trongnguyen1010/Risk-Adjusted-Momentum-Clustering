"""Seal the user-crawler handoff report from actual immutable runs and logs."""
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_crawl import verify
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_batch_evidence import seal
from delta_t1.ingestion.financial_documents import verify_inventory


def build():
    out=ROOT/'artifacts/reports/financial-crawl-user-v1'
    names=['crawl_user_pilot_v1','crawl_user_pilot_v2_network','crawl_user_pilot_v3_pdf',
           'crawl_user_pilot_v4_pdf_verified','crawl_user_pilot_v5_final','crawl_user_pilot_v6_replay',
           'crawl_user_discovery_v1','crawl_user_clean_v1','crawl_user_quarter_v1','crawl_user_quarter_v2_final']
    runs={}
    for name in names:
        relative='data/financial/'+name
        verify(ROOT,relative)
        runs[name]=json.loads((ROOT/relative/'results.json').read_bytes())
    a,b=[ROOT/'data/financial'/name for name in names[4:6]]
    replay={p:(a/p).read_bytes()==(b/p).read_bytes() for p in
            ['candidates.jsonl','candidates.csv','coverage.csv','review-queue.json']}
    assert all(replay.values())
    final=runs['crawl_user_pilot_v5_final']; clean=runs['crawl_user_clean_v1']; quarter=runs['crawl_user_quarter_v2_final']
    assert all(v==0 for k,v in runs['crawl_user_pilot_v6_replay']['metrics'].items() if k!='cache_hits')
    ocr=final['documents'][0]['extraction']['payload']['cell_candidates']
    assert len(ocr)==3 and all(r['reference_qa']['passed'] for r in ocr)
    package=json.loads((out/'package.json').read_bytes())
    assert digest((ROOT/package['path']).read_bytes())==package['sha256']
    full=(out/'logs/full-suite-local.log').read_text(encoding='utf8')
    assert 'Ran 316 tests' in full and 'FAILED (errors=1)' in full and 'M2-PREP input hash mismatch: docs/DECISIONS.md' in full
    handoff=(out/'logs/handoff-tests.log').read_text(encoding='utf8')
    assert re.search(r'Ran 14 tests',handoff) and '\nOK' in handoff
    changed=['src/delta_t1/experiments/financial_crawl.py','src/delta_t1/ingestion/financial_crawl_candidates.py',
        'src/delta_t1/ingestion/financial_crawl_pdf.py','scripts/crawl_financial.py','scripts/crawl_financial.ps1',
        'scripts/package_financial_crawler.py','scripts/build_financial_crawl_user_report.py',
        'tests/unit/experiments/test_financial_crawl.py','configs/data/financial_crawl_user.example.json',
        'configs/data/financial_crawl_requirements.txt','configs/data/financial_crawl_pilot_v1.json',
        'configs/data/financial_crawl_pilot_pdf_v1.json','configs/data/financial_crawl_discovery_pilot_v1.json',
        'configs/data/financial_crawl_quarter_pilot_v1.json','configs/data/financial_execution_plan_v9.json',
        'docs/crawl/FINANCIAL_CRAWLER_USER_GUIDE.md','docs/crawl/README.md','docs/README.md',
        'docs/CURRENT_STATUS.md','docs/DECISIONS.md','CHANGELOG.md']
    summary=dict(date='2026-10-06',branch='m1-cafef-primary-experiment',
        handoff_status='COMPLETE_BOUNDED_CANDIDATE_CRAWLER',financial_acceptance='PENDING',
        financial_features_allowed=False,full_universe_allowed=False,financial_cluster_eligible_rows=0,
        final_metrics=final['metrics'],wire_cells=final['summary']['wire_cells'],
        in_target_cells=final['summary']['in_target_cells'],new_accepted_facts=0,
        clean_metrics=clean['metrics'],quarter_ambiguous_cells=quarter['summary']['statuses']['HEADER_PERIOD_DUPLICATION_REVIEW_REQUIRED'],
        replay_byte_identical=replay,tests=dict(new=14,source_package=14,full_pass=315,full_total=316,
                                             known_failure='Frozen M2-PREP docs/DECISIONS.md checksum'),
        package=package,changed_files=changed,
        file_sha256={p:digest((ROOT/p).read_bytes()) for p in changed},
        run_manifests={'data/financial/'+name:digest((ROOT/'data/financial'/name/'manifest.json').read_bytes()) for name in names})
    table='\n'.join(f"| {name} | {r['engineering_status']} | {r['metrics']['logical_requests']} | {r['metrics']['cache_hits']} | {r['metrics']['text_pages']} | {r['metrics']['ocr_pages']} |" for name,r in runs.items())
    report=f'''# Report bàn giao financial crawler — 06/10/2026

Đã tạo **flow có thể đưa cho người dùng chạy** trên nhánh `m1-cafef-primary-experiment`:
config → doctor/plan → structured data → document discovery hoặc exact issuer URLs →
PDF/text/selected-page OCR → candidates/coverage/accounting QA → review queue → verify.
Trạng thái **COMPLETE cho bounded candidate crawler**, tối đa10 mã/batch pilot.
Financial acceptance/full-universe/financial cluster vẫn **PENDING/false**.
Flow chưa tự lấy đủ mọi input score hoặc nghiệm thu dữ liệu của1.000 mã.

## Những thay đổi đã thực hiện

- CLI `scripts/crawl_financial.py` có doctor, plan, run/resume và verify; PowerShell
  launcher tự kiểm Python chạy được. Config mẫu không có path tới pilot artifacts.
- Structured KBS: raw giữ hash, normalizer giữ từng wire cell/header/null, crosswalk
  theo report/sector chỉ tạo candidate. Coverage ghi cụ thể mã/kỳ/field còn thiếu.
- Structured rows có cùng period identity ở nhiều cột không được cấp target coverage.
  Header dài/pageSize không tạo thêm values; không lấy metadata dates làm PIT.
- PDF: trích text mọi trang trong cap; OCR trang vật lý được chọn, kể cả thuyết minh
  ở cuối PDF. Cell template gắn exact PDF hash, xuất tọa độ và reference QA.
- A=L+E QA chỉ dùng cùng response/header; conflict/missing không average/fill.
  Raw JSONL và CSV/coverage exports đi kèm source hash; CSV escape spreadsheet formulas.
- Checkpoints/resume kế thừa transport/budgets/hard-stop latch cũ. Verifier kiểm cả
  seed manifest ngoài run và candidate raw copies; lỗi dependency chặn trước network.
- Gói source-only {package['files']} files, {package['bytes']} bytes, không chứa raw/cache.
  Đã giải nén vào thư mục riêng, verify manifest, doctor và14 tests PASS.

## Quá trình chạy và xử lý lỗi

| Run | Collection | Logical network calls | Cache hits | Text pages mới | OCR attempts mới |
|---|---|---:|---:|---:|---:|
{table}

Lượt sandbox đầu tái dùng12 structured responses của bốn pilot;18 calls cho sáu mã
mới lỗi transport. Lượt có quyền network phù hợp lấy đủ18 responses; giữ nguyên
run/log cũ. Không có workaround access control hoặc hidden provider fallback.

OCR lần đầu bị sandbox chặn PowerShell script (`AuthorizationManager`); stderr được
lưu vào checkpoint, run trả PARTIAL. Chạy local được phép hoàn thành OCR một trang.
Không thêm ExecutionPolicy Bypass hoặc thay chính sách bảo mật hệ thống.

Discovery thực tế bốn mã: FPT/VNM CafeF attachments404, PVS/ACV có exact cached PDF.
Không bẻ URL404. Config bàn giao dùng exact FPT issuer/VNM mirror/PVS-ACV attachment
đã thu thập độc lập trước đó; vẫn giữ failed discovery artifacts và publication pending.

Quarterly FPT phát hiện wire headers lặp Q4 cho nhiều cột có giá trị khác nhau.
Lượt v1 giữ evidence nhưng còn đếm các header đó vào candidates theo kỳ; sau bổ sung
duplicate-header guard, v2 có **654 cells mơ hồ**, không được đếm target coverage.
Không suy kỳ đúng từ magnitude hoặc chuyển cột sang quý khác.

Python `.venv` ban đầu không khởi động trong sandbox; kiểm ngoài sandbox xác nhận
venv vẫn hợp lệ. Bundled Python dùng cho PDF runs; đã cài pypdf6.10.0 vào project
venv và default launcher doctor READY. Không thay dependency global.

## Kết quả thực tế

**Batch10 mã annual:**30 structured responses,8.720 wire cells,2.180 cells target2025.
552 monetary candidates/69 per-share unit exceptions là counts trên mọi wire years,
không phải số chỉ số hoặc accepted facts.10 balance-equation checks PASS trên
target2025; các monetary semantics vẫn phải đối chiếu PDF.

Core candidate gaps2025: diluted EPS ở VNM/ACV/HPG; noncurrent loan/finance-lease
ở DGC/MWG/VHC. Đây chỉ là gaps của candidate crosswalk; strict F/M, thuyết minh,
PIT/revisions, TTM/events và historical identity còn yêu cầu riêng.

**Clean user run4 mã, không seed/resume:**12 structured responses +4 PDF downloads,
3.488 wire cells/872 target2025 cells;343 PDF/text pages và1 selected OCR page.
Mọi acquisition/extraction được yêu cầu COMPLETE; coverage/acceptance vẫn PARTIAL.
FPT note EPS trang vật lý55 trích3 ô và match reference đã review:
numerator8.865.959.921.832 VND; weighted basic shares1.699.740.091; printed EPS5.216.
Đã xem ảnh và xác nhận đúng hàng/cột2025. Template này chỉ dùng cho exact PDF hash.

**Replay10 mã:**32 cache hits,0 network/download/text/OCR/new checkpoints.
Candidates JSONL/CSV, coverage và review queue byte-identical giữa final/replay.
Các scan pages chưa chọn OCR vẫn được giữ trong queue; COMPLETE chỉ nói về scope
crawl/extraction được cấu hình. Lượt này **0 accepted facts mới/0 cluster eligible**;
pilot reference calculations cũ và strict task matrix không được nâng trạng thái.

## Kiểm chứng và self-review

-14 tests mới PASS: no-pilot entrypoint, offline/resume nhiều đời, 401/403/429 latch,
  corrupt dependencies, budget, JSON invalid/empty/nonfinite, sector/report templates,
  duplicate headers, accounting conflicts, discovery404/vintages, selected OCR/QA.
- Clean-room source package14 tests PASS; doctor READY; manifest hash PASS.
- Full suite local315/316 PASS; lỗi duy nhất là frozen M2-PREP
  `docs/DECISIONS.md` checksum đã có từ trước. Không sửa assertion/evidence để làm xanh.
- Compile và synthetic smoke PASS; verifier final/replay/clean và git diff check PASS.
- Full suite trong sandbox trước đó còn lỗi localhost HTTP và thiếu matplotlib;
  log giữ riêng. Chạy bằng project venv ngoài sandbox đã loại các lỗi môi trường này.
- Self-review: ingestion không tính model; feature/network boundaries giữ nguyên;
  không sửa market-only protocol, canonical market hoặc frozen artifacts.
  Source dates/identity/missing semantics không bị promote; không mở scale bằng
  cách chia toàn universe thành batches nhỏ.

## Bàn giao và cách chạy

- [Hướng dẫn người dùng](../../../docs/crawl/FINANCIAL_CRAWLER_USER_GUIDE.md).
- [Gói source ZIP](../../financial_crawler/financial_crawler_user_v1.zip).
- [Config mẫu](../../../configs/data/financial_crawl_user.example.json).
- [Changelog](../../../CHANGELOG.md), [execution plan v9](../../../configs/data/financial_execution_plan_v9.json).
- [Final results](../../../data/financial/crawl_user_pilot_v5_final/results.json),
  [clean-run report](../../../data/financial/crawl_user_clean_v1/report.md).
- Log chi tiết trong `logs/`; source/file/run hashes và changed files trong `report.json`.

```powershell
.\\scripts\\crawl_financial.ps1 -Action doctor
.\\scripts\\crawl_financial.ps1 -Action run -Output data/financial/my_run_01 -ExecuteNetwork
.\\scripts\\crawl_financial.ps1 -Action verify -Run data/financial/my_run_01
```

Máy khác cần Python>=3.11, pinned requirements, Poppler/Windows OCR cho selected
scan pages. Config mẫu là FY2025 bốn mã có exact sources; mã/năm mới dùng discovery
và source-resolution queue, không tự coi nguồn mới nhất là PIT.

## Phần chưa nghiệm thu để mở financial cluster/1.000 mã

Parser và semantic templates trên unseen PDF; các notes/input strict F/M; dated
publication từng vintage, revisions, compatible TTM/share events; security/sector
history, ít nhất3 năm usable history; approved feature subset và frozen financial
protocol. Cần benchmark độc lập và khóa accuracy/coverage/review-cost trước batch
20–30 rồi mở scale. User crawler v1 đã bàn giao được; full financial acceptance
không thể suy từ trạng thái download/OCR hoặc số wire cells.

Report này được sealed bằng manifest; sửa phải tạo report version mới.
'''
    immutable_write(out/'report.md',report.encode('utf8'))
    immutable_write(out/'report.json',encoded(summary))
    immutable_write(out/'self-review.json',encoded(dict(status='PASS_FOR_BOUNDED_CRAWLER_HANDOFF',
        financial_acceptance='PENDING',immutable_evidence_preserved=True,
        no_market_protocol_change=True,no_access_bypass=True,closed_gates=True,
        source_package_tests=14,full_suite_known_failure=True)))
    immutable_write(out/'builder.py',Path(__file__).read_bytes())
    seal(out)
    verify_inventory(out)
    print(json.dumps(dict(report=str(out/'report.md'),package=package['path'],handoff=summary['handoff_status'])))


if __name__=='__main__':
    build()
