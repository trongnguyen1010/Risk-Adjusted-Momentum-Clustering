"""Rà cache sửa đổi MBS 25/09/2025; không acquisition/approval/application."""
from collections import Counter
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import read, rows, write, hashes
from delta_t1.ingestion.corporate_actions.mbs_revision_cache import (
    vsdc_search_coverage, classify_document, recommendation,
)
from delta_t1.ingestion.corporate_action_sources import Document, sha, terms, kinds
from delta_t1.ingestion.corporate_action_decision_packet import (
    inspect_history_document, TITLE_CHANGE, BODY_CHANGE, RIGHTS_CODE, OUTCOME, change_scope,
)
from delta_t1.ingestion.corporate_action_offline_reconcile import date_view
from delta_t1.ingestion.hnx_announcement_batch import verify_artifact
from delta_t1.ingestion.hnx_announcement_discovery import parse_search_page


def dump_lines(path, values):
    with path.open("x", encoding="utf-8") as stream:
        for value in values: stream.write(json.dumps(value, ensure_ascii=False) + "\n")


def render(result, vsdc, hnx, quote):
    table = "".join("<tr>" + "".join("<td>" + escape(str(v)) + "</td>" for v in (
        d["provider_article_id"], d["title"], ", ".join(d["record_dates"]), d["review"]["status"])) + "</tr>"
        for d in vsdc if d["ticker"] == "MBS")
    listing = "".join("<li>" + escape(f"{d['provider_article_id']}: {d['title']}") + "</li>" for d in hnx)
    return '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>MBS — kết quả rà cache sửa đổi</title><style>body{font:17px/1.65 system-ui;background:#f3f6fa;color:#17283b}main{max-width:1000px;margin:32px auto;padding:32px;background:white;border-radius:12px}h1{font-size:27px}h2{font-size:21px}.hold{background:#fff1da;padding:20px;border-left:5px solid #b36a00}blockquote{background:#eaf5ee;padding:18px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:10px;border:1px solid #ccd5df;text-align:left}code{overflow-wrap:anywhere}</style><main>
