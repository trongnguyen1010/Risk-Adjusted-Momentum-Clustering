"""Kiểm tra approval scope, provenance và chặn dữ liệu trước publication instant."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.publisher_timestamp_overlay import eligible_fields, run


class PublisherTimestampOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp_parent = (ROOT / "tmp").resolve()
        self.temp_parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.temp_parent, prefix="ca-timestamp-overlay-test-")
        self.addCleanup(self.cleanup_temp)
        self.root = Path(self.temp.name)
        self.time = "2024-01-16T14:51:00+07:00"
        self.title = "SYNTHETIC ORS rights notice"
        self.url = "https://public.example/article/1"
        self.pdf_url = "https://public.example/notice.pdf"
        self.mapping = [{"row_id": "1.ticker", "event_id": "1", "exact_ticker": "ORS", "field": "ticker", "field_scope": "ORIGINAL_TERMS", "value": "ORS"},
                        {"row_id": "1.ratio", "event_id": "1", "exact_ticker": "ORS", "field": "ratio", "field_scope": "ORIGINAL_TERMS", "value": "2:1"}]
        old = [{**{k: v for k, v in x.items() if k != "value"}, "review_value": x["value"]} for x in self.mapping]
        old += [{"row_id": "2.ticker", "event_id": "2", "field": "ticker", "field_scope": "ORIGINAL_TERMS", "review_value": "OTHER"}]
        self.article = {"@type": "NewsArticle", "headline": self.title, "publisher": {"name": "FireAnt"}, "datePublished": "2024-01-16T07:51:00Z"}
        self.post = {"postID": 1, "title": self.title, "date": self.time, "taggedSymbols": [{"symbol": "ORS"}], "files": [{"fileContentUrl": self.pdf_url}]}
        self.policy = {"policy_id": "SYNTHETIC-ONLY", "status": "OWNER_APPROVED", "activated": True,
                       "purpose": "PRODUCT_M3_PILOT", "DATE_ONLY_enabled": False, "canonical_build": False,
                       "strict_research_gate_opened": False, "event_id": "1", "exact_ticker": "ORS",
                       "timestamp": self.time, "field_count": 2, "baseline_rows": 3, "publisher": "FireAnt",
                       "allow_missing_modified_only_for_pinned_mappings": True,
                       "owner_approval_ref": self.write_json("approval.json", {"owner_message": "hãy thực hiện", "event_id": "1", "timestamp": self.time, "field_count": 2, "purpose": "PRODUCT_M3_PILOT"}),
                       "field_mappings_ref": self.write_json("mapping.json", self.mapping),
                       "prior_proposed_mappings_ref": self.write_json("prior.json", self.mapping),
                       "baseline_packets": [self.write_json("packet.json", {"rows": old})],
                       "evidence": {"article_url": self.url, "post_id": 1, "headline": self.title,
                                    "attachment_url": self.pdf_url,
                                    "original_HOSE_PDF_ref": self.write("original.pdf", b"%PDF SYNTHETIC ONLY")}}
        self.refresh_html()
        self.refresh_pdf()

    def cleanup_temp(self):
        if not Path(self.temp.name).resolve().is_relative_to(self.temp_parent):
            raise ValueError("TEST_CLEANUP_OUTSIDE_WORKSPACE_TMP")
        self.temp.cleanup()

    def write(self, name, body):
        (self.root / name).write_bytes(body)
        return {"path": name, "sha256": hashlib.sha256(body).hexdigest()}

    def write_json(self, name, value):
        return self.write(name, json.dumps(value, ensure_ascii=False).encode())

    def receipt(self, name, raw, url):
        return self.write_json(name, {"url": url, "method": "GET", "status": 200, "challenge": False,
                                     "raw_path": raw["path"], "sha256": raw["sha256"], "bytes": (self.root / raw["path"]).stat().st_size})

    def refresh_html(self, anchor=True):
        html = '<script id="__NEXT_DATA__">' + json.dumps({"props": {"pageProps": {"initialPost": self.post}}}) + '</script>'
        html += '<script type="application/ld+json">' + json.dumps(self.article) + '</script>'
        if anchor:
            html += '<a href="' + self.pdf_url + '">PDF</a>'
        raw = self.write("article.html", html.encode())
        self.policy["evidence"].update(article_ref=raw, article_receipt_ref=self.receipt("article.receipt.json", raw, self.url))

    def refresh_pdf(self, body=b"%PDF SYNTHETIC ONLY"):
        raw = self.write("attachment.pdf", body)
        self.policy["evidence"].update(attachment_ref=raw, attachment_receipt_ref=self.receipt("pdf.receipt.json", raw, self.pdf_url))

    def execute(self):
        self.write_json("policy.json", self.policy)
        return run("policy.json", "output", self.root)

    def test_exact_instant_before_at_after_and_other_row_held(self):
        summary = self.execute()
        self.assertEqual((2, 1), (summary["admitted_rows"], summary["held_rows"]))
        for clock, expected in [("2024-01-16T14:50:59+07:00", 0), (self.time, 2), ("2024-01-16T07:51:00Z", 2), ("2024-01-16T14:51:01+07:00", 2)]:
            self.assertEqual(expected, len(eligible_fields("output", clock, root=self.root)))
        rows = eligible_fields("output", self.time, root=self.root)
        self.assertEqual({"1.ticker", "1.ratio"}, {x["row_id"] for x in rows})
        self.assertTrue(all(x["usable_from_date"] is None and not x["strict_research_eligible"] and not x["first_exchange_publication_proved"] for x in rows))

    def test_inactive_date_only_and_research_or_canonical_policy_rejected(self):
        cases = [("activated", False), ("status", "MANUAL_REVIEW_REQUIRED"), ("purpose", "STRICT_RESEARCH"), ("DATE_ONLY_enabled", True), ("canonical_build", True), ("strict_research_gate_opened", True)]
        for key, value in cases:
            with self.subTest(key=key):
                old = self.policy[key]
                self.policy[key] = value
                with self.assertRaises(ValueError):
                    self.execute()
                self.policy[key] = old
                self.assertFalse((self.root / "output").exists())

    def test_approval_scope_mismatch_rejected(self):
        approval = {"owner_message": "hãy thực hiện", "event_id": "OTHER", "timestamp": self.time, "field_count": 2, "purpose": "PRODUCT_M3_PILOT"}
        self.policy["owner_approval_ref"] = self.write_json("approval.json", approval)
        with self.assertRaisesRegex(ValueError, "OWNER_APPROVAL_SCOPE"):
            self.execute()

    def test_changed_value_scope_or_event_even_with_updated_mapping_hash_rejected(self):
        for key, value in [("value", "1:1"), ("field_scope", "REVISION_TERMS"), ("event_id", "2"), ("exact_ticker", "ORS123")]:
            with self.subTest(key=key):
                rows = copy.deepcopy(self.mapping)
                rows[1][key] = value
                self.policy["field_mappings_ref"] = self.write_json("mapping.json", rows)
                with self.assertRaises(ValueError):
                    self.execute()

    def test_extra_or_duplicate_mappings_rejected(self):
        for rows in [self.mapping + [self.mapping[0]], [self.mapping[0], self.mapping[0]]]:
            with self.subTest(rows=rows):
                self.policy["field_mappings_ref"] = self.write_json("mapping.json", rows)
                with self.assertRaisesRegex(ValueError, "MAPPING_COUNT_OR_DUPLICATE"):
                    self.execute()

    def test_timestamp_disagreement_and_missing_offset_rejected(self):
        for value in ["2024-01-16T14:51:00Z", "2024-01-16T14:51:00", "2024-01-16"]:
            with self.subTest(value=value):
                self.post["date"] = value
                self.refresh_html()
                with self.assertRaises(ValueError):
                    self.execute()

    def test_modified_later_null_and_missing_without_scoped_acceptance_rejected(self):
        for value in ["2024-01-17T07:51:00Z", None]:
            with self.subTest(value=value):
                self.article["dateModified"] = value
                self.refresh_html()
                with self.assertRaises(ValueError):
                    self.execute()
        del self.article["dateModified"]
        self.refresh_html()
        self.policy["allow_missing_modified_only_for_pinned_mappings"] = False
        with self.assertRaisesRegex(ValueError, "MISSING_MODIFIED"):
            self.execute()

    def test_modified_equal_accepted_without_imputing_absent_value(self):
        self.article["dateModified"] = "2024-01-16T07:51:00Z"
        self.refresh_html()
        self.execute()
        self.assertEqual(self.article["dateModified"], eligible_fields("output", self.time, root=self.root)[0]["source_dateModified"])

    def test_access_denial_or_receipt_url_mismatch_rejected(self):
        base = json.loads((self.root / "article.receipt.json").read_bytes())
        for key, value in [("status", 403), ("challenge", True), ("url", "https://other.example"), ("bytes", 0), ("method", "POST")]:
            with self.subTest(key=key):
                r = {**base, key: value}
                self.policy["evidence"]["article_receipt_ref"] = self.write_json("article.receipt.json", r)
                with self.assertRaisesRegex(ValueError, "HTTP_RECEIPT_BINDING"):
                    self.execute()

    def test_missing_direct_anchor_or_different_pdf_rejected(self):
        self.refresh_html(anchor=False)
        with self.assertRaisesRegex(ValueError, "DIRECT_ATTACHMENT"):
            self.execute()
        self.refresh_html()
        self.refresh_pdf(b"%PDF DIFFERENT NOTICE")
        with self.assertRaisesRegex(ValueError, "ORIGINAL_PDF"):
            self.execute()

    def test_hash_tampering_and_path_escape_rejected(self):
        (self.root / "article.html").write_text("tampered")
        with self.assertRaisesRegex(ValueError, "INPUT_HASH"):
            self.execute()
        self.policy["evidence"]["article_ref"]["path"] = "../outside.html"
        with self.assertRaisesRegex(ValueError, "PATH_OUTSIDE_ROOT"):
            self.execute()

    def test_existing_artifact_cannot_be_overwritten(self):
        self.execute()
        original = (self.root / "output/manifest.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_OUTPUT"):
            self.execute()
        self.assertEqual(original, (self.root / "output/manifest.json").read_bytes())

    def test_consumer_rejects_other_purposes_and_naive_clock(self):
        self.execute()
        for purpose in ["STRICT_RESEARCH", "CANONICAL"]:
            with self.assertRaisesRegex(ValueError, "NOT_APPROVED"):
                eligible_fields("output", self.time, root=self.root, purpose=purpose)
        for clock in ["2024-01-16", "2024-01-16T14:51:00"]:
            with self.assertRaises(ValueError):
                eligible_fields("output", clock, root=self.root)

    def test_consumer_rejects_tampered_rows_even_with_rehashed_manifest(self):
        self.execute()
        target = self.root / "output/field_availability.jsonl"
        rows = [json.loads(x) for x in target.read_text().splitlines()]
        rows[-1]["available_at"] = self.time
        target.write_text("\n".join(json.dumps(x) for x in rows))
        manifest = json.loads((self.root / "output/manifest.json").read_bytes())
        manifest["files"][target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
        (self.root / "output/manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "CONTENT_DIFFERS"):
            eligible_fields("output", self.time, root=self.root)

    def test_offline_execution_and_read_do_not_open_network(self):
        with patch("socket.socket", side_effect=AssertionError("NETWORK_FORBIDDEN")):
            self.execute()
            self.assertEqual(2, len(eligible_fields("output", self.time, root=self.root)))


if __name__ == "__main__":
    unittest.main()
