import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from delta_t1.ingestion.cafef_financial import digest, encoded
from delta_t1.ingestion.financial_documents import consolidated_rows, collect_vintages, verify_inventory
from delta_t1.ingestion.financial_pdf_evidence import validate_pdf
from delta_t1.ingestion.sources.base import AccessControlError, SemanticValidationError


def row(identity="v1", quarter=5):
    return {"id": identity, "Year": 2020, "Quarter": quarter, "Name": "Báo cáo tài chính hợp nhất", "Link": "https://cafefnew.mediacdn.vn/v1.pdf"}


class FinancialDocumentTests(unittest.TestCase):
    def test_separate_vintages_and_scope(self):
        a, b = row(), row("v2")
        separate = dict(row("v3"), Name="Báo cáo riêng")
        self.assertEqual([a, b], consolidated_rows(encoded({"Success": True, "Data": [b, separate, a]}), 2020))

    def test_invalid_envelope_identity_and_duplicate(self):
        for payload in ({"Success": False, "Data": []}, {"Success": True, "Data": [row(), row()]},
                        {"Success": True, "Data": [row("../escape")]}, {"Success": True, "Data": [row(quarter=0)]}):
            with self.assertRaises(SemanticValidationError):
                consolidated_rows(encoded(payload), 2020)

    def test_exact_inventory_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.pdf").write_bytes(b"%PDF-a")
            (root / "manifest.json").write_bytes(encoded({"files": {"a.pdf": digest(b"%PDF-a")}}))
            verify_inventory(root)
            (root / "unexpected.txt").write_text("extra")
            with self.assertRaises(ValueError):
                verify_inventory(root)
            (root / "unexpected.txt").unlink()
            (root / "a.pdf").write_bytes(b"%PDF-b")
            with self.assertRaises(ValueError):
                verify_inventory(root)

    def test_pdf_signature_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.pdf"
            path.write_bytes(b"HTML")
            with self.assertRaises(ValueError):
                validate_pdf(path, digest(b"HTML"))
            path.write_bytes(b"%PDF-a")
            validate_pdf(path, digest(b"%PDF-a"))
            with self.assertRaises(ValueError):
                validate_pdf(path, digest(b"%PDF-b"))

    def test_reused_external_document_must_still_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = root / "source.pdf"
            external.write_bytes(b"%PDF-original")
            run = root / "run"
            run.mkdir()
            body = encoded({"documents": [{"status": "REUSED_VERIFIED_RAW", "path": str(external), "sha256": digest(external.read_bytes())}]})
            (run / "inventory.json").write_bytes(body)
            (run / "manifest.json").write_bytes(encoded({"files": {"inventory.json": digest(body)}}))
            verify_inventory(run)
            external.write_bytes(b"%PDF-replaced")
            with self.assertRaisesRegex(ValueError, "referenced document hash"):
                verify_inventory(run)

    def fixture(self, root):
        detail, gap = root / "detail", root / "gap"
        detail.mkdir(); gap.mkdir()
        (detail / "config.json").write_bytes(encoded({"symbols": ["FPT"]}))
        (gap / "inventory.json").write_bytes(encoded({"gaps": []}))
        (gap / "manifest.json").write_bytes(encoded({"files": {"inventory.json": digest((gap / "inventory.json").read_bytes())}}))
        return detail, gap

    @patch("delta_t1.ingestion.financial_documents.verify_detail", return_value={"streams": []})
    def test_access_stop_no_retry_or_future_inference(self, _):
        class Denied:
            calls = 0
            def get(self, url):
                self.calls += 1
                raise AccessControlError("denied")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            detail, gap = self.fixture(root)
            client = Denied()
            run, result = collect_vintages(detail, gap, root / "out", start_year=2019, end_year=2020, client=client)
            self.assertEqual(client.calls, 1)
            self.assertEqual(result["execution_status"], "HARD_STOP")
            self.assertFalse(result["financial_features_allowed"])
            verify_inventory(run)

    @patch("delta_t1.ingestion.financial_documents.verify_detail", return_value={"streams": []})
    def test_download_cap_and_versions_have_no_availability(self, _):
        class Client:
            def get(self, url):
                return (encoded({"Success": True, "Data": [row(), row("v2")]}), 200) if "FileBCTC" in url else (b"%PDF-test", 200)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            detail, gap = self.fixture(root)
            run, result = collect_vintages(detail, gap, root / "out", start_year=2020, end_year=2020, max_downloads=1, client=Client())
            self.assertEqual([r["status"] for r in result["documents"]], ["DOWNLOADED", "NOT_REQUESTED_CAP"])
            self.assertTrue(all(r["available_at"] is None for r in result["documents"]))
            self.assertEqual(result["execution_status"], "PARTIAL")
            verify_inventory(run)


if __name__ == "__main__":
    unittest.main()
