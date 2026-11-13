from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions.third_source_reconcile import (
    EvidenceError, FORMAT, RULE_ID, reconcile_case, run,
)

ROOT = Path(__file__).resolve().parents[4]


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fixture(values=(10, 20, 20)):
    key = dict(exact_security="AAA", event_identity="ISSUE_2024", field="price",
               semantic_scope="ORIGINAL_SUBSCRIPTION", unit="VND_PER_SHARE",
               effective_period="2024-01", revision_state="REVIEWED_OPERATIONAL")
    review = {"comparison_key": key, "origin": {"qualified": True},
              "revision": "Reviewed matched effective field; dissent retained.",
              "selected_value": 999999}  # Never trust an upstream selected value.
    blobs, sources = {}, []
    for role, value in zip("ABC", values):
        raw_path, receipt_path = f"raw/{role}.pdf", f"raw/{role}.receipt.json"
        body = ("synthetic public document " + role).encode()
        sha = digest(body)
        source = dict(role=role, source_id=role, value=value,
                      comparison_key=deepcopy(key), superseded=False,
                      document_id="DOC_" + role, origin_group_id="ORIGIN_" + role,
                      source_url="https://example.test/" + role,
                      artifact_path=raw_path, sha256=sha, receipt_path=receipt_path,
                      evidence_type="HTTP_RESPONSE_ENTITY_BODY",
                      review_ref={"path": "review.json", "pointer": "/source_" + role})
        review["source_" + role] = {
            k: source[k] for k in ("source_id", "source_url", "artifact_path", "sha256", "receipt_path", "evidence_type")}
        review["source_" + role]["observed_value"] = value
        blobs[raw_path] = body
        blobs[receipt_path] = encoded(dict(status=200, body_bytes=len(body),
            source_url=source["source_url"], sha256=sha, raw_path=raw_path, route_stop=False))
        sources.append(source)
    blobs["review.json"] = encoded(review)
    case = dict(case_id="case1", ticker="AAA", comparison_key=key, observations=sources,
                comparison_review_ref={"path": "review.json", "pointer": "/comparison_key"},
                origin_review_ref={"path": "review.json", "pointer": "/origin"},
                revision_review_ref={"path": "review.json", "pointer": "/revision"},
                known_superseding_revision=False, additional_known_source_ids=[],
                discovery_order=["A", "B", "C"], value_locators={"A": "p1", "B": "p2", "C": "p3"})
    return case, blobs


def alter_json(blobs, path, change):
    value = json.loads(blobs[path])
    change(value)
    blobs[path] = encoded(value)


