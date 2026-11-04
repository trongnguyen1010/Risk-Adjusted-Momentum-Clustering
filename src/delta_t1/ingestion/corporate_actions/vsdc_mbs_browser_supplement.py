"""Bounded MBS four-page query plus one exact public detail; no field promotion."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

from ..corporate_action_sources import Document, sha, kinds
from ..corporate_action_cache_audit import search_links
from ..hnx_announcement_batch import verify_artifact
from .hnx_local_supplement import read, write, hashes
from .hnx_local_pvs import seal
from .vsdc_pagination_audit import snapshot_coverage
from . import vsdc_mbs_browser_html as old

CONFIG = "configs/data/corporate_actions/vsdc_mbs_browser_supplement_v1.json"
TYPE = "vsdc-mbs-browser-four-page-one-detail-v1"
PREP_TYPE = "vsdc-mbs-browser-supplement-preparation-v1"
DETAIL_URL = "https://vsdc.vn/vi/ad/187243"
PARENTS = {
    "prior_preparation": ("data/corporate_actions/work/vsdc_mbs_browser_html_preparation_20261103_v1",
        "18c7bf6b12f34413be0aa23d7d68fa711dbadc38e6a94872289c670b85700d05", old.PREP_TYPE),
    "prior_run": ("data/corporate_actions/work/vsdc_mbs_browser_html_pilot_v1/run-20261103T052324145483Z/state",
        "d1b3dbb52c2972bb0672755de4417354b53a02744dde0f7a6833d067c4bed8fa", old.TYPE),
    "prior_review": ("data/corporate_actions/work/vsdc_mbs_browser_html_live_review_20261103_v1",
        "ed625c65678317d35917faaca94b6b0c3d60fd878d4cd132d7bd1ef06ebdcbaa", "vsdc-mbs-browser-html-offline-live-review-v1"),
}


def validate(config):
    expected = dict(read_default_contract())
    if config != expected:
        raise ValueError("FIXED_MBS_FOUR_PAGE_ONE_DETAIL_CONTRACT_REQUIRED")


def read_default_contract():
    # Independent of the on-disk config: the executable scope cannot be expanded by editing JSON.
    return {"stage": "VSDC_MBS_BROWSER_FOUR_PAGE_ONE_DETAIL_V1", "ticker": "MBS",
        "url": old.search_url("MBS"), "detail_url": DETAIL_URL, "max_list_pages": 4,
        "max_business_requests": 5, "max_context_request_attempts": 160, "max_asset_attempts": 155,
        "max_seconds": 150, "business_interval_seconds": 8, "operation_timeout_seconds": 15,
        "max_html_bytes": 2000000, "channel": "chrome", "headless": False,
        "playwright_version": "1.57.0", "workers": 1, "retry": False, "resume": False,
        "persistent_profile": False, "export_cookies_or_auth": False, "ignore_https_errors": False,
        "canonical_build": False, "automatic_approval": False,
        "output_base": "data/corporate_actions/work/vsdc_mbs_browser_supplement_v1",
        "preparation": "data/corporate_actions/work/vsdc_mbs_browser_supplement_preparation_20261103_v1"}


def runtime(project):
    names = [CONFIG, "src/delta_t1/ingestion/corporate_actions/vsdc_mbs_browser_supplement.py",
        "scripts/corporate_actions/prepare_vsdc_mbs_browser_supplement_v1.py",
        "scripts/corporate_actions/collect_vsdc_mbs_browser_supplement_v1.py"]
    return {**old.runtime(project), **{n: sha((project / n).read_bytes()) for n in names}}


def parents(project):
    _, prep = old.load_preparation(project)
    for name, (rel, digest, kind) in PARENTS.items():
        path = project / rel
        if sha((path / "manifest.json").read_bytes()) != digest:
            raise ValueError("MBS_SUPPLEMENT_PARENT_CHANGED: " + name)
        verify_artifact(path, {kind})
    if read(project / PARENTS["prior_review"][0] / "review.json")["status"] != "PASS_BOUNDED_BROWSER_HTML_PAGE2":
        raise ValueError("REVIEWED_BROWSER_PAGE2_PASS_REQUIRED")
    return prep


def load_preparation(project):
    config = read(project / CONFIG); validate(config); parents(project)
    prep = project / config["preparation"]
    verify_artifact(prep, {PREP_TYPE})
    if read(prep / "runtime.json") != runtime(project) or read(prep / "plan.json")["config"] != config:
        raise ValueError("MBS_SUPPLEMENT_PREPARED_RUNTIME_CHANGED")
    old.protected_check(project, read(prep / "protected_old_files.json"))
    if "187243" in read(prep / "cached_article_ids.json"):
        raise ValueError("KNOWN_DETAIL_MUST_BE_REUSED_NOT_REDOWNLOADED")
    return config, prep


def prepare(project):
    project = Path(project).resolve(); config = read(project / CONFIG); validate(config)
    old_prep = parents(project); out = project / config["preparation"]
    if out.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    protected = read(old_prep / "protected_old_files.json")
    for rel, _, _ in PARENTS.values():
        folder = project / rel
        for name in ["manifest.json", *read(folder / "manifest.json")["files"]]:
            path = folder / name
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    protected.update(old.runtime(project))
    cached = read(old_prep / "cached_article_ids.json")
    if len(cached) != 27730 or "187243" in cached:
        raise ValueError("AUDITED_CACHE_CANDIDATE_CONTEXT_CHANGED")
    out.mkdir(parents=True)
    (out / "cached_article_ids.json").write_bytes((old_prep / "cached_article_ids.json").read_bytes())
    (out / "candidate_187243.json").write_bytes(
        (project / PARENTS["prior_review"][0] / "mbs_candidate_187243.json").read_bytes())
    write(out / "plan.json", {"config": config, "status": "PREPARED_NOT_EXECUTED",
        "source_requests": 0, "browser_launches": 0, "readiness": old.readiness(config),
        "query_snapshot": "Read up to four list pages in one fresh browser; stable total/ranges and unique IDs required",
        "detail_gate": "Only187243, only after complete fresh query with candidate present and not in audited cache",
        "revision_scope": "List titles plus exact candidate content only; do not fetch referenced corrections/attachments automatically",
        "coverage": "Even full query exhaustion is not certified historical event/revision coverage or field approval"})
    write(out / "parent_manifests.json", {k: {"path": v[0], "manifest_sha256": v[1]} for k,v in PARENTS.items()})
    write(out / "protected_old_files.json", protected)
    write(out / "runtime.json", runtime(project))
    write(out / "manifest.json", {"artifact_type": PREP_TYPE, "files": hashes(out)})
    load_preparation(project)
    return {"status": "PREPARED_NOT_EXECUTED", "source_requests": 0,
        "protected_old_files": len(protected), "readiness": old.readiness(config), "output": str(out)}


class Guard(old.Guard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_complete = False
        self.expected_detail_title = None

    def admit(self, url, method, resource, body=None, redirected=False):
        if url not in {self.config["url"], DETAIL_URL}:
            return super().admit(url, method, resource, body, redirected)
        self.attempts += 1
        event = {"event": "REQUEST_ATTEMPT", "number": self.attempts,
                 "url": url, "method": method, "resource_type": resource}
        try:
            self.check(); self.check_old()
            if self.attempts > self.config["max_context_request_attempts"]:
                raise ValueError("BROWSER_CONTEXT_REQUEST_BUDGET_EXHAUSTED")
            if redirected: raise ValueError("BROWSER_REDIRECT_NOT_FOLLOWED")
            if len(self.business) >= 5: raise ValueError("MBS_BUSINESS_BUDGET_EXHAUSTED")
            if self.business and self.clock() - self.business[-1]["at_monotonic"] < 8:
                raise ValueError("MBS_SHARED_BUSINESS_INTERVAL_REQUIRED")
            if url == DETAIL_URL:
                if (not self.list_complete or not self.expected_detail_title
                        or any(r["url"] == DETAIL_URL for r in self.business)
                        or method != "GET" or resource != "document" or body is not None):
                    raise ValueError("EXACT_DETAIL_AFTER_COMPLETE_FRESH_QUERY_REQUIRED")
                category = "BUSINESS_DETAIL"
            else:
                index = len(self.business)
                if self.list_complete or index >= 4:
                    raise ValueError("MBS_MAX_FOUR_LIST_PAGES_REQUIRED")
                if index == 0:
                    if method != "GET" or resource != "document" or body is not None:
                        raise ValueError("FRESH_QUERY_GET_REQUIRED")
                elif (method != "POST" or resource not in {"xhr", "fetch"}
                        or json.loads(body or "null") != {"SearchKey":4,"CurrentPage":index+1}):
                    raise ValueError("SEQUENTIAL_MBS_UI_PAGE_REQUIRED")
                category = "BUSINESS_LIST"
            if not self.business: self.first_business_at = self.clock()
            self.business.append({"url":url,"method":method,"at_monotonic":self.clock(),"classification":category})
            self.allowed += 1; event.update(allowed=True, classification=category)
            self.log(event); return True
        except Exception as exc:
            self.fail(str(exc));event.update(allowed=False,stop_reason=self.stop_reason);self.log(event);return False

    def response(self, url, method, status, headers):
        if url == DETAIL_URL:
            safe = {k.casefold():v for k,v in headers.items()
                    if k.casefold() in {"content-type","content-length","retry-after"}}
            row={"url":url,"method":method,"status":status,"headers":safe}
            self.responses.append(row);self.log({"event":"BUSINESS_RESPONSE",**row})
        super().response(url,method,status,headers)


def list_page(fragment, number, total=None, seen=()):
    old.fragment_bytes(fragment,2000000)
    articles=search_links(fragment.encode(),old.search_url("MBS"))
    ids=[a["provider_article_id"] for a in articles]
    coverage=snapshot_coverage(fragment.encode(),ids)
    count=coverage.get("reported_total")
    if (not isinstance(count,int) or count < 1 or count > 80 or number not in range(1,5)
            or (total is not None and count != total)
            or coverage.get("first") != (number-1)*20+1 or coverage.get("last") != min(number*20,count)
            or len(ids) != min(20,count-(number-1)*20) or len(ids)!=len(set(ids)) or set(ids)&set(seen)):
        raise ValueError("MBS_QUERY_RANGE_TOTAL_DUPLICATE_OR_PAGE_BUDGET_MISMATCH")
    return {"page":number,"coverage":coverage,"articles":articles,"article_ids":ids}


def public_detail(fragment, expected_title):
    data=fragment.encode("utf-8");root=Document(fragment).root
    # Reuse the privacy gate by wrapping only the public article nodes.
    old.fragment_bytes('<div id="divGlSearchArticles">'+fragment+'</div>',2000000)
    titles,contents=root.find(cls="title-category"),root.find(cls="content-category")
    if len(titles)!=1 or len(contents)!=1:raise ValueError("EXACT_VSDC_PUBLIC_DETAIL_LAYOUT_REQUIRED")
    title=titles[0].text()
    normalize=lambda text:re.sub(r"\s*:\s*",": "," ".join(text.split()))
    if (normalize(title)!=normalize(expected_title) or not re.match(r"^MBS\s*:",title)
            or not {"RIGHTS_ISSUE","BONUS_SHARE"}.issubset(set(kinds(title)))):
        raise ValueError("CANDIDATE187243_DETAIL_TITLE_SCOPE_MISMATCH")
    return data,{"provider_article_id":"187243","url":DETAIL_URL,"title":title,
        "public_text":contents[0].text(),
        "source_time_texts":[n.text() for n in root.find(cls="time-newstcph")],
        "time_semantics":"SOURCE_LABEL_ONLY_NOT_HISTORICAL_AVAILABLE_AT",
        "terms_verified":False,"record_date_verified":False,
        "price_verified":False,"revision_coverage_verified":False,"canonical_fields_applied":0}


class Driver(old.PlaywrightDriver):
    def _route(self, route):
        # Parent route only records functional header values for the query, never tokens/cookies.
        super()._route(route)

    def next_page(self, number, previous):
        selector=f'#divGlSearchArticles #d_number_of_page button[onclick="changePageArticles({number})"]'
        button=self.page.locator(selector).filter(has_text=re.compile(rf"^\s*{number}\s*$"))
        if button.count()!=1:raise ValueError("UNIQUE_OBSERVED_NEXT_PAGE_BUTTON_REQUIRED")
        with self.page.expect_response(lambda r:r.url==self.config["url"] and r.request.method=="POST",
                                       timeout=self.guard.timeout_ms()) as pending:
            button.click(timeout=self.guard.timeout_ms(),no_wait_after=True)
        response=pending.value;self.guard.check()
        if response.status!=200:raise ValueError("MBS_NEXT_PAGE_HTTP200_REQUIRED")
        self.page.wait_for_function("old => {const el=document.querySelector('#divGlSearchArticles'); return el && el.outerHTML !== old;}",
                                    arg=previous,timeout=self.guard.timeout_ms())
        return self._snapshot(response,False)

    def detail(self):
        response=self.page.goto(DETAIL_URL,wait_until="domcontentloaded",timeout=self.guard.timeout_ms())
        self.guard.check()
        if self.page.url!=DETAIL_URL or response is None or response.status!=200:
            raise ValueError("EXACT_DETAIL_URL_HTTP200_REQUIRED")
        nodes=[]
        for selector in ['.title-category','.content-category']:
            locator=self.page.locator(selector)
            if locator.count()!=1:raise ValueError("UNIQUE_PUBLIC_DETAIL_CONTAINER_REQUIRED")
            nodes.append(locator.evaluate('(el) => el.outerHTML',timeout=self.guard.timeout_ms()))
        timing=self.page.locator('.time-newstcph')
        if timing.count()>1:raise ValueError('AMBIGUOUS_DETAIL_TIME_LAYOUT')
        if timing.count()==1:
            nodes.append(timing.evaluate('(el) => el.outerHTML',timeout=self.guard.timeout_ms()))
        body=response.body()
        if len(body)>2000000 or old.CHALLENGE.search(body.decode('utf-8',errors='replace')):
            raise ValueError("DETAIL_BODY_SIZE_OR_CHALLENGE_STOP")
        self.guard.check()
        return {"url":DETAIL_URL,"http_status":200,"fragment":"\n".join(nodes),
                "http_body_sha256":sha(body),"http_body_bytes":len(body)}


def run(project, output, *, dry_run=False, driver_factory=Driver, clock=time.monotonic):
    project,output=Path(project).resolve(),Path(output).resolve()
    config,prep=load_preparation(project)
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    ready=old.readiness(config)
    if dry_run:return {"status":"OFFLINE_CHECK_PASS" if ready["ready"] else "SETUP_REQUIRED",
        "browser_launched":False,"source_requests":0,"readiness":ready,"max_list_pages":4,"max_detail_requests":1}
    output.mkdir(parents=True);(output/'network_ledger.jsonl').touch()
    protected=read(prep/'protected_old_files.json');check=lambda:old.protected_check(project,protected)
    guard=Guard(config,output,check,clock)
    result={"stage":config['stage'],"status":"STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED",
        "browser_launched":False,"source_stopped":False,"resumable":False,"fresh_query_complete":False,
        "detail_captured":False,"bulk_collection_ready":False,"normalized_observations":0,
        "canonical_fields_applied":0,"pit_or_identity_promoted":False,"openai_api_calls":0}
    for name in ['cached_article_ids.json','protected_old_files.json','candidate_187243.json','parent_manifests.json']:
        (output/name).write_bytes((prep/name).read_bytes())
    write(output/'plan.json',config);write(output/'runtime.json',runtime(project));write(output/'environment.json',ready)
    write(output/'input_provenance.json',{'preparation_path':str(prep),
        'manifest_sha256':sha((prep/'manifest.json').read_bytes()),'capture_kind':'PUBLIC_RENDERED_FRAGMENTS_NOT_RAW_HTTP'})
    def archive(name,value):
        if value['http_status']!=200:raise ValueError('BUSINESS_HTTP200_REQUIRED')
        folder=output/'rendered_html';folder.mkdir(exist_ok=True)
        with (folder/(name+'.html')).open('xb') as f:f.write(value['fragment'].encode())
        write(output/(name+'_receipt.json'),{'url':value['url'],'captured_at':datetime.now(timezone.utc).isoformat(),
            'fragment_sha256':sha(value['fragment'].encode()),'http_status':200,
            'http_body_hash_not_archived':value['http_body_sha256'],'http_body_bytes':value['http_body_bytes'],
            'raw_http_body_archived':False})
    try:
        if not ready['ready']:raise ValueError('LOCAL_PLAYWRIGHT_CHROME_SETUP_REQUIRED')
        with driver_factory(config,guard) as driver:
            result['browser_launched']=True
            write(output/'browser.json',{'version':driver.version,'channel':'chrome','persistent':False,
                'default_identity':True,'cookie_auth_exported':False,'TLS_ignore_errors':False})
            current=driver.first();guard.check()
            write(output/'fresh_source_contract.json',old.prior.source_contract(current['scope_html']))
            seen=[];all_articles=[];total=None;previous=''
            for number in range(1,5):
                if number>1:
                    check();driver.pace(max(0,8-(clock()-guard.business[-1]['at_monotonic'])))
                    current=driver.next_page(number,previous);guard.check()
                if current['url']!=config['url']:raise ValueError('QUERY_URL_CHANGED')
                old.fragment_bytes(current['fragment'],2000000)
                archive(f'page{number}',current)
                parsed=list_page(current['fragment'],number,total,seen)
                write(output/f'page{number}.json',parsed)
                total=parsed['coverage']['reported_total'];seen.extend(parsed['article_ids']);all_articles.extend(parsed['articles'])
                previous=current['fragment']
                if len(seen)==total:break
            if len(seen)!=total or len(guard.business)!=math.ceil(total/20):
                raise ValueError('FRESH_LIST_EXHAUSTION_NOT_VERIFIED')
            result.update(fresh_query_complete=True,list_pages=number,query_article_ids=len(seen),reported_total=total)
            cached=set(read(prep/'cached_article_ids.json'))
            write(output/'complete_query_articles.json',{'articles':all_articles,'query_exhausted_in_session':True,
                'new_to_audited_cache_IDs':[a['provider_article_id'] for a in all_articles if a['provider_article_id'] not in cached],
                'historical_event_coverage_certified':False})
            candidates=[a for a in all_articles if a['url']==DETAIL_URL and a['provider_article_id']=='187243']
            if len(candidates)!=1:raise ValueError('EXACT_CANDIDATE_ABSENT_FROM_FRESH_QUERY')
            if '187243' in cached:raise ValueError('CACHED_DETAIL_REUSE_REQUIRED')
            guard.list_complete=True;guard.expected_detail_title=candidates[0]['title']
            check();driver.pace(max(0,8-(clock()-guard.business[-1]['at_monotonic'])))
            detail=driver.detail();guard.check()
            if detail['url']!=DETAIL_URL:raise ValueError('DETAIL_URL_CHANGED')
            data,preview=public_detail(detail['fragment'],guard.expected_detail_title)
            archive('detail187243',detail);write(output/'detail187243_public_text.json',preview)
            result['detail_captured']=True
            if len(guard.business)!=number+1 or [r['status'] for r in guard.responses]!=[200]*(number+1):
                raise ValueError('EXACT_BUSINESS_RECEIPT_SEQUENCE_REQUIRED')
            result['status']='PASS_FRESH_MBS_QUERY_AND_EXACT_DETAIL_REVIEW_REQUIRED';guard.check()
        guard.check()
    except KeyboardInterrupt:
        result.update(status='CANCELLED_REVIEW_REQUIRED',stop_reason='USER_INTERRUPT_NO_REPLAY')
    except Exception as exc:
        result.update(status='STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED',source_stopped=True,
            error_type=type(exc).__name__,stop_reason=guard.stop_reason or str(exc))
    finally:
        try:check()
        except Exception as exc:result.update(status='PROTECTED_OLD_FILE_CHANGED_REVIEW_REQUIRED',source_stopped=True,stop_reason=str(exc))
        result.update(context_request_attempts=guard.attempts,allowed_context_request_attempts=guard.allowed,
            asset_attempts=guard.assets,external_resources_blocked=guard.external_blocked,business_requests=len(guard.business),
            detail_requests=sum(r['url']==DETAIL_URL for r in guard.business),
            http_business_statuses=[r['status'] for r in guard.responses],elapsed_seconds=clock()-guard.started)
        write(output/'business_requests.json',guard.business);write(output/'business_responses.json',guard.responses)
        write(output/'checkpoint.json',{'status':result['status'],'resumable':False,'old_runs_never_resumed':True})
        write(output/'result.json',result)
    return result
