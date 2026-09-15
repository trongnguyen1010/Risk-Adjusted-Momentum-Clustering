"""Point-in-time selectors for financial report vintages and facts."""
from datetime import datetime


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("point-in-time timestamp requires timezone")
    return parsed


def available_reports(reports: list[dict], security_id: str, decision_at: str) -> list[dict]:
    """Return only report vintages legally/operationally available at decision time."""
    cutoff = _timestamp(decision_at)
    eligible = []
    for report in reports:
        if report["security_id"] != security_id:
            continue
        if not report.get("published_at") or not report.get("available_at"):
            raise ValueError("financial report requires published_at and available_at")
        published, available = _timestamp(report["published_at"]), _timestamp(report["available_at"])
        if available < published:
            raise ValueError("financial report available_at precedes published_at")
        if available <= cutoff:
            eligible.append(report)
    return sorted(eligible, key=lambda row: (row["period_end"], row["statement_scope"], row["revision"], row["available_at"]))


def latest_report_vintages(reports: list[dict], security_id: str, decision_at: str) -> list[dict]:
    """Select latest available revision per fiscal period and statement scope."""
    selected: dict[tuple, dict] = {}
    for report in available_reports(reports, security_id, decision_at):
        key = (report["fiscal_year"], report.get("fiscal_quarter"), report["statement_scope"])
        current = selected.get(key)
        if current is None or (report["revision"], report["available_at"], report["report_id"]) > (
                current["revision"], current["available_at"], current["report_id"]):
            selected[key] = report
    order = lambda key: (key[0], -1 if key[1] is None else key[1], key[2])
    return [selected[key] for key in sorted(selected, key=order)]


def facts_for_vintages(facts: list[dict], reports: list[dict]) -> list[dict]:
    report_ids = {report["report_id"] for report in reports}
    return [fact for fact in facts if fact["report_id"] in report_ids]