class ThirdSourceTests(unittest.TestCase):
    def invoke(self, case, blobs):
        def read(name):
            if name not in blobs:
                raise EvidenceError("INPUT_NOT_PINNED:" + name)
            return blobs[name]
        return reconcile_case(case, read)

    def hold(self, result, reason):
        self.assertEqual("UNRESOLVED", result["status"])
        self.assertIsNone(result["selected_value"])
        self.assertFalse(result["owner_action_required"])
        self.assertTrue(any(reason in r for r in result["reasons"]), result)

    def test_third_matches_first_selects_first_and_keeps_second_dissent(self):
        case, blobs = fixture((10, 20, 10))
        result = self.invoke(case, blobs)
        self.assertEqual(10, result["selected_value"])
        self.assertEqual(["A", "C"], result["supporting_source_ids"])
        self.assertEqual(["B"], result["dissenting_source_ids"])

    def test_third_matches_second_recomputes_not_upstream_selection(self):
        case, blobs = fixture()
        result = self.invoke(case, blobs)
        self.assertEqual(20, result["selected_value"])
        self.assertEqual(["B", "C"], result["supporting_source_ids"])
        self.assertEqual(["A"], result["dissenting_source_ids"])
        self.assertEqual(3, len(result["observations"]))
        self.assertFalse(result["canonical_applied"])
        self.assertFalse(result["price_factor_computed"])
        self.assertEqual("NOT_PROMOTED", result["pit_status"])

    def test_third_disagrees_with_both_no_fourth_search_or_average(self):
        self.hold(self.invoke(*fixture((10, 20, 30))), "DISAGREES_WITH_BOTH")

    def test_missing_third_is_queueable_hold(self):
        case, blobs = fixture(); case["observations"].pop()
        self.hold(self.invoke(case, blobs), "THIRD_SOURCE_REQUIRED")

    def test_malformed_observations_hold_instead_of_becoming_votes(self):
        for observations in [{"A": 1}, ["A", "B", "C"]]:
            case, blobs = fixture(); case["observations"] = observations
            self.hold(self.invoke(case, blobs), "OBSERVATION_LIST_REQUIRED")

    def test_known_extra_counter_evidence_cannot_be_ignored(self):
        case, blobs = fixture(); case["additional_known_source_ids"] = ["D"]
        self.hold(self.invoke(case, blobs), "ADDITIONAL_KNOWN_EVIDENCE")

    def test_cannot_cherry_pick_order_or_fourth_source(self):
        case, blobs = fixture(); case["observations"].reverse()
        self.hold(self.invoke(case, blobs), "ORDERED_A_B_C")
        case, blobs = fixture(); case["observations"].append(deepcopy(case["observations"][2]))
        self.hold(self.invoke(case, blobs), "ORDERED_A_B_C")

    def test_reposted_document_id_and_shared_origin_are_not_third(self):
        for field in ["document_id", "origin_group_id"]:
            with self.subTest(field=field):
                case, blobs = fixture()
                case["observations"][2][field] = case["observations"][1][field]
                self.hold(self.invoke(case, blobs), "COPY_OR_SHARED_ORIGIN")

    def test_byte_identical_third_does_not_count_even_other_document_id(self):
        case, blobs = fixture(); c = case["observations"][2]
        body = blobs["raw/B.pdf"]; blobs[c["artifact_path"]] = body
        c["sha256"] = digest(body)
        alter_json(blobs, c["receipt_path"], lambda r: r.update(sha256=c["sha256"], body_bytes=len(body)))
        alter_json(blobs, "review.json", lambda r: r["source_C"].update(sha256=c["sha256"]))
        self.hold(self.invoke(case, blobs), "COPY_OR_SHARED_ORIGIN")

    def test_unqualified_origin_and_superseding_revision_hold(self):
        case, blobs = fixture()
        alter_json(blobs, "review.json", lambda r: r["origin"].update(qualified=False))
        self.hold(self.invoke(case, blobs), "ORIGIN_UNQUALIFIED")
        case, blobs = fixture(); case["known_superseding_revision"] = True
        self.hold(self.invoke(case, blobs), "SUPERSEDING_REVISION")

    def test_field_scope_unit_security_and_effective_mismatch_hold(self):
        for field in ["field", "unit", "exact_security", "semantic_scope", "effective_period", "revision_state"]:
            with self.subTest(field=field):
                case, blobs = fixture(); case["observations"][2]["comparison_key"][field] = "DIFFERENT"
                self.hold(self.invoke(case, blobs), "COMPARISON_KEY_MISMATCH")

    def test_missing_key_or_comparability_review_cannot_pass(self):
        case, blobs = fixture(); del case["comparison_key"]["unit"]
        self.hold(self.invoke(case, blobs), "COMPLETE_COMPARISON_KEY")
        case, blobs = fixture()
        alter_json(blobs, "review.json", lambda r: r["comparison_key"].update(field="other"))
        self.hold(self.invoke(case, blobs), "COMPARABILITY_REVIEW_MISMATCH")

    def test_superseded_observation_cannot_vote(self):
        case, blobs = fixture(); case["observations"][0]["superseded"] = True
        self.hold(self.invoke(case, blobs), "UNREVIEWED_OR_SUPERSEDED")

    def test_body_and_receipt_tampering_hold(self):
        case, blobs = fixture(); blobs["raw/C.pdf"] += b"tamper"
        self.hold(self.invoke(case, blobs), "SOURCE_BODY_HASH")
        case, blobs = fixture()
        alter_json(blobs, "raw/C.receipt.json", lambda r: r.update(sha256="0"*64))
        self.hold(self.invoke(case, blobs), "RECEIPT_BODY_HASH")

    def test_failed_http_challenge_empty_and_wrong_url_hold(self):
        for update, reason in [({"status": 400}, "HTTP200"), ({"route_stop": True}, "ACCESS_CONTROL"),
                               ({"source_url": "https://example.test/wrong"}, "URL_MISMATCH")]:
            case, blobs = fixture()
            alter_json(blobs, "raw/C.receipt.json", lambda r: r.update(update))
            self.hold(self.invoke(case, blobs), reason)
        case, blobs = fixture(); blobs["raw/C.pdf"] = b""
        self.hold(self.invoke(case, blobs), "HASH_OR_EMPTY")

    def test_review_binding_and_observed_value_required(self):
        case, blobs = fixture(); case["observations"][2]["value"] = 10
        self.hold(self.invoke(case, blobs), "REVIEW_VALUE_MISMATCH")
        case, blobs = fixture()
        alter_json(blobs, "review.json", lambda r: r["source_C"].update(source_id="another"))
        self.hold(self.invoke(case, blobs), "REVIEW_BINDING_MISMATCH")

    def test_unpinned_locator_holds(self):
        case, blobs = fixture(); del blobs["review.json"]
        self.hold(self.invoke(case, blobs), "INPUT_NOT_PINNED")

    def test_dom_receipt_allowed_but_cannot_be_relabelled_http(self):
        case, blobs = fixture(); case["observations"][1]["evidence_type"] = "REUSED_RENDERED_DOM_TEXT"
        alter_json(blobs, "review.json", lambda r: r["source_B"].update(evidence_type="REUSED_RENDERED_DOM_TEXT"))
        receipt = json.loads(blobs["raw/B.receipt.json"])
        receipt.pop("status"); receipt.pop("raw_path")
        receipt.update(evidence_type="RENDERED_DOM_TEXT", http_status=None, http_receipt_available=False)
        blobs["raw/B.receipt.json"] = encoded(receipt)
        self.assertEqual(20, self.invoke(case, blobs)["selected_value"])
        for field, value in [("http_status", 200), ("status", 200), ("raw_cache", True), ("raw_path", "raw/B.pdf")]:
            with self.subTest(field=field):
                blobs["raw/B.receipt.json"] = encoded({**receipt, field: value})
                self.hold(self.invoke(case, blobs), "DOM_RECEIPT")

    def test_exact_values_support_objects_and_never_bool_number_coercion(self):
        result = self.invoke(*fixture((True, 1, 1)))
        self.assertEqual(["B", "C"], result["supporting_source_ids"])
        self.hold(self.invoke(*fixture((1, 1.0, 1))), "INITIAL_PAIR_IS_NOT")
        self.hold(self.invoke(*fixture((10.00000000001, 20, 10))), "DISAGREES_WITH_BOTH")
        self.assertEqual({"rights": 2}, self.invoke(*fixture(({"rights": 1}, {"rights": 2}, {"rights": 2})))["selected_value"])

    def test_missing_nonfinite_and_text_numeric_are_not_inferred(self):
        self.hold(self.invoke(*fixture((10, 20, None))), "VALUE_MISSING")
        self.hold(self.invoke(*fixture((10, 20, float("nan")))), "NON_FINITE")
        self.hold(self.invoke(*fixture((10, 20, "20"))), "DISAGREES_WITH_BOTH")

    def test_input_objects_unchanged_and_no_publication_claim(self):
        case, blobs = fixture(); before = deepcopy((case, blobs))
        result = self.invoke(case, blobs)
        self.assertEqual(before, (case, blobs))
        self.assertNotIn("available_at", result)


