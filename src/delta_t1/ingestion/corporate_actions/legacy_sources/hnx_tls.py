"""Complete HNX's omitted intermediate only after validation to an existing trust root."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import ssl
import subprocess

from .corporate_action_sources import SourceLimitation, sha

INTERMEDIATE_DER_SHA256 = "1b2928021a4b89cf0f572a2436e914e25412ad58edee221e6c7c3c5437179a26"
EXISTING_ROOT_SHA256 = "cbb522d7b7f127ad6a0113865bdf1cd4102e7d0759af635a7cf4720dc963c53b"


def validated_hnx_context(project, output, *, context=None, openssl_binary=None, run=subprocess.run):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    output.mkdir(parents=True)
    report = {"mode": "VALIDATED_INTERMEDIATE_ONLY", "status": "BLOCKED", "network_requests": 0,
              "new_root_trust": False, "hostname_verification": True, "certificate_verification": "CERT_REQUIRED"}
    try:
        config = json.loads((project / "configs/data/hnx_tls_chain_v1.json").read_text(encoding="utf-8"))
        if config["certificate_der_sha256"] != INTERMEDIATE_DER_SHA256 or config["existing_trusted_root_der_sha256"] != EXISTING_ROOT_SHA256:
            raise SourceLimitation("TLS_PIN_POLICY_MISMATCH")
        path = (project / config["certificate_file"]).resolve()
        if not path.is_relative_to(project.resolve()):
            raise SourceLimitation("TLS_CERTIFICATE_PATH_OUTSIDE_PROJECT")
        pem = path.read_bytes()
        if pem.count(b"-----BEGIN CERTIFICATE-----") != 1 or pem.count(b"-----END CERTIFICATE-----") != 1:
            raise SourceLimitation("TLS_EXACTLY_ONE_INTERMEDIATE_REQUIRED")
        if sha(pem) != config["certificate_pem_sha256"] or sha(ssl.PEM_cert_to_DER_cert(pem.decode("ascii"))) != INTERMEDIATE_DER_SHA256:
            raise SourceLimitation("TLS_INTERMEDIATE_CHECKSUM_MISMATCH")
        context = context if context is not None else ssl.create_default_context()
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise SourceLimitation("TLS_BASELINE_VERIFICATION_NOT_STRICT")
        flags = int(context.verify_flags)
        roots = [der for der in context.get_ca_certs(binary_form=True) if sha(der) == EXISTING_ROOT_SHA256]
        if len(roots) != 1:
            raise SourceLimitation("TLS_REQUIRED_ROOT_NOT_ALREADY_TRUSTED")
        root_path = output / "existing_trusted_root.pem"
        root_path.write_text(ssl.DER_cert_to_PEM_cert(roots[0]), encoding="ascii")
        intermediate_path = output / "pinned_intermediate.pem"
        intermediate_path.write_bytes(pem)
        binary = openssl_binary or shutil.which("openssl")
        if not binary:
            raise SourceLimitation("TLS_OFFLINE_OPENSSL_TOOL_MISSING")
        command = [binary, "verify", "-x509_strict", "-purpose", "sslserver", "-CAfile", str(root_path),
                   "-no-CApath", "-no-CAstore", str(intermediate_path)]
        checked = run(command, capture_output=True, text=True, timeout=15)
        report.update(openssl_command=command, openssl_returncode=checked.returncode,
                      openssl_stdout=checked.stdout, openssl_stderr=checked.stderr,
                      intermediate_der_sha256=INTERMEDIATE_DER_SHA256, existing_trusted_root_der_sha256=EXISTING_ROOT_SHA256)
        if checked.returncode != 0:
            raise SourceLimitation("TLS_INTERMEDIATE_OFFLINE_CHAIN_VALIDATION_FAILED")
        # Only now add the authenticated intermediate; never add a new root or relax flags.
        context.load_verify_locations(cadata=pem.decode("ascii"))
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname or int(context.verify_flags) != flags:
            raise SourceLimitation("TLS_VERIFICATION_SETTINGS_CHANGED")
        report.update(status="VALIDATED", verify_flags_before=flags, verify_flags_after=int(context.verify_flags),
                      cert_store_stats=context.cert_store_stats(), source_url=config["source_url"])
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
        (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SourceLimitation("TLS_CHAIN_PREPARATION_FAILED: " + str(exc)) from exc
    (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return context, report
