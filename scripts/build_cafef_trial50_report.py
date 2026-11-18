"""Offline report builder for the bounded CafeF candidate trial."""
import argparse
import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.cafef_financial_trial import CLOSED
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from crawl_cafef_financial import verify_handoff


def load(folder,name):return json.loads((folder/name).read_bytes())


def analyze(root,relative):
    folder=root/relative;verification=verify_handoff(root,relative)
    r=load(folder,'results.json');coverage=load(folder,'coverage.json')
    tasks=load(folder,'feature-readiness.json');requirements=load(folder,'requirements.json')
    queue=load(folder,'review-queue.json');members={m['ticker']:m for m in load(folder,'plan.json')['members']}
    rows=[]
    for s in r['symbols']:
        cov=[x for x in coverage if x['symbol']==s];req=[x for x in requirements if x['symbol']==s]
        requests=[x for x in r['requests'] if x['symbol']==s];task=[x for x in tasks if x['symbol']==s]
        periods=defaultdict(list)
        for x in cov:periods[x['year'],x['quarter']].append(x)
        rows.append(dict(symbol=s,proposed_type=members.get(s,{}).get('proposed_company_type','Regular'),
            base_parsed=sum(x['phase']=='BASE' and x['status']=='PARSED_CANDIDATES' for x in requests),
            request_errors=sum(x['status']!='PARSED_CANDIDATES' for x in requests),
            annual_wire=sum(x['quarter']==0 and x['wire_present'] for x in cov),annual_targets=15,
            quarter_wire=sum(x['quarter']>0 and x['wire_present'] for x in cov),quarter_targets=24,
            complete_three_statement_periods=sum(all(x['wire_present'] for x in p) for p in periods.values()),
            target_periods=13,annual_candidate_cells=sum(x['status']=='UNVERIFIED_CANDIDATE_PRESENT' for x in req),
            value_conflicts=sum(x['status']=='VALUE_CONFLICT' for x in req),
            candidate_task_inputs=sum(x['candidate_input_cells'] for x in task),
            required_task_inputs=sum(x['required_input_cells'] for x in task),strict_tasks_ready=0))
    byperiod=[]
    for year,quarter in sorted({(x['year'],x['quarter']) for x in coverage}):
        cov=[x for x in coverage if (x['year'],x['quarter'])==(year,quarter)]
        groups=defaultdict(list)
        for x in cov:groups[x['symbol']].append(x)
        byperiod.append(dict(year=year,quarter=quarter,wire=sum(x['wire_present'] for x in cov),targets=len(cov),
            symbols_with_all_three=sum(all(x['wire_present'] for x in group) for group in groups.values())))
    bytask=[]
    for task in sorted({x['task'] for x in tasks}):
        group=[x for x in tasks if x['task']==task]
        bytask.append(dict(task=task,task_year_rows=len(group),candidate_inputs=sum(x['candidate_input_cells'] for x in group),
            required_inputs=sum(x['required_input_cells'] for x in group),
            all_exact_candidate_inputs=sum(x['candidate_input_cells']==x['required_input_cells'] for x in group),
            strict_ready=0,computed_values=0))
    sizes=[p.stat().st_size for p in folder.rglob('*') if p.is_file()]
    stats=dict(version='cafef-trial50-report-v1',run=relative,run_manifest_sha256=digest((folder/'manifest.json').read_bytes()),
        verification=verification,status=r['engineering_status'],symbols=r['symbols'],attempted_symbols=r['attempted_symbols'],
        base_expected=r['base_expected'],base_parsed=r['base_success'],gap_requests=r['gap_requests'],
        request_status_counts=dict(Counter(x['status'] for x in r['requests'])),
        physical_attempts=r['trial_totals']['transport_attempts'],logical_requests=r['trial_totals']['logical_requests'],
        downloaded_bytes=r['trial_totals']['downloaded_bytes'],reserved_bytes=r['trial_totals']['reserved_bytes'],
        elapsed_seconds=r['collection_seconds'],access_boundary=r['trial_totals']['boundary'],budget_stop=r['trial_totals']['budget_stop'],
        wire_present=r['present_statement_periods'],wire_targets=r['target_statement_periods'],
        wire_pct=round(100*r['present_statement_periods']/r['target_statement_periods'],2),
        raw_candidate_cells=r['wire_cells'],mapped_candidate_annual_cells=sum(x['annual_candidate_cells'] for x in rows),
        full_history_symbols=sum(x['annual_wire']==15 and x['quarter_wire']==24 for x in rows),
        qa_counts=r['qa_counts'],qa_replay_matches_benchmark=r['qa_replay_matches_benchmark'],
        conflicts=r['conflicts'],review_queue_counts=dict(Counter(x['stage'] for x in queue)),
        output_files=len(sizes),output_bytes=sum(sizes),accepted_facts=0,strict_tasks_ready=0,
        pdf_downloads=0,ocr_pages=0,per_symbol=rows,per_period=byperiod,per_task=bytask,**CLOSED)
    return stats


