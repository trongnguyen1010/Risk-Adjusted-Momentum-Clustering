"""Đối chiếu ba nguồn offline từ observation đã review/pin; không tạo canonical."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re


RULE_ID = "CA-THIRD-SOURCE-V1"
FORMAT = "CORPORATE_ACTION_THIRD_SOURCE_RECONCILE_V1"
COMPARISON_FIELDS = (
    "exact_security", "event_identity", "field", "semantic_scope", "unit",
    "effective_period", "revision_state",
)
HTTP_TYPES = {"HTTP_RAW_GET_200", "HTTP_RESPONSE_ENTITY_BODY"}
DOM_TYPES = {"RENDERED_DOM_TEXT", "REUSED_RENDERED_DOM_TEXT"}


class EvidenceError(ValueError):
    """Evidence không đủ điều kiện để chọn field, không làm mất case độc lập."""


def _hash(body):
    return hashlib.sha256(body).hexdigest()


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _loads(body):
    def invalid_number(value):
        raise EvidenceError("NON_FINITE_JSON_NUMBER:" + value)

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise EvidenceError("DUPLICATE_JSON_KEY:" + key)
            result[key] = value
        return result

    return json.loads(body, parse_constant=invalid_number, object_pairs_hook=unique_keys)


def _value_key(value):
    """So chính xác; không tolerance, suy đơn vị hay coi bool là số 1/0."""
    if value is None:
        raise EvidenceError("VALUE_MISSING")
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise EvidenceError("NON_FINITE_VALUE")
        return ("number", Decimal(str(value)))
    if isinstance(value, str):
        if not value.strip():
            raise EvidenceError("VALUE_MISSING")
        return ("string", value)
    if isinstance(value, dict) and value and all(isinstance(k, str) for k in value):
        return ("object", tuple((k, _value_key(v)) for k, v in sorted(value.items())))
    if isinstance(value, list) and value:
        return ("array", tuple(_value_key(v) for v in value))
    raise EvidenceError("UNSUPPORTED_OR_EMPTY_VALUE")


def _pointer(value, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise EvidenceError("REVIEW_POINTER_REQUIRED")
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _review(ref, read_verified):
    return _pointer(_loads(read_verified(ref["path"])), ref["pointer"])


def _verify_source(source, key, read_verified):
    if source["comparison_key"] != key:
        raise EvidenceError("COMPARISON_KEY_MISMATCH:" + source["source_id"])
    if source.get("superseded") is not False:
        raise EvidenceError("REVISION_STATE_UNREVIEWED_OR_SUPERSEDED")
    if not source.get("document_id") or not source.get("origin_group_id"):
        raise EvidenceError("DOCUMENT_ORIGIN_REQUIRED")
    review = _review(source["review_ref"], read_verified)
    for name in ("source_id", "artifact_path", "sha256", "receipt_path", "source_url", "evidence_type"):
        if review[name] != source[name]:
            raise EvidenceError("SOURCE_REVIEW_BINDING_MISMATCH:" + name)
    if _value_key(review["observed_value"]) != _value_key(source["value"]):
        raise EvidenceError("OBSERVATION_REVIEW_VALUE_MISMATCH")
    body = read_verified(source["artifact_path"])
    if not body or _hash(body) != source["sha256"]:
        raise EvidenceError("SOURCE_BODY_HASH_OR_EMPTY")
    receipt = _loads(read_verified(source["receipt_path"]))
    if receipt.get("source_url") != source["source_url"]:
        raise EvidenceError("RECEIPT_URL_MISMATCH")
    digest = receipt.get("sha256", receipt.get("source_hash"))
    if digest != source["sha256"]:
        raise EvidenceError("RECEIPT_BODY_HASH_MISMATCH")
    if receipt.get("route_stop"):
        raise EvidenceError("ACCESS_CONTROL_RECEIPT")
    kind = source["evidence_type"]
    if kind in HTTP_TYPES:
        if receipt.get("status") != 200 or receipt.get("body_bytes") != len(body):
            raise EvidenceError("HTTP200_NONEMPTY_RECEIPT_REQUIRED")
        if receipt.get("raw_path") != source["artifact_path"]:
            raise EvidenceError("HTTP_RAW_PATH_MISMATCH")
    elif kind in DOM_TYPES:
        if (receipt.get("evidence_type") != "RENDERED_DOM_TEXT"
                or receipt.get("http_status") is not None
                or receipt.get("status") is not None
                or receipt.get("raw_path") is not None
                or receipt.get("raw_cache") is True
                or receipt.get("http_receipt_available") is True):
            raise EvidenceError("DOM_RECEIPT_MUST_NOT_CLAIM_HTTP_RAW")
    else:
        raise EvidenceError("UNSUPPORTED_EVIDENCE_TYPE")


def reconcile_case(case, read_verified):
    """Tính lại lựa chọn; metadata origin/so sánh đến từ review đã pin, không từ URL.

    Không tìm nguồn qua network hoặc tự đọc hiểu PDF. Field observations và đánh
    giá nguồn gốc phải do upstream parser/agent review cung cấp, có pin/locator.
    selected_value của receipt cũ không tham gia phép chọn.
    """
    result = {
        "case_id": case.get("case_id"), "rule_id": RULE_ID,
        "comparison_key": deepcopy(case.get("comparison_key")),
        "status": "UNRESOLVED", "selected_value": None,
        "supporting_source_ids": [], "dissenting_source_ids": [],
        "observations": deepcopy(case.get("observations", [])),
        "reasons": [], "canonical_applied": False, "price_factor_computed": False,
        "pit_status": "NOT_PROMOTED", "historical_identity": "UNVERIFIED",
        "owner_action_required": False,
    }
    try:
        key = case["comparison_key"]
        if any(not isinstance(key.get(k), str) or not key[k].strip()
               for k in COMPARISON_FIELDS):
            raise EvidenceError("COMPLETE_COMPARISON_KEY_REQUIRED")
        if key["exact_security"] != case["ticker"]:
            raise EvidenceError("EXACT_SECURITY_MISMATCH")
        if _review(case["comparison_review_ref"], read_verified) != key:
            raise EvidenceError("COMPARABILITY_REVIEW_MISMATCH")
        origin = _review(case["origin_review_ref"], read_verified)
        if origin.get("qualified") is not True:
            raise EvidenceError("THIRD_SOURCE_ORIGIN_UNQUALIFIED")
        revision = _review(case["revision_review_ref"], read_verified)
        if not isinstance(revision, str) or not revision.strip():
            raise EvidenceError("REVISION_REVIEW_REQUIRED")
        if case.get("known_superseding_revision") is not False:
            raise EvidenceError("SUPERSEDING_REVISION_OR_REVIEW_GAP")
        if case.get("additional_known_source_ids") != []:
            raise EvidenceError("ADDITIONAL_KNOWN_EVIDENCE_REQUIRES_REVIEW")
        if not case.get("discovery_order"):
            raise EvidenceError("DISCOVERY_ORDER_REQUIRED")
        obs = case["observations"]
        if not isinstance(obs, list) or any(not isinstance(s, dict) for s in obs):
            raise EvidenceError("OBSERVATION_LIST_REQUIRED")
        if len(obs) < 3:
            raise EvidenceError("THIRD_SOURCE_REQUIRED")
        if len(obs) != 3 or [s["role"] for s in obs] != ["A", "B", "C"]:
            raise EvidenceError("EXACT_ORDERED_A_B_C_REQUIRED")
        for source in obs:
            _verify_source(source, key, read_verified)
        a, b, c = obs
        if len({s["source_id"] for s in obs}) != 3:
            raise EvidenceError("DUPLICATE_SOURCE_ID")
        if (c["sha256"] in {a["sha256"], b["sha256"]}
                or c["document_id"] in {a["document_id"], b["document_id"]}
                or c["origin_group_id"] in {a["origin_group_id"], b["origin_group_id"]}):
            raise EvidenceError("THIRD_SOURCE_COPY_OR_SHARED_ORIGIN")
        av, bv, cv = [_value_key(s["value"]) for s in obs]
        if av == bv:
            raise EvidenceError("INITIAL_PAIR_IS_NOT_A_VALUE_CONFLICT")
        if cv != av and cv != bv:
            raise EvidenceError("THIRD_SOURCE_DISAGREES_WITH_BOTH")
        matching = a if cv == av else b
        dissent = b if cv == av else a
        result.update(
            status="SELECTED_BY_THIRD_SOURCE_CORROBORATION",
            selected_value=deepcopy(matching["value"]),
            supporting_source_ids=[matching["source_id"], c["source_id"]],
            dissenting_source_ids=[dissent["source_id"]],
            document_origin_assessment=deepcopy(origin),
            revision_scope_check=revision,
            discovery_order=deepcopy(case["discovery_order"]),
            value_locators=deepcopy(case.get("value_locators", {})),
            evidence_hashes={s["source_id"]: s["sha256"] for s in obs},
            caveats=deepcopy(case.get("caveats", [])),
            selection_scope="OFFLINE_REVIEW_FIELD_ONLY_NOT_CANONICAL",
        )
    except (EvidenceError, KeyError, TypeError, ValueError, OSError, IndexError) as exc:
        result["reasons"].append(str(exc))
    return result


def _under(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("PATH_OUTSIDE_WORKSPACE")
    return path


def run(config_path, output, root):
    """Chạy đúng bundle offline được pin; output mới, không sửa pipeline/archive cũ."""
    root = Path(root).resolve()
    config_path = _under(root, config_path)
    config_bytes = config_path.read_bytes()
    config = _loads(config_bytes)
    allowed = config.get("allowed_tickers")
    if (config.get("format") != FORMAT or config.get("rule_id") != RULE_ID
            or config.get("rule_authorized") is not True
            or config.get("network_requests") != 0
            or config.get("canonical_build") is not False
            or config.get("automatic_field_approval") is not False
            or config.get("selection_scope") != "OFFLINE_REVIEW_FIELD_ONLY_NOT_CANONICAL"
            or not isinstance(allowed, list) or not allowed
            or any(not isinstance(t, str) or not t.strip() for t in allowed)):
        raise ValueError("OFFLINE_REVIEW_POLICY_GUARD")
    output = _under(root, output)
    if output.exists():
        raise FileExistsError("REFUSE_OUTPUT_OVERWRITE")
    observed = {str(config_path.relative_to(root)).replace("\\", "/"): _hash(config_bytes)}

    def envelope(name, expected):
        path = _under(root, name)
        body = path.read_bytes()
        if _hash(body) != expected:
            raise ValueError("ENVELOPE_HASH_MISMATCH:" + str(name))
        observed[str(path.relative_to(root)).replace("\\", "/")] = expected
        return _loads(body)

    authorization = envelope(config["authorization_path"], config["authorization_sha256"])
    if (authorization.get("rule_id") != RULE_ID
            or authorization.get("status") != "OWNER_DIRECTED_RULE_RECORDED"
            or authorization.get("per_case_owner_approval_required") is not False):
        raise ValueError("RULE_AUTHORIZATION_REQUIRED")
    pins = envelope(config["input_manifest_path"], config["input_manifest_sha256"])["files"]
    package = envelope(config["cases_path"], config["cases_sha256"])
    if package.get("format") != "REVIEWED_THREE_SOURCE_CASES_V1":
        raise ValueError("CASE_PACKAGE_FORMAT")

    def verified_read(name):
        path = _under(root, name)
        relative = str(path.relative_to(root)).replace("\\", "/")
        if relative not in pins:
            raise EvidenceError("INPUT_NOT_PINNED:" + relative)
        body = path.read_bytes()
        digest = _hash(body)
        if digest != pins[relative]:
            raise EvidenceError("INPUT_HASH_MISMATCH:" + relative)
        observed[relative] = digest
        return body

    cases = package["cases"]
    if not isinstance(cases, list) or any(not isinstance(c, dict) for c in cases):
        raise ValueError("CASE_PACKAGE_LIST_REQUIRED")
    ids = [case.get("case_id") for case in cases]
    if (not cases or len(ids) != len(set(ids))
            or any(not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)
            or any(c.get("ticker") not in config["allowed_tickers"] for c in cases)):
        raise ValueError("CASE_IDS_OR_TICKER_SCOPE")
    results = [reconcile_case(case, verified_read) for case in cases]
    selected = sum(r["status"] == "SELECTED_BY_THIRD_SOURCE_CORROBORATION" for r in results)
    queue = [{"case_id": r["case_id"], "comparison_key": r["comparison_key"],
              "status": r["status"], "reasons": r["reasons"],
              "source_ids": [s.get("source_id") for s in r["observations"] if isinstance(s, dict)]
                            if isinstance(r["observations"], list) else [],
              "owner_action_required": False,
              "next_action": "ACQUIRE_OR_REVIEW_QUALIFYING_EVIDENCE_IN_AUTHORIZED_STAGE"}
             for r in results if r["status"] == "UNRESOLVED"]
    summary = {"format": FORMAT, "rule_id": RULE_ID,
               "status": "PASS_ALL_CASES_SELECTED" if selected == len(results) else "PARTIAL_UNRESOLVED_CASES",
               "case_count": len(results), "selected_count": selected, "unresolved_count": len(queue),
               "network_requests": 0, "canonical_fields_applied": 0,
               "price_factors_computed": 0, "automatic_field_approval": False,
               "upstream_reviewed_observations_required": True,
               "source_discovery_or_pdf_semantic_review_automated": False}
    output.mkdir(parents=True, exist_ok=False)

    def write(name, value):
        with (output / name).open("xb") as handle:
            handle.write(_encoded(value))

    write("results.json", results)
    write("unresolved_queue.json", queue)
    write("summary.json", summary)
    write("input_replay.json", {"algorithm": "sha256", "files": observed})
    write("runtime.json", {"module_sha256": _hash(Path(__file__).read_bytes()),
                           "created_at": datetime.now(timezone.utc).isoformat()})
    write("manifest.json", {"algorithm": "sha256", "files": {
        p.name: _hash(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()}})
    return summary
