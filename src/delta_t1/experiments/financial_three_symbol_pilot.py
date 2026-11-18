"""Bounded offline annual pilot from pinned visual reviews, never OCR auto-acceptance."""
import json
import re
from datetime import date, datetime
from decimal import Decimal, localcontext
from pathlib import Path
from urllib.parse import unquote

from ..features.financial_reference import calculate, calculate_f_score
from ..features.financial_ttm_reference import reported_ttm
from ..features.financial_vas_reference import (
    REGISTRY, calculate_disclosed_basic_eps, calculate_period_eps,
    calculate_reported_valuation, calculate_vas_f_score, calculate_vas_m_score,
)
from ..ingestion.cafef_financial import encoded, immutable_write
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.sources.cafef import classify_cafef_page_row, map_trade_history_row, price_band_row_status
from .financial_ttm_valuation import file_hash

METHOD = 'HUMAN_VISUAL_EXACT_RENDERED_PDF_PAGE_NOT_AUTOMATIC_OCR_ACCEPTANCE'
GATES = dict(financial_features_allowed=False, research_ready=False, full_universe_allowed=False)
CALCULATION_SOURCES = {
    'src/delta_t1/experiments/financial_three_symbol_pilot.py',
    'src/delta_t1/features/financial_vas_reference.py', 'src/delta_t1/features/financial_reference.py',
    'src/delta_t1/features/financial_ttm_reference.py', 'src/delta_t1/ingestion/sources/cafef.py',
    'src/delta_t1/features/registry.py', 'src/delta_t1/ingestion/financial_pilot_readiness.py',
}


def pinned(root, relative, expected):
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or file_hash(path) != expected:
        raise ValueError('input outside workspace or checksum mismatch: ' + str(relative))
    return path


def next_session(calendar, exchange, publication):
    date.fromisoformat(publication)
    return min((r['trade_date'] for r in calendar if r['exchange'] == exchange
                and r['is_open'] is True and r['trade_date'] > publication), default=None)


def eligible(usable, decision):
    return bool(usable and usable <= decision)


def numeric(value):
    if value is None or type(value) is bool:
        raise ValueError('missing or boolean value')
    n = Decimal(str(value))
    if not n.is_finite():
        raise ValueError('nonfinite value')
    return n


