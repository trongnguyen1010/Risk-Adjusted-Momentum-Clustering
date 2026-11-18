"""Resolve the explicitly released Assessment artifact without selecting data."""

from __future__ import annotations

import json
import hashlib
import re
import csv
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
        "artifact_version",
        "artifact_dir",
        "assessment_context",
        "as_of",
        "required_price_session",
        "evidence_cutoff_at",
        "verification_status",
        "policy_revision",
        "manifest_sha256",
        "deterministic_content_sha256",
        "input_hashes",
    }
)
REQUIRED_INPUT_HASHES = frozenset({"indicators_sqlite_sha256", "availability_csv_sha256", "bpit_labels_csv_sha256"})
REQUIRED_SERVING_FILES = frozenset({"assessments.jsonl", "peer_benchmarks.csv", "coverage.csv", "feature_history.jsonl"})
FINANCIAL_FEATURES = frozenset({"roe", "roa", "gross_margin", "net_margin", "debt_to_equity", "current_ratio", "asset_turnover", "revenue_growth", "cfo_to_ni"})
MARKET_FEATURES = frozenset({"mom_21", "mom_63", "mom_126", "mom_252", "vol_63", "mdd_126", "beta_126", "liquidity_21", "downside_vol_63"})
ASSESSMENT_FEATURES = FINANCIAL_FEATURES | MARKET_FEATURES
VALID_VERDICTS = frozenset({"WORTH_CONSIDERING", "MONITOR", "LOW_PRIORITY", "INSUFFICIENT_EVIDENCE"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AssessmentRelease:
    """Pinned, read-only release context; artifact contents are checked in R3-02."""

    release_id: str
    release_revision: str
    artifact_version: str
    artifact_dir: Path
    assessment_context: str
    as_of: str
    required_price_session: str
    evidence_cutoff_at: str | None
    verification_status: str
    policy_revision: str
    manifest_sha256: str
    deterministic_content_sha256: str
    input_hashes: dict[str, str]


@dataclass(frozen=True)
class AssessmentReleaseResolution:
    """A non-serving state used by the API layer to distinguish an unavailable release."""

    status: str
    reason: str | None
    release: AssessmentRelease | None

    @property
    def ready(self) -> bool:
        return self.status == "READY"


@dataclass(frozen=True)
class AssessmentPayload:
    """Parsed offline data; values are carried through without recalculation."""

    assessments: dict[str, dict[str, Any]]
    peer_benchmarks: tuple[dict[str, Any], ...]
    coverage: dict[str, dict[str, Any]]
    feature_history: dict[str, tuple[dict[str, Any], ...]]


@dataclass(frozen=True)
class AssessmentPayloadResolution:
    status: str
    reason: str | None
    release: AssessmentRelease | None
    payload: AssessmentPayload | None

    @property
    def ready(self) -> bool:
        return self.status == "READY"


@dataclass(frozen=True)
class AssessmentLookupResolution:
    status: str
    reason: str | None
    release: AssessmentRelease | None
    assessment: dict[str, Any] | None

    @property
    def found(self) -> bool:
        return self.assessment is not None


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


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


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

    text_fields = (
        "release_id", "release_revision", "artifact_version", "artifact_dir", "assessment_context",
        "verification_status", "policy_revision", "manifest_sha256", "deterministic_content_sha256",
    )
    if any(not isinstance(config.get(field), str) or not config[field].strip() for field in text_fields):
        return _not_ready("RELEASE_POINTER_INVALID")
    if config["assessment_context"] not in VALID_CONTEXTS:
        return _not_ready("RELEASE_CONTEXT_INVALID")
    if not _valid_date(config["as_of"]) or not _valid_date(config["required_price_session"]):
        return _not_ready("RELEASE_DATE_INVALID")
    cutoff = config["evidence_cutoff_at"]
    if cutoff is not None and (not isinstance(cutoff, str) or not cutoff.strip()):
        return _not_ready("RELEASE_CUTOFF_INVALID")
    if not _valid_sha256(config["manifest_sha256"]) or not _valid_sha256(config["deterministic_content_sha256"]):
        return _not_ready("RELEASE_HASH_PIN_INVALID")
    input_hashes = config["input_hashes"]
    if not isinstance(input_hashes, dict) or set(input_hashes) != REQUIRED_INPUT_HASHES:
        return _not_ready("SOURCE_PIN_MISSING")
    if any(not _valid_sha256(value) for value in input_hashes.values()):
        return _not_ready("SOURCE_PIN_INVALID")

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
            artifact_version=config["artifact_version"],
            artifact_dir=artifact_dir,
            assessment_context=config["assessment_context"],
            as_of=config["as_of"],
            required_price_session=config["required_price_session"],
            evidence_cutoff_at=cutoff,
            verification_status=config["verification_status"],
            policy_revision=config["policy_revision"],
            manifest_sha256=config["manifest_sha256"],
            deterministic_content_sha256=config["deterministic_content_sha256"],
            input_hashes=dict(input_hashes),
        ),
    )


