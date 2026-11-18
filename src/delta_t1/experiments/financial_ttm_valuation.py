"""Immutable bounded FPT TTM/share-event reference execution from reviewed evidence."""
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from ..features.financial_ttm_reference import REGISTRY, VARIANT, reported_ttm, reported_ttm_valuation
from ..ingestion.financial_share_events import select_common_shares
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.cafef_financial import digest, encoded, immutable_write


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify_review(review, root):
    """Verify all linked files once, including separate publication page evidence."""
    checked=set()
    def walk(value):
        if isinstance(value,dict):
            for kind in ['pdf','image']:
                if f'{kind}_path' in value:
                    p=Path(value[f'{kind}_path']).resolve(); expected=value[f'{kind}_sha256']
                    if not p.is_relative_to(root/'data'):raise ValueError('evidence outside data')
                    key=(p,expected)
                    if key not in checked:
                        if file_hash(p)!=expected:raise ValueError('evidence changed')
                        checked.add(key)
            for nested in value.values():walk(nested)
        elif isinstance(value,list):
            for nested in value:walk(nested)
    walk(review)
    for run,sha in review['input_manifest_sha256'].items():
        p=Path(run).resolve()
        if not p.is_relative_to(root/'data') or file_hash(p/'manifest.json')!=sha:
            raise ValueError('upstream manifest changed')
        verify_inventory(p)
    if not review['checks'] or not all(c['passed'] is True for c in review['checks']):
        raise ValueError('review QA failed')


def select_price(rows, decision_at, symbol, security_id):
    decision=datetime.fromisoformat(decision_at)
    if decision.utcoffset() is None:raise ValueError('timezone-aware decision required')
    choices=[r for r in rows if r['ticker']==symbol and r['trade_date']==decision.date().isoformat()
             and r['security_id']==security_id and r['exchange']=='HOSE'
             and r.get('market_observation_status')=='OBSERVED_VALID']
    if len(choices)!=1:return dict(status='EXACT_DATE_PRICE_MISSING_OR_AMBIGUOUS',value=None)
    r=choices[0]; available=datetime.fromisoformat(r['available_at'])
    if available.utcoffset() is None or available>decision:
        return dict(status='PRICE_NOT_YET_AVAILABLE',value=None)
    return dict(status='RAW_PRICE_REFERENCE_SELECTED',value=r['raw_close'],row=r,price_basis='RAW_CLOSE_VND_PER_SHARE')


def export(root, config_path, output):
    root=Path(root).resolve();c=json.loads((root/config_path).read_bytes());out=(root/output).resolve()
    if not out.is_relative_to(root/'data'):raise ValueError('outputs under data only')
    if any(c.get(k) is not False for k in ['financial_features_allowed','research_ready','full_universe_allowed']):
        raise ValueError('reference only')
    if c.get('variant')!=VARIANT or c.get('symbol')!='FPT' or not 1<=len(c['decision_at'])<=4:
        raise ValueError('bounded exact reviewed FPT stage only')
    run=root/c['review_run'];verify_inventory(run);review=json.loads((run/'review.json').read_bytes())
    verify_review(review,root)
    policy=json.loads((root/c['date_policy']).read_bytes());cp=root/policy['calendar_path']
    if (policy.get('availability_rule')!='FIRST_OBSERVED_EXCHANGE_SESSION_STRICTLY_AFTER_PUBLICATION_DATE'
            or policy.get('financial_features_allowed') is not False
            or policy.get('timestamp_inference_allowed') is not False):
        raise ValueError('unapproved date policy')
    if file_hash(cp)!=policy['calendar_sha256']:raise ValueError('calendar changed')
    calendar=[json.loads(l) for l in cp.read_text(encoding='utf8').splitlines()]
    pp=root/c['price_path']
    if file_hash(pp)!=c['price_sha256']:raise ValueError('price changed')
    dates={datetime.fromisoformat(v).date().isoformat() for v in c['decision_at']}
    rows=[]
    with pp.open(encoding='utf8') as stream:
        for line in stream:
            if '"FPT"' in line:
                row=json.loads(line)
                if row.get('ticker')=='FPT' and row.get('trade_date') in dates:rows.append(row)
    results=[]
    for decision in c['decision_at']:
        day=datetime.fromisoformat(decision).date().isoformat()
        if day>c['max_observed_date']:raise ValueError('outside approved market snapshot')
        ttm=reported_ttm(review['periods'],review['scope_bridge'],day)
        shares=select_common_shares(review['initial_share_snapshot'],review['share_events'],day,calendar)
        price=select_price(rows,decision,c['symbol'],c['provisional_security_id'])
        b=review['latest_balance'];balance_usable=b['evidence']['usable_from_date']<=day
        if shares['value'] is None or price['value'] is None or not balance_usable:
            valuation=dict(status='PRICE_SHARES_OR_BALANCE_UNAVAILABLE',pe=None,pb=None,
                strict_event_adjusted_pb=None,financial_features_allowed=False,research_ready=False)
        else:
            valuation=reported_ttm_valuation(price['value'],ttm,b['parent_equity'],shares['value'])
        results.append(dict(decision_at=decision,ttm=ttm,shares=shares,price=price,valuation=valuation,
            balance_available=balance_usable,balance_date=b['balance_date'],
            statement_age_days=(date.fromisoformat(day)-date.fromisoformat(b['balance_date'])).days,
            equity_event_bridge='POST_BALANCE_ESOP_PROCEEDS_AND_FEES_NOT_FINALIZED',
            strict_financial_task_ready=False,historical_identity_status='PROVISIONAL_NOT_VERIFIED'))
    result=dict(version=c['version'],results=results,review=review,feature_registry=[
        vars(REGISTRY.get(n)) for n in REGISTRY.names()],
        stage_status='REFERENCE_CALCULATION_PASS_STRICT_ACCEPTANCE_PARTIAL',
        financial_features_allowed=False,research_ready=False,full_universe_allowed=False,
        production_review_status='MANUAL_REVIEW_REQUIRED',
        source_hashes=dict(review_manifest=file_hash(run/'manifest.json'),calendar=file_hash(cp),price=file_hash(pp)))
    out.mkdir(parents=True,exist_ok=False)
    for name,value in [('results.json',encoded(result)),('config.json',(root/config_path).read_bytes()),
            ('runner.py',Path(__file__).read_bytes()),
            ('calculator.py',(root/'src/delta_t1/features/financial_ttm_reference.py').read_bytes()),
            ('events.py',(root/'src/delta_t1/ingestion/financial_share_events.py').read_bytes())]:
        immutable_write(out/name,value)
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return result