def annual_math(values, eps_basis, no_dilution):
    """Caller supplies reviewed semantic mappings; unknowns stay absent."""
    v = {k: str(numeric(x)) for k, x in values.items()}
    derived = []
    for offset in [0, -1]:
        debt_keys = [('noncurrent_loans_and_finance_leases', offset),
                     ('current_portion_original_long_term_debt', offset)]
        if all(k in v for k in debt_keys):
            v['long_term_debt_including_current_portion', offset] = str(sum(numeric(v[k]) for k in debt_keys))
            derived.append(dict(field='long_term_debt_including_current_portion', offset=offset,
                                inputs=[list(k) for k in debt_keys], formula='sum'))
    current = {f: x for (f, o), x in v.items() if o == 0}
    if all(f in current for f in ['profit_before_tax', 'interest_expense']):
        current['document_reconciled_ebit'] = str(numeric(current['profit_before_tax']) + numeric(current['interest_expense']))
        derived.append(dict(field='document_reconciled_ebit', offset=0,
                            inputs=[['profit_before_tax', 0], ['interest_expense', 0]], formula='sum'))
    numerator_key = ('eps_adjusted_earnings_numerator' if eps_basis == 'RESERVE_DEDUCTED_REPORTED_NOTE'
                     else 'reported_eps_numerator')
    eps = calculate_disclosed_basic_eps(current.get(numerator_key), current.get('weighted_average_basic_shares'), 12)
    eps['basis'] = eps_basis
    eps['reported_numerator_field'] = numerator_key
    if no_dilution:
        eps['dilution_reference'] = calculate_period_eps(current.get(numerator_key),
            current.get('weighted_average_basic_shares'), current.get('weighted_average_basic_shares'), 12)
    else:
        eps['dilution_reference'] = dict(value=None, status='DILUTION_NOT_VERIFIED')
    qa = []
    for offset in [0, -1]:
        if all((f, offset) in v for f in ['total_assets', 'total_equity', 'total_liabilities']):
            difference = numeric(v['total_assets', offset]) - numeric(v['total_equity', offset]) - numeric(v['total_liabilities', offset])
            qa.append(dict(check='assets_equal_liabilities_plus_equity', offset=offset,
                           difference=str(difference), passed=difference == 0))
        if all((f, offset) in v for f in ['parent_net_profit', 'eps_reserve_deduction', 'eps_adjusted_earnings_numerator']):
            difference = numeric(v['parent_net_profit', offset]) - numeric(v['eps_reserve_deduction', offset]) - numeric(v['eps_adjusted_earnings_numerator', offset])
            qa.append(dict(check='reported_eps_profit_minus_reserve', offset=offset,
                           difference=str(difference), passed=difference == 0))
    if eps['value'] is not None and 'vendor_basic_eps' in current:
        qa.append(dict(check='rounded_basic_eps_equals_disclosed_eps', passed=numeric(eps['rounded']) == numeric(current['vendor_basic_eps'])))
    if any(q['passed'] is not True for q in qa):
        raise ValueError('annual arithmetic QA failed: ' + json.dumps(qa))
    return dict(f_vas=calculate_vas_f_score(v), f_strict=calculate_f_score(v),
                m_sensitivity=calculate_vas_m_score(v, 'GROSS_SHORT_TERM_TRADE'),
                m_strict=dict(value=None, status='RECEIVABLES_AND_ORDINARY_EARNINGS_MAPPING_UNRESOLVED'),
                z=calculate('Z_SCORE', current), eps=eps, qa=qa, derivations=derived)


def publication_for(case, document, publications, root):
    exact = [p for p in publications if p['pdf_sha256'] == document['pdf_sha256']
             and p['symbol'] == case['symbol'] and p['year'] == 2025]
    if case['publication_status'] == 'ISSUER_EXPLICIT_PUBLICATION_IN_SAME_PDF':
        if len(exact) != 1 or exact[0]['publication_date'] != case['publication_date']:
            raise ValueError('exact publication mismatch')
        evidence = exact[0]['evidence']
        pinned(root, evidence['image_path'], evidence['image_sha256'])
        return exact[0]
    if case['publication_status'] != 'MIRRORED_EXCHANGE_DATE_REFERENCE_EXACT_ATTACHMENT_BYTE_IDENTICAL':
        raise ValueError('unsupported publication reference')
    mirror = case['publication_mirror']
    run = pinned(root, mirror['run'] + '/manifest.json', mirror['manifest_sha256']).parent
    verify_inventory(run)
    html = pinned(root, mirror['html_path'], mirror['html_sha256']).read_text(encoding='utf8')
    pinned(root, mirror['attachment_path'], mirror['attachment_sha256'])
    if (mirror['attachment_sha256'] != document['pdf_sha256']
            or mirror['publication_date'] != case['publication_date']
            or mirror['date_literal'] not in html or mirror['attachment_url'] not in html):
        raise ValueError('mirror date / exact attachment mismatch')
    return dict(publication_date=case['publication_date'], precision='DATE_ONLY',
                validation_status=mirror['status'], evidence=mirror, primary_publication_verified=False)