def _validate_opened_artifact(release: AssessmentRelease) -> str | None:
    """Verify the release pins and serving files without calculating any assessment."""

    if release.verification_status != "PASS":
        return "RELEASE_NOT_VERIFIED"
    manifest_path = release.artifact_dir / "manifest.json"
    if not manifest_path.is_file():
        return "MANIFEST_NOT_FOUND"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "MANIFEST_INVALID"
    if not isinstance(manifest, dict):
        return "MANIFEST_INVALID"
    if _sha256_file(manifest_path) != release.manifest_sha256:
        return "MANIFEST_HASH_MISMATCH"
    if manifest.get("version") != release.artifact_version:
        return "ARTIFACT_VERSION_MISMATCH"
    if manifest.get("as_of") != release.as_of:
        return "ARTIFACT_AS_OF_MISMATCH"
    if manifest.get("deterministic_content_sha256") != release.deterministic_content_sha256:
        return "CONTENT_HASH_PIN_MISMATCH"
    if manifest.get("input_hashes") != release.input_hashes:
        return "SOURCE_PIN_MISMATCH"

    output_files = manifest.get("output_files")
    if not isinstance(output_files, dict) or not REQUIRED_SERVING_FILES.issubset(output_files):
        return "SERVING_FILES_UNPINNED"
    for filename in REQUIRED_SERVING_FILES:
        expected_hash = output_files.get(filename)
        payload_path = release.artifact_dir / filename
        if not _valid_sha256(expected_hash):
            return "SERVING_FILE_HASH_INVALID"
        if not payload_path.is_file():
            return "SERVING_FILE_NOT_FOUND"
        if _sha256_file(payload_path) != expected_hash:
            return "SERVING_FILE_HASH_MISMATCH"
    return None


def open_assessment_release(
    config_path: Path | str | None = None,
    *,
    repository_root: Path | str | None = None,
) -> AssessmentReleaseResolution:
    """Open only a fully pinned release; reject tampered or mismatched artifacts."""

    resolution = resolve_assessment_release(config_path, repository_root=repository_root)
    if not resolution.ready:
        return resolution
    reason = _validate_opened_artifact(resolution.release)
    return resolution if reason is None else _not_ready(reason)


def _number_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool))


def _parse_float_or_null(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _load_assessments(path: Path, release: AssessmentRelease) -> dict[str, dict[str, Any]]:
    assessments: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"assessment line {line_number} is not an object")
        ticker = record.get("ticker")
        if not isinstance(ticker, str) or not ticker or ticker in assessments:
            raise ValueError(f"assessment line {line_number} has invalid ticker")
        if record.get("as_of") != release.as_of or record.get("verdict") not in VALID_VERDICTS:
            raise ValueError(f"assessment line {line_number} has incompatible context or verdict")
        for field, expected in (("financial_features", FINANCIAL_FEATURES), ("market_features", MARKET_FEATURES)):
            values = record.get(field)
            if not isinstance(values, dict) or set(values) != expected or any(not _number_or_null(value) for value in values.values()):
                raise ValueError(f"assessment line {line_number} has invalid {field}")
        peers = record.get("peer_comparisons")
        if not isinstance(peers, dict) or (set(peers) != ASSESSMENT_FEATURES and not (record["verdict"] == "INSUFFICIENT_EVIDENCE" and peers == {})):
            raise ValueError(f"assessment line {line_number} has invalid peer comparisons")
        assessments[ticker] = record
    return assessments