<h1>MBS: chưa đủ cơ sở đề nghị duyệt giá sau khi rà cache</h1>
<p>Đợt quyền mua 12%, ngày GDKHQ 24/09/2025, ngày ĐKCC 25/09/2025. Đã rà offline, không gọi thêm nguồn.</p>
<div class="hold"><strong>Giữ chờ: cache lịch sử chưa đầy đủ.</strong> Chưa phát hiện thông báo sửa đổi liên quan trong phần cache đã kiểm tra. Kết quả này chưa chứng minh không có sửa đổi; điều kiện review revision chưa được gỡ.</div>
<h2>Giá gốc vẫn có bằng chứng trực tiếp</h2><blockquote>''' + escape(quote) + '''</blockquote>
<p>Giá 10.000 đồng/CP nằm trong mục quyền mua 100:12 của bài HNX581051. Không phát hiện giá khác cho đúng đợt này trong cache được rà. Đề xuất hiện tại vẫn chưa ký, duyệt hoặc áp dụng.</p>
<h2>Khoảng trống cụ thể</h2><ul><li>VSDC query MBS báo 63 dòng kết quả, nhưng cache chỉ lưu trang đầu gồm 20 dòng. 43 dòng còn lại không có trong snapshot query đã lưu; đây là số dòng tìm kiếm, không phải 43 sự kiện.</li>
<li>Dòng cũ nhất trên trang đã lưu là 24/10/2025, vẫn sau đợt ngày 25/09/2025. Cache VSDC chưa có thông báo gốc hoặc revision cho đúng đợt này.</li>
<li>HNX list đã lưu có đủ 3 bài trong group CORPORATE_NEWS, cửa sổ 26/05–31/12/2025. Chưa bao phủ các group khác hoặc các thông báo ngoài cửa sổ đó; một bài họp chỉ có title, chưa có detail.</li>
<li>Không có issuer revision inventory đầy đủ trong scope đã kiểm tra. Không dùng sự vắng mặt trong cache làm chứng nhận lịch sử.</li></ul>
<h2>Bốn VSDC documents đúng mã cổ phiếu MBS</h2><table><tr><th>ID</th><th>Tiêu đề</th><th>Ngày ĐKCC</th><th>Phân loại</th></tr>''' + table + '''</table>
<p>16 documents khác trong query là các mã chứng khoán khác, chủ yếu trái phiếu có tên bắt đầu bằng MBS; không gộp vào cổ phiếu MBS. Bài quyền mua 193811 có record 03/04/2026 và tỷ lệ 2:1, là đợt khác dù cũng có giá 10.000 đồng/CP.</p>
<h2>HNX list đã lưu</h2><ul>''' + listing + '''</ul>
<p>Đã kiểm tra body hai bài có detail, phân biệt việc huỷ cổ phiếu lẻ/huỷ mã quyền theo lịch với huỷ cả đợt chào bán. Không thấy linked revision signal; không tự gỡ HOLD do coverage gap.</p>
<h2>Kết luận và bước tiếp theo</h2><p><strong>Chưa đề nghị bạn duyệt giá ở stage này.</strong> Bước tiếp theo đề xuất là chuẩn bị lượt tra cứu VSDC giới hạn riêng cho MBS, ưu tiên phần lịch sử chưa được lưu quanh 25/09/2025, cache-first và user-run với budget/STOP rõ ràng. Chưa thực hiện lượt tra cứu đó.</p>
<p>Checkpoint HNX STOP/resumable=false và các proposal/queue cũ được giữ nguyên. PIT, historical identity và final freeze không được phê duyệt ở đây.</p>
<p><small>Trạng thái: ''' + escape(result["recommendation"]["status"]) + '''. Manifest, hashes, raw copies và các phép đối chiếu nằm cùng thư mục.</small></p></main></html>'''


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8")
    config_path = ROOT / "configs/data/corporate_actions/mbs_revision_cache_review_v1.json"
    config = read(config_path)
    if (config["ticker"] != "MBS" or config["network_requests"] != 0 or config["canonical_build"] is not False
            or config["automatic_field_approval"] is not False): raise ValueError("EXACT_OFFLINE_MBS_REVIEW_REQUIRED")
    out = ROOT / config["output"]
    if out.exists(): raise FileExistsError("REFUSE_OVERWRITE")
    directories, pins = {}, {}
    for name, item in config["inputs"].items():
        path = ROOT / item["path"]
        if sha((path / "manifest.json").read_bytes()) != item["manifest_sha256"]: raise ValueError("INPUT_CHANGED: " + name)
        verify_artifact(path);directories[name] = path;pins[name] = item
    proposal, = rows(directories["proposal"] / "unsigned_mbs_price_proposal.jsonl")
    if proposal["vci_payload_sha256"] != config["vci_payload_sha256"] or proposal["owner_decision"] is not None:
        raise ValueError("EXACT_UNSIGNED_MBS_PROPOSAL_REQUIRED")
    target = {"ticker": "MBS", "original_sdk_row": proposal["original_sdk_row"],
        "expected_price_vnd": config["expected_price_vnd_per_share"]}
    assert date_view(target["original_sdk_row"]["record_date"]) == config["record_date_review_view"]
    checkpoint = directories["hnx_state"] / "checkpoint.json"
    checkpoint_hash = sha(checkpoint.read_bytes())
    assert read(checkpoint)["resumable"] is False and read(checkpoint)["source_stopped"]
    raw_copies, raw_proofs, vsdc_documents = {}, {}, []

    def raw(path, expected, name):
        body = path.read_bytes()
        if sha(body) != expected: raise ValueError("RAW_CHANGED: " + str(path))
        raw_copies[name] = body
        raw_proofs[str(path)] = {"sha256": expected, "copy_path": name}
        return body

    index = rows(directories["cache"] / "raw_document_index.jsonl")
    receipt_root = ROOT / config["vsdc_receipt_root"]
    ledger_path = receipt_root / "requests.json"
    ledger = read(ledger_path)
    scoped = [r for r in index if r.get("ticker") == "MBS" or r.get("title_ticker_hint") == "MBS"
        or (ROOT / r["raw_path"]).resolve().is_relative_to(receipt_root.resolve())]
    for doc in scoped:
        body = raw(ROOT / doc["raw_path"], doc["source_hash"], f"raw/vsdc-{doc['provider_article_id']}.html")
        matches = [r for r in ledger if r.get("source_hash") == doc["source_hash"] and r["url"] == doc["source_url"]]
        if len(matches) != 1 or matches[0]["status"] != 200: raise ValueError("RAW_RECEIPT_JOIN_REQUIRED")
        view = inspect_history_document(body, doc["source_url"])
        for key in ("ticker", "title", "record_dates", "ex_dates"):
            if view[key] != doc[key]: raise ValueError("INDEX_VIEW_CHANGED")
        parsed_terms, _ = terms("RIGHTS_ISSUE", view["article_text"]) if view["kinds"] == ["RIGHTS_ISSUE"] else ({}, [])
        prices = [int(Decimal(parsed_terms["rights_subscription_price"]))] if "rights_subscription_price" in parsed_terms else []
        view.update(source_url=doc["source_url"], source_hash=doc["source_hash"],
            raw_path=doc["raw_path"], isolated_rights_prices_vnd=prices)
        view["review"] = classify_document(view, target)
        vsdc_documents.append(view)
    search_receipt, = [r for r in ledger if r["url"].startswith("https://vsdc.vn/vi/search?")]
    search_body = raw(receipt_root / search_receipt["path"], search_receipt["source_hash"], "raw/vsdc-mbs-search.html")
    coverage = vsdc_search_coverage(search_body.decode("utf-8-sig"))
    saved_links = [r for r in rows(directories["cache"] / "discovered_article_links.jsonl")
        if r["search_source_hash"] == search_receipt["source_hash"]]
    if len(saved_links) != coverage["rows_on_page"] or len(scoped) != 20: raise ValueError("SEARCH_DETAIL_COUNT_REQUIRES_REVIEW")
    search_dates = [d["date_hint"] for d in scoped]
    coverage.update(saved_distinct_article_ids=len({r["provider_article_id"] for r in saved_links}),
        oldest_cached_query_date=min(search_dates), newest_cached_query_date=max(search_dates),
        date_hint_is_not_verified_publication=True)
    if (coverage["first"], coverage["last"], coverage["total_reported"], coverage["oldest_cached_query_date"]) != (1, 20, 63, "2025-10-24"):
        raise ValueError("FROZEN_COVERAGE_FACTS_REQUIRE_REVIEW")
    hnx_folder = directories["hnx_state"] / "work/MBS"
    records = rows(hnx_folder / "discovery/discovered_articles.jsonl")
    hnx_result = read(hnx_folder / "discovery/result.json")
    list_receipt = records[0]["list_receipt"]
    list_body = raw(hnx_folder / "discovery" / list_receipt["path"], list_receipt["source_hash"], "raw/hnx-mbs-list.html")
    replay, total = parse_search_page(list_body.decode("utf-8-sig"), "MBS", "HNX", 1)
    if replay != [{k: v for k, v in r.items() if k != "list_receipt"} for r in records] or total != len(records):
        raise ValueError("EXACT_HNX_LIST_REPLAY_REQUIRED")
    hnx_documents, title_only, target_price_in_raw = [], [], False
    for record in records:
        aid = record["provider_article_id"]
        folder = hnx_folder / ("detail-" + aid)
        if not folder.exists():
            title_only.append(record);continue
        verify_artifact(folder)
        response, = rows(folder / "detail_responses.jsonl")
        receipt = response["receipt"]
        body = raw(folder / receipt["path"], receipt["source_hash"], "raw/hnx-" + aid + ".html")
        root = Document(body.decode("utf-8-sig")).root
        title, text = root.find(cls="Box-TieuDe")[0].text(), root.find(cls="Box-Noidung")[0].text()
        if title != record["title"]: raise ValueError("HNX_LIST_DETAIL_TITLE_MISMATCH")
        isolated_prices = []
        if aid == config["provider_article_id"]:
            component = proposal["evidence"]["component_evidence"]["component_text"]
            quote = proposal["evidence"]["primary_price_quotes"][0]
            if component not in text or quote not in component:
                raise ValueError("PRIMARY_COMPONENT_QUOTE_NOT_IN_RAW")
            parsed_terms, _ = terms("RIGHTS_ISSUE", component)
            if "rights_subscription_price" not in parsed_terms: raise ValueError("PRICE_NOT_EXTRACTED_FROM_COMPONENT")
            isolated_prices = [int(Decimal(parsed_terms["rights_subscription_price"]))]
            target_price_in_raw = isolated_prices == [config["expected_price_vnd_per_share"]]
            if not target_price_in_raw: raise ValueError("PRIMARY_PRICE_DIFFERS_FROM_PROPOSAL")
        view = {"ticker": "MBS", "title_ticker_hint": "MBS", "provider_article_id": aid, "title": title,
            "source_url": receipt["url"], "source_hash": receipt["source_hash"], "article_text": text,
            "kinds": kinds(title + " " + text), "rights_codes": sorted(set(RIGHTS_CODE.findall(text))),
            "record_dates": sorted({date_view(reformat_date(m)) for m in re.findall(r"Ngày đăng ký cuối cùng\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.I)}),
            "ex_dates": sorted({date_view(reformat_date(m)) for m in re.findall(r"Ngày giao dịch không hưởng quyền\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.I)}),
            "title_change_markers": [m.group() for m in TITLE_CHANGE.finditer(title)],
            "body_change_quotes": [m.group() for m in BODY_CHANGE.finditer(text)],
            "possible_outcome_title": bool(OUTCOME.search(title)), "change_scope_review": change_scope(text, title),
            "isolated_rights_prices_vnd": isolated_prices}
        view["review"] = classify_document(view, target, selected_provider_ids=[config["provider_article_id"]])
        hnx_documents.append(view)
    # Old cumulative shards are read, never restored or mutated.
    old_scan = read(directories["old_hnx_cache_scan"] / "hnx_cache_scan.json")
    old_shards = []
    for archive_info in old_scan["archives"]:
        archive = Path(archive_info["path"])
        if sha(archive.read_bytes()) != archive_info["sha256"]: raise ValueError("OLD_SHARD_CHANGED")
        with zipfile.ZipFile(archive) as z:
            states = json.loads(z.read(archive_info["latest_checkpoint"]))["states"]
            if "MBS" in states:
                mbs = states["MBS"]
                if mbs["discovery"] is not None or mbs["details"]: raise ValueError("OLD_MBS_CACHE_REQUIRES_EXPANDED_OFFLINE_REVIEW")
                old_shards.append({**archive_info, "MBS_state": mbs})
    gaps = ["VSDC_QUERY_ONLY_FIRST_20_OF_63_ROWS_SAVED", "VSDC_SAVED_PAGE_OLDEST_20251024_AFTER_TARGET_20250925",
        "HNX_ONLY_CORPORATE_NEWS_20250526_20251231_NOT_ALL_GROUPS_OR_LATER_NOTICES",
        "HNX_586647_DETAIL_NOT_CACHED_TITLE_ONLY", "ISSUER_AND_UNASSIGNED_DOCUMENT_HISTORY_NOT_COMPLETELY_INDEXED_IN_SCOPE"]
    reviews = [d["review"] for d in [*vsdc_documents, *hnx_documents]]
    decision = recommendation(reviews, gaps)
    assert decision["status"] == "HOLD_CACHE_COVERAGE_GAP"
    counts = Counter(r["status"] for r in reviews)
    assert len(vsdc_documents) == 20 and sum(d["ticker"] == "MBS" for d in vsdc_documents) == 4
    assert len(hnx_documents) == 2 and len(title_only) == 1 and len(old_shards) == 1
    result = {"stage": config["stage"], "technical_status": "PASS_OFFLINE_CACHE_REVIEW", "recommendation": decision,
        "price_evidence_10000_vnd_per_share_retained": target_price_in_raw, "revision_review_complete": False,
        "vsdc_query_coverage": coverage, "reviewed_vsdc_docs": 20, "vsdc_exact_equity_docs": 4,
        "excluded_other_security_docs": 16, "hnx_list_articles": len(records), "hnx_detail_docs": 2,
        "hnx_title_only_articles": len(title_only), "old_cumulative_zip_hashes_verified": len(old_scan["archives"]),
        "document_status_counts": dict(counts), "raw_hashes_verified": len(raw_proofs),
        "network_requests": 0, "approved_fields": 0, "applied_fields": 0, "queue_modified": False,
        "old_owner_choices_modified": False, "checkpoint_resumable": False,
        "next_stage_proposal": "Prepare a separately scoped user-run VSDC MBS historical lookup around 2025-09-25; do not resume HNX STOP or request in this review"}
    out.mkdir(parents=True)
    for name, body in raw_copies.items():
        path = out / name;path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(body)
    dump_lines(out / "reviewed_documents.jsonl", [*vsdc_documents, *hnx_documents])
    write(out / "hnx_title_only_records.json", title_only)
    write(out / "old_shard_MBS_states.json", old_shards)
    write(out / "inputs.json", {"directories": pins, "raw_proofs": raw_proofs,
        "vsdc_ledger_sha256": sha(ledger_path.read_bytes()), "checkpoint_sha256": checkpoint_hash})
    write(out / "config.json", config);write(out / "result.json", result)
    quote = proposal["evidence"]["primary_price_quotes"][0]
    (out / "ket_luan_ra_cache_MBS.html").write_text(render(result, vsdc_documents, records, quote), encoding="utf-8")
    assert sha(checkpoint.read_bytes()) == checkpoint_hash
    write(out / "runtime.json", {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [Path(__file__), config_path,
        ROOT / "src/delta_t1/ingestion/corporate_actions/mbs_revision_cache.py",
        ROOT / "src/delta_t1/ingestion/corporate_action_decision_packet.py"]})
    write(out / "manifest.json", {"artifact_type": "mbs-cached-revision-review-v1", "files": hashes(out)})
    print(json.dumps(result, ensure_ascii=False, indent=2))


def reformat_date(value):
    from datetime import datetime
    return datetime.strptime(value, "%d/%m/%Y").date().isoformat()


if __name__ == "__main__": main()
