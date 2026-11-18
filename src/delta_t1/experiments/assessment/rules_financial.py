"""R2-13: financial profitability/cash-flow components under D-ASS-01.

NI is operational denominator evidence, not a nineteenth scoring feature. Cells and
metadata are verified by S1 upstream; this module does not certify raw sources or
activate/rebuild the current Assessment builder.
"""
from collections.abc import Mapping
from .rules_common import load_policy, read_evidence, evaluate_expression, rule_result

MANDATORY = ('roa','net_margin')
WATCH_FEATURES = ('gross_margin','current_ratio','revenue_growth')


def _derived_qualifier(source, name, value):
    return dict(source,metadata=name,value=value if source['usable'] else None,
                derived_from='ni_denominator')


def evaluate_financial(features, *, denominator, ratio_validity, policy=None):
    policy = load_policy(policy)
    if not isinstance(features,Mapping):
        raise ValueError('Financial features must map to verified evidence cells')
    extra = set(features) - set(policy['features']['financial'])
    if extra:
        raise ValueError('Non-whitelisted financial features: ' + ', '.join(sorted(extra)))
    # Validate direct signals; operational qualifiers may not become score features.
    def validate_expression(node):
        if 'feature' in node and node['feature'] not in (*MANDATORY,'cfo_to_ni',*WATCH_FEATURES):
            raise ValueError('Unsupported direct financial signal')
        if 'metadata' in node and node['metadata'] not in ('ni_denominator_sign','ni_denominator_observed','cfo_ratio_valid'):
            raise ValueError('Unsupported financial qualifier')
        if 'rule_ref' in node and node['rule_ref'] not in ('financial.cash_positive','financial.cash_negative'):
            raise ValueError('Unsupported financial rule reference')
        for key in ('all','any'):
            for child in node.get(key,[]):validate_expression(child)
    for name in ('cash_positive','cash_negative','favorable','profitability_adverse'):
        validate_expression(policy['rules']['financial'][name])
    watch_expressions = policy['rules']['warnings']['watch']['any']
    if len(watch_expressions) != 3 or {e.get('feature') for e in watch_expressions} != set(WATCH_FEATURES):
        raise ValueError('Policy must contain one watch check per financial watch feature')
    for expression in watch_expressions:validate_expression(expression)
    used = (*MANDATORY,'cfo_to_ni',*WATCH_FEATURES)
    cells = {name:read_evidence(name,features.get(name),rule_id='FINANCIAL_INPUT',policy=policy) for name in used}
    ni = read_evidence('ni_denominator',denominator,rule_id='CFO_DENOMINATOR',policy=policy,as_metadata=True)
    ratio = read_evidence('cfo_ratio_valid',ratio_validity,rule_id='CFO_RATIO_VALIDITY',policy=policy,
                          categorical_values=(True,False))
    issues, optional_issues = [], []
    for name in MANDATORY:
        if not cells[name]['usable']:
            issues.append(dict(field=name,status=cells[name]['status'],reason=cells[name]['validation_status']))
    core_ready = all(cells[name]['usable'] for name in MANDATORY)
    period = cells['roa']['period'] if core_ready else None
    if core_ready and cells['roa']['period'] != cells['net_margin']['period']:
        issues.append(dict(field='financial_profitability',status='CONFLICT',reason='FINANCIAL_PERIOD_MISMATCH'))
        core_ready = False; period = None
    if ni['usable'] and period is not None and ni['period'] != period:
        ni.update(usable=False,validation_status='DENOMINATOR_PERIOD_MISMATCH')
    if not ni['usable']:
        issues.append(dict(field='ni_denominator',status=ni['status'],reason=ni['validation_status']))
    ni_sign = None if not ni['usable'] else 'POSITIVE' if ni['value'] > 0 else 'NEGATIVE' if ni['value'] < 0 else 'ZERO'
    positive_ni = ni_sign == 'POSITIVE'
    cfo_period = period if period is not None else ni['period'] if ni['usable'] else None
    for name in ('cfo_to_ni',*WATCH_FEATURES):
        reference = cfo_period if name == 'cfo_to_ni' else period
        if cells[name]['usable'] and reference is not None and cells[name]['period'] != reference:
            cells[name].update(usable=False,validation_status='FINANCIAL_PERIOD_MISMATCH')
    if ratio['usable'] and cfo_period is not None and ratio['period'] != cfo_period:
        ratio.update(usable=False,validation_status='RATIO_VALIDITY_PERIOD_MISMATCH')
    cfo_ready = bool(positive_ni and cells['cfo_to_ni']['usable'] and ratio['usable'] and ratio['value'] is True)
    if positive_ni:
        if not cells['cfo_to_ni']['usable']:
            issues.append(dict(field='cfo_to_ni',status=cells['cfo_to_ni']['status'],reason=cells['cfo_to_ni']['validation_status']))
        if not ratio['usable'] or ratio['value'] is not True:
            issues.append(dict(field='cfo_ratio_valid',status=ratio['status'],
                               reason=ratio['validation_status'] if not ratio['usable'] else 'INVALID_CFO_RATIO'))
    metadata = dict(ni_denominator_sign=_derived_qualifier(ni,'ni_denominator_sign',ni_sign),
                    ni_denominator_observed=_derived_qualifier(ni,'ni_denominator_observed',ni['is_observed']),
                    cfo_ratio_valid=ratio)
    profitability_adverse = evaluate_expression(policy['rules']['financial']['profitability_adverse'],cells) if core_ready else None
    if cfo_ready:
        cash_positive = evaluate_expression(policy['rules']['financial']['cash_positive'],cells,metadata=metadata)
        cash_negative = evaluate_expression(policy['rules']['financial']['cash_negative'],cells,metadata=metadata)
        cash_sign = 'POSITIVE' if cash_positive else 'NEGATIVE' if cash_negative else 'ZERO'
        base_favorable = evaluate_expression(policy['rules']['financial']['favorable'],cells,metadata=metadata,rules=policy['rules']) if core_ready else None
    elif ni_sign in ('ZERO','NEGATIVE'):
        cash_positive = cash_negative = None
        cash_sign = 'NOT_INFERRED'
        base_favorable = False if core_ready else None
    else:
        cash_positive = cash_negative = base_favorable = None
        cash_sign = 'UNKNOWN'
    watch_results = []
    for expression in watch_expressions:
        name = expression['feature']; entry = cells[name]
        # Optional missing/invalid cells skip the check, never become zero or a G1 failure.
        if entry['usable'] and period is not None:
            matched = evaluate_expression(expression,cells)
            result = rule_result('WATCH_'+name.upper(),matched,evidence=[entry])
        else:
            result = rule_result('WATCH_'+name.upper(),None,evidence=[entry])
            reason = entry['validation_status'] if not entry['usable'] else 'CORE_PERIOD_NOT_READY'
            result.update(status='SKIPPED',skipped_reason=reason)
            optional_issues.append(dict(field=name,status=entry['status'],reason=reason))
        watch_results.append(result)
    watch = any(r['matched'] is True for r in watch_results)
    major = cash_negative if cfo_ready else False if ni_sign in ('ZERO','NEGATIVE') else None
    favorable = None if issues else bool(base_favorable and not watch and major is not True)
    condition = 'UNKNOWN' if issues else 'ADVERSE' if major is True or profitability_adverse is True else 'FAVORABLE' if favorable else 'MIXED'
    qualifiers = [ni,metadata['ni_denominator_sign'],metadata['ni_denominator_observed'],ratio]
    results = [rule_result('FINANCIAL_PROFIT_CASH_FAVORABLE',base_favorable,
                           evidence=[cells[k] for k in (*MANDATORY,'cfo_to_ni')],qualifiers=qualifiers),
               rule_result('FINANCIAL_PROFITABILITY_ADVERSE',profitability_adverse,evidence=[cells[k] for k in MANDATORY]),
               rule_result('CFO_POSITIVE',cash_positive,evidence=[cells['cfo_to_ni']],qualifiers=qualifiers),
               rule_result('CFO_NEGATIVE',cash_negative,evidence=[cells['cfo_to_ni']],qualifiers=qualifiers)]
    if ni_sign in ('ZERO','NEGATIVE'):
        for result in results[2:]:
            result.update(status='SKIPPED',skipped_reason='DENOMINATOR_NOT_OBSERVED_POSITIVE')
    return dict(component='FINANCIAL',policy_id=policy['policy_id'],policy_version=policy['version'],
                status='INSUFFICIENT_EVIDENCE' if issues else 'PASS',financial_condition=condition,
                financial_favorable=favorable,profitability_adverse=profitability_adverse,cash_flow_sign=cash_sign,
                major_warning=major,watch_warning=watch,eligibility_issues=issues,optional_issues=optional_issues,
                rules=results+watch_results,verdict_issued=False)