def render(a):
    n=len(a['symbols']);lines=[f'# CafeF-first financial trial50 — report 08/10/2026', '',
        f"Lượt crawl đã thử **{a['attempted_symbols']}/{n} mã**, status **{a['status']}**. "
        f"Có **{a['wire_present']}/{a['wire_targets']} ({a['wire_pct']}%)** target statement-periods chứa raw value. "
        'Đây là độ phủ raw; chưa nghiệm thu số liệu, PIT hoặc mở financial cluster.', '',
        '## Phạm vi và các công việc đã thực hiện', '',
        '1. Giữ frozen membership50 và market snapshot, nhánh `m1-cafef-primary-experiment`; '
        'không đổi market-only clustering hoặc plan financial năm giai đoạn.',
        '2. Tạo runner/version CafeF detail riêng; ticker/header/anchor/row width/numeric grammar '
        'được kiểm trước crosswalk. KBS không tham gia lượt này.',
        '3. Pilot4 sử dụng48 raw benchmark,11 request bù; replay59 cache hits,0 request mới, '
        'exports được đối chiếu byte-identical. Pilot consistency gate giữ72 MATCH/5 DIFFERENCE/1 UNMAPPED '
        'trên78 reference cells, không bỏ exceptions hoặc coi là acceptance.',
        '4. Crawl fresh50: 600 base anchors (annual2021–2025, quarter2024–2025), '
        'gap phase tối đa120 requests; request spacing≥2s,≤900 attempts/300MB/2h.',
        '5. Raw dedupSHA; một durable hash-chain JSONL cho counters/reservations/cache; '
        'OS epoch lock và latest-parent resume. Không tạo thư mục ledger cho từng chunk.',
        '6. Xuất coverage1950 rows, exact annual requirements,900 task-year checklist rows, '
        'numeric/sector/notes/PIT/revision queues, sealed manifests và compact feedback.', '',
        '## Kết quả đo được', '',
        '| Phép đo | Kết quả |', '|---|---|',
        f"| Base parse | {a['base_parsed']}/{a['base_expected']} |",
        f"| Gap requests | {a['gap_requests']} |",
        f"| Logical / physical attempts | {a['logical_requests']} / {a['physical_attempts']} |",
        f"| Bytes tải / reserved chưa xác nhận | {a['downloaded_bytes']:,} / {a['reserved_bytes']:,} |",
        f"| Acquisition + parse + checklist, trước ghi export/seal | {a['elapsed_seconds']:.1f}s |",
        f"| Wire statement-periods | {a['wire_present']}/{a['wire_targets']} ({a['wire_pct']}%) |",
        f"| Mã đủ wire cả5 annual +8 quarter, mỗi kỳ3 statements | {a['full_history_symbols']}/{n} |",
        f"| Raw candidate cells / mapped annual field-year candidates | {a['raw_candidate_cells']:,} / {a['mapped_candidate_annual_cells']:,} |",
        f"| Conflicting annual field-year candidates | {a['conflicts']} |",
        f"| Files / bytes toàn output, không gồm parent inputs | {a['output_files']:,} / {a['output_bytes']:,} |",
        f"| Access boundary / budget stop | {a['access_boundary']} / {a['budget_stop']} |",
        '| PDF / OCR / accepted facts / strict task-ready | 0 / 0 / 0 / 0 |', '',
        'Wire có ít nhất một raw numeric cell; mapped field đòi code+label token và proposed '
        'Regular template. Tỷ lệ này không đánh giá completeness từng statement. '
        'Raw candidate cells gồm cả cột ngoài target và cột lặp giữa responses; không '
        'được coi là unique accepted facts. Không suy fiscal year, scale hoặc scope '
        'từ target/header/magnitude.', '',
        '### Theo kỳ', '', '| Kỳ | Wire statements | Mã có cả3 statements |', '|---|---|---|']
    for row in a['per_period']:
        label=f"FY{row['year']}" if row['quarter']==0 else f"Q{row['quarter']}/{row['year']}"
        lines.append(f"| {label} | {row['wire']}/{row['targets']} | {row['symbols_with_all_three']}/{n} |")
    lines+=['', '### Đầu vào cho chỉ số', '',
        '| Task | Candidate input cells / required | Rows đủ exact candidate inputs | Strict ready |', '|---|---|---|---|']
    for row in a['per_task']:
        lines.append(f"| {row['task']} | {row['candidate_inputs']}/{row['required_inputs']} | {row['all_exact_candidate_inputs']}/{row['task_year_rows']} | 0 |")
    lines+=['', 'Candidate counts là dependency cells có thể lặp giữa task/năm; không phải '
        'independent facts hoặc scores. Vendor EPS chưa thay recomputed/TTM EPS; P/E/P/B '
        'còn cần valuation price/share basis và availability. Sector variants không nhận Regular '
        'crosswalk. Kết quả arithmetic reference pilot cũ giữ lineage riêng, không được '
        'cộng vào trial50 production-ready count.', '', '### QA và review queue', '',
        f"Fresh QA chỉ cho các mã reference thực sự thuộc50: `{json.dumps(a['qa_counts'],ensure_ascii=False)}`. "
        'Không đủ independent references cho các mã còn lại; numeric accuracy toàn50 và '
        'manual-review minutes chưa đo.', '',
        f"Review queue: `{json.dumps(a['review_queue_counts'],ensure_ascii=False)}`. "
        f"Request status: `{json.dumps(a['request_status_counts'],ensure_ascii=False)}`.", '',
        'Đọc `per-symbol.csv` và raw `review-queue.json` để chọn gaps cụ thể; giữ từng '
        'HTTP302/missing/conflict, không follow redirects, không chuyển missing thành0. '
        'Pilot gap endpoints trả header đúng nhưng cells vẫn null: retry anchor đơn thuần '
        'không khắc phục được dữ liệu nguồn thiếu.', '', '## So với lượt KBS50 trước', '',
        'Lượt KBS07/10 có300 base parse nhưng150 quarter responses duplicate headers, '
        'FY2025 wire50/50 và Q4/2025 wire0/50;409 requests,113.538.490 bytes và '
        '48.368 manifest entries. CafeF hiện parse theo observed distinct headers và '
        'journal compact. Hai lượt khác thời điểm, target request shape và PDF scope; '
        'không so latency/bytes như paired benchmark hoặc suy source accuracy toàn universe. '
        'Benchmark9 mã trước vẫn là paired source evidence.', '',
        '## Quyết định sau lượt chạy', '',
        'Giữ CafeF detail làm nguồn structured candidate chính cho workflow này, KBS chỉ '
        'diagnostic. Chưa mở100 mã hoặc automatic numeric acceptance/financial cluster. '
        'Các bước cần làm tiếp:', '',
        '1. Ưu tiên gap theo mã/kỳ và sector, tìm exact issuer/exchange annual/interim '
        'documents cho cells thiếu; finite document discovery, không tải hàng loạt không mục đích.',
        '2. Review representative templates (Regular, fiscal-year khác lịch, Bank, Securities, '
        'Insurance); exact page/column facts, units/scope/revisions và exceptions phải được giải quyết.',
        '3. Chọn đúng note pages cho EPS/weighted shares/receivables/PPE/depreciation '
        'theo exact task inputs; embedded text trước, OCR selected scan pages bằng flow hiện có.',
        '4. Gắn ngày publication có evidence; DATE_ONLY dùng phiên exchange quan sát đầu tiên '
        'sau ngày công bố, giải quyết revisions/share events và historical identity/sector.',
        '5. Replay/check accepted facts rồi tính F/M/Z/EPS/P-E/P-B theo variant đã chốt; '
        'đo công QA/cost trước quyết định trial100. Không cần sửa methodology để tăng coverage.', '',
        '## Verification và bàn giao', '',
        f"Run: `{a['run']}`; manifestSHA `{a['run_manifest_sha256']}`. "
        f"Verifier: `{json.dumps(a['verification'])}`.", '',
        '[Runbook PowerShell](../../../docs/crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md), '
        '[changelog](../../../CHANGELOG.md), [analysis](analysis.json), '
        '[theo mã](per-symbol.csv), [test logs](validation.json), [self-review](self-review.md).', '',
        'Không chỉnh sealed raw/manifests/report cũ. Retention registry trỏ latest run và '
        'dependencies giữ pilot/benchmark/reference closure; stage này không xóa thêm data. '
        'Feedback ZIP không chứa raw/PDF, local verifier vẫn cần parent evidence.', '']
    return '\n'.join(lines)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();a=analyze(ROOT,args.run);out=ROOT/args.output
    immutable_write(out/'analysis.json',encoded(a))
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(a['per_symbol'][0]));writer.writeheader();writer.writerows(a['per_symbol'])
    immutable_write(out/'per-symbol.csv',stream.getvalue().encode('utf-8-sig'))
    immutable_write(out/'report.md',render(a).encode('utf8'))
    print(json.dumps({k:a[k] for k in ['status','attempted_symbols','wire_present','wire_targets','output_files','output_bytes']},ensure_ascii=False))
