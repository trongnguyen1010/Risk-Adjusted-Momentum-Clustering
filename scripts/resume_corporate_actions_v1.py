"""Resume a sealed C8 v2 checkpoint in a bounded foreground batch."""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion import corporate_actions_v1 as base
from delta_t1.ingestion import corporate_action_collection as legacy
from delta_t1.ingestion import corporate_action_multisource as multi
from delta_t1.ingestion.corporate_action_sources import PublicTransport, SourceLimitation, now


def as_reference(path):
    path=Path(path).resolve()
    return '@repo/'+path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def resolve_reference(value,owner=None):
    if str(value).startswith('@repo/'):
        path=(ROOT/str(value)[6:]).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('REFERENCE_PATH_ESCAPE')
        return path
    path=Path(value)
    if re.match(r'^[A-Za-z]:[\\/]',str(value)) and not path.is_absolute():
        raise ValueError('WINDOWS_REFERENCE_ON_NON_WINDOWS: use the portable bundle')
    return (path if path.is_absolute() else (owner or ROOT)/path).resolve()


def scope_keys(rows):
    return {(r['security_id'],r['ticker'],r['exchange'],r.get('valid_from') or '',r.get('valid_to') or '') for r in rows}


def canonical_keys():
    path=ROOT/'artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl'
    return scope_keys(legacy.read_jsonl(path))


def verified_checkpoint(root):
    root=root.resolve()
    if not (root/'manifest.json').exists():
        snapshots=sorted((root/'checkpoints').glob('state-*.json'))
        if not snapshots:raise ValueError('No sealed checkpoint or durable progress snapshot')
        state=json.loads(snapshots[-1].read_text())
        upstream=resolve_reference(state['upstream_checkpoint'])
        if base.digest(upstream/'manifest.json')!=state['upstream_manifest_sha256']:
            raise ValueError('UPSTREAM_CHECKPOINT_CHANGED')
        previous,scope=verified_checkpoint(upstream)
        if base.digest(root/'scope.csv')!=state['scope_sha256'] or state['scope_sha256']!=previous['scope_sha256']:
            raise ValueError('STOP_AND_REPORT_SCOPE_MISMATCH')
        for entry in state.get('verified_collections',[]):
            path=resolve_reference(entry['path'])
            if base.digest(path/'manifest.json')!=entry['sha256']:raise ValueError('PROGRESS_COLLECTION_CHANGED')
            multi.load(path)
        return state,scope
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    if manifest.get('artifact_type') not in {'corporate-action-c8-v2-checkpoint','corporate-action-c8-v2-resume-batch'}:
        raise ValueError('Unsupported checkpoint')
    for name,expected in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or base.digest(path)!=expected:
            raise ValueError('CHECKPOINT_CHECKSUM_MISMATCH: '+name)
    state=json.loads((root/'resume_state.json').read_text(encoding='utf-8'))
    scope=legacy.load_scope(root/'scope.csv')
    if len(scope)!=1522 or base.digest(root/'scope.csv')!=state['scope_sha256'] or scope_keys(scope)!=canonical_keys():
        raise ValueError('STOP_AND_REPORT_SCOPE_MISMATCH')
    if (state['start'],state['end'])!=('2019-01-31','2025-12-31'):
        raise ValueError('Window mismatch')
    return state,scope


