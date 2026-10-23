"""Exact calendar-quarter/YTD review checks, without period or availability inference."""
from calendar import monthrange
from datetime import date
from decimal import Decimal
from ..features.financial_vas_reference import calculate_disclosed_basic_eps


def period_identity(fact):
    year, quarter = fact['year'], fact['quarter']
    if type(year) is not int or type(quarter) is not int or not 1 <= quarter <= 4:
        raise ValueError('explicit calendar year/quarter required')
    end=date(year,quarter*3,monthrange(year,quarter*3)[1]).isoformat()
    interval=fact['interval']
    if interval=='INSTANT':start=None
    elif interval=='QUARTER_STANDALONE':start=date(year,quarter*3-2,1).isoformat()
    elif interval=='YTD':start=date(year,1,1).isoformat()
    else:raise ValueError('unsupported explicit quarter/YTD interval')
    if (fact['period_start'],fact['period_end'])!=(start,end):
        raise ValueError('quarter/YTD period does not match disclosed bounds')
    return fact['symbol'],start,end,interval


def publication_status(candidate):
    catalogue=candidate.get('catalogue_date')
    created=candidate.get('document_creation_date')
    if catalogue and created and date.fromisoformat(catalogue)<date.fromisoformat(created):
        return 'DOCUMENT_POSTDATES_CATALOGUE_REQUIRES_VERSION_EVIDENCE'
    return 'EXACT_DOCUMENT_PUBLICATION_NOT_ACCEPTED'


def check_quarter_v2(review):
    if review.get('version')!='financial-quarter-reference-review-v2' or review.get('fiscal_basis')!='CALENDAR_YEAR':
        raise ValueError('explicit reviewed calendar-quarter contract required')
    values={};groups={};pdfs=set()
    for fact in review['facts']:
        if (fact.get('review_status')!='REVIEWED_REFERENCE_ONLY' or fact.get('scope')!='CONSOLIDATED'
                or fact.get('framework')!='VAS' or fact.get('pit_ready',False) is not False
                or fact.get('available_at') is not None):
            raise ValueError('quarter review cannot accept source semantics or PIT implicitly')
        group=period_identity(fact);key=group+(fact['field'],)
        if key in values:raise ValueError('duplicate quarterly field/period')
        unit='SHARES' if fact['field']=='weighted_average_basic_shares' else 'VND/share' if fact['field']=='vendor_basic_eps' else 'VND'
        if fact['unit']!=unit or type(fact['value']) is bool or not Decimal(fact['value']).is_finite():
            raise ValueError('invalid quarter value/unit')
        values[key]=Decimal(fact['value']);groups.setdefault(group,set()).add(fact['field'])
        pdfs.add(fact['provenance']['pdf_sha256'])
    if len(pdfs)!=1:raise ValueError('quarter review mixes document vintages')
    checks=[]
    for group,fields in sorted(groups.items(),key=lambda x:str(x[0])):
        equations=([('BALANCE','total_assets',['total_liabilities','total_equity']),
                    ('ASSET_SPLIT','total_assets',['current_assets','noncurrent_assets'])]
                   if group[-1]=='INSTANT' else
                   [('GROSS_PROFIT','net_revenue',['cost_of_goods_sold','gross_profit'])])
        for name,left,right in equations:
            missing=sorted(set([left]+right)-fields)
            row=dict(symbol=group[0],period_start=group[1],period_end=group[2],interval=group[3],check=name)
            if missing:
                checks.append(dict(row,status='MISSING_REVIEWED_INPUTS',missing=missing));continue
            difference=values[group+(left,)]-sum(values[group+(field,)] for field in right)
            if difference:raise ValueError('quarter reviewed accounting difference: '+name)
            checks.append(dict(row,status='PASS',difference='0'))
    return checks


def period_eps(review):
    check_quarter_v2(review)
    groups={}
    for fact in review['facts']:
        key=period_identity(fact)
        if key[-1]!='INSTANT':groups.setdefault(key,{})[fact['field']]=fact
    rows=[]
    for key,facts in sorted(groups.items()):
        names=['eps_adjusted_earnings_numerator','weighted_average_basic_shares']
        missing=[name for name in names if name not in facts]
        months=3 if key[-1]=='QUARTER_STANDALONE' else date.fromisoformat(key[2]).month
        result=(dict(value=None,status='MISSING_REVIEWED_EPS_NOTE_INPUTS') if missing else
                calculate_disclosed_basic_eps(facts[names[0]]['value'],facts[names[1]]['value'],months))
        rows.append(dict(symbol=key[0],period_start=key[1],period_end=key[2],interval=key[3],
                         family='EPS',months=months,result=result,value=result['value'],
                         dependency_ids=[facts[n]['id'] for n in names if n in facts],missing_inputs=missing,
                         annualized=False,ttm=False,diluted_eps=None,pit_ready=False,financial_features_allowed=False))
    return rows
