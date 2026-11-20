"""D-ASS-01 verdict composition after S1 evidence verification.

Pure evaluator: source pins/metadata are S1 verification receipts, not raw-file QA.
Explicit fixture mode cannot publish a verdict or activate the legacy builder.
"""
from collections.abc import Mapping
from datetime import date
import re

from delta_t1.m3.universe import stale_after
from .rules_common import load_policy
from .rules_market import evaluate_market, MOMENTUM
from .rules_financial import evaluate_financial

PRIORITY = ('INSUFFICIENT_EVIDENCE', 'CAUTION', 'RESEARCH_FAVORABLE', 'WATCH')


def _mapping(value):
    return value if isinstance(value, Mapping) else {}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _condition(node, states, references):
    """Evaluate policy verdict expressions using verified component outcomes."""
    if 'state' in node:
        return states[node['state']]
    if 'rule_ref' in node:
        return references[node['rule_ref']]
    if 'always' in node:
        return node['always']
    if 'not' in node:
        result = _condition(node['not'], states, references)
        return None if result is None else not result
    for op in ('all', 'any'):
        if op in node:
            values = [_condition(child, states, references) for child in node[op]]
            if op == 'all':
                return False if False in values else None if None in values else True
            return True if True in values else None if None in values else False
    raise ValueError('Unsupported verdict condition')


def _eligibility(context, market_features, financial_features, liquidity,
                 denominator, ratio_validity, policy):
    context = _mapping(context)
    issues = []

    def issue(field, reason):
        issues.append(dict(field=field, reason=reason))

    metadata = _mapping(context.get('metadata'))
    references = _mapping(context.get('metadata_evidence_refs'))
    for field in policy['eligibility']['required_metadata']:
        if metadata.get(field) is not True or not _text(references.get(field)):
            issue(field, 'MISSING_OR_UNVERIFIED_GATE')
    pins = _mapping(context.get('source_pins'))
    for name in policy['eligibility']['required_source_pins']:
        pin = _mapping(pins.get(name))
        expected, actual = pin.get('expected_sha256'), pin.get('actual_sha256')
        valid_hashes = all(isinstance(value, str) and re.fullmatch(r'[0-9a-fA-F]{64}', value)
                           for value in (expected, actual))
        if not (valid_hashes and expected.lower() == actual.lower()
                and pin.get('verified') is True and _text(pin.get('evidence_ref'))):
            issue(name, 'MISSING_OR_MISMATCHED_SOURCE_PIN')

    dates = {}
    for key in ('as_of', 'required_price_session', 'last_price_date',
                'required_market_snapshot_date', 'market_snapshot_date',
                'usable_from_date', 'model_cutoff'):
        value = context.get(key)
        try:
            if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError()
            dates[key] = date.fromisoformat(value)
        except ValueError:
            issue(key, 'MISSING_OR_INVALID_DATE')
    mode = context.get('assessment_context')
    if mode == 'SIMULATED_AS_OF':
        for key, scope_key in (('as_of', 'as_of'), ('required_price_session', 'required_price_session'),
                               ('required_market_snapshot_date', 'market_snapshot_date')):
            if context.get(key) != policy['scope'][scope_key]:
                issue(key, 'SIMULATED_SCOPE_MISMATCH')
    elif mode == 'CURRENT_AS_OF':
        if context.get('monthly_release_schedule_accepted') is not True or not _text(context.get('monthly_release_schedule_ref')):
            issue('monthly_release_schedule', 'ACCEPTED_MONTHLY_SCHEDULE_REQUIRED')
    else:
        issue('assessment_context', 'UNSUPPORTED_CONTEXT')
    for actual, expected in (('last_price_date', 'required_price_session'),
                              ('market_snapshot_date', 'required_market_snapshot_date')):
        if actual in dates and expected in dates and dates[actual] != dates[expected]:
            issue(actual, 'EXPECTED_DATE_MISMATCH')
    if 'as_of' in dates:
        for key, value in dates.items():
            if value > dates['as_of']:
                issue(key, 'FUTURE_EVIDENCE')

    year = context.get('fiscal_year')
    year_valid = type(year) is int and year in policy['scope']['fiscal_years_enriched']
    if not year_valid:
        issue('fiscal_year', 'INVALID_OR_UNSUPPORTED_FISCAL_YEAR')
    for name in ('latest_usable_fiscal_year', 'model_fiscal_year'):
        if type(context.get(name)) is not int or context[name] != year:
            issue(name, 'LATEST_FY_MODEL_REQUIRED_NO_FALLBACK')
    if year_valid and 'as_of' in dates:
        if dates['as_of'] > date.fromisoformat(stale_after(year, policy['scope']['financial_stale_months'])):
            issue('financial_age', 'FINANCIAL_STALE')
    if context.get('market_model') != policy['scope']['market_model']:
        issue('market_model', 'WRONG_MODEL_SOURCE')
    if context.get('financial_model') != policy['scope']['financial_model']:
        issue('financial_model', 'WRONG_MODEL_SOURCE_NO_BASELINE_FALLBACK')

    # Bind evidence to the selected snapshot/FY, not merely to each other.
    for name, cell in [(name, market_features.get(name)) for name in MOMENTUM] + [('liquidity_flag', liquidity)]:
        if _mapping(cell).get('period') != context.get('market_snapshot_date'):
            issue(name, 'MARKET_SCOPE_PERIOD_MISMATCH')
    financial_cells = [('roa', financial_features.get('roa')), ('net_margin', financial_features.get('net_margin')),
                       ('ni_denominator', denominator)]
    if _mapping(denominator).get('value') is not None:
        ni_value = _mapping(denominator).get('value')
        if type(ni_value) in (int, float) and ni_value > 0:
            financial_cells += [('cfo_to_ni', financial_features.get('cfo_to_ni')), ('cfo_ratio_valid', ratio_validity)]
    for name, cell in financial_cells:
        if not year_valid or _mapping(cell).get('period') not in (str(year), 'FY' + str(year)):
            issue(name, 'FINANCIAL_SCOPE_PERIOD_MISMATCH')
    return issues


