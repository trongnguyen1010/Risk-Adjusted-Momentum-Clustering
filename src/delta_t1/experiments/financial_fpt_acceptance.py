"""Bounded FPT handoff across six metric families, with per-basis acceptance."""
import json
from datetime import datetime
from pathlib import Path

from ..features.financial_equity_reference import REGISTRY, VARIANT, gross_capital_bridge
from ..ingestion.cafef_financial import encoded, immutable_write
from ..ingestion.financial_documents import verify_inventory
from .financial_ttm_valuation import file_hash, verify_review

CONTRACT = dict(F_SCORE='PIOTROSKI_VAS_REPORTED_NET_PROFIT_REFERENCE',
                M_SCORE='BENEISH_2013_VAS_REPORTED_PROFIT_OWNED_PPE_SENSITIVITY',
                Z_SCORE='EM_Z_DOUBLE_PRIME_PLUS_3_25_REFERENCE',
                EPS_RECOMPUTE='REPORTED_NUMERATOR_SHARE_DAYS_TTM_REFERENCE',
                PE='RAW_CLOSE_REPORTED_TTM_REFERENCE', PB=VARIANT,
                unknown_input_policy='NULL_WITH_REASON_NOT_ZERO', classification_thresholds=None,
                production_review_status='MANUAL_REVIEW_REQUIRED')


def unique_usable(rows, year, day, date_key='decision_date'):
    """Require an explicit single result at the latest already-usable decision."""
    choices = [r for r in rows if r['year'] == year and r[date_key] <= day]
    if not choices:
        return None
    latest = max(r[date_key] for r in choices)
    exact = [r for r in choices if r[date_key] == latest]
    if len(exact) != 1:
        raise ValueError('ambiguous annual result; no source priority')
    return exact[0]


def metric_matrix(annual, ttm_row, bridge, year):
    day = datetime.fromisoformat(ttm_row['decision_at']).date().isoformat()
    f = unique_usable(annual['f_score'], year, day)
    m = unique_usable(annual['m_score'], year, day)
    z = unique_usable([r for r in annual['existing_eps_z'] if r['task'] == 'Z_SCORE'], year, day, 'usable_from_date')
    eps = unique_usable([r for r in annual['existing_eps_z'] if r['task'] == 'EPS_RECOMPUTE'], year, day, 'usable_from_date')
    if (f and f['vas_reference']['variant'] != CONTRACT['F_SCORE']) or (m and m['gross_trade_reference']['variant'] != CONTRACT['M_SCORE']):
        raise ValueError('annual variant mismatch')
    for result in [z, eps]:
        if result and (result['status'] != 'REFERENCE_QA_PASS' or result['qa']['passed'] is not True):
            raise ValueError('annual evidence QA failed')
    # Every row retains its source result and inputs. Annual score basis is not H1/TTM.
    metrics = [
        dict(task='F_SCORE', basis='ANNUAL_VAS_REPORTED_NET_PROFIT', period=str(year),
             value=f['vas_reference']['value'] if f else None, source_result=f,
             limitations=['VAS adaptation; strict ordinary-income field unresolved']),
        dict(task='M_SCORE', basis='ANNUAL_OWNED_PPE_GROSS_TRADE_SENSITIVITY', period=str(year),
             value=m['gross_trade_reference']['value'] if m else None, source_result=m,
             limitations=['Conditional allowance allocation; no classification threshold']),
        dict(task='Z_SCORE', basis='ANNUAL_EM_Z_DOUBLE_PRIME_PLUS_3_25', period=str(year),
             value=z['value']['em_z_double_prime_reference'] if z else None, source_result=z,
             limitations=['Continuous diagnostic; no calibrated Vietnam distress threshold']),
        dict(task='EPS_RECOMPUTE', basis='REPORTED_NUMERATOR_SHARE_DAYS_TTM_REFERENCE',
             period='2025-07-01/2026-06-30', value=ttm_row['ttm']['value'],
             annual_reference=eps, source_result=ttm_row['ttm'],
             limitations=['Unestimated interim reserve and period allocation unresolved']),
        dict(task='PE', basis='RAW_CLOSE_OVER_REPORTED_TTM_EPS', period='2025-07-01/2026-06-30',
             value=ttm_row['valuation']['pe'], source_result=ttm_row['valuation'],
             limitations=['Reported EPS deduction practices; provisional security identity']),
        dict(task='PB', basis=VARIANT, period='2026-06-30_PLUS_GROSS_REGISTERED_ESOP_CAPITAL',
             value=bridge['value'], source_result=bridge,
             latest_reported_equity_reference=ttm_row['valuation']['pb'],
             limitations=['Gross capital bridge; unknown fee treatment and cash classification',
                          'Subsequent operating results and complete events not observed'])]
    for row in metrics:
        row['calculation_status'] = 'REFERENCE_VALUE_AVAILABLE' if row['value'] is not None else 'REFERENCE_UNAVAILABLE'
        row['production_accepted'] = False
        row['historical_identity_status'] = 'PROVISIONAL_NOT_VERIFIED'
    return metrics


