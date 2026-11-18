from __future__ import annotations

import unittest
from email.message import Message
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError

from delta_t1.ingestion.financial_pit_continuation import (
    BoundaryError,
    Collector,
    _is_pdf_response,
    _persist_response_before_validation,
    _same_issuer_redirect,
    _validate_persisted_response,
    sha256_bytes,
    validate_proposal,
)


class _Response:
    status = 200

    def __init__(self, body: bytes, content_type: str = "application/pdf") -> None:
        self.body = body
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def read(self, size: int) -> bytes:
        return self.body[:size]

    def geturl(self) -> str:
        return "https://fpt.com/api/media/test.pdf"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _Opener:
    def __init__(self, outcome) -> None:
        self.outcome = outcome
        self.open_count = 0

    def open(self, request, timeout):
        del request, timeout
        self.open_count += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class ContinuationTests(unittest.TestCase):
    def policy(self) -> dict:
        return {"maximum_requests": 1, "maximum_response_bytes": 20, "maximum_total_bytes": 20,
                "minimum_interval_seconds": 2, "timeout_seconds": 30, "user_agent": "test", "accept": "application/pdf"}

    def test_counts_successful_request_and_bytes(self) -> None:
        collector = Collector(self.policy(), opener=_Opener(_Response(b"%PDF-1.7\n%%EOF")), sleeper=lambda _: None, monotonic=lambda: 1.0)
        result = collector.get("https://fpt.com/api/media/test.pdf")
        self.assertEqual(result["kind"], "response")
        self.assertEqual(collector.requests, 1)
        self.assertEqual(collector.bytes, 14)

    def test_response_bound_is_fail_closed(self) -> None:
        collector = Collector(self.policy(), opener=_Opener(_Response(b"x" * 21)), sleeper=lambda _: None, monotonic=lambda: 1.0)
        with self.assertRaises(BoundaryError):
            collector.get("https://fpt.com/api/media/test.pdf")

    def test_access_control_is_fail_closed(self) -> None:
        headers = Message()
        collector = Collector(self.policy(), opener=_Opener(HTTPError("url", 403, "denied", headers, None)), sleeper=lambda _: None, monotonic=lambda: 1.0)
        with self.assertRaises(BoundaryError):
            collector.get("https://fpt.com/api/media/test.pdf")

    def test_redirect_requires_same_issuer(self) -> None:
        allowed = {"fpt.com", "www.fpt.com"}
        self.assertTrue(_same_issuer_redirect("https://fpt.com/a", "https://www.fpt.com/b", allowed))
        self.assertFalse(_same_issuer_redirect("https://fpt.com/a", "https://cdn.example/b", allowed))

    def test_pdf_content_type_guard_uses_text_not_bytes(self) -> None:
        self.assertTrue(_is_pdf_response(b"%PDF-1.7\n%%EOF", "application/pdf"))
        self.assertFalse(_is_pdf_response(b"<html>error</html>", "text/html"))

    def test_valid_pdf_is_persisted_byte_exact_with_provenance_before_validation(self) -> None:
        body = b"%PDF-1.7\nobject\n%%EOF\n"
        result = {"status": 200, "url": "https://fpt.com/api/media/test.pdf", "content_type": "application/pdf", "body": body}
        with TemporaryDirectory(dir=Path.cwd() / ".tmp") as temporary:
            output = Path(temporary)
            evidence = _persist_response_before_validation(output, "request-01", result, "2026-10-04T00:00:00+00:00")
            self.assertEqual((output / evidence["raw_path"]).read_bytes(), body)
            self.assertEqual(evidence["sha256"], sha256_bytes(body))
            self.assertEqual(evidence["final_url"], result["url"])
            self.assertEqual(_validate_persisted_response(result, acquisition=True), "pdf")

    def test_validation_failure_preserves_raw_and_metadata(self) -> None:
        body = b"%PDF-1.7\nmissing-eof"
        result = {"status": 200, "url": "https://fpt.com/api/media/broken.pdf", "content_type": "application/pdf", "body": body}
        with TemporaryDirectory(dir=Path.cwd() / ".tmp") as temporary:
            output = Path(temporary)
            evidence = _persist_response_before_validation(output, "request-01", result, "2026-10-04T00:00:00+00:00")
            with self.assertRaisesRegex(BoundaryError, "NON_PDF_OR_INVALID_PDF"):
                _validate_persisted_response(result, acquisition=True)
            self.assertEqual((output / evidence["raw_path"]).read_bytes(), body)
            self.assertTrue((output / evidence["metadata_path"]).is_file())

    def test_unexpected_status_is_checked_after_raw_persistence(self) -> None:
        body = b"%PDF-1.7\n%%EOF"
        result = {"status": 206, "url": "https://fpt.com/api/media/partial.pdf", "content_type": "application/pdf", "body": body}
        with TemporaryDirectory(dir=Path.cwd() / ".tmp") as temporary:
            output = Path(temporary)
            evidence = _persist_response_before_validation(output, "request-01", result, "2026-10-04T00:00:00+00:00")
            with self.assertRaisesRegex(BoundaryError, "UNEXPECTED_HTTP_STATUS_206"):
                _validate_persisted_response(result, acquisition=True)
            self.assertEqual((output / evidence["raw_path"]).read_bytes(), body)

    def test_immutable_response_write_rejects_overwrite(self) -> None:
        result = {"status": 200, "url": "https://fpt.com/api/media/test.pdf", "content_type": "application/pdf", "body": b"%PDF-1.7\n%%EOF"}
        with TemporaryDirectory(dir=Path.cwd() / ".tmp") as temporary:
            output = Path(temporary)
            _persist_response_before_validation(output, "request-01", result, "2026-10-04T00:00:00+00:00")
            with self.assertRaises(FileExistsError):
                _persist_response_before_validation(output, "request-01", result, "2026-10-04T00:00:00+00:00")

    def test_invalid_pdf_does_not_retry_and_request_accounting_is_preserved(self) -> None:
        opener = _Opener(_Response(b"%PDF-1.7\nmissing-eof"))
        collector = Collector(self.policy(), opener=opener, sleeper=lambda _: None, monotonic=lambda: 1.0)
        result = collector.get("https://fpt.com/api/media/test.pdf")
        with TemporaryDirectory(dir=Path.cwd() / ".tmp") as temporary:
            evidence = _persist_response_before_validation(Path(temporary), "request-01", result, "2026-10-04T00:00:00+00:00")
            with self.assertRaises(BoundaryError):
                _validate_persisted_response(result, acquisition=True)
            self.assertTrue((Path(temporary) / evidence["raw_path"]).is_file())
        self.assertEqual(opener.open_count, 1)
        self.assertEqual(collector.requests, 1)
        self.assertEqual(collector.bytes, len(result["body"]))

    def test_frozen_v2_proposal_is_bounded_and_zero_network(self) -> None:
        path = Path("artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json")
        result = validate_proposal(path)
        self.assertEqual(result["branches"], 5)
        self.assertEqual(result["requests"], 11)
        self.assertEqual(result["documents"], 7)
        self.assertEqual(result["bytes"], 155189248)
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["status"], "PENDING_APPROVAL")


if __name__ == "__main__":
    unittest.main()
