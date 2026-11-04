"""Consolidate observed field proposals, never sign or apply owner decisions."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from html import escape
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def exact_ratio(value):
    n, d = value["numerator"], value["denominator"]
    if any(type(v) is not int or v <= 0 for v in (n, d)):
        raise ValueError("POSITIVE_EXACT_FRACTION_REQUIRED")
    ratio = Fraction(n, d)
    return {"numerator": ratio.numerator, "denominator": ratio.denominator}


def field_choice(payload, field, value, evidence_ids, conditions=(), dependencies=()):
    if field == "rights_subscription_price":
        if not isinstance(value, str) or not value.isdigit() or int(value) <= 0:
            raise ValueError("EXPLICIT_POSITIVE_VND_SHARE_PRICE_REQUIRED")
        unit = "VND/share"
    elif field == "rights_ratio":
        value = exact_ratio(value)
        unit = "new_shares_per_existing_share"
    else:
        raise ValueError("FIELD_OUTSIDE_PACKET_SCOPE")
    if not evidence_ids:
        raise ValueError("EVIDENCE_REFERENCES_REQUIRED")
    identity = {"payload": payload, "field": field, "value": value, "evidence_ids": sorted(evidence_ids)}
    return {"choice_id": digest(identity), "field": field, "observed_value_proposed": value, "unit": unit,
        "evidence_ids": sorted(evidence_ids), "approval_conditions": list(conditions),
        "requires_approval_of_fields_in_same_case": list(dependencies),
        "owner_decision": None, "review_status": "MANUAL_REVIEW_REQUIRED", "applied": False}


def assemble_case(request, revision=None, primary=None, primary_documents=()):
    """Pure assembly of an already reviewed SDK payload and its linked evidence."""
    r = deepcopy(request)
    if r.get("owner_decision") is not None or r.get("canonical_written") or r.get("signature_created"):
        raise ValueError("UNSIGNED_UNAPPLIED_INPUT_REQUIRED")
    payload, ticker = r["vci_payload_sha256"], r["ticker"]
    sources = r["sources"]
    if not sources or any(not s["ticker_record_supported"] for s in sources):
        raise ValueError("SCOPED_TICKER_RECORD_SOURCE_REQUIRED")
    if len({s["price_vnd"] for s in sources}) != 1 or len({Fraction(s["ratio_exact"]["numerator"], s["ratio_exact"]["denominator"]) for s in sources}) != 1:
        raise ValueError("CONFLICTING_OBSERVED_SOURCE_FIELDS")
    if any(not s["primary_unit_explicit"] for s in sources) and not (ticker == "ASG" and primary):
        raise ValueError("PRIMARY_UNIT_REQUIRED")
    price = str(r["observed_price_vnd"])
    ratio = exact_ratio(sources[0]["ratio_exact"])
    if price != str(sources[0]["price_vnd"]):
        raise ValueError("PRICE_SOURCE_MISMATCH")
    conditions = ["CONFIRM_EXACT_PAYLOAD_COMPONENT_AND_RECORD_DATE", "PIT_AND_HISTORICAL_IDENTITY_REMAIN_SEPARATE"]
    evidences = [s["document_id"] for s in sources]
    group, held = None, False
    ratio_choice = False
    if r["decision_class"] == "EXISTING_RULE_PRICE_SELECTION_PROPOSAL":
        group = "A_EXISTING_RATIO_COMPATIBLE_PRICE"
    elif r["decision_class"] == "CASE_SPECIFIC_EXACT_SOURCE_SELECTION_PROPOSAL":
        group, ratio_choice = "B_CASE_SPECIFIC_EXACT_SOURCE_RATIO", True
    elif r["decision_class"] == "HOLD_LINKED_CHANGE_REVIEW":
        if not revision or revision["vci_payload_sha256"] != payload or revision["original_sdk_row"] != r["original_sdk_row"]:
            raise ValueError("EXACT_PAYLOAD_REVISION_REVIEW_REQUIRED")
        if revision.get("owner_decision") is not None or revision.get("applied_fields") or revision.get("canonical_written"):
            raise ValueError("UNSIGNED_REVISION_REVIEW_REQUIRED")
        edges = revision["edges"]
        if revision["status"] == "CONTEXTUAL_FIELD_PROPOSAL_PENDING_APPROVAL" and edges and all(e["contextual_link_supported"] for e in edges):
            ratio_choice = "rights_ratio" in revision["observed_fields_for_owner_review"]
            group = "B_CASE_SPECIFIC_EXACT_SOURCE_RATIO" if ratio_choice else "A_EXISTING_RATIO_COMPATIBLE_PRICE"
            conditions.append("CONFIRM_CONTEXTUAL_REVISION_SCOPE_WITHOUT_SIGNED_NOTICE_BINDING_CLAIM")
        elif ticker == "KPF" and revision["status"] == "HOLD_LINEAGE_GAP_OR_ANOMALY" and revision["hold_reasons"]:
            group, held = "H_KPF_NOTICE_DATE_ANOMALY", True
        else:
            raise ValueError("UNRESOLVED_OR_CONTRADICTORY_REVISION_STATUS")
    elif r["decision_class"] == "HOLD_RATIO_REQUIRES_ADDITIONAL_PRIMARY_EVIDENCE" and ticker == "DTP":
        if not primary or primary["vci_payload_sha256"] != payload or primary["observed_rights_ratio"] is None:
            raise ValueError("DTP_PRIMARY_RATIO_EVIDENCE_REQUIRED")
        if ratio != {"numerator": 333333, "denominator": 1000000} or primary.get("one_third_inferred") is not False or primary.get("source_ratio_percent_literal") != "33,3333%":
            raise ValueError("DTP_OBSERVED_LITERAL_ONLY_NOT_ONE_THIRD")
        group, ratio_choice = "C_DTP_OBSERVED_LITERAL_RATIO", True
        conditions.append("SELECT_LITERAL_333333_OVER_1000000_NOT_INFERRED_ONE_THIRD")
    elif r["decision_class"] == "PRIMARY_UNIT_DOCUMENT_PROPOSAL" and ticker == "ASG":
        if not primary or primary["vci_payload_sha256"] != payload or primary.get("residual_price_unit_borrowed"):
            raise ValueError("ASG_PRIMARY_UNIT_EVIDENCE_REQUIRED")
        group = "A_EXISTING_RATIO_COMPATIBLE_PRICE"
        conditions.append("CONFIRM_ASG_PROSPECTUS_TO_VSDC_EVENT_CONTEXT_NO_RESIDUAL_UNIT_BORROWING")
    else:
        raise ValueError("UNSUPPORTED_INPUT_DISPOSITION")
    if primary:
        if primary.get("field_approved") or primary.get("canonical_written"):
            raise ValueError("UNAPPROVED_PRIMARY_PROPOSAL_REQUIRED")
        if primary["original_sdk_row"] != r["original_sdk_row"] or primary["record_date"] != r["original_record_date_review_view"]:
            raise ValueError("PRIMARY_TARGET_MISMATCH")
        if exact_ratio(primary["observed_rights_ratio"]) != ratio or str(primary["observed_price_vnd_per_share"]) != price:
            raise ValueError("PRIMARY_FIELDS_CONFLICT")
        if {d["id"] for d in primary_documents} != set(primary["source_documents"]):
            raise ValueError("PRIMARY_DOCUMENT_SET_MISMATCH")
        priced = [d for d in primary_documents if "primary_price_vnd" in d]
        if not priced or any(str(d["primary_price_vnd"]) != price or d.get("primary_price_unit_literal") not in {"đồng/cổ phiếu", "đồng/cổ phần"} for d in priced):
            raise ValueError("PRIMARY_PDF_PRICE_UNIT_MISMATCH")
        evidences += [d["id"] for d in primary_documents]
    if ratio_choice:
        conditions.append("CASE_SPECIFIC_SOURCE_RATIO_SELECTION_NO_PROVIDER_ROUNDING_INFERENCE_OR_GLOBAL_TOLERANCE")
    price_choice = field_choice(payload, "rights_subscription_price", price, evidences, conditions,
                                ["rights_ratio"] if ratio_choice else [])
    fields = [price_choice]
    if ratio_choice:
        fields.append(field_choice(payload, "rights_ratio", ratio, evidences, conditions))
    if held:
        price_choice["review_status"] = "HOLD_REQUIRES_MORE_EVIDENCE"
    return {"case_id": payload, "ticker": ticker, "record_date_review_view": r["original_record_date_review_view"],
        "group": group, "vci_payload_sha256": payload, "original_sdk_row": r["original_sdk_row"],
        "sdk_ratio_preserved": r["original_sdk_row"].get("ratio"), "source_ratio_exact_for_context": ratio,
        "status": "HOLD_REQUIRES_MORE_EVIDENCE" if held else "PROPOSAL_PENDING_OWNER_APPROVAL",
        "proposed_fields": [] if held else fields, "held_fields": fields if held else [],
        "source_evidence": sources, "primary_document_evidence": deepcopy(list(primary_documents)),
        "prior_decision_class": r["decision_class"],
        "primary_review": deepcopy(primary), "revision_review": deepcopy(revision),
        "precision_diagnostics_for_context_only": r.get("precision_diagnostics", []),
        "owner_decision": None, "signature_created": False, "canonical_written": False,
        "entity_scope": "VCI_SDK_PAYLOAD_NOT_CANONICAL_ECONOMIC_EVENT_ID",
        "pit_status": "NOT_PROMOTED", "historical_identity": "UNVERIFIED",
        "revision_flags_preserved": True, "research_readiness_promoted": False}


def owner_template(cases, packet_id):
    return {"artifact_type": "unsigned-owner-field-review-template-v1", "packet_content_id": packet_id,
        "importable_as_production_decisions": False, "owner_name": None, "owner_decided_at": None,
        "signature": None, "applied": False,
        "allowed_proposal_responses": ["SELECT_OBSERVED_VALUE", "REJECT_PROPOSAL", "KEEP_PENDING"],
        "cases": [{"case_id": c["case_id"], "ticker": c["ticker"], "record_date": c["record_date_review_view"],
            "owner_decision": None, "field_decisions": [{"choice_id": f["choice_id"], "field": f["field"],
                "observed_value_proposed": f["observed_value_proposed"], "owner_decision": None} for f in c["proposed_fields"]],
            "hold_must_remain": bool(c["held_fields"])} for c in cases]}


def render_html(cases, summary, packet_id):
    def value(v):
        return f"{v['numerator']}/{v['denominator']}" if isinstance(v, dict) else str(v)
    groups = {"A_EXISTING_RATIO_COMPATIBLE_PRICE": "A · Giá, ratio theo rule hiện có",
        "B_CASE_SPECIFIC_EXACT_SOURCE_RATIO": "B · Giá + exact source ratio theo từng case",
        "C_DTP_OBSERVED_LITERAL_RATIO": "C · DTP: literal 33,3333%",
        "H_KPF_NOTICE_DATE_ANOMALY": "HOLD · KPF: ngày văn bản mâu thuẫn"}
    rows = []
    for c in cases:
        fields = c["proposed_fields"] or c["held_fields"]
        choices = "<br>".join(escape(f["field"] + " = " + value(f["observed_value_proposed"]) + " " + f["unit"]) for f in fields)
        conditions = sorted({condition for f in fields for condition in f["approval_conditions"]})
        detail = {"case_id": c["case_id"], "field_choices": fields, "conditions": conditions,
            "source_evidence": c["source_evidence"], "primary_document_evidence": c["primary_document_evidence"],
            "revision_review": c["revision_review"]}
        rows.append(f'<tr class="{"held" if c["held_fields"] else "proposal"}"><td>{escape(c["ticker"])}</td>'
            f'<td>{escape(c["record_date_review_view"])}</td><td>{escape(groups[c["group"]])}</td>'
            f'<td>{escape(str(c["sdk_ratio_preserved"]))}</td><td>{escape(value(c["source_ratio_exact_for_context"]))}</td>'
            f'<td>{choices}</td><td><details><summary>Nguồn, điều kiện và choice IDs</summary><pre>{escape(json.dumps(detail,ensure_ascii=False,indent=2))}</pre></details></td></tr>')
    return ('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>DELTA — Gói lựa chọn corporate actions chờ duyệt</title><style>'
        'body{font:15px/1.55 system-ui,sans-serif;color:#172b3a;background:#f5f7fa;margin:0;padding:28px}'
        'main{max-width:1500px;margin:auto}h1{font-size:27px;margin-bottom:8px}.note{background:#fff;border-left:5px solid #b47717;padding:18px}'
        'table{border-collapse:collapse;width:100%;background:#fff;margin:24px 0;font-size:14px}th,td{padding:12px;border:1px solid #d8e0e7;text-align:left;vertical-align:top}'
        'th{background:#18384c;color:#fff;position:sticky;top:0}.held{background:#fff1e8}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:520px;overflow:auto;font-size:12px}'
        'summary{cursor:pointer}code{overflow-wrap:anywhere}.small{font-size:13px;color:#42576a}</style><main>'
        '<h1>DELTA — Lựa chọn field chờ owner duyệt</h1>'
        f'<p>{summary["payload_count"]} SDK payloads / {summary["ticker_count"]} mã; '
        f'{summary["proposed_case_count"]} case với {summary["proposed_field_count"]} field requests; 1 case KPF giữ HOLD.</p>'
        '<div class="note"><strong>MANUAL_REVIEW_REQUIRED · Chưa có quyết định được duyệt hoặc áp dụng.</strong>'
        '<p>Phạm vi chỉ lựa chọn các giá trị quan sát được cho từng payload. Mỗi ratio là số cổ phiếu mới trên một cổ phiếu cũ; '
        'fraction là exact value, không phải tỷ lệ đã được SDK xác nhận. Giá thuộc primary offer và có unit VND/share.</p>'
        '<p>Với nhóm B/C, lựa chọn giá phụ thuộc việc owner duyệt exact source ratio của cùng case. DTP giữ 333333/1000000, không suy 1/3. '
        'CIA thuộc rule so sánh 10 chữ số hiện có, không coi SDK bằng exact fraction. Giữ KPF HOLD do notice44 có hai ngày07/01 và08/01/2021.</p>'
        '<p>Không xác minh publication PIT, historical identity, signed notice binding, terminal execution, price-basis policy hoặc research readiness. '
        'Không cộng/tái đầu tư cổ tức tiền mặt, không tính giá điều chỉnh hoặc backtest ở bước này.</p></div>'
        f'<p class="small">Packet content ID: <code>{packet_id}</code>. Template JSON để ghi ý kiến owner; không import như signed production decisions.</p>'
        '<table><thead><tr><th>Mã</th><th>ĐKCC (review view)</th><th>Nhóm</th><th>SDK ratio giữ nguyên</th><th>Source ratio (context)</th><th>Field đề xuất / giữ HOLD</th><th>Bằng chứng</th></tr></thead><tbody>'
        + ''.join(rows) + '</tbody></table><p class="small">Mọi quyết định owner, chữ ký và timestamp đều để trống. Raw và artifact cũ giữ nguyên.</p></main></html>')
