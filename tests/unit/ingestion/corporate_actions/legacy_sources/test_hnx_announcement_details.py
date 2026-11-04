import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.hnx_announcement_details import acquire_details, load_selection
from delta_t1.ingestion.hnx_announcement_discovery import DETAIL_URL
from delta_t1.ingestion.corporate_action_sources import SourceLimitation


def seal(root):
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"}
    (root / "manifest.json").write_text(json.dumps({"artifact_type": "hnx-disclosure-discovery-pilot-v1", "files": files}), encoding="utf-8")


def fixture(root):
    root.mkdir(); (root / "raw").mkdir(); (root / "raw/list.bin").write_bytes(b"source-list")
    receipt = {"status": 200, "path": "raw/list.bin", "source_hash": hashlib.sha256(b"source-list").hexdigest()}
    rows = [{"provider_article_id": aid, "file_attach": 0, "ticker_filter": ticker, "exchange_filter": exchange,
             "list_receipt": receipt, "detail_request": {"url": DETAIL_URL, "method": "POST",
             "form": {"pArticlesID": aid, "pFileAttach": "0"}}} for aid, ticker, exchange in
            [("100", "PVS", "HNX"), ("200", "ACV", "UPCOM")]]
    (root / "discovered_articles.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    (root / "requests.json").write_text(json.dumps([receipt]), encoding="utf-8")
    (root / "result.json").write_text(json.dumps({"status": "PARTIAL_DISCOVERY_ONLY", "limitations": []}), encoding="utf-8")
    (root / "plan.json").write_text("{}", encoding="utf-8"); seal(root)


class Transport:
    def __init__(self, root, **kwargs):
        self.root, self.requests, self.options = root, [], kwargs
    def fetch(self, url, payload, content_type=None):
        self.assert_request = parse_qs(payload.decode())
        body = b"<html>Enable JavaScript</html>"
        path = "raw/response-" + str(len(self.requests)) + ".bin"
        (self.root / "raw").mkdir(exist_ok=True); (self.root / path).write_bytes(body)
        receipt = {"url": url, "request_body": payload.decode(), "status": 200,
                   "path": path, "source_hash": hashlib.sha256(body).hexdigest()}
        self.requests.append(receipt)
        return body.decode(), receipt


class HnxAnnouncementDetailsTests(unittest.TestCase):
    def test_two_responses_preserve_ids_payload_raw_and_no_verified_content(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); fixture(root / "discovery"); clients = []
            def factory(path, **kwargs):
                client = Transport(path, **kwargs); clients.append(client); return client
            result = acquire_details(root / "discovery", ["100", "200"], root / "out", transport_factory=factory)
            self.assertEqual(2, result["successful_public_responses"])
            self.assertEqual(0, result["article_contents_verified"])
            self.assertFalse(result["canonical_build"]); self.assertEqual(0, result["normalized_observations"])
            self.assertEqual({"max_requests": 2, "interval": 2, "timeout": 15}, clients[0].options)
            self.assertEqual(["200"], clients[0].assert_request["pArticlesID"])
            records = [json.loads(s) for s in (root / "out/detail_responses.jsonl").read_text().splitlines()]
            self.assertEqual(["100", "200"], [r["provider_article_id"] for r in records])
            manifest = json.loads((root / "out/manifest.json").read_text())
            for name, digest in manifest["files"].items():
                self.assertEqual(digest, hashlib.sha256((root / "out" / name).read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                acquire_details(root / "discovery", ["100"], root / "out")

    def test_failure_stops_without_retry_or_next_article_and_seals_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); fixture(root / "discovery")
            class Blocked(Transport):
                def fetch(self, *args, **kwargs):
                    self.requests.append({"status": 403}); raise SourceLimitation("SOURCE_ACCESS_LIMITATION")
            result = acquire_details(root / "discovery", ["100", "200"], root / "out", transport_factory=Blocked)
            self.assertEqual(1, result["network_requests"]); self.assertEqual("FAILED_OR_DEFERRED", result["status"])
            self.assertEqual(0, result["successful_public_responses"]); self.assertTrue((root / "out/manifest.json").is_file())

    def test_checksum_failure_precedes_network_and_output_creation(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); fixture(root / "discovery")
            (root / "discovery/raw/list.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "CHECKSUM"):
                acquire_details(root / "discovery", ["100"], root / "out", transport_factory=lambda *a, **k: self.fail("network"))
            self.assertFalse((root / "out").exists())

    def test_bad_endpoint_or_payload_even_if_resealed_is_rejected(self):
        for field, value in [("url", "https://example.com/"), ("method", "GET"),
                             ("form", {"pArticlesID": "999", "pFileAttach": "0"})]:
            with tempfile.TemporaryDirectory() as t:
                root = Path(t) / "discovery"; fixture(root)
                rows = [json.loads(s) for s in (root / "discovered_articles.jsonl").read_text().splitlines()]
                rows[0]["detail_request"][field] = value
                (root / "discovered_articles.jsonl").write_text("\n".join(json.dumps(r) for r in rows)); seal(root)
                with self.assertRaisesRegex(ValueError, "OUTSIDE_OBSERVED"):
                    load_selection(root, ["100"])

    def test_selection_limits_and_unknown_ids(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "discovery"; fixture(root)
            for ids in [[], ["100", "200", "300"], ["100", "100"], ["abc"], ["999"]]:
                with self.assertRaises(ValueError): load_selection(root, ids)

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "discovery"; fixture(root); (root.parent / "outside").write_bytes(b"x")
            manifest = json.loads((root / "manifest.json").read_text())
            manifest["files"]["../outside"] = hashlib.sha256(b"x").hexdigest()
            (root / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "CHECKSUM"): load_selection(root, ["100"])

    def test_dry_run_no_transport_or_output(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); fixture(root / "discovery")
            result = acquire_details(root / "discovery", ["100"], root / "out", dry_run=True,
                                     transport_factory=lambda *a, **k: self.fail("network"))
            self.assertEqual(0, result["network_requests"]); self.assertFalse((root / "out").exists())


if __name__ == "__main__": unittest.main()