def reviewed_cell(root, case, documents, field, offset, value, run, stem, page):
    if type(offset) is not int or offset not in [0, -1, -2]:
        raise ValueError('invalid comparative offset')
    document = documents[run, stem]
    if not any(a <= page <= b for a, b in document['ranges']):
        raise ValueError('page outside extracted range')
    proof = case['page_reviews'][f'{run}/{stem}/{page}']
    if proof['validation_status'] != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED' or proof['review_method'] != METHOD:
        raise ValueError('unreviewed cell')
    image = pinned(root, proof['image_path'], proof['image_sha256'])
    if image.parent != (root / run / stem).resolve() or int(image.stem.split('-')[-1]) != page:
        raise ValueError('review image mapped to wrong page')
    ocr = json.loads(image.with_name(image.stem + '.ocr.json').read_bytes())
    if ocr['image_sha256'] != proof['image_sha256']:
        raise ValueError('OCR attached to another image')
    tokens = {re.sub(r'[^0-9]', '', w['text']) for line in ocr.get('lines', []) for w in line.get('words', [])}
    ocr_match = str(numeric(value)) in tokens
    return dict(symbol=case['symbol'], field=field, offset=offset, year=2025 + offset,
                value=str(numeric(value)), unit='SHARES' if field in ['common_shares', 'weighted_average_basic_shares'] else
                'VND_PER_SHARE' if field == 'vendor_basic_eps' else
                'BINARY_REVIEW_INDICATOR' if field == 'parent_common_equity_issuance_verified' else 'VND',
                statement_scope='CONSOLIDATED', accounting_framework='VAS',
                period_start=f'{2025+offset}-01-01', period_end=f'{2025+offset}-12-31',
                evidence_status='VISUALLY_REVIEWED_REFERENCE_FACT', pdf_path=document['pdf_path'],
                pdf_sha256=document['pdf_sha256'], pdf_page=page, image_path=proof['image_path'],
                image_sha256=proof['image_sha256'], source_report_year=document['report_year'],
                ocr_numeric_token_match=ocr_match, ocr_is_acceptance_evidence=False,
                revision_policy='KEEP_AT_SOURCE_VINTAGE_NEVER_BACKFILL', production_accepted=False)


def verify_price_references(root, run, expected):
    folder = pinned(root, run + '/manifest.json', expected).parent
    verify_inventory(folder)
    quotes = json.loads((folder / 'quotes.json').read_bytes())
    if len(quotes) > 2:
        raise ValueError('quote budget exceeded')
    for q in quotes:
        evidence = q['evidence']
        if (q['ticker'] not in ['VNM', 'PVS'] or q.get('canonical_market_accepted') is not False
                or q.get('financial_features_allowed') is not False or q['trade_date'] != '2026-08-28'
                or q['available_at'] != '2026-08-28T17:00:00+07:00'
                or q['adjustment_basis'] != 'RAW_CLOSE' or not 1 <= evidence['page'] <= 2):
            raise ValueError('reference quote scope changed')
        body = pinned(root, folder / evidence['path'], evidence['sha256'])
        payload = json.loads(body.read_bytes())
        raw = payload['Data'][evidence['row_index']]
        row = map_trade_history_row(raw, q['ticker'], q['exchange'])
        if (payload['Success'] is not True or classify_cafef_page_row(raw['TradeDate'], evidence['page'], evidence['row_index']) != 'HISTORICAL'
                or price_band_row_status(row) != 'VALID' or row['trade_date'] != q['trade_date']
                or numeric(row['cafef_close_price']) != numeric(q['raw_close'])):
            raise ValueError('quote does not match exact raw source')
    return quotes


