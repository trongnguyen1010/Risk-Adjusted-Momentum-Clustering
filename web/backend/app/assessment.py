"""Pure mapper from a pinned offline Assessment record to the public response."""

from datetime import datetime, timezone

from .schemas import AssessmentResponse


VERDICT_STATUS = {
    'RESEARCH_FAVORABLE': 'RESEARCH_FAVORABLE',
    'WATCH': 'WATCH',
    'CAUTION': 'CAUTION',
    'INSUFFICIENT_EVIDENCE': 'INSUFFICIENT_EVIDENCE',
    'WORTH_CONSIDERING': 'RESEARCH_FAVORABLE',
    'MONITOR': 'WATCH',
    'LOW_PRIORITY': 'CAUTION',
}
FINANCIAL = {'roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover', 'revenue_growth', 'cfo_to_ni'}


def map_assessment_response(lookup, *, request_time: str | None = None, lookback_years: int = 10, history_rows=()) -> AssessmentResponse:
    """Map one lookup result only; no feature, peer or verdict is recomputed here."""
    if not lookup.found:
        raise ValueError(lookup.reason or 'ASSESSMENT_NOT_FOUND')
    record, release = lookup.assessment, lookup.release
    features = []
    for category, values in (('FINANCIAL', record['financial_features']), ('MARKET', record['market_features'])):
        for feature_id, value in values.items():
            peer = record['peer_comparisons'].get(feature_id) if record['peer_comparisons'] else None
            features.append({
                'feature_id': feature_id, 'category': category, 'value': value,
                'status': 'OK' if value is not None else 'DATA_MISSING', 'unit': 'ratio',
                'period': str(record['latest_fy']) if category == 'FINANCIAL' and record.get('latest_fy') is not None else release.required_price_session,
                'usable_from_date': record.get('usable_from_date'), 'peer': peer, 'evidence_ref': None,
            })
    def cluster(cluster_id, version, period):
        return None if cluster_id is None else {'id': cluster_id, 'model_version': version, 'date_or_fy': period, 'profile': None, 'quality_flags': [], 'source_revision': release.release_revision}
    evidence = lambda messages, direction: [{'feature_id': None, 'direction': direction, 'message': message, 'value': None, 'status': None, 'evidence_ref': None} for message in messages]
    if lookback_years not in (5, 10):
        raise ValueError('lookback_years must be 5 or 10')
    start_year = int(release.as_of[:4]) - lookback_years + 1
    history = [{'feature_id': row['metric'], 'period': str(row.get('fiscal_year', '')), 'value': row.get('value'), 'status': row['status'], 'usable_from_date': row.get('usable_from_date') or None, 'source': row['source']} for row in history_rows if int(row.get('fiscal_year', 0)) >= start_year]
    return AssessmentResponse.model_validate({
        'ticker': record['ticker'], 'request_time': request_time or datetime.now(timezone.utc).isoformat(),
        'as_of': release.as_of, 'required_price_session': release.required_price_session, 'evidence_cutoff_at': release.evidence_cutoff_at,
        'assessment_context': release.assessment_context, 'availability_status': 'DATA_MISSING' if lookup.status == 'INSUFFICIENT_EVIDENCE' else 'READY',
        'assessment_status': VERDICT_STATUS[record['verdict']], 'rationale': record['rationale'],
        'market_cluster': cluster(record.get('cluster_a'), 'A-v4', release.required_price_session),
        'financial_cluster': cluster(record.get('cluster_b'), 'B-PIT-v1', str(record.get('latest_fy') or '')),
        'features': features, 'drivers': evidence(record.get('favorable_signals', []), 'FAVORABLE'),
        'risks': evidence(record.get('caution_signals', []), 'CAUTION'), 'counter_evidence': [], 'history': history,
        'references': {'release_revision': release.release_revision, 'policy_revision': release.policy_revision, 'manifest_sha256': release.manifest_sha256, 'deterministic_content_sha256': release.deterministic_content_sha256, 'source_hashes': release.input_hashes},
        'scope': 'AS_OF_ASSESSMENT_ONLY',
    })