class RunnerTests(unittest.TestCase):
    def prepare(self, root, *, partial=False):
        case, blobs = fixture()
        cases = [case]
        if partial:
            missing = deepcopy(case); missing["case_id"] = "missing"; missing["observations"].pop()
            cases.append(missing)
        for name, data in blobs.items():
            p = root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        pins = {name: digest(data) for name, data in blobs.items()}
        (root/"pins.json").write_bytes(encoded({"files": pins}))
        (root/"cases.json").write_bytes(encoded({"format": "REVIEWED_THREE_SOURCE_CASES_V1", "cases": cases}))
        (root/"authorization.json").write_bytes(encoded(dict(rule_id=RULE_ID, status="OWNER_DIRECTED_RULE_RECORDED", per_case_owner_approval_required=False)))
        config = dict(format=FORMAT, rule_id=RULE_ID, rule_authorized=True, network_requests=0,
                      canonical_build=False, automatic_field_approval=False,
                      selection_scope="OFFLINE_REVIEW_FIELD_ONLY_NOT_CANONICAL", allowed_tickers=["AAA"],
                      authorization_path="authorization.json", authorization_sha256=digest((root/"authorization.json").read_bytes()),
                      input_manifest_path="pins.json", input_manifest_sha256=digest((root/"pins.json").read_bytes()),
                      cases_path="cases.json", cases_sha256=digest((root/"cases.json").read_bytes()))
        (root/"config.json").write_bytes(encoded(config))

    def temp(self):
        return tempfile.TemporaryDirectory(dir=ROOT/"tmp")

    def test_local_run_no_network_preserves_dissent_and_seals_output(self):
        with self.temp() as t:
            root = Path(t); self.prepare(root)
            with patch("socket.socket", side_effect=AssertionError("NETWORK_FORBIDDEN")):
                summary = run("config.json", "out", root)
            self.assertEqual(1, summary["selected_count"])
            self.assertEqual([], json.loads((root/"out/unresolved_queue.json").read_bytes()))
            result = json.loads((root/"out/results.json").read_bytes())[0]
            self.assertEqual(["A"], result["dissenting_source_ids"])
            manifest = json.loads((root/"out/manifest.json").read_bytes())
            for name, h in manifest["files"].items():
                self.assertEqual(h, digest((root/"out"/name).read_bytes()))
            with self.assertRaises(FileExistsError):run("config.json", "out", root)

    def test_one_missing_third_does_not_block_other_case(self):
        with self.temp() as t:
            root = Path(t); self.prepare(root, partial=True)
            result = run("config.json", "out", root)
            self.assertEqual((1, 1), (result["selected_count"], result["unresolved_count"]))
            queue = json.loads((root/"out/unresolved_queue.json").read_bytes())
            self.assertFalse(queue[0]["owner_action_required"])

    def test_cli_partial_exit_three_and_overwrite_exit_two(self):
        with self.temp() as t:
            root = Path(t); self.prepare(root, partial=True)
            command = [sys.executable, str(ROOT/"scripts/corporate_actions/reconcile_third_source_v1.py"),
                       "--root", str(root), "--config", "config.json", "--output", "out"]
            first = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(3, first.returncode, first.stderr)
            self.assertEqual(1, json.loads(first.stdout)["unresolved_count"])
            second = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(2, second.returncode)
            self.assertIn("REFUSE_OUTPUT_OVERWRITE", second.stderr)

    def test_raw_tampering_becomes_unresolved_not_false_selection(self):
        with self.temp() as t:
            root = Path(t); self.prepare(root); (root/"raw/C.pdf").write_bytes(b"tamper")
            self.assertEqual(1, run("config.json", "out", root)["unresolved_count"])

    def test_envelope_tampering_refuses_before_output_creation(self):
        for name in ["pins.json", "cases.json", "authorization.json"]:
            with self.subTest(name=name), self.temp() as t:
                root = Path(t); self.prepare(root); (root/name).write_bytes(b"{}")
                with self.assertRaisesRegex(ValueError, "ENVELOPE_HASH"):
                    run("config.json", "out", root)
                self.assertFalse((root/"out").exists())

    def test_unapproved_rule_record_refuses_even_if_config_boolean_true(self):
        with self.temp() as t:
            root = Path(t); self.prepare(root)
            (root/"authorization.json").write_bytes(encoded(dict(rule_id=RULE_ID, status="PROPOSED", per_case_owner_approval_required=False)))
            config = json.loads((root/"config.json").read_bytes())
            config["authorization_sha256"] = digest((root/"authorization.json").read_bytes())
            (root/"config.json").write_bytes(encoded(config))
            with self.assertRaisesRegex(ValueError, "RULE_AUTHORIZATION_REQUIRED"):
                run("config.json", "out", root)
            self.assertFalse((root/"out").exists())

    def test_invalid_json_numbers_and_duplicate_keys_refuse_before_output(self):
        for kind in ["nan", "duplicate"]:
            with self.subTest(kind=kind), self.temp() as t:
                root = Path(t); self.prepare(root)
                body = (root/"cases.json").read_bytes()
                if kind == "nan":
                    body = body.replace(b'"value": 20', b'"value": NaN', 1)
                else:
                    body = b'{"format":"OTHER",' + body[1:]
                (root/"cases.json").write_bytes(body)
                config = json.loads((root/"config.json").read_bytes())
                config["cases_sha256"] = digest(body)
                (root/"config.json").write_bytes(encoded(config))
                with self.assertRaisesRegex(ValueError, "NON_FINITE_JSON|DUPLICATE_JSON"):
                    run("config.json", "out", root)
                self.assertFalse((root/"out").exists())

    def test_runtime_guards_and_output_escape_refuse(self):
        for field, value in [("canonical_build", True), ("automatic_field_approval", True),
                             ("network_requests", 1), ("rule_authorized", False), ("allowed_tickers", "AAA")]:
            with self.subTest(field=field), self.temp() as t:
                root = Path(t); self.prepare(root)
                config = json.loads((root/"config.json").read_bytes()); config[field] = value
                (root/"config.json").write_bytes(encoded(config))
                with self.assertRaisesRegex(ValueError, "POLICY_GUARD"):
                    run("config.json", "out", root)
        with self.temp() as t:
            root = Path(t); self.prepare(root)
            with self.assertRaisesRegex(ValueError, "PATH_OUTSIDE"):
                run("config.json", "../escape", root)


if __name__ == "__main__":
    unittest.main()