def cached_transport_factory(cache, state, budget):
    """Cache preserves receipt timestamps; only physical requests spend global budget."""
    mutex=threading.RLock()
    host_locks={host:threading.Lock() for host in PublicTransport.HOSTS}
    host_last={}
    def key(url,payload=None):
        return (url,payload.decode() if payload else None)
    class CachedTransport(PublicTransport):
        def fetch(self,url,payload=None,content_type='application/json',binary=False):
            host=urlsplit(url).hostname
            if urlsplit(url).scheme!='https' or host not in self.HOSTS or urlsplit(url).username:
                raise SourceLimitation('SOURCE_ACCESS_LIMITATION: URL outside approved public adapters')
            with mutex:
                if host in budget['stopped_hosts']:
                    raise SourceLimitation('SOURCE_ACCESS_LIMITATION: checkpoint host stopped; no retry')
            if payload is not None and host in state.get('deferred_post_hosts',[]):
                raise SourceLimitation('PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400')
            entry=cache.get(key(url,payload))
            if entry is not None:
                if entry.get('status')!=200 or entry.get('error'):
                    raise SourceLimitation('ARCHIVED_SOURCE_FAILURE_NOT_RETRIED')
                raw_path=Path(entry['archive_path'])
                if base.digest(raw_path)!=entry['source_hash']:
                    raise ValueError('RAW_CACHE_CHECKSUM_MISMATCH')
                data=raw_path.read_bytes()
                path=self.root/'raw'/f'response-{len(self.requests)+1:04}.bin'
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('xb') as stream: stream.write(data)
                evidence={k:v for k,v in copy.deepcopy(entry).items() if k!='archive_path'}
                evidence.update(path=path.relative_to(self.root).as_posix(),cache_reused=True)
                self.requests.append(evidence)
                with mutex:budget['cache_hits']+=1
                return (data if binary else data.decode('utf-8-sig',errors='replace')),evidence
            # One in-flight request per host. Different domains may overlap;
            # all workers share the same host clock, stop state and total budget.
            with host_locks[host]:
                with mutex:
                    if host in budget['stopped_hosts']:
                        raise SourceLimitation('SOURCE_ACCESS_LIMITATION: shared host stopped; no retry')
                    if budget['physical_requests']>=budget['max_requests']:
                        raise SourceLimitation('REQUEST_BUDGET_EXHAUSTED: RESUME_BATCH')
                    budget['physical_requests']+=1
                count=len(self.requests)
                try:
                    time.sleep(max(0,2-(time.monotonic()-host_last.get(host,0.))))
                    host_last[host]=time.monotonic()
                    return super().fetch(url,payload,content_type,binary)
                finally:
                    with mutex:
                        if len(self.requests)==count:budget['physical_requests']-=1
                        budget['stopped_hosts'].update(self.stopped_hosts)
    return CachedTransport


