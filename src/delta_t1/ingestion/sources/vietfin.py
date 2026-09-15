"""VietFin source interface; underlying provider and rights remain unverified."""
from .base import SourceAdapter


class VietFinSource(SourceAdapter):
    source_id = "vietfin"
    verification_status = "DISCOVERED"

    def acquire(self, request: dict) -> dict:
        self.require_verified_semantics()
        raise AssertionError("VietFin acquisition is unavailable until verification is recorded")
