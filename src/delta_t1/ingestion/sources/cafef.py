"""CafeF source interface; endpoint semantics and rights are not yet verified."""
from .base import SourceAdapter


class CafeFSource(SourceAdapter):
    source_id = "cafef"
    verification_status = "DISCOVERED"

    def acquire(self, request: dict) -> dict:
        self.require_verified_semantics()
        raise AssertionError("CafeF acquisition is unavailable until verification is recorded")
