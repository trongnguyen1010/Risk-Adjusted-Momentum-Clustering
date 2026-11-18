"""Resolve the explicitly released Assessment artifact without selecting data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ASSESSMENT_RELEASE_SCHEMA_VERSION = "assessment-release-pointer-v1"
DEFAULT_RELEASE_CONFIG = Path("configs/product/assessment_release_v1.json")
VALID_CONTEXTS = frozenset({"SIMULATED_AS_OF", "CURRENT_AS_OF"})
REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "release_status",
        "release_id",
        "release_revision",
        "artifact_dir",
        "assessment_context",
        "as_of",
        "required_price_session",
        "evidence_cutoff_at",
        "verification_status",
    }
)


@dataclass(frozen=True)
class AssessmentRelease:
    """Pinned, read-only release context; artifact contents are checked in R3-02."""

    release_id: str
    release_revision: str
    artifact_dir: Path
    assessment_context: str
    as_of: str
    required_price_session: str
    evidence_cutoff_at: str | None
    verification_status: str


@dataclass(frozen=True)
class AssessmentReleaseResolution:
    """A non-serving state used by the API layer to distinguish an unavailable release."""

    status: str
    reason: str | None
    release: AssessmentRelease | None

    @property
    def ready(self) -> bool:
        return self.status == "READY"


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _not_ready(reason: str) -> AssessmentReleaseResolution:
    return AssessmentReleaseResolution(status="NOT_READY", reason=reason, release=None)


def resolve_assessment_release(
    config_path: Path | str | None = None,
    *,
    repository_root: Path | str | None = None,
) -> AssessmentReleaseResolution:
    """Resolve only the path explicitly pinned by the release config.

    This function deliberately does not inspect manifests, list sibling runs, or
    choose a fallback release. Manifest integrity belongs to R3-02.
    """

    root = Path(repository_root).resolve() if repository_root is not None else _repository_root()
    configured_path = Path(config_path) if config_path is not None else DEFAULT_RELEASE_CONFIG
    config_file = configured_path.resolve() if configured_path.is_absolute() else (root / configured_path).resolve()
    if not config_file.is_file():
        return _not_ready("CONFIG_NOT_FOUND")

    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _not_ready("CONFIG_INVALID")
    if not isinstance(config, dict):
        return _not_ready("CONFIG_INVALID")
    if REQUIRED_FIELDS - set(config):
        return _not_ready("RELEASE_POINTER_MISSING")
    if config.get("schema_version") != ASSESSMENT_RELEASE_SCHEMA_VERSION:
        return _not_ready("CONFIG_SCHEMA_UNSUPPORTED")
    if config.get("release_status") != "RELEASED":
        return _not_ready("RELEASE_NOT_PUBLISHED")

    text_fields = ("release_id", "release_revision", "artifact_dir", "assessment_context", "verification_status")
    if any(not isinstance(config.get(field), str) or not config[field].strip() for field in text_fields):
        return _not_ready("RELEASE_POINTER_INVALID")
    if config["assessment_context"] not in VALID_CONTEXTS:
        return _not_ready("RELEASE_CONTEXT_INVALID")
    if not _valid_date(config["as_of"]) or not _valid_date(config["required_price_session"]):
        return _not_ready("RELEASE_DATE_INVALID")
    cutoff = config["evidence_cutoff_at"]
    if cutoff is not None and (not isinstance(cutoff, str) or not cutoff.strip()):
        return _not_ready("RELEASE_CUTOFF_INVALID")

    configured_artifact = Path(config["artifact_dir"])
    if configured_artifact.is_absolute():
        return _not_ready("ARTIFACT_PATH_NOT_RELATIVE")
    artifact_dir = (root / configured_artifact).resolve()
    if root not in artifact_dir.parents:
        return _not_ready("ARTIFACT_PATH_OUTSIDE_REPOSITORY")
    if not artifact_dir.is_dir():
        return _not_ready("ARTIFACT_NOT_FOUND")

    return AssessmentReleaseResolution(
        status="READY",
        reason=None,
        release=AssessmentRelease(
            release_id=config["release_id"],
            release_revision=config["release_revision"],
            artifact_dir=artifact_dir,
            assessment_context=config["assessment_context"],
            as_of=config["as_of"],
            required_price_session=config["required_price_session"],
            evidence_cutoff_at=cutoff,
            verification_status=config["verification_status"],
        ),
    )