def review_interims(root, config, documents, calendar, decision_date):
    reviews = config.get('interim_reviews', [])
    if len(reviews) > 5:
        raise ValueError('interim review budget exceeded')
    output = []
    for r in reviews:
        document = documents[r['ocr_run'], r['pdf_stem']]
        proof = r['evidence']
        if proof['validation_status'] != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED':
            raise ValueError('interim visual review required')
        image = pinned(root, proof['image_path'], proof['image_sha256'])
        if image.parent != (root / r['ocr_run'] / r['pdf_stem']).resolve() or int(image.stem.split('-')[-1]) != proof['pdf_page']:
            raise ValueError('interim image mismatch')
        publication = r['publication_evidence']
        folder = pinned(root, publication['run'] + '/manifest.json', publication['manifest_sha256']).parent
        verify_inventory(folder)
        html = pinned(root, publication['html_path'], publication['html_sha256']).read_text(encoding='utf8')
        if publication['date_literal'] not in html or unquote(publication['attachment_literal']) not in unquote(html):
            raise ValueError('interim publication date or attachment mismatch')
        inventory = json.loads((folder / 'inventory.json').read_bytes())['requests']
        matching = [x for x in inventory if x.get('sha256') == document['pdf_sha256'] and x.get('kind') == 'pdf']
        if len(matching) != 1 or unquote(publication['attachment_literal']) not in unquote(matching[0]['url']):
            raise ValueError('interim publication points to other PDF')
        usable = next_session(calendar, r['exchange'], publication['publication_date'])
        start, end = map(date.fromisoformat, [r['period_start'], r['period_end']])
        if start != date(end.year, 1, 1) or end != date(end.year, 6, 30) or publication['publication_date'] <= r['source_period_end']:
            raise ValueError('interim period or release precedes report end')
        if not eligible(usable, decision_date):
            raise ValueError('future reviewed interim cannot enter calculations')
        if numeric(r['parent_profit']) - numeric(r['reported_deduction']) != numeric(r['reported_eps_numerator']):
            raise ValueError('interim numerator bridge failed')
        eps = calculate_disclosed_basic_eps(r['reported_eps_numerator'], r['weighted_basic_shares'], 6)
        printed = r['printed_eps_evidence']
        pinned(root, printed['image_path'], printed['image_sha256'])
        if numeric(eps['rounded']) != numeric(r['disclosed_basic_eps']):
            raise ValueError('interim EPS does not round to printed value')
        output.append(dict(r, pdf_path=document['pdf_path'], pdf_sha256=document['pdf_sha256'],
            usable_from_date=usable, eps=eps, revision_policy='COMPARATIVE_KNOWN_AT_CURRENT_SOURCE_RELEASE_ONLY', **GATES))
    return output


def optional_ttm(root, case, values, interims, usable, day, documents):
    """Same-parent/share-basis bridge reviewed explicitly, not inferred from ticker."""
    bridge = case.get('ttm_bridge')
    if not bridge:
        return dict(value=None, status='TTM_BRIDGE_NOT_VERIFIED', **GATES)
    if bridge['validation_status'] != 'VALUE_UNIT_PERIOD_VISUALLY_VERIFIED' or bridge['scope_status'] != 'SAME_PARENT_COMMON_EARNINGS_SCOPE_REVIEWED':
        raise ValueError('TTM scope bridge unreviewed')
    if not 2 <= len(bridge['evidence']) <= 4:
        raise ValueError('bounded TTM PDF/page proofs required')
    for proof in bridge['evidence']:
        image = pinned(root, proof['image_path'], proof['image_sha256'])
        pinned(root, proof['pdf_path'], proof['pdf_sha256'])
        document = documents[proof['ocr_run'], proof['pdf_stem']]
        if (document['pdf_sha256'] != proof['pdf_sha256']
                or image.parent != (root / proof['ocr_run'] / proof['pdf_stem']).resolve()
                or int(image.stem.split('-')[-1]) != proof['pdf_page']):
            raise ValueError('TTM bridge PDF/page mismatch')
    selected = {year: [r for r in interims if r['symbol'] == case['symbol'] and r['period_end'] == f'{year}-06-30'
                       and r['source_period_end'] == '2026-06-30'] for year in [2025, 2026]}
    if any(len(v) != 1 for v in selected.values()):
        raise ValueError('exact current-release YTD comparisons required')
    prior, current = selected[2025][0], selected[2026][0]
    old = bridge['old_h125_diagnostic']
    for key in ['parent_profit', 'reported_deduction', 'reported_eps_numerator', 'weighted_basic_shares']:
        if numeric(old[key]) != numeric(prior[key]):
            return dict(value=None, status='PRIOR_EARNINGS_OR_SHARE_BASIS_CHANGED', **GATES)
    weighted = [values.get(('weighted_average_basic_shares', 0)), prior['weighted_basic_shares'], current['weighted_basic_shares']]
    if len(set(weighted)) != 1:
        return dict(value=None, status='SHARE_EVENT_BRIDGE_REQUIRED', **GATES)
    basis = bridge['share_basis_id']
    base = dict(symbol=case['symbol'], numerator_unit='VND', share_unit='SHARES', statement_scope='CONSOLIDATED',
                accounting_framework='VAS', validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',
                share_basis_id=basis, deduction_policy='ACTUAL_REPORTED_DEDUCTION')
    periods = dict(fy=dict(base, period_start='2025-01-01', period_end='2025-12-31', usable_from_date=usable,
        reported_eps_numerator=values['eps_adjusted_earnings_numerator', 0], weighted_basic_shares=weighted[0],
        parent_profit=values['parent_net_profit', 0], reported_deduction=values['eps_reserve_deduction', 0]))
    for key, r in [('current_ytd', current), ('prior_ytd', prior)]:
        periods[key] = dict(base, **{k:r[k] for k in ['period_start', 'period_end', 'usable_from_date',
            'reported_eps_numerator', 'weighted_basic_shares', 'parent_profit', 'reported_deduction']})
    result = reported_ttm(periods, dict(parent_earnings_unchanged=True, h1_parent_profit_comparison_equal=True,
                                      usable_from_date=current['usable_from_date']), day)
    return dict(result, periods=periods, bridge=bridge, publication_quality='MIRRORED_EXCHANGE_DATE_REFERENCE_PRIMARY_PENDING')


