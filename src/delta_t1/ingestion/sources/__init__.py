"""Source adapters preserve provider envelopes; they do not define canonical truth."""

from .base import SourceAdapter, SourceNotVerifiedError

__all__ = ["SourceAdapter", "SourceNotVerifiedError"]
