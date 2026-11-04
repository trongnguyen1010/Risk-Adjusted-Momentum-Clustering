"""Chẩn đoán đúng một lần SDK login, che key trước khi lưu thông báo lỗi."""
import base64
import contextlib
import importlib.metadata
import io
import json
from pathlib import Path
import re
from urllib.parse import quote, quote_plus


def scrub(text, secret):
    value = str(text)
    if secret:
        variants = {secret, quote(secret, safe=""), quote_plus(secret),
                    base64.b64encode(secret.encode()).decode()}
        if len(secret) >= 16:
            variants.update((secret[:8], secret[-8:]))
        for item in sorted(variants, key=len, reverse=True):
            value = value.replace(item, "[KEY_REMOVED]")
    value = re.sub(r"https?://[^\s<>\"']+", "[URL_REMOVED]", value)
    value = re.sub(r"(?i)\bbearer\s+[^\s,;]+", "Bearer [REMOVED]", value)
    value = re.sub(r"[A-Za-z0-9_+/=-]{24,}", "[LONG_TOKEN_REMOVED]", value)
    return value[:2000]


def exception_detail(exc, key, stage):
    result = {"stage": stage, "error_type": type(exc).__name__}
    code = getattr(exc, "code", None)
    if isinstance(code, str) and re.fullmatch(r"VNSTOCK_[A-Z0-9_]{1,90}", code) and (not key or key not in code):
        result["sdk_code"] = code
    kind = getattr(exc, "kind", None)
    if kind in {"input", "auth", "entitlement", "network", "provider", "schema", "unsupported", "internal"}:
        result["sdk_kind"] = kind
    http = getattr(exc, "status", None)
    if type(http) is int:
        result["http_status"] = http
    retryable = getattr(exc, "retryable", None)
    if type(retryable) is bool:
        result["sdk_retryable"] = retryable
    result["message_redacted"] = scrub(getattr(exc, "message_en", None) or str(exc), key)
    action = getattr(exc, "action_en", None) or getattr(exc, "action", None)
    if action:
        result["action_redacted"] = scrub(action, key)
    return result


def diagnose(sdk, key):
    report = {"stage": "VNSTOCK_AUTH_DIAGNOSTIC_V1", "calendar_calls": 0,
              "hnx_requests": 0, "automatic_retry": False}
    stripped = key.strip()
    if not stripped or any(c.isspace() for c in stripped) or stripped[:1] in {"'", '"'}:
        return dict(report, status="KEY_INPUT_REVIEW_REQUIRED", reason="Empty, embedded whitespace or wrapping quotes; no login attempted.")
    try:
        # Capture and discard SDK's own output, which may contain account data.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sdk.login(stripped)
        report["status"] = "LOGIN_RETURNED_WITHOUT_EXCEPTION_NOT_A_DATA_GATE"
    except Exception as exc:
        report.update(status="LOGIN_FAILED", diagnostic=exception_detail(exc, stripped, "SDK_LOGIN"))
    return report


def run_kaggle_diagnostic():
    from datetime import datetime, timezone
    import zipfile
    from kaggle_secrets import UserSecretsClient
    key = None
    report = {"status": "NOT_STARTED", "calendar_calls": 0, "hnx_requests": 0}
    try:
        key = UserSecretsClient().get_secret("VNSTOCK_API_KEY")
        version = importlib.metadata.version("vnstock")
        if version != "5.0.1":
            report = dict(report, status="SDK_VERSION_MISMATCH", installed_version=version)
        else:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                import vnstock
            report = diagnose(vnstock, key)
            report["installed_sdk_version"] = version
    except Exception as exc:
        report = dict(report, status="DIAGNOSTIC_SETUP_ERROR",
                      diagnostic=exception_detail(exc, key or "", "SECRET_VERSION_OR_IMPORT"))
    finally:
        key = None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path("/kaggle/working") / ("delta-vnstock-auth-" + stamp + ".json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = output.with_suffix(".zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(output, "auth_diagnostic.json")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("TẢI ZIP CHẨN ĐOÁN:", archive)
    return report
