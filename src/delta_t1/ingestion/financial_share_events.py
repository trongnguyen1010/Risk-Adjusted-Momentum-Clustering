"""Date-aware common-share declarations, plans and conflicting effective dates."""
from datetime import date
from .financial_date_pit import next_session


def select_common_shares(snapshot, events, decision_date, calendar):
    date.fromisoformat(decision_date)
    base = dict(value=None, financial_features_allowed=False, research_ready=False)
    usable, _ = next_session(snapshot['publication_date'], snapshot['exchange'], calendar)
    if not usable or usable > decision_date or snapshot['balance_date'] > decision_date:
        return dict(base, status='INITIAL_SNAPSHOT_UNAVAILABLE')
    if snapshot.get('validation_status') != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED':
        return dict(base, status='UNREVIEWED_INITIAL_SNAPSHOT')
    shares = snapshot['common_shares']
    if type(shares) is not int or shares <= 0:
        return dict(base, status='INVALID_INITIAL_COMMON_SHARES')
    accepted, excluded = [], []
    ordered = sorted(events, key=lambda e: (e.get('effective_not_before') or '9999-12-31', e['event_id']))
    if len({e['event_id'] for e in events}) != len(events):
        return dict(base, status='DUPLICATE_EVENT_ID')
    for event in ordered:
        if event['exchange'] != snapshot['exchange'] or event['symbol'] != snapshot['symbol']:
            return dict(base, status='INCOMPATIBLE_EVENT_IDENTITY')
        first, _ = next_session(event['publication_date'], event['exchange'], calendar)
        if not first or first > decision_date:
            known = event.get('known_notice_publication_date')
            known_usable, _ = next_session(known, event['exchange'], calendar) if known else (None, None)
            if (known_usable and known_usable <= decision_date
                    and event['event_type'] == 'ACTUAL_COMMON_ISSUANCE'):
                return dict(base, status='KNOWN_ISSUANCE_EFFECTIVE_BASIS_REVIEW_PENDING',
                    event_id=event['event_id'], accepted=accepted, excluded=excluded)
            excluded.append(dict(event_id=event['event_id'], reason='NOT_YET_AVAILABLE')); continue
        if event['event_type'] != 'ACTUAL_COMMON_ISSUANCE':
            excluded.append(dict(event_id=event['event_id'], reason='PLAN_OR_CASH_EVENT_NOT_SHARE_ISSUANCE')); continue
        if event.get('validation_status') != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED':
            return dict(base, status='UNREVIEWED_SHARE_EVENT')
        lo, hi = event.get('effective_not_before'), event.get('effective_not_after')
        if not lo or not hi or lo > hi:
            return dict(base, status='EFFECTIVE_DATE_EVIDENCE_MISSING')
        date.fromisoformat(lo); date.fromisoformat(hi)
        if hi <= snapshot['balance_date']:
            excluded.append(dict(event_id=event['event_id'], reason='ALREADY_REFLECTED_IN_INITIAL_SNAPSHOT')); continue
        if decision_date < lo:
            excluded.append(dict(event_id=event['event_id'], reason='NOT_YET_EFFECTIVE')); continue
        if lo <= decision_date < hi:
            return dict(base, status='EFFECTIVE_DATE_BASIS_UNRESOLVED', event_id=event['event_id'],
                effective_date_bounds=[lo, hi], accepted=accepted, excluded=excluded)
        if (type(event.get('new_shares')) is not int or event['new_shares'] <= 0
                or event['before_common_shares'] != shares
                or event['after_common_shares'] != shares + event['new_shares']):
            return dict(base, status='SHARE_ROLLFORWARD_FAILED')
        shares = event['after_common_shares']; accepted.append(event)
    return dict(base, value=shares, status='COMMON_SHARE_REFERENCE_SELECTED',
        accepted=accepted, excluded=excluded, event_coverage='REVIEWED_DECLARATIONS_ONLY_NOT_EXHAUSTIVE')
