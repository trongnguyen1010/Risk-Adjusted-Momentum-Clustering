"""R2-12: market direction and ILLIQUID warning under the pinned D-ASS-01 policy.

Input cells carry value/status/unit/period/evidence_ref and S1 verification flags.
This component is independently testable; it neither issues investment verdicts
nor integrates/activates the current S1/S3 builder.
"""
from collections.abc import Mapping
from .rules_common import load_policy, read_evidence, evaluate_expression, rule_result

MOMENTUM = ('mom_21','mom_63','mom_126','mom_252')


def evaluate_market(features, *, liquidity, policy=None):
    policy = load_policy(policy)
    if not isinstance(features, Mapping):
        raise ValueError('Market features must be a mapping of verified evidence cells')
    extra = set(features) - set(policy['features']['market'])
    if extra:
        raise ValueError('Non-whitelisted market features: ' + ', '.join(sorted(extra)))
    def validate_trend_expression(node):
        if 'feature' in node:
            if node['feature'] not in MOMENTUM:
                raise ValueError('Market trend may use only the four momentum features')
            if set(node) != {'feature','op','value'} or node['op'] not in ('>','<'):
                raise ValueError('Unsupported market trend comparison')
        elif len(node) == 1 and ('all' in node or 'any' in node):
            for child in node.get('all',node.get('any',[])):
                validate_trend_expression(child)
        else:
            raise ValueError('Market trend accepts only momentum comparisons and all/any')
    for direction in ('favorable','adverse'):
        validate_trend_expression(policy['rules']['market'][direction])
    liquidity_conditions = []
    def find_liquidity(node):
        if isinstance(node,dict):
            if node.get('metadata') == 'liquidity_flag':
                liquidity_conditions.append(node)
            for value in node.values():
                find_liquidity(value)
        elif isinstance(node,list):
            for item in node:
                find_liquidity(item)
    find_liquidity(policy['rules']['warnings']['major'])
    if len(liquidity_conditions) != 1 or liquidity_conditions[0] != {
            'metadata':'liquidity_flag','op':'==','value':'ILLIQUID'}:
        raise ValueError('Policy must define one ILLIQUID major warning')
    cells = {name:read_evidence(name,features.get(name),rule_id='MARKET_MOMENTUM_INPUT',policy=policy)
             for name in MOMENTUM}
    flag = read_evidence('liquidity_flag',liquidity,rule_id='MARKET_ILLIQUID',policy=policy,
                         categorical_values=('LIQUID','ILLIQUID'))
    alignment_issues = []
    ready = all(c['usable'] for c in cells.values())
    if ready:
        for key in ('period','unit'):
            if len({c[key] for c in cells.values()}) != 1:
                alignment_issues.append(dict(field='market_momentum',status='CONFLICT',reason=key.upper()+'_MISMATCH'))
        ready = not alignment_issues
    if ready and flag['usable'] and flag['period'] != cells['mom_21']['period']:
        flag.update(usable=False,validation_status='LIQUIDITY_PERIOD_MISMATCH')
    # All four momenta are mandatory even if the OR branch could be decided without one.
    favorable = evaluate_expression(policy['rules']['market']['favorable'],cells) if ready else None
    adverse = evaluate_expression(policy['rules']['market']['adverse'],cells) if ready else None
    condition = 'UNKNOWN' if not ready else 'FAVORABLE' if favorable else 'ADVERSE' if adverse else 'MIXED'
    illiquid = evaluate_expression(liquidity_conditions[0],{},
                                   metadata={'liquidity_flag':flag})
    issues = [dict(field=c['metric'],status=c['status'],reason=c['validation_status'])
              for c in cells.values() if not c['usable']]
    issues.extend(alignment_issues)
    if not flag['usable']:
        issues.append(dict(field='liquidity_flag',status=flag['status'],reason=flag['validation_status']))
    return dict(component='MARKET',policy_id=policy['policy_id'],policy_version=policy['version'],
                status='INSUFFICIENT_EVIDENCE' if issues else 'PASS',market_condition=condition,
                major_warning=illiquid,eligibility_issues=issues,
                rules=[rule_result('MARKET_FAVORABLE',favorable,evidence=cells.values()),
                       rule_result('MARKET_ADVERSE',adverse,evidence=cells.values()),
                       rule_result('MARKET_ILLIQUID',illiquid,qualifiers=[flag])],
                verdict_issued=False)
