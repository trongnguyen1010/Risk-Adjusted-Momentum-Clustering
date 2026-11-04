"""User-run, bounded public-browser HTML pilot; never replays HTTP POSTs."""
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

from ..corporate_action_sources import Document, sha, search_url
from ..hnx_announcement_batch import verify_artifact
from .hnx_local_supplement import read, rows, write, hashes
from .hnx_local_pvs import seal
from . import vsdc_mbs_pilot_v2 as prior

CONFIG = "configs/data/corporate_actions/vsdc_mbs_browser_html_pilot_v1.json"
TYPE = "vsdc-mbs-browser-html-two-page-pilot-v1"
PREP_TYPE = "vsdc-mbs-browser-html-preparation-v1"
CONTAINER = "#divGlSearchArticles"
BUTTON = '#divGlSearchArticles #d_number_of_page button[onclick="changePageArticles(2)"]'
CHALLENGE = re.compile(r"captcha|verify you are human|access denied|cloudflare challenge|cf-chl-", re.I)
STATIC_PREFIXES = ("/assets/", "/js/", "/lib/")


def validate(config):
    expected = {
        "stage": "VSDC_MBS_BROWSER_HTML_TWO_PAGE_PILOT_V1", "ticker": "MBS", "url": search_url("MBS"),
        "max_business_requests": 2, "max_context_request_attempts": 80, "max_asset_attempts": 78,
        "max_seconds": 90, "business_interval_seconds": 8, "operation_timeout_seconds": 15,
        "max_html_bytes": 2000000, "workers": 1, "channel": "chrome", "headless": False,
        "playwright_version": "1.57.0", "retry": False, "resume": False, "details": False,
        "persistent_profile": False, "export_cookies_or_auth": False, "ignore_https_errors": False,
        "output_base": "data/corporate_actions/work/vsdc_mbs_browser_html_pilot_v1",
        "preparation": "data/corporate_actions/work/vsdc_mbs_browser_html_preparation_20261103_v1",
        "v2_preparation": "data/corporate_actions/work/vsdc_mbs_pagination_preparation_20261103_v2",
        "v2_preparation_manifest_sha256": "4ef0965de83c95f153f81f34489883864f3986725d33661033948527e8e3e122",
        "v2_run": "data/corporate_actions/work/vsdc_mbs_pagination_pilot_v2/run-20261103T050150450791Z/state",
        "v2_run_manifest_sha256": "49485453ccfccbb1752ce365b78b7c3cf0ece59ccdd964e8de2f8045ef507e50",
        "v2_review": "data/corporate_actions/work/vsdc_mbs_pagination_live_review_20261103_v2",
        "v2_review_manifest_sha256": "e7ef3dd151762273ced8423cd6afce203d6525897aad5ca008fe726ed1217481",
    }
    if set(config) != set(expected) or any(config[k] != v for k, v in expected.items()):
        raise ValueError("FIXED_BROWSER_HTML_PILOT_CONTRACT_REQUIRED")


def runtime(project):
    names = [CONFIG, "scripts/corporate_actions/collect_vsdc_mbs_browser_html_pilot_v1.py",
             "scripts/corporate_actions/prepare_vsdc_mbs_browser_html_pilot_v1.py",
             "src/delta_t1/ingestion/corporate_actions/vsdc_mbs_browser_html.py"]
    return {**prior.runtime(project), **{n: sha((project / n).read_bytes()) for n in names}}


def parents(project, config):
    _, old_prep = prior.load_preparation(project)
    if old_prep != project / config["v2_preparation"]:
        raise ValueError("V2_PREPARATION_PATH_CHANGED")
    for key, kind in [("v2_preparation", prior.PREPARATION_TYPE), ("v2_run", prior.TYPE),
                      ("v2_review", "vsdc-mbs-pagination-offline-live-review-v2")]:
        folder = project / config[key]
        if sha((folder / "manifest.json").read_bytes()) != config[key + "_manifest_sha256"]:
            raise ValueError("BROWSER_PARENT_MANIFEST_CHANGED: " + key)
        verify_artifact(folder, {kind})
    if read(project / config["v2_run"] / "result.json")["http_statuses"] != [200, 400]:
        raise ValueError("V2_FAILURE_CONTEXT_CHANGED")
    return old_prep