def evaluate_verdict(market_features, financial_features, *, liquidity, denominator,
                     ratio_validity, context, policy=None, fixture_only=False, peers=None):
    """Return four-way classification; Peers are reserved for G4 explanation only.

    context carries dates, selected/latest/model FY, model source identities, all
    required_metadata booleans plus metadata_evidence_refs, and source_pins with
    expected_sha256/actual_sha256/verified/evidence_ref. Upstream S1 must establish
    these from real sources. fixture_only=True is explicit and never publishable.
    """
    policy = load_policy(policy)
    if tuple(policy['verdicts']['priority']) != PRIORITY or policy['verdicts']['first_match_wins'] is not True:
        raise ValueError('D-ASS-01 requires fixed first-match verdict priority')
    if type(fixture_only) is not bool:
        raise ValueError('fixture_only must be a boolean')
    market = evaluate_market(market_features, liquidity=liquidity, policy=policy)
    financial = evaluate_financial(financial_features, denominator=denominator,
                                  ratio_validity=ratio_validity, policy=policy)
    issues = _eligibility(context, market_features, financial_features, liquidity,
                          denominator, ratio_validity, policy)
    for component in (market, financial):
        issues.extend(dict(item, component=component['component']) for item in component['eligibility_issues'])
    activation_issues = []
    if not fixture_only:
        if policy.get('runtime_enabled') is not True or policy['activation']['do_not_rebuild_or_publish_real_verdicts'] is not False:
            activation_issues.append('RUNTIME_NOT_ENABLED')
        for key in ('current_builder_reads_policy', 'activation_enforcement_verified'):
            if policy['integration'].get(key) is not True:
                activation_issues.append(key.upper())
        gates = _mapping(_mapping(context).get('activation_gates'))
        for gate in policy['activation']['required_gates']:
            receipt = _mapping(gates.get(gate))
            if receipt.get('status') != 'PASS' or not _text(receipt.get('evidence_ref')):
                activation_issues.append(gate)
    issues.extend(dict(field='activation', reason=reason) for reason in activation_issues)
    major = market['major_warning'] is True or financial['major_warning'] is True
    references = {'market.favorable': market['market_condition'] == 'FAVORABLE',
                  'market.adverse': market['market_condition'] == 'ADVERSE',
                  'financial.favorable': financial['financial_favorable'],
                  'financial.profitability_adverse': financial['profitability_adverse'],
                  'warnings.major': major, 'warnings.watch': financial['watch_warning']}
    states = {'eligibility_pass': not issues}
    matches = {code: _condition(policy['verdicts']['conditions'][code], states, references) for code in PRIORITY}
    verdict = next(code for code in PRIORITY if matches[code] is True)
    publishable = not fixture_only and not activation_issues
    return dict(policy_id=policy['policy_id'], policy_version=policy['version'],
                verdict=verdict, label_vi=policy['verdicts']['labels_vi'][verdict],
                eligibility_pass=not issues, eligibility_issues=issues,
                verdict_matches=matches, priority=list(PRIORITY), market=market, financial=financial,
                fixture_only=fixture_only, publishable=publishable, verdict_issued=publishable,
                assessment_context=_mapping(context).get('assessment_context'),
                as_of=_mapping(context).get('as_of'), peers_used_for_verdict=False)