def _load_peers(path: Path, tickers: set[str]) -> tuple[dict[str, Any], ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"ticker", "metric", "peer_basis", "peer_count", "peer_median", "p25", "p75"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("peer benchmark columns missing")
        rows = []
        for row in reader:
            if row["ticker"] not in tickers or row["metric"] not in ASSESSMENT_FEATURES or not row["peer_basis"]:
                raise ValueError("peer benchmark has incompatible ticker or metric")
            count = int(row["peer_count"])
            if count < 0:
                raise ValueError("peer count is negative")
            rows.append({**row, "peer_count": count, "peer_median": _parse_float_or_null(row["peer_median"]), "p25": _parse_float_or_null(row["p25"]), "p75": _parse_float_or_null(row["p75"])})
    return tuple(rows)


def _load_coverage(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"feature", "category", "total_tickers", "valid_count", "coverage_pct"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("coverage columns missing")
        rows: dict[str, dict[str, Any]] = {}
        for row in reader:
            feature = row["feature"]
            if feature not in ASSESSMENT_FEATURES or feature in rows:
                raise ValueError("coverage has invalid feature")
            rows[feature] = {**row, "total_tickers": int(row["total_tickers"]), "valid_count": int(row["valid_count"]), "coverage_pct": float(row["coverage_pct"])}
    if set(rows) != ASSESSMENT_FEATURES:
        raise ValueError("coverage does not contain the Assessment whitelist")
    return rows


def _load_history(path: Path, tickers: set[str]) -> dict[str, tuple[dict[str, Any], ...]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        record = json.loads(line)
        if not isinstance(record, dict) or record.get("ticker") not in tickers or record.get("metric") not in ASSESSMENT_FEATURES:
            raise ValueError(f"history line {line_number} has invalid ticker or metric")
        if not _number_or_null(record.get("value")) or not isinstance(record.get("status"), str) or not record["status"] or not isinstance(record.get("source"), str) or not record["source"]:
            raise ValueError(f"history line {line_number} has invalid value or status")
        grouped.setdefault(record["ticker"], []).append(record)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}


def load_assessment_payload(
    config_path: Path | str | None = None,
    *,
    repository_root: Path | str | None = None,
) -> AssessmentPayloadResolution:
    """Load the verified release into memory without changing raw artifact content."""

    opened = open_assessment_release(config_path, repository_root=repository_root)
    if not opened.ready:
        return AssessmentPayloadResolution("NOT_READY", opened.reason, None, None)
    try:
        assessments = _load_assessments(opened.release.artifact_dir / "assessments.jsonl", opened.release)
        payload = AssessmentPayload(
            assessments=assessments,
            peer_benchmarks=_load_peers(opened.release.artifact_dir / "peer_benchmarks.csv", set(assessments)),
            coverage=_load_coverage(opened.release.artifact_dir / "coverage.csv"),
            feature_history=_load_history(opened.release.artifact_dir / "feature_history.jsonl", set(assessments)),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return AssessmentPayloadResolution("NOT_READY", "PAYLOAD_SCHEMA_INVALID", None, None)
    return AssessmentPayloadResolution("READY", None, opened.release, payload)


def lookup_assessment(
    ticker: str,
    *,
    assessment_context: str | None = None,
    as_of: str | None = None,
    required_price_session: str | None = None,
    release_revision: str | None = None,
    config_path: Path | str | None = None,
    repository_root: Path | str | None = None,
) -> AssessmentLookupResolution:
    """Read one pinned assessment without substituting release context or verdict."""

    loaded = load_assessment_payload(config_path, repository_root=repository_root)
    if not loaded.ready:
        return AssessmentLookupResolution("NOT_READY", loaded.reason, None, None)
    release = loaded.release
    expected = {
        "assessment_context": assessment_context,
        "as_of": as_of,
        "required_price_session": required_price_session,
        "release_revision": release_revision,
    }
    if any(value is not None and value != getattr(release, field) for field, value in expected.items()):
        return AssessmentLookupResolution("NOT_READY", "RELEASE_CONTEXT_MISMATCH", release, None)
    normalized = str(ticker).strip().upper()
    if not normalized or not normalized.replace("-", "").isalnum():
        return AssessmentLookupResolution("NOT_FOUND", "TICKER_INVALID", release, None)
    assessment = loaded.payload.assessments.get(normalized)
    if assessment is None:
        return AssessmentLookupResolution("NOT_FOUND", "TICKER_NOT_FOUND", release, None)
    status = "INSUFFICIENT_EVIDENCE" if assessment["verdict"] == "INSUFFICIENT_EVIDENCE" else "READY"
    return AssessmentLookupResolution(status, None, release, assessment)