def export(root, config_path, output):
    root = Path(root).resolve()
    c = json.loads((root / config_path).read_bytes())
    if (c['symbol'] != 'FPT' or c['year'] != 2025 or c['pb_variant'] != VARIANT or c['metric_contract'] != CONTRACT
            or any(c.get(k) is not False for k in ['financial_features_allowed', 'research_ready', 'full_universe_allowed'])):
        raise ValueError('bounded reference contract only')
    inputs = {}
    for key in ['annual_run', 'ttm_run', 'equity_review_run']:
        run = (root / c[key]).resolve()
        if not run.is_relative_to(root / 'data'):
            raise ValueError('input outside data')
        if file_hash(run / 'manifest.json') != c['input_manifest_sha256'][key]:
            raise ValueError('upstream manifest changed')
        verify_inventory(run)
        filename = dict(annual_run='result.json', ttm_run='results.json', equity_review_run='review.json')[key]
        inputs[key] = json.loads((run / filename).read_bytes())
    annual, ttm, review = [inputs[k] for k in ['annual_run', 'ttm_run', 'equity_review_run']]
    if any(x.get('financial_features_allowed') is not False or x.get('research_ready') is not False
           for x in [annual, ttm, review]):
        raise ValueError('upstream reference gates changed')
    verify_review(review, root)
    verify_review(ttm['review'], root)
    cards_path = Path(review['publication_cards_path']).resolve()
    if not cards_path.is_relative_to(root / 'data') or file_hash(cards_path) != review['publication_cards_sha256']:
        raise ValueError('publication cards changed')
    if not 1 <= len(ttm['results']) <= 4 or [r['decision_at'] for r in ttm['results']] != c['decision_at']:
        raise ValueError('decision scope changed')
    results = []
    for row in ttm['results']:
        day = datetime.fromisoformat(row['decision_at']).date().isoformat()
        if day > c['max_observed_date']:
            raise ValueError('outside observed market snapshot')
        bridge = gross_capital_bridge(review['snapshot'], review['event'], row['price']['value'], row['shares']['value'], day)
        metrics = metric_matrix(annual, row, bridge, c['year'])
        results.append(dict(decision_at=row['decision_at'], metrics=metrics, equity_bridge=bridge,
                            reference_metric_families_available=sum(m['value'] is not None for m in metrics),
                            production_metric_families_accepted=0))
    result = dict(version=c['version'], symbol=c['symbol'], results=results, equity_review=review,
                  policy=c['metric_contract'], feature_registry=[vars(REGISTRY.get(n)) for n in REGISTRY.names()],
                  stage_status='REFERENCE_HANDOFF_COMPLETE_STRICT_ACCEPTANCE_PARTIAL',
                  financial_features_allowed=False, research_ready=False, full_universe_allowed=False,
                  production_review_status='MANUAL_REVIEW_REQUIRED',
                  input_manifest_sha256=c['input_manifest_sha256'],
                  next_stage='BOUNDED_VNM_PVS_ACV_REFERENCE_PILOT',
                  remaining=['Strict F/M input definitions and mappings', 'Unestimated reserve allocation',
                             'ESOP fee treatment and pre-balance cash classification',
                             'Complete corporate event coverage and historical share effective basis',
                             'Historical security/sector identity', 'Other three reviewed pilot symbols'])
    out = (root / output).resolve()
    if not out.is_relative_to(root / 'data'):
        raise ValueError('output under data only')
    out.mkdir(parents=True, exist_ok=False)
    for name, content in [('results.json', encoded(result)), ('config.json', (root / config_path).read_bytes()),
                          ('runner.py', Path(__file__).read_bytes()),
                          ('calculator.py', (root / 'src/delta_t1/features/financial_equity_reference.py').read_bytes())]:
        immutable_write(out / name, content)
    immutable_write(out / 'manifest.json', encoded({'files': {p.name: file_hash(p) for p in out.iterdir()}}))
    return result