def resume(checkpoint,output,max_securities=25,max_requests=2000,dry_run=False,max_seconds=None,workers=1,exchanges=None,shard_count=1,shard_index=0):
    state,scope=verified_checkpoint(checkpoint)
    if not 1<=max_securities<=1522 or not 1<=max_requests<=100000:
        raise ValueError('Invalid batch budget')
    if max_seconds is not None and not 1<=max_seconds<=86400:raise ValueError('Invalid time budget')
    if not 1<=workers<=3:raise ValueError('workers must be 1..3; host interval remains 2 seconds')
    if not 1<=shard_count<=1522 or not 0<=shard_index<shard_count:raise ValueError('Invalid shard index/count')
    pending=state['pending_securities']
    tickers={r['ticker'] for r in scope}
    if len(pending)!=len(set(pending)) or not set(pending)<=tickers or set(pending)&set(state['processed_securities']):
        raise ValueError('Invalid resume membership')
    exchange_filter=set(exchanges or [])
    if exchange_filter-set(['HOSE','HNX','UPCOM']):raise ValueError('Invalid exchange filter')
    ownership={ticker:{s['exchange'] for s in scope if s['ticker']==ticker} for ticker in tickers}
    if exchange_filter and any(len(ownership[t])!=1 for t in pending):raise ValueError('SHARD_ASSIGNMENT_AMBIGUOUS')
    universe=sorted(tickers,key=lambda ticker:sorted((s['security_id'],s.get('valid_from') or '',s.get('valid_to') or '',s['exchange']) for s in scope if s['ticker']==ticker))
    # Ownership is frozen against the entire canonical scope, never the shrinking pending list.
    shard_members={t for i,t in enumerate(universe) if i%shard_count==shard_index}
    assigned=[t for t in pending if t in shard_members and (not exchange_filter or ownership[t]&exchange_filter)]
    selected=assigned[:max_securities]
    if dry_run:
        return dict(status='DRY_RUN',network_requests=0,next_securities=selected,pending_count=len(pending),assigned_pending_count=len(assigned),
                    scope_count=len(scope),workers=workers,exchange_filter=sorted(exchange_filter),minimum_host_interval_seconds=2,shard_count=shard_count,shard_index=shard_index)
    if output.exists(): raise ValueError('OUTPUT_EXISTS: use a new immutable batch')
    output.mkdir(parents=True)
    shutil.copyfile(checkpoint/'scope.csv',output/'scope.csv')
    cache={}
    index=checkpoint/'source_receipts/index.jsonl'
    if index.exists():
        for entry in legacy.read_jsonl(index):
            cache[(entry['url'],entry.get('request_body'))]=dict(entry,archive_path=str(resolve_reference(entry['archive_path'],checkpoint)))
    elif state.get('upstream_checkpoint'):
        parent=resolve_reference(state['upstream_checkpoint'])
        parent_index=parent/'source_receipts/index.jsonl'
        if parent_index.exists():
            for entry in legacy.read_jsonl(parent_index):cache[(entry['url'],entry.get('request_body'))]=dict(entry,archive_path=str(resolve_reference(entry['archive_path'],parent)))
    budget=dict(physical_requests=0,cache_hits=0,max_requests=max_requests,last=0.,stopped_hosts=set(state.get('stopped_hosts',[])))
    factory=cached_transport_factory(cache,state,budget)
    processed=list(state['processed_securities']);results=[]
    failed=set(state.get('failed_deferred_securities',[]))
    verified_collections=list(state.get('verified_collections',[]))
    anchor=checkpoint if (checkpoint/'manifest.json').exists() else resolve_reference(state['upstream_checkpoint'])
    started=time.monotonic();stop_reason='SECURITY_BATCH_LIMIT'
    def collect_one(ticker):
        own=[r for r in scope if r['ticker']==ticker]
        scoped=output/'security_scopes'/f'{ticker}.csv';scoped.parent.mkdir(exist_ok=True)
        base.write_new(scoped,base.csv_text(tuple(own[0]),own))
        child=output/'source_receipts'/ticker
        sources=['VSDC']+(['HOSE'] if any(r['exchange']=='HOSE' for r in own) else ['HNX'])
        try:
            result=multi.collect(scoped,child,state['start'],state['end'],max_pages=20,max_details=100,max_requests=160,
                                 sources=sources,transport_factory=factory)
            receipts=json.loads((child/'requests.json').read_text())
            if not any(r.get('status')==200 and not r.get('error') for r in receipts):
                return dict(ticker=ticker,status='FAILED_OR_DEFERRED',collection=as_reference(child),reason='NO_SUCCESSFUL_SOURCE_RESPONSE; KEEP_PENDING')
            return dict(ticker=ticker,status='SOURCE_PARTIAL',collection=as_reference(child),
                        observations=result['observation_count'],receipt_count=result['network_requests'])
        except KeyboardInterrupt:
            return dict(ticker=ticker,status='FAILED_OR_DEFERRED',reason='LOCAL_INTERRUPT_UNFINISHED_RAW_PRESERVED')
        except Exception as error:
            return dict(ticker=ticker,status='FAILED_OR_DEFERRED',reason=type(error).__name__+': '+str(error))
    def record(result):
        ticker=result['ticker'];results.append(result)
        if result['status']!='SOURCE_PARTIAL':failed.add(ticker);return
        failed.discard(ticker)
        processed.append(ticker)
        child=resolve_reference(result['collection'])
        verified_collections.append(dict(path=as_reference(child),sha256=base.digest(child/'manifest.json')))
        print(json.dumps(dict(ticker=ticker,processed=len(processed),total=1522,physical_requests=budget['physical_requests']),ensure_ascii=False),flush=True)
        snapshot=dict(state,created_at=now(),processed_securities=list(processed),pending_securities=[t for t in pending if t not in processed],
                      upstream_checkpoint=as_reference(anchor),upstream_manifest_sha256=base.digest(anchor/'manifest.json'),verified_collections=list(verified_collections),
                      stopped_hosts=sorted(budget['stopped_hosts']),scope_sha256=base.digest(output/'scope.csv'),
                      completed_count=len(processed),partial_count=len(processed),last_completed_security=processed[-1],
                      next_security=next((t for t in pending if t not in processed),None),failed_deferred_securities=sorted(failed),failed_deferred_count=len(failed))
        base.write_new(output/'checkpoints'/f'state-{len(processed):04}.json',base.json_text(snapshot))
    def can_start():
        nonlocal stop_reason
        if max_seconds is not None and time.monotonic()-started>=max_seconds:
            stop_reason='TIME_BUDGET_REACHED';return False
        if budget['physical_requests']>=max_requests or (output/'STOP').exists():
            stop_reason='REQUEST_BUDGET_OR_LOCAL_STOP';return False
        return True
    if workers==1:
        for ticker in selected:
            if not can_start():break
            result=collect_one(ticker);record(result)
            if result['status']!='SOURCE_PARTIAL':
                stop_reason='EXECUTION_ERROR_OR_INTERRUPT';break
    else:
        iterator=iter(selected);futures={};stop_scheduling=False
        with ThreadPoolExecutor(max_workers=workers) as pool:
            def fill():
                while len(futures)<workers and not stop_scheduling and can_start():
                    ticker=next(iterator,None)
                    if ticker is None:break
                    futures[pool.submit(collect_one,ticker)]=ticker
            fill()
            while futures:
                try:done,_=wait(futures,return_when=FIRST_COMPLETED)
                except KeyboardInterrupt:
                    stop_scheduling=True;stop_reason='LOCAL_INTERRUPT_DRAIN_IN_FLIGHT';continue
                for future in done:
                    futures.pop(future)
                    result=future.result();record(result)
                    if result['status']!='SOURCE_PARTIAL':
                        stop_scheduling=True;stop_reason='EXECUTION_ERROR_DRAIN_IN_FLIGHT'
                fill()
    remaining=[t for t in pending if t not in processed]
    new_state=dict(state,created_at=now(),processed_securities=processed,pending_securities=remaining,
                   last_completed_security=processed[-1] if processed else None,next_security=remaining[0] if remaining else None,
                   upstream_checkpoint=as_reference(anchor),upstream_manifest_sha256=base.digest(anchor/'manifest.json'),verified_collections=verified_collections,
                   stopped_hosts=sorted(budget['stopped_hosts']),scope_sha256=base.digest(output/'scope.csv'),completed_count=len(processed),partial_count=len(processed),
                   failed_deferred_securities=sorted(failed),failed_deferred_count=len(failed))
    base.write_new(output/'resume_state.json',base.json_text(new_state))
    base.write_new(output/'batch_results.json',base.json_text(dict(results=results,physical_requests=budget['physical_requests'],cache_hits=budget['cache_hits'],coverage='INCOMPLETE',
        stop_reason=stop_reason,elapsed_seconds=round(time.monotonic()-started,2),max_seconds=max_seconds,workers=workers,exchange_filter=sorted(exchange_filter),
        minimum_host_interval_seconds=2,assigned_pending_after_batch=sum(t not in processed for t in assigned),shard_count=shard_count,shard_index=shard_index)))
    # Carry the cache index forward; new successful receipts augment it without changing old timestamps.
    for request_file in (output/'source_receipts').glob('*/requests.json'):
        for request in json.loads(request_file.read_text()):
            relative=Path(request['path']) if request.get('path') else None
            if relative is None: continue
            child=request_file.parent
            raw=child/relative
            if not raw.exists() or base.digest(raw)!=request.get('source_hash'):
                raw=child/'source_collection_v1_1'/relative
            if not raw.exists() or base.digest(raw)!=request.get('source_hash'):
                raw=next((p for p in child.rglob(relative.name) if base.digest(p)==request.get('source_hash')),raw)
            if raw.exists(): cache[(request['url'],request.get('request_body'))]=dict(request,archive_path=str(raw.resolve()))
    base.write_new(output/'source_receipts/index.jsonl',legacy.dump_jsonl([dict(entry,archive_path=as_reference(entry['archive_path'])) for entry in cache.values()]))
    files={p.relative_to(output).as_posix():base.digest(p) for p in output.rglob('*') if p.is_file()}
    base.write_new(output/'manifest.json',base.json_text(dict(artifact_type='corporate-action-c8-v2-resume-batch',schema_version='1.2.0',status='PARTIAL',
        files=files,script_sha256=base.digest(Path(__file__)),q11_status='STILL_OPEN',q17_status='NOT_TOUCHED',price_return_adjusted_series='NOT_BUILT')))
    return dict(status='PARTIAL',processed=len(processed),total=1522,next_security=new_state['next_security'],physical_requests=budget['physical_requests'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Foreground bounded resume; no backtest or price adjustment')
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-securities',type=int,default=25)
    parser.add_argument('--max-requests',type=int,default=2000)
    parser.add_argument('--max-seconds',type=int,help='Stop between securities after this elapsed-time budget')
    parser.add_argument('--workers',type=int,default=1,help='1..3 workers, sharing per-host rate/stop/budget controls')
    parser.add_argument('--exchange',nargs='+',choices=['HOSE','HNX','UPCOM'],help='Work assignment only; full canonical scope remains unchanged')
    parser.add_argument('--shard-count',type=int,default=1,help='Stable partitions of the full canonical scope')
    parser.add_argument('--shard-index',type=int,default=0,help='Zero-based partition index; keep fixed across resumes')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    result=resume(args.checkpoint,args.output,args.max_securities,args.max_requests,args.dry_run,args.max_seconds,args.workers,args.exchange,args.shard_count,args.shard_index)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if args.dry_run else 2)