def protected_check(project, protected):
    for name, digest in protected.items():
        if not (project / name).is_file() or sha((project / name).read_bytes()) != digest:
            raise ValueError("PROTECTED_OLD_FILE_CHANGED: " + name)


def readiness(config):
    try:
        version = importlib.metadata.version("playwright")
    except importlib.metadata.PackageNotFoundError:
        version = None
    candidates = [Path(os.environ.get(key, "C:/__missing__")) / suffix for key, suffix in [
        ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
        ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
        ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe")]]
    chrome = next((str(p) for p in candidates if p.is_file()), None)
    return {"playwright_version": version, "chrome_executable_found": chrome,
            "ready": version == config["playwright_version"] and chrome is not None,
            "browser_launched": False}


def load_preparation(project):
    config = read(project / CONFIG); validate(config); parents(project, config)
    prep = project / config["preparation"]
    verify_artifact(prep, {PREP_TYPE})
    if read(prep / "runtime.json") != runtime(project) or read(prep / "plan.json")["config"] != config:
        raise ValueError("BROWSER_PREPARED_RUNTIME_OR_CONFIG_CHANGED")
    protected_check(project, read(prep / "protected_old_files.json"))
    return config, prep


def prepare(project):
    project = Path(project).resolve(); config = read(project / CONFIG); validate(config)
    old_prep = parents(project, config)
    out = project / config["preparation"]
    if out.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    protected = read(old_prep / "protected_old_files.json")
    for key in ["v2_preparation", "v2_run", "v2_review"]:
        folder = project / config[key]
        for name in ["manifest.json", *read(folder / "manifest.json")["files"]]:
            path = folder / name
            protected[path.relative_to(project).as_posix()] = sha(path.read_bytes())
    protected.update(prior.runtime(project))
    out.mkdir(parents=True)
    (out / "cached_article_ids.json").write_bytes((old_prep / "cached_article_ids.json").read_bytes())
    write(out / "plan.json", {"config": config, "status": "PREPARED_NOT_EXECUTED",
        "source_requests": 0, "browser_launches": 0, "readiness": readiness(config),
        "acquisition": "Fresh non-persistent public Chrome; one navigation and one ordinary page2 button click",
        "raw_policy": "Archive exact public rendered container fragments, not whole DOM, cookies, tokens, HAR or profile",
        "request_budget": "2 business requests; up to 78 assets/blocked external attempts, 80 total context attempts",
        "browser_session": "Default browser identity; automatic ephemeral first-party session, never imported/exported"})
    write(out / "protected_old_files.json", protected)
    write(out / "runtime.json", runtime(project))
    write(out / "manifest.json", {"artifact_type": PREP_TYPE, "files": hashes(out)})
    load_preparation(project)
    return {"status": "PREPARED_NOT_EXECUTED", "source_requests": 0,
            "protected_old_files": len(protected), "readiness": readiness(config), "output": str(out)}


class Guard:
    def __init__(self, config, output, check_old=lambda: None, clock=time.monotonic):
        self.config, self.output, self.check_old, self.clock = config, output, check_old, clock
        self.started = clock(); self.first_business_at = None
        self.attempts = self.allowed = self.assets = self.external_blocked = 0
        self.business = []; self.responses = []; self.stop_reason = None

    def fail(self, reason):
        if self.stop_reason is None: self.stop_reason = reason

    def check(self):
        if self.clock() - self.started >= self.config["max_seconds"]:
            self.fail("BROWSER_RUN_TIME_BUDGET_EXHAUSTED")
        if self.stop_reason: raise ValueError(self.stop_reason)

    def timeout_ms(self):
        self.check()
        return max(1, int(min(self.config["operation_timeout_seconds"],
                             self.config["max_seconds"] - (self.clock() - self.started)) * 1000))

    def log(self, event):
        with (self.output / "network_ledger.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def admit(self, url, method, resource, body=None, redirected=False):
        self.attempts += 1
        parts = urlsplit(url)
        safe_url = self.config["url"] if url == self.config["url"] else (
            f"{parts.scheme}://{parts.hostname}{parts.path}" if parts.hostname == "vsdc.vn"
            and parts.path.startswith(STATIC_PREFIXES) else f"{parts.scheme}://{parts.hostname}/[OUT_OF_SCOPE]")
        event = {"event": "REQUEST_ATTEMPT", "number": self.attempts,
                 "url": safe_url, "method": method, "resource_type": resource}
        try:
            self.check()
            if self.attempts > self.config["max_context_request_attempts"]:
                raise ValueError("BROWSER_CONTEXT_REQUEST_BUDGET_EXHAUSTED")
            if redirected: raise ValueError("BROWSER_REDIRECT_NOT_FOLLOWED")
            if parts.username or parts.password: raise ValueError("BROWSER_URL_CREDENTIALS_BLOCKED")
            if re.search(r"captcha|challenge|login|signin", parts.path, re.I):
                raise ValueError("BROWSER_ACCESS_BOUNDARY")
            if url == self.config["url"]:
                self.check_old()
                index = len(self.business)
                if (index >= 2 or method != ("GET" if index == 0 else "POST")
                        or resource not in ({"document"} if index == 0 else {"xhr", "fetch"})
                        or (index == 0 and body is not None)):
                    raise ValueError("BROWSER_FIXED_BUSINESS_SCOPE_OR_SEQUENCE_REQUIRED")
                if index == 1 and json.loads(body or "null") != {"SearchKey": 4, "CurrentPage": 2}:
                    raise ValueError("BROWSER_FIXED_PAGE2_PAYLOAD_REQUIRED")
                if index == 1 and self.clock() - self.first_business_at < 8:
                    raise ValueError("BROWSER_BUSINESS_INTERVAL_REQUIRED")
                if index == 0: self.first_business_at = self.clock()
                self.business.append({"method": method, "url": url, "at_monotonic": self.clock()})
                event["classification"] = "BUSINESS_LIST"
            else:
                self.assets += 1
                if self.assets > self.config["max_asset_attempts"]:
                    raise ValueError("BROWSER_ASSET_BUDGET_EXHAUSTED")
                if method != "GET" or resource not in {"script", "stylesheet", "image", "font", "media", "other"}:
                    raise ValueError("BROWSER_OTHER_BUSINESS_OR_DETAIL_REQUEST_BLOCKED")
                if parts.hostname != "vsdc.vn":
                    self.external_blocked += 1
                    event.update(classification="EXTERNAL_RESOURCE_BLOCKED", allowed=False)
                    self.log(event); return False
                if (parts.scheme != "https" or parts.port not in {None, 443}
                        or not (parts.path.startswith(STATIC_PREFIXES) or parts.path == "/favicon.ico")):
                    raise ValueError("BROWSER_ASSET_SCOPE_REQUIRED")
                event["classification"] = "FIRST_PARTY_ASSET"
            self.allowed += 1; event["allowed"] = True; self.log(event); return True
        except Exception as exc:
            self.fail(str(exc)); event.update(allowed=False, stop_reason=self.stop_reason)
            self.log(event); return False

    def response(self, url, method, status, headers):
        safe = {k.casefold(): v for k, v in headers.items()
                if k.casefold() in {"content-type", "content-length", "retry-after"}}
        if url == self.config["url"]:
            row = {"url": url, "method": method, "status": status, "headers": safe}
            self.responses.append(row); self.log({"event": "BUSINESS_RESPONSE", **row})
        if not 200 <= status < 300: self.fail("BROWSER_HTTP_ERROR_OR_REDIRECT: " + str(status))
        if safe.get("retry-after"): self.fail("BROWSER_RETRY_AFTER_STOP")
        length = safe.get("content-length", "")
        if str(length).isdigit() and int(length) > self.config["max_html_bytes"]:
            self.fail("BROWSER_DECLARED_RESPONSE_SIZE_LIMIT")
        if self.stop_reason:
            parts = urlsplit(url)
            self.log({"event": "RESPONSE_BOUNDARY", "host": parts.hostname, "path": parts.path,
                      "status": status, "stop_reason": self.stop_reason})


def fragment_bytes(fragment, limit):
    data = fragment.encode("utf-8")
    if len(data) > limit: raise ValueError("RENDERED_HTML_SIZE_LIMIT")
    root = Document(fragment).root
    if len(root.find(id="divGlSearchArticles")) != 1:
        raise ValueError("RENDERED_PUBLIC_ARTICLE_CONTAINER_REQUIRED")
    if any(root.find(tag) for tag in ["script", "input", "form", "iframe", "textarea"]):
        raise ValueError("RENDERED_FRAGMENT_PRIVATE_OR_EXECUTABLE_CONTENT_NOT_ARCHIVED")
    if any(re.search(r"token|password|cookie|authorization|csrf", key, re.I)
           for node in root.find() for key in node.attrs):
        raise ValueError("RENDERED_FRAGMENT_SENSITIVE_ATTRIBUTE_NOT_ARCHIVED")
    if CHALLENGE.search(root.text()): raise ValueError("BROWSER_CHALLENGE_STOP")
    return data


class PlaywrightDriver:
    def __init__(self, config, guard):
        self.config, self.guard = config, guard
        self.manager = self.browser = self.context = self.page = None
        self.blocked = set()
        self.closing = False

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        try:
            self.manager = sync_playwright().start()
            self.browser = self.manager.chromium.launch(channel="chrome", headless=False,
                                                       timeout=self.guard.timeout_ms())
            self.context = self.browser.new_context(ignore_https_errors=False, accept_downloads=False,
                                                     service_workers="block")
            self.context.route("**/*", self._route)
            self.context.on("response", self._response)
            self.context.on("requestfailed", self._failed)
            self.context.route_web_socket("**/*", self._websocket)
            self.page = self.context.new_page()
            self.context.on("page", self._popup)
            self.page.on("dialog", self._dialog)
            self.version = self.browser.version
            return self
        except Exception:
            self.__exit__(None, None, None); raise

    def _route(self, route):
        r = route.request
        allowed = self.guard.admit(r.url, r.method, r.resource_type,
                                   r.post_data, r.redirected_from is not None)
        if allowed:
            if r.url == self.config["url"]:
                content_type = r.header_value("content-type")
                ajax = r.header_value("x-requested-with")
                self.guard.business[-1].update(
                    request_header_names=sorted(r.headers.keys()),
                    request_content_type=(content_type if content_type in {
                        None, "application/json;charset=UTF-8", "application/json;charset=utf-8"} else "OTHER_VALUE_OMITTED"),
                    x_requested_with=(ajax if ajax in {None, "XMLHttpRequest"} else "OTHER_VALUE_OMITTED"))
            route.continue_()
        else:
            self.blocked.add(r); route.abort("blockedbyclient")

    def _response(self, response):
        self.guard.response(response.url, response.request.method, response.status,
                            {k: response.header_value(k) for k in ["content-type", "content-length", "retry-after"]})

    def _failed(self, request):
        if not self.closing and request not in self.blocked:
            self.guard.fail("BROWSER_REQUEST_FAILED_TLS_OR_TRANSPORT")

    def _websocket(self, socket):
        self.guard.fail("BROWSER_WEBSOCKET_NOT_AUTHORIZED"); socket.close()

    def _popup(self, page):
        self.guard.fail("BROWSER_UNEXPECTED_PAGE"); page.close()

    def _dialog(self, dialog):
        self.guard.fail("BROWSER_UNEXPECTED_DIALOG"); dialog.dismiss()

    def _snapshot(self, response, include_scope):
        self.guard.check()
        if self.page.url != self.config["url"]: raise ValueError("BROWSER_QUERY_URL_CHANGED")
        fragment = self.page.locator(CONTAINER).evaluate("(el) => el.outerHTML", timeout=self.guard.timeout_ms())
        body = response.body()  # DOM is ready: document/XHR body is already complete.
        if len(body) > self.config["max_html_bytes"]: raise ValueError("BUSINESS_HTTP_BODY_SIZE_LIMIT")
        if CHALLENGE.search(body.decode("utf-8", errors="replace")):
            raise ValueError("BROWSER_RESPONSE_CHALLENGE_STOP")
        scope = self.page.content() if include_scope else None
        if scope and len(scope.encode("utf-8")) > self.config["max_html_bytes"]:
            raise ValueError("BROWSER_FULL_DOM_SIZE_LIMIT")
        self.guard.check()
        return {"url": self.page.url, "fragment": fragment, "scope_html": scope,
                "http_body_sha256": sha(body), "http_body_bytes": len(body), "http_status": response.status}

    def first(self):
        response = self.page.goto(self.config["url"], wait_until="domcontentloaded",
                                  timeout=self.guard.timeout_ms())
        self.guard.check()
        if response is None or response.status != 200: raise ValueError("BROWSER_PAGE1_HTTP200_REQUIRED")
        return self._snapshot(response, True)

    def pace(self, seconds):
        if seconds > 0:
            if seconds * 1000 >= self.guard.timeout_ms(): raise ValueError("BROWSER_PACING_TIME_BUDGET")
            self.page.wait_for_timeout(seconds * 1000)
        self.guard.check()

    def second(self, first_fragment):
        button = self.page.locator(BUTTON).filter(has_text=re.compile(r"^\s*2\s*$"))
        if button.count() != 1: raise ValueError("UNIQUE_OBSERVED_PAGE2_BUTTON_REQUIRED")
        with self.page.expect_response(lambda r: r.url == self.config["url"] and r.request.method == "POST",
                                       timeout=self.guard.timeout_ms()) as pending:
            button.click(timeout=self.guard.timeout_ms(), no_wait_after=True)
        response = pending.value
        self.guard.check()
        if response.status != 200: raise ValueError("BROWSER_PAGE2_HTTP200_REQUIRED")
        self.page.wait_for_function("old => {const el=document.querySelector('#divGlSearchArticles'); return el && el.outerHTML !== old;}",
                                    arg=first_fragment, timeout=self.guard.timeout_ms())
        return self._snapshot(response, False)

    def __exit__(self, *args):
        self.closing = True
        for item in [self.context, self.browser]:
            if item is not None:
                try: item.close()
                except Exception: pass
        if self.manager is not None:
            try: self.manager.stop()
            except Exception: pass


def run(project, output, *, dry_run=False, driver_factory=PlaywrightDriver, clock=time.monotonic):
    project, output = Path(project).resolve(), Path(output).resolve()
    config, prep = load_preparation(project)
    if output.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    ready = readiness(config)
    if dry_run:
        return {"status": "OFFLINE_CHECK_PASS" if ready["ready"] else "SETUP_REQUIRED",
                "browser_launched": False, "source_requests": 0, "readiness": ready,
                "max_business_requests": 2, "max_context_request_attempts": 80}
    output.mkdir(parents=True); (output / "network_ledger.jsonl").touch()
    protected = read(prep / "protected_old_files.json")
    check_old = lambda: protected_check(project, protected)
    guard = Guard(config, output, check_old, clock)
    result = {"stage": config["stage"], "status": "STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED",
              "resumable": False, "page2_verified": False, "bulk_collection_ready": False,
              "browser_launched": False,
              "detail_requests": 0, "normalized_observations": 0, "canonical_fields_applied": 0,
              "pit_or_identity_promoted": False, "openai_api_calls": 0, "source_stopped": False}
    write(output / "plan.json", config); write(output / "runtime.json", runtime(project))
    write(output / "protected_old_files.json", protected); write(output / "environment.json", ready)
    (output / "cached_article_ids.json").write_bytes((prep / "cached_article_ids.json").read_bytes())
    write(output / "input_provenance.json", {"preparation_path": str(prep),
        "preparation_manifest_sha256": sha((prep / "manifest.json").read_bytes()),
        "parents": {k: config[k] for k in config if k.endswith("manifest_sha256")},
        "capture_kind": "PUBLIC_RENDERED_DOM_CONTAINER_NOT_RAW_HTTP_OR_FULL_DOM"})
    def snapshot(number, value, total=None, prior_ids=()):
        guard.check()
        if value["url"] != config["url"] or value["http_status"] != 200:
            raise ValueError("SNAPSHOT_SCOPE_AND_HTTP200_REQUIRED")
        data = fragment_bytes(value["fragment"], config["max_html_bytes"])
        folder = output / "rendered_html"; folder.mkdir(exist_ok=True)
        with (folder / f"page{number}.html").open("xb") as stream: stream.write(data)
        write(output / f"page{number}_receipt.json", {"url": value["url"], "page": number,
            "captured_at": datetime.now(timezone.utc).isoformat(), "fragment_sha256": sha(data),
            "http_status": value["http_status"], "http_body_sha256_not_archived": value["http_body_sha256"],
            "http_body_bytes": value["http_body_bytes"], "raw_http_body_archived": False})
        parsed = prior.page(value["fragment"], number, total, prior_ids)
        write(output / f"page{number}.json", parsed)
        return parsed
    try:
        if not ready["ready"]: raise ValueError("LOCAL_PLAYWRIGHT_OR_CHROME_SETUP_REQUIRED")
        with driver_factory(config, guard) as driver:
            result["browser_launched"] = True
            first_value = driver.first(); guard.check()
            write(output / "browser.json", {"version": driver.version, "channel": "chrome", "persistent": False,
                "default_identity": True, "cookie_auth_exported": False, "TLS_ignore_errors": False})
            write(output / "fresh_source_contract.json", prior.source_contract(first_value["scope_html"]))
            first = snapshot(1, first_value)
            total = first["coverage"]["reported_total"]
            if total <= 20:
                result["status"] = "PARTIAL_FRESH_QUERY_HAS_NO_SECOND_PAGE"
            else:
                if first["coverage"]["last"] != 20: raise ValueError("BROWSER_PAGE1_SIZE20_REQUIRED")
                check_old()
                driver.pace(max(0, 8 - (clock() - guard.first_business_at)))
                guard.check()
                second_value = driver.second(first_value["fragment"])
                second = snapshot(2, second_value, total, first["article_ids"])
                if ([r["method"] for r in guard.business] != ["GET", "POST"]
                        or [r["status"] for r in guard.responses] != [200, 200]):
                    raise ValueError("TWO_BROWSER_BUSINESS_RESPONSES_REQUIRED")
                cached = set(read(prep / "cached_article_ids.json"))
                result.update(status="PASS_BROWSER_HTML_PAGE2_REVIEW_REQUIRED", page2_verified=True,
                    page1_article_ids=len(first["article_ids"]), page2_article_ids=len(second["article_ids"]),
                    cached_page2_provider_ids=len(set(second["article_ids"]) & cached), reported_total=total,
                    remaining_query_rows=total - len(first["article_ids"]) - len(second["article_ids"]))
                guard.check()
        guard.check()
    except KeyboardInterrupt:
        result.update(status="CANCELLED_REVIEW_REQUIRED", stop_reason="USER_INTERRUPT_NO_REPLAY")
    except Exception as exc:
        result.update(status="STOPPED_BROWSER_OR_LAYOUT_REVIEW_REQUIRED", source_stopped=True,
                      error_type=type(exc).__name__, stop_reason=guard.stop_reason or str(exc), page2_verified=False)
    finally:
        try: check_old()
        except Exception as exc:
            result.update(status="PROTECTED_OLD_FILE_CHANGED_REVIEW_REQUIRED", source_stopped=True,
                          stop_reason=str(exc), page2_verified=False)
        result.update(context_request_attempts=guard.attempts, allowed_context_request_attempts=guard.allowed,
                      business_requests=len(guard.business), asset_attempts=guard.assets,
                      external_resources_blocked=guard.external_blocked,
                      http_business_statuses=[r["status"] for r in guard.responses])
        write(output / "business_requests.json", guard.business)
        write(output / "business_responses.json", guard.responses)
        write(output / "checkpoint.json", {"status": result["status"], "resumable": False,
              "business_requests": len(guard.business), "old_runs_never_resumed": True})
        write(output / "result.json", result)
    return result
