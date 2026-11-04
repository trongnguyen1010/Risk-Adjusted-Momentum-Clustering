"""Audit pagination/root cause across C8 v2 using archived receipts only."""
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import read, rows, write, hashes
from delta_t1.ingestion.corporate_actions.vsdc_pagination_audit import snapshot_coverage, physical_failures, supplementation_scope, locate_receipt_body, is_deferred_pagination
from delta_t1.ingestion.corporate_action_sources import sha
from delta_t1.ingestion.hnx_announcement_batch import verify_artifact


def jsonl(path, values):
    with path.open("x", encoding="utf-8") as stream:
        for value in values: stream.write(json.dumps(value, ensure_ascii=False) + "\n")


def render(summary, mbs):
    counts = summary["latest_query_status_counts"]
    trs = ''.join('<tr><td>'+escape(k)+'</td><td>'+str(v)+'</td></tr>' for k,v in counts.items())
    return '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>VSDC — vì sao thu thiếu và cần bổ sung gì</title>
<style>body{font:17px/1.65 system-ui;background:#f2f5f9;color:#182d42}main{max-width:980px;margin:32px auto;background:white;padding:32px}h1{font-size:27px}h2{font-size:21px}.note{padding:18px;background:#fff1d8;border-left:5px solid #ab6800}table{border-collapse:collapse;width:100%}td,th{padding:10px;border:1px solid #cbd5df;text-align:left}code{overflow-wrap:anywhere}</style><main>
<h1>VSDC: đợt cũ có thiếu lịch sử do phân trang</h1><div class="note">Cần lập lượt bổ sung cho mọi query bị ảnh hưởng sau khi xác minh pagination bằng pilot giới hạn. Giữ raw đã có; không tải lại toàn bộ details hoặc tự mở bulk ở stage audit.</div>
<h2>Nguyên nhân đã xác định</h2><ol><li>Bốn POST trang 2 ban đầu cho A32, AAA, AAM, SSI trả HTTP400. Chúng được lặp trong 12 ledger entries do parent/child/replay, không phải 12 requests độc lập.</li>
<li>Checkpoint thêm vsdc.vn vào deferred_post_hosts. Runner chủ động chặn POST sau đó với lý do PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400.</li>
<li>Với MBS, plan cho phép 20 pages/100 details, nhưng page 2 bị deferred. Vì vậy vẫn chỉ có 20/63 query rows.</li></ol>
<p>Không có body giải thích bốn HTTP400. Saved first-party JavaScript sử dụng cùng URL/query, POST JSON SearchKey/CurrentPage; chưa chứng minh vì sao request bị từ chối hoặc một protocol sửa lại đã chạy được. Không gỡ guard để thử hàng loạt.</p>
<h2>Phạm vi audit</h2><p>Đã xét '''+str(summary['inventory_tickers'])+''' query tickers của C8 v2, từ '''+str(summary['search_response_snapshots'])+''' response snapshots đã hash-verify.</p><table><tr><th>Trạng thái snapshot query mới nhất đã lưu</th><th>Số mã</th></tr>'''+trs+'''</table>
<p>Tổng các vị trí dòng query chưa được discover trong các snapshot không đầy đủ: <strong>'''+str(summary['unseen_query_row_slots_sum'])+'''</strong>. Số này có thể trùng giữa query, gồm trái phiếu/thông báo họp/thông tin ngoài kỳ; không phải số sự kiện thiếu hoặc số request cần chạy.</p>
<h2>Cần thu bổ sung toàn bộ hay không?</h2><p>Cần xử lý toàn bộ phạm vi query bị ảnh hưởng nếu mục tiêu là hoàn thiện phần lịch sử chưa thu. Lượt mới phải discover phần thiếu, đối chiếu ID/hash với raw cache, rồi chỉ tải những details còn thiếu và đúng scope. Query đã hết kết quả trong snapshot cũng chưa chứng nhận full historical event coverage.</p>
<p>Đã có '''+str(summary['global_cached_article_ids'])+''' distinct provider article IDs trong audited cache; các response versions/hashes cũ được giữ nguyên. Chưa biết số details mới cần tải trước khi thấy các trang còn thiếu.</p>
<h2>Phân biệt processed và complete</h2><p>Các shard cũ ghi SOURCE_PARTIAL/coverage INCOMPLETE, complete_coverage_count=0. Processed nghĩa là đã xử lý lượt thu có giới hạn, không phải đã thu đầy đủ lịch sử.</p>
<h2>Bước tiếp theo</h2><p>Chuẩn bị pilot user-run VSDC MBS giới hạn để kiểm tra pagination theo source contract đã xác minh. Chỉ sau pilot mới lập budget và danh sách thu bổ sung cho toàn bộ affected queries. Không resume state HNX STOP hoặc xoá deferred guard trong audit này.</p>
<p>0 source requests/0 field approvals/0 canonical changes trong stage này. Các JSONL cùng thư mục chứa đầy đủ từng query, snapshots, root-cause evidence và continuation inventory.</p></main></html>'''


def reuse_audit(config_path, config, out):
    """Preserve expensive verified reads; normalize diagnostic suffixes in a new artifact."""
    reference=config['reuse_verified_audit'];parent=ROOT/reference['path']
    if sha((parent/'manifest.json').read_bytes())!=reference['manifest_sha256']:raise ValueError('PARENT_AUDIT_CHANGED')
    verify_artifact(parent)
    summary=read(parent/'summary.json');root_cause=read(parent/'root_cause.json')
    queries=rows(parent/'all_1522_query_reviews.jsonl')
    cause_tickers={r['check']['ticker'] for r in root_cause['deferred_check_records'] if is_deferred_pagination(r['check'].get('pagination_error'))}
    gap_tickers={r['ticker'] for r in queries if r['query_status']=='QUERY_LIST_INCOMPLETE'}
    if cause_tickers!=gap_tickers:raise ValueError('DEFERRED_VS_GAP_SCOPE_REQUIRES_REVIEW')
    summary['tickers_with_deferred_page_check_evidence']=len(cause_tickers)
    summary['all_known_gap_queries_have_deferred_pagination_evidence']=True
    summary['unverified_query_tickers']=[r['ticker'] for r in queries if r['query_status']=='SEARCH_LAYOUT_UNVERIFIED']
    summary['same_stage_verified_parent_reused']=reference
    out.mkdir(parents=True)
    for name in ['all_search_snapshots.jsonl','all_1522_query_reviews.jsonl','supplement_candidates.jsonl','root_cause.json','verified_inputs.json']:
        (out/name).write_bytes((parent/name).read_bytes())
    write(out/'summary.json',summary);write(out/'config.json',config)
    write(out/'lineage.json',{'parent':reference,'raw_hashes_verified_in_parent':True,
        'reused_query_review_rows':len(queries),'original_reason_strings_preserved':True,
        'change':'Count both exact deferred reason and deferred reason with explanatory suffix; do not recompute raw or alter old evidence'})
    (out/'ket_qua_kiem_tra_VSDC.html').write_text(render(summary,next(r for r in queries if r['ticker']=='MBS')),encoding='utf-8')
    write(out/'runtime.json',{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__),config_path,
        ROOT/'src/delta_t1/ingestion/corporate_actions/vsdc_pagination_audit.py']})
    write(out/'manifest.json',{'artifact_type':'vsdc-pagination-scope-offline-audit-v2','files':hashes(out)})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'): stream.reconfigure(encoding='utf-8')
    config_path=ROOT/'configs/data/corporate_actions/vsdc_pagination_scope_audit_v1.json';config=read(config_path)
    if any(config[k] for k in ['network_requests','canonical_build','automatic_approval','bulk_collection_authorized']):
        raise ValueError('OFFLINE_AUDIT_ONLY')
    out=ROOT/config['output']
    if out.exists():raise FileExistsError('REFUSE_OVERWRITE')
    if config.get('reuse_verified_audit'):
        reuse_audit(config_path,config,out)
        return
    cache=ROOT/config['cache'];cm=read(cache/'manifest.json')
    if sha((cache/'manifest.json').read_bytes())!=config['cache_manifest_sha256']:raise ValueError('CACHE_MANIFEST_CHANGED')
    verify_artifact(cache)
    canonical=ROOT/config['canonical'];securities=rows(canonical);scope={r['ticker']:r for r in securities}
    if len(scope)!=1522 or len(securities)!=1522:raise ValueError('C8_V2_1522_REQUIRED')
    proofs={};ledger_cache={}
    def pinned(path, expected):
        body=path.read_bytes()
        if sha(body)!=expected:raise ValueError('INPUT_CHANGED: '+str(path))
        proofs[str(path)]={'sha256':expected,'bytes':len(body)}
        return body
    def load_ledger(relative):
        if relative not in ledger_cache:
            expected=cm['inputs_verified'][relative]['sha256']
            ledger_cache[relative]=json.loads(pinned(ROOT/relative,expected))
        return ledger_cache[relative]
    views={r['source_hash']:r for r in rows(cache/'parsed_raw_views.jsonl') if r['role']=='SEARCH'}
    source_receipts=[r for r in rows(cache/'request_inventory.jsonl') if r['role']=='SEARCH']
    cached_urls={r['source_url'] for r in rows(cache/'raw_document_index.jsonl')}
    cached_ids={r['provider_article_id'] for r in rows(cache/'raw_document_index.jsonl')}
    snapshots=[];grouped=defaultdict(list)
    for item in source_receipts:
        ticker=parse_qs(urlsplit(item['url']).query).get('text',[''])[0]
        if ticker not in scope:raise ValueError('QUERY_OUTSIDE_C8')
        view=views[item['source_hash']];rawpath=ROOT/view['raw_path'];body=pinned(rawpath,item['source_hash'])
        links=view['view']
        if not isinstance(links,list):raise ValueError('PARSED_SEARCH_LINKS_REQUIRED')
        reference=item['ledger_references'][0];receipt=load_ledger(reference['path'])[reference['index']]
        if receipt['url']!=item['url'] or receipt['source_hash']!=item['source_hash'] or receipt['status']!=200:
            raise ValueError('QUERY_RECEIPT_JOIN_MISMATCH')
        coverage=snapshot_coverage(body,[r['provider_article_id'] for r in links])
        record={'ticker':ticker,'exchange':scope[ticker]['exchange'],'url':item['url'],'raw_path':view['raw_path'],
            'source_hash':item['source_hash'],'original_fetched_at':receipt['fetched_at'],'method':receipt['method'],
            'request_body':receipt.get('request_body'),'ledger_references':item['ledger_references'],
            'known_article_urls':[r['url'] for r in links],**coverage}
        snapshots.append(record);grouped[ticker].append(record)
    if set(grouped)!=set(scope):raise ValueError('ALL_C8_QUERIES_MUST_BE_ACCOUNTED_FOR')
    query_reviews=[]
    for ticker in sorted(scope):
        variants=sorted(grouped[ticker],key=lambda r:(datetime.fromisoformat(r['original_fetched_at'].replace('Z','+00:00')),r['source_hash']))
        latest=variants[-1]
        known={u for r in variants for u in r['known_article_urls']}
        query_reviews.append({**latest,'saved_snapshot_count':len(variants),
            'supplement_scope':supplementation_scope(latest,known,cached_urls),
            'latest_selection_is_query_audit_only_not_PIT':True})
    failures=physical_failures(rows(cache/'failed_request_receipts.jsonl'))
    for failure in failures:
        receipt=failure['receipt'];candidates=[]
        for ref in failure['ledger_references']:
            actual=load_ledger(ref['path'])[ref['index']]
            if actual!=receipt:raise ValueError('FAILURE_RECEIPT_CHANGED')
            candidates.append((ROOT/ref['path']).parent/receipt['path'])
        candidate,rejected=locate_receipt_body(candidates,receipt['source_hash'])
        pinned(candidate,receipt['source_hash'])
        failure['verified_raw_path']=str(candidate)
        failure['non_matching_relative_candidates_preserved']=rejected
    check_records=[];states=[]
    for relative,digest in config['source_manifests'].items():
        base=ROOT/relative;manifest=json.loads(pinned(base/'manifest.json',digest))
        state=json.loads(pinned(base/'resume_state.json',manifest['files']['resume_state.json']))
        states.append({'root':relative,**{k:state.get(k) for k in ['completed_count','partial_count','complete_coverage_count','deferred_post_hosts','stopped_hosts']}})
        for name,expected in manifest['files'].items():
            if not name.endswith('source_checks.json'):continue
            data=json.loads(pinned(base/name,expected))
            for check in data.get('checks',[]):
                if check.get('source')=='VSDC':check_records.append({'source_checks':str(base/name),'check':check})
    affected=[r for r in query_reviews if r['query_status']=='QUERY_LIST_INCOMPLETE']
    cause_tickers={r['check']['ticker'] for r in check_records if is_deferred_pagination(r['check'].get('pagination_error'))}
    mbs=next(r for r in query_reviews if r['ticker']=='MBS')
    mbs_plan_path=ROOT/'data/corporate_actions/work/outputs/batch_shard_3/source_receipts/MBS/plan.json'
    mbs_plan=read(mbs_plan_path)
    protocol_body=(ROOT/mbs['raw_path']).read_bytes().decode('utf-8-sig')
    js_start=protocol_body.index('function searchGlSearch(type)')
    js=protocol_body[js_start:protocol_body.index('</script>',js_start)]
    for token in ['type: "POST"','window.location.pathname + window.location.search','SearchKey: type','CurrentPage: Number(_spage)']:
        if token not in js:raise ValueError('SAVED_FIRST_PARTY_PAGINATION_CONTRACT_CHANGED')
    roots={str(ROOT/p):sha((ROOT/p).read_bytes()) for p in ['scripts/resume_corporate_actions_v1.py','src/delta_t1/ingestion/corporate_action_sources.py']}
    summary={'stage':config['stage'],'technical_status':'PASS_OFFLINE_AUDIT','source_protocol_status':'LIVE_PAGINATION_NOT_CERTIFIED',
        'inventory_tickers':len(scope),'search_response_snapshots':len(snapshots),'query_tickers':len(query_reviews),
        'latest_query_status_counts':dict(Counter(r['query_status'] for r in query_reviews)),
        'queries_with_known_list_gap':len(affected),'unseen_query_row_slots_sum':sum(r['unseen_query_row_slots'] for r in affected),
        'global_cached_article_ids':len(cached_ids),'known_query_urls_without_raw_count':len(set(u for r in query_reviews for u in r['supplement_scope']['known_urls_without_raw'])),
        'physical_pagination_HTTP400_attempts':len(failures),'failure_ledger_occurrences':sum(len(r['ledger_references']) for r in failures),
        'tickers_with_deferred_page_check_evidence':len(cause_tickers),'affected_by_exchange':dict(Counter(r['exchange'] for r in affected)),
        'MBS':{k:mbs[k] for k in ['reported_total','known_list_ids','unseen_query_row_slots','query_status']},
        'network_requests':0,'automatic_approval':False,'canonical_rows_written':0,'old_guards_and_checkpoints_modified':False,
        'continuation_inventory_is_not_execution_authorization':True,
        'counts_are_query_rows_not_distinct_events_or_new_requests':True,
        'next_stage_proposal':'Prepare a separately approved user-run MBS pagination protocol pilot; then plan cache-first supplements for all affected queries, without refetching existing raw'}
    evidence={'archived_page_two_failures':failures,'source_states':states,'MBS_runtime_plan':mbs_plan,
        'deferred_check_records':check_records,'saved_first_party_JS':js,'code_hashes':roots,
        'cause':'Initial POST page-two HTTP400 then persistent deferred_post_hosts guard; not MBS max_pages20/max_details100 cap',
        'not_established':['Why server returned400 with empty bodies','A corrected request proven to succeed live','Exact number of new details required before discovering and deduplicating missing pages']}
    out.mkdir(parents=True)
    jsonl(out/'all_search_snapshots.jsonl',snapshots);jsonl(out/'all_1522_query_reviews.jsonl',query_reviews)
    jsonl(out/'supplement_candidates.jsonl',affected);write(out/'root_cause.json',evidence)
    write(out/'summary.json',summary);write(out/'config.json',config)
    write(out/'verified_inputs.json',{'files':proofs,'canonical_sha256':sha(canonical.read_bytes()),'cache_manifest_sha256':config['cache_manifest_sha256']})
    (out/'ket_qua_kiem_tra_VSDC.html').write_text(render(summary,mbs),encoding='utf-8')
    write(out/'runtime.json',{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__),config_path,
        ROOT/'src/delta_t1/ingestion/corporate_actions/vsdc_pagination_audit.py']})
    write(out/'manifest.json',{'artifact_type':'vsdc-pagination-scope-offline-audit-v1','files':hashes(out)})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
