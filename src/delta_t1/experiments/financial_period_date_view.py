"""Monthly date-as-of period EPS references; no TTM, identity or research promotion."""
from calendar import monthrange
from datetime import date

from ..features.financial_vas_reference import calculate_disclosed_basic_eps
from ..ingestion.financial_date_pit import next_session, select_as_of
from .financial_quarterly_review import check_quarter_v2, period_identity


def monthly_decisions(years):
    return [date(y,m,monthrange(y,m)[1]).isoformat() for y in years for m in range(1,13)]


def build_date_view(slices, calendar, policy, decisions):
    if (policy.get('precision')!='DATE_ONLY' or policy.get('timestamp_inference_allowed') is not False
            or policy.get('financial_features_allowed') is not False
            or policy.get('availability_rule')!='FIRST_OBSERVED_EXCHANGE_SESSION_STRICTLY_AFTER_PUBLICATION_DATE'
            or not policy.get('owner_approval')):
        raise ValueError('existing approved date-only reference policy required')
    if len(slices)>min(policy['max_documents'],40):raise ValueError('publication slice cap exceeded')
    groups={};names=['eps_adjusted_earnings_numerator','weighted_average_basic_shares']
    for item in slices:
        review,pub=item['review'],item['publication']
        check_quarter_v2(review)
        if pub.get('validation_status')!='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED' or pub.get('precision')!='DATE_ONLY':
            raise ValueError('exact-document explicit publication required')
        usable,status=next_session(pub['publication_date'],item['exchange'],calendar)
        if (usable,status)!=(pub['usable_from_date'],pub['date_pit_status']):
            raise ValueError('publication/calendar overlay differs')
        if not usable:raise ValueError('publication outside observed calendar')
        for fact in review['facts']:
            if fact['symbol']!=pub['symbol'] or fact['provenance']['pdf_sha256']!=pub['pdf_sha256']:
                raise ValueError('publication belongs to a different document/symbol')
            if pub['publication_date']<=fact['period_end']:
                raise ValueError('publication predates period completion')
            key=period_identity(fact)
            if key[-1]=='INSTANT' or fact['field'] not in names:continue
            legacy_fact=dict(fact,item=fact['field'],statement_scope=fact['scope'],accounting_framework=fact['framework'])
            reference=dict(fact=legacy_fact,publication=pub,usable_from_date=usable,date_pit_status=status)
            groups.setdefault(key,{}).setdefault(fact['field'],[]).append(reference)
    rows=[]
    for decision in decisions:
        if date.fromisoformat(decision).isoformat()!=decision:raise ValueError('ISO decision date required')
        for key,fields in sorted(groups.items()):
            chosen={};reason=None
            for name in names:
                if name not in fields:reason='MISSING_REVIEWED_EPS_NOTE_INPUTS';break
                selection=select_as_of(fields[name],decision)
                if selection['selected'] is None:reason=selection['status'];break
                chosen[name]=selection['selected']
            refs=[r for values in chosen.values() for r in values]
            pdfs={r['publication']['pdf_sha256'] for r in refs}
            if reason is None and len(pdfs)!=1:reason='MIXED_OR_AMBIGUOUS_DOCUMENT_VINTAGE_INPUTS'
            months=3 if key[-1]=='QUARTER_STANDALONE' else date.fromisoformat(key[2]).month
            result=(dict(value=None,status=reason) if reason else
                    calculate_disclosed_basic_eps(chosen[names[0]][0]['fact']['value'],
                                                 chosen[names[1]][0]['fact']['value'],months))
            rows.append(dict(decision_date=decision,symbol=key[0],period_start=key[1],period_end=key[2],
                             interval=key[3],months=months,family='DISCLOSED_PERIOD_BASIC_EPS_REFERENCE',
                             value=result['value'],result=result,date_eligible_reference=result['value'] is not None,
                             dependency_ids=sorted({r['fact']['id'] for r in refs}),
                             source_pdf_sha256=sorted(pdfs),usable_from_date=max((r['usable_from_date'] for r in refs),default=None),
                             period_age_days=((date.fromisoformat(decision)-date.fromisoformat(key[2])).days
                                              if result['value'] is not None else None),
                             annualized=False,ttm=False,strict_pit_ready=False,research_ready=False,
                             financial_features_allowed=False,
                             decision_date_basis='CALENDAR_MONTH_END_INFORMATION_REFERENCE_NOT_TRADE_EXECUTION'))
    return rows