def export(root, config_path, output):
    root = Path(root).resolve()
    config = json.loads((root / config_path).read_bytes())
    if (config['year'] != 2025 or config['review_method'] != METHOD
            or config.get('unit') != 'VND' or config.get('statement_scope') != 'CONSOLIDATED'
            or config.get('accounting_framework') != 'VAS'
            or any(config.get(k) is not False for k in GATES)
            or not 1 <= len(config['cases']) <= 3
            or len({c['symbol'] for c in config['cases']}) != len(config['cases'])
            or not {c['symbol'] for c in config['cases']} <= {'VNM', 'PVS', 'ACV'}):
        raise ValueError('bounded consolidated VAS reference pilot only')
    decision = datetime.fromisoformat(config['decision_at'])
    if decision.utcoffset() is None:
        raise ValueError('decision timezone required')
    if set(config.get('calculation_source_sha256', {})) != CALCULATION_SOURCES:
        raise ValueError('calculation source pins required')
    day = decision.date().isoformat()
    policy = json.loads(pinned(root, config['date_policy_path'], config['date_policy_sha256']).read_bytes())
    if policy['timestamp_inference_allowed'] is not False or policy['availability_rule'] != 'FIRST_OBSERVED_EXCHANGE_SESSION_STRICTLY_AFTER_PUBLICATION_DATE':
        raise ValueError('date policy changed')
    for path, expected in config.get('calculation_source_sha256', {}).items():
        pinned(root, path, expected)
    calendar = [json.loads(l) for l in pinned(root, config['calendar_path'], config['calendar_sha256']).read_text().splitlines()]
    if day > max(r['trade_date'] for r in calendar):
        raise ValueError('decision beyond observed calendar')
    pub_run = pinned(root, config['publication_review_run'] + '/manifest.json', config['publication_review_manifest_sha256']).parent
    verify_inventory(pub_run)
    publications = json.loads((pub_run / 'publications.json').read_bytes())['documents']
    documents = {}
    for run, expected in config['ocr_manifest_sha256'].items():
        folder = pinned(root, run + '/manifest.json', expected).parent
        verify_inventory(folder)
        for d in json.loads((folder / 'index.json').read_bytes())['documents']:
            pinned(root, d['pdf_path'], d['pdf_sha256'])
            key = (run, Path(d['pdf_path']).stem)
            if key not in documents:
                year = 2026 if '-2026' in key[1] else 2025 if '-2025' in key[1] else 2024
                documents[key] = dict(d, ranges=[], report_year=year)
            documents[key]['ranges'].append((d['first_page'], d['last_page']))
    symbols = {c['symbol'] for c in config['cases']}
    price_rows = []
    with pinned(root, config['price_path'], config['price_sha256']).open(encoding='utf8') as handle:
        for line in handle:
            r = json.loads(line)
            if r['ticker'] in symbols and r['trade_date'] == day:
                price_rows.append(r)
    if config.get('price_reference_run'):
        price_rows.extend(verify_price_references(root, config['price_reference_run'], config['price_reference_manifest_sha256']))
    interims = review_interims(root, config, documents, calendar, day)
    facts, results = [], []
    for case in config['cases']:
        if not 1 <= len(case['cells']) <= 40 or len(case.get('supplemental_cells', [])) > 8:
            raise ValueError('review cell budget exceeded')
        case_facts = []
        for field, page, pair in case['cells']:
            if len(pair) != 2:
                raise ValueError('exact current/comparative pair required')
            for offset, value in zip([0, -1], pair):
                if value is not None:
                    case_facts.append(reviewed_cell(root, case, documents, field, offset, value,
                                      case['ocr_run'], case['pdf_stem'], page))
        for s in case.get('supplemental_cells', []):
            case_facts.append(reviewed_cell(root, case, documents, s['field'], s['offset'], s['value'],
                                           s['ocr_run'], s['pdf_stem'], s['page']))
        if len({(f['field'], f['offset']) for f in case_facts}) != len(case_facts):
            raise ValueError('duplicate or competing facts; no priority')
        publication = publication_for(case, documents[case['ocr_run'], case['pdf_stem']], publications, root)
        usable = next_session(calendar, case['exchange'], publication['publication_date'])
        if not eligible(usable, day):
            raise ValueError('annual report not yet available at decision')
        for f in case_facts:
            exact = [p for p in publications if p['pdf_sha256'] == f['pdf_sha256']]
            f['publication_date'] = publication['publication_date'] if f['source_report_year'] == 2025 else (exact[0]['publication_date'] if len(exact) == 1 else None)
            f['usable_from_date'] = next_session(calendar, case['exchange'], f['publication_date']) if f['publication_date'] else None
            f['pit_status'] = 'DATE_REFERENCE_USABLE' if eligible(f['usable_from_date'], day) else 'AUXILIARY_PUBLICATION_UNVERIFIED'
            if f['publication_date'] and not eligible(f['usable_from_date'], day):
                raise ValueError('future auxiliary source')
        no_dilution = case['dilution']['status'] == 'EXPLICIT_NO_POTENTIAL_DILUTIVE_COMMON_SHARES'
        if no_dilution:
            proof = case['page_reviews'][f"{case['ocr_run']}/{case['pdf_stem']}/{case['dilution']['page']}"]
            pinned(root, proof['image_path'], proof['image_sha256'])
        elif case['dilution']['status'] != 'NOT_YET_VERIFIED':
            raise ValueError('undeclared dilution basis')
        if case['eps_basis'] not in ['RESERVE_DEDUCTED_REPORTED_NOTE', 'REPORTED_UNESTIMATED_RESERVE_NOT_NORMALIZED']:
            raise ValueError('undeclared reported EPS basis')
        values = {(f['field'], f['offset']): f['value'] for f in case_facts}
        maths = annual_math(values, case['eps_basis'], no_dilution)
        ttm = optional_ttm(root, case, values, interims, usable, day, documents)
        price = [r for r in price_rows if r['ticker'] == case['symbol'] and r['exchange'] == case['exchange']]
        if len(price) > 1 or (price and (datetime.fromisoformat(price[0]['available_at']) > decision or numeric(price[0]['raw_close']) <= 0)):
            raise ValueError('ambiguous / unavailable / nonpositive raw price')
        equity = str(numeric(values['total_equity', 0]) - numeric(values['noncontrolling_equity', 0]))
        valuation = calculate_reported_valuation(price[0]['raw_close'], maths['eps']['value'], equity, values.get(('common_shares', 0))) if price else dict(
            pe=None, pb=None, bvps=None, status='NO_EXACT_DECISION_DATE_RAW_PRICE', **GATES)
        valuation.update(basis='RAW_CLOSE_OVER_ANNUAL_2025_EPS_AND_2025_REPORTED_COMMON_SHARE_BOOK_SNAPSHOT',
                         equity_date='2025-12-31', strict_current_pe=None, strict_current_pb=None,
                         current_event_adjustment_verified=False, annual_pe_not_ttm=True,
                         parent_reported_equity=equity, reported_common_shares=values.get(('common_shares', 0)))
        with localcontext() as context:
            context.prec = 36
            ttm_pe = str(numeric(price[0]['raw_close']) / numeric(ttm['value'])) if price and ttm['value'] and numeric(ttm['value']) > 0 else None
        metrics = dict(F_SCORE=maths['f_vas']['value'], M_SCORE=maths['m_sensitivity']['value'],
                       Z_SCORE=maths['z']['value'].get('em_z_double_prime_reference') if maths['z']['value'] else None,
                       EPS_RECOMPUTE=maths['eps']['value'], PE=valuation['pe'], PB=valuation['pb'])
        results.append(dict(symbol=case['symbol'], exchange=case['exchange'], year=2025,
            decision_at=config['decision_at'], metrics=metrics, annual_math=maths, valuation=valuation, ttm=ttm,
            ttm_pe=ttm_pe,
            publication=publication, usable_from_date=usable, price=price[0] if price else None,
            historical_identity_status='PROVISIONAL_NOT_VERIFIED',
            all_auxiliary_publications_verified=all(f['pit_status'] == 'DATE_REFERENCE_USABLE' for f in case_facts),
            reference_metric_families_with_arithmetic=sum(v is not None for v in metrics.values()),
            production_metric_families_accepted=0, fact_count=len(case_facts), warnings=case['warnings'], **GATES))
        facts.extend(case_facts)
    result = dict(version=config['version'], stage_status='ANNUAL_REFERENCE_PILOT_COMPLETE_ACCEPTANCE_PARTIAL',
        results=results, reviewed_fact_count=len(facts), interim_reviews=interims,
        ttm_readiness=config.get('ttm_readiness', []), production_review_status='MANUAL_REVIEW_REQUIRED',
        classification_thresholds=None, feature_registry=[vars(REGISTRY.get(n)) for n in REGISTRY.names()],
        remaining=['Interim EPS numerator/share-basis bridges for TTM', 'Complete corporate-event coverage',
                   'VNM original long-term current debt portion', 'Primary VNM publication and auxiliary dates',
                   'Strict ordinary-income/receivables mappings', 'Historical identity and bounded-scale acceptance'], **GATES)
    out = (root / output).resolve()
    if not out.is_relative_to(root / 'data'):
        raise ValueError('output must be under data')
    out.mkdir(parents=True, exist_ok=False)
    for name, data in [('results.json', encoded(result)), ('facts.json', encoded(facts)),
                       ('config.json', encoded(config)), ('runner.py', Path(__file__).read_bytes())]:
        immutable_write(out / name, data)
    for path in config.get('calculation_source_sha256', {}):
        immutable_write(out / ('source_' + Path(path).name), (root / path).read_bytes())
    immutable_write(out / 'manifest.json', encoded(dict(files={p.name: file_hash(p) for p in out.iterdir() if p.is_file()})))
    return result
