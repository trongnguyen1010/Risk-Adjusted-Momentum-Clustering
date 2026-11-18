"""D-ASS-01 evidence-backed rationale; independent of legacy builder activation.

Re-evaluates the verdict from input cells; never accepts caller-authored verdicts
or free text. Peer membership/comparability receipts must be verified by S1.
"""
from collections.abc import Mapping
from copy import deepcopy

from .rules_common import load_policy, read_evidence
from .verdict import evaluate_verdict
from .rules_market import MOMENTUM

TEMPLATE_VERSION = 'D-ASS-01-RATIONALE-1'
TEMPLATES = {
    'SIGN_POSITIVE': '{metric} = {value:g} > 0; tín hiệu riêng thuận chiều, không tự quyết định verdict.',
    'SIGN_NEGATIVE': '{metric} = {value:g} < 0; tín hiệu riêng bất lợi.',
    'SIGN_ZERO': '{metric} = 0; chưa có tín hiệu thuận hoặc bất lợi theo dấu.',
    'CFO_POSITIVE': 'CFO/NI = {value:g} > 0; điều kiện NI quan sát dương và tỷ số hợp lệ đã đạt.',
    'CFO_NEGATIVE': 'CFO/NI = {value:g} < 0; kích hoạt cảnh báo trọng yếu khi NI quan sát dương và tỷ số hợp lệ.',
    'CFO_ZERO': 'CFO/NI = 0; chưa đạt điều kiện dòng tiền thuận lợi.',
    'WATCH_GROSS_MARGIN': 'gross_margin = {value:g} < 0; kích hoạt cảnh báo theo dõi.',
    'WATCH_CURRENT_RATIO': 'current_ratio = {value:g} < 1; kích hoạt cảnh báo theo dõi.',
    'WATCH_REVENUE_GROWTH': 'revenue_growth = {value:g} < 0; kích hoạt cảnh báo theo dõi.',
    'CONTEXT_ONLY': '{metric} = {value:g}; bằng chứng bối cảnh, không chấm điểm hoặc tự đổi verdict.',
}


def _map(value):
    return value if isinstance(value, Mapping) else {}


def _point(cell, rule_id, template_id, direction, qualifiers=()):
    point = deepcopy(cell)
    point.update(rule_id=rule_id, template_id=template_id, direction=direction,
                 qualifiers=deepcopy(list(qualifiers)), peer_median=None)
    text = TEMPLATES[template_id].format(**point)
    if point['status'] == 'IMPUTED_MEDIAN':
        text += ' Giá trị điền trung vị (IMPUTED_MEDIAN), không phải số liệu quan sát của doanh nghiệp.'
    else:
        text += ' Trạng thái OK; giữ bằng chứng nguồn của ô dữ liệu.'
    point['text'] = text
    return point


def _percentile(values, fraction):
    position = (len(values) - 1) * fraction
    left = int(position)
    right = min(left + 1, len(values) - 1)
    weight = position - left
    return (1 - weight) * values[left] + weight * values[right]


def _peer_explanations(peers, cells, context, policy, target_ticker, context_verified):
    """Render S1-compatible member cells; do not select clusters or new pools."""
    if peers is None:
        return []
    if not isinstance(peers, Mapping):
        raise ValueError('Peers must map whitelisted metrics to S1 membership receipts')
    if set(peers) - set(policy['features']['whitelist']):
        raise ValueError('Peers metric outside the 18-feature whitelist')
    output = []
    target_labels = _map(_map(context).get('metadata'))
    for metric in sorted(peers):
        record = _map(peers[metric])
        target = cells.get(metric)
        row = dict(rule_id='G4_PEERS', metric=metric, role='EXPLANATION_ONLY',
                   peer_basis=record.get('peer_basis'), peer_count=0, members=[],
                   peer_median=None, p25=None, p75=None, relative_position=None,
                   evidence_ref=record.get('evidence_ref'), status='UNVERIFIED_PEERS')
        output.append(row)
        if not (target_labels.get('a_label_valid') is True and target_labels.get('b_pit_label_valid') is True):
            row['status']='TARGET_LABELS_REQUIRED'
            continue
        if not context_verified:
            row['status']='TARGET_CONTEXT_UNVERIFIED'
            continue
        allowed = (policy['peers']['preferred_basis'], policy['peers']['fallback_basis'][
            'financial' if metric in policy['features']['financial'] else 'market'])
        if not target or not target['usable']:
            row['status']='TARGET_EVIDENCE_UNUSABLE'
            continue
        if not (isinstance(target_ticker, str) and target_ticker.strip()):
            row['status']='TARGET_ID_REQUIRED'
            continue
        if not (record.get('peer_basis') in allowed and record.get('membership_verified') is True
                and record.get('comparability_verified') is True
                and isinstance(record.get('evidence_ref'), str) and record['evidence_ref'].strip()):
            continue
        row['target_evidence'] = deepcopy(target)
        members = record.get('members')
        if not isinstance(members, list):
            continue
        # Duplicate identities are excluded entirely, not resolved by input order.
        counts = {}
        for member in members:
            ticker = _map(member).get('ticker')
            if isinstance(ticker,str):
                counts[ticker.strip().upper()] = counts.get(ticker.strip().upper(),0)+1
        approved = policy['imputed_policy']
        for member in members:
            member = _map(member)
            ticker = member.get('ticker')
            if not isinstance(ticker,str) or not ticker.strip():
                continue
            ticker = ticker.strip().upper()
            if ticker == target_ticker.strip().upper() or counts[ticker] != 1:
                continue
            source = _map(member.get('cell'))
            if source.get('status') == 'IMPUTED_MEDIAN' and not (
                    approved.get('allowed_for_peers') is True
                    and 'PEERS' in approved.get('approval',{}).get('scope',[])):
                continue
            cell = read_evidence(metric, source, rule_id='G4_PEERS', policy=policy)
            if not cell['usable'] or any(cell[key] != target[key] for key in ('period','unit')):
                continue
            row['members'].append(dict(ticker=ticker, **cell))
        row['members'].sort(key=lambda item:item['ticker'])
        row.update(peer_count=len(row['members']), unit=target['unit'], period=target['period'])
        if row['peer_count'] < policy['peers']['min_valid_peers']:
            row.update(status='BELOW_MINIMUM', text='Chưa đủ 3 Peers hợp lệ; chỉ hiển thị các ô hiện có, không tính trung vị.')
        else:
            values = sorted(item['value'] for item in row['members'])
            center = _percentile(values,.5)
            row.update(status='VALID', peer_median=center, p25=_percentile(values,.25), p75=_percentile(values,.75),
                       relative_position='ABOVE' if target['value'] > center else 'BELOW' if target['value'] < center else 'EQUAL',
                       text='So sánh tương đối với trung vị Peers; cao/thấp hơn không tự đồng nghĩa tốt/xấu và không đổi verdict.')
    return output


def build_rationale(market_features, financial_features, *, liquidity, denominator,
                    ratio_validity, context, policy=None, fixture_only=False, peers=None,
                    target_ticker=None):
    """Build drivers/risks/counter_evidence from fixed versioned templates.

    Peers: {metric: {peer_basis, membership_verified, comparability_verified,
    evidence_ref, members: [{ticker, cell}]}}. S1 verifies PIT, definition, source,
    report type, membership and complete pool before passing these receipts.
    Legacy summaries without member evidence are not accepted as verified Peers.
    """
    policy = load_policy(policy)
    assessment = evaluate_verdict(market_features, financial_features, liquidity=liquidity,
                                 denominator=denominator, ratio_validity=ratio_validity,
                                 context=context, policy=policy, fixture_only=fixture_only)
    all_features = dict(market_features, **financial_features)
    cells = {metric:read_evidence(metric, cell, rule_id='CONTEXT_ONLY', policy=policy)
             for metric,cell in all_features.items()}
    rules = {rule['rule_id']:rule for component in (assessment['market'],assessment['financial'])
             for rule in component['rules']}
    # A known invalid source/date/model gate cannot back a narrative claim.
    # Component-local missing cells do not erase independently valid evidence.
    context_verified = not any('component' not in issue and issue['field'] != 'activation'
                               for issue in assessment['eligibility_issues'])
    points, skipped, metadata_warnings = [], [], []
    for metric in policy['features']['whitelist']:
        cell = cells.get(metric)
        if not context_verified:
            skipped.append(dict(metric=metric,reason='TARGET_CONTEXT_UNVERIFIED'))
            continue
        if not cell or not cell['usable']:
            skipped.append(dict(metric=metric,reason=cell['validation_status'] if cell else 'MISSING_INPUT'))
            continue
        expected = _map(context).get('market_snapshot_date') if metric in policy['features']['market'] else None
        if expected is None:
            expected = str(_map(context).get('fiscal_year'))
            periods = (expected,'FY'+expected)
        else:
            periods = (expected,)
        if cell['period'] not in periods:
            cell.update(usable=False,validation_status='SCOPE_PERIOD_MISMATCH')
            skipped.append(dict(metric=metric,reason='SCOPE_PERIOD_MISMATCH'))
            continue
        template, rule_id, direction, qualifiers = 'CONTEXT_ONLY','CONTEXT_ONLY','CONTEXT',[]
        if metric in (*MOMENTUM,'roa','net_margin'):
            sign = 'POSITIVE' if cell['value']>0 else 'NEGATIVE' if cell['value']<0 else 'ZERO'
            template, rule_id = 'SIGN_'+sign, 'MOMENTUM_SIGN' if metric in MOMENTUM else 'PROFITABILITY_SIGN'
            direction = 'SUPPORTING' if sign=='POSITIVE' else 'ADVERSE' if sign=='NEGATIVE' else 'NEUTRAL'
        elif metric == 'cfo_to_ni':
            cash_sign = assessment['financial']['cash_flow_sign']
            if cash_sign in ('POSITIVE','NEGATIVE','ZERO'):
                template = rule_id = 'CFO_'+cash_sign
                direction = 'SUPPORTING' if cash_sign=='POSITIVE' else 'ADVERSE' if cash_sign=='NEGATIVE' else 'NEUTRAL'
                qualifiers = rules['CFO_POSITIVE']['qualifiers']
            # Unknown/nonpositive NI: ratio can be context, never infer CFO sign.
        elif metric in ('gross_margin','current_ratio','revenue_growth'):
            rule = rules['WATCH_'+metric.upper()]
            if rule['status']=='SKIPPED':
                skipped.append(dict(metric=metric,reason=rule['skipped_reason']))
                continue
            if rule['matched'] is True:
                template = rule_id = rule['rule_id']; direction='ADVERSE'
        points.append(_point(cell,rule_id,template,direction,qualifiers))
    liquidity_rule = rules['MARKET_ILLIQUID']
    if context_verified and liquidity_rule['matched'] is True:
        metadata_warnings.append(dict(rule_id='MARKET_ILLIQUID',direction='ADVERSE',
                                      template_id='ILLIQUID_METADATA',
                                      text='Cờ thanh khoản ILLIQUID kích hoạt cảnh báo trọng yếu.',
                                      qualifiers=deepcopy(liquidity_rule['qualifiers'])))
    peer_explanations = _peer_explanations(peers,cells,context,policy,target_ticker,context_verified)
    peer_by_metric = {row['metric']:row for row in peer_explanations}
    for point in points:
        peer = peer_by_metric.get(point['metric'])
        if peer and peer['status']=='VALID':
            point.update(peer_median=peer['peer_median'],peer_evidence_ref=peer['evidence_ref'])
    supporting = [point for point in points if point['direction']=='SUPPORTING']
    adverse = [point for point in points if point['direction']=='ADVERSE']
    verdict = assessment['verdict']
    counter = supporting if verdict in ('CAUTION','INSUFFICIENT_EVIDENCE') else adverse if verdict=='RESEARCH_FAVORABLE' else supporting+adverse
    return dict(template_version=TEMPLATE_VERSION, policy_id=policy['policy_id'], policy_version=policy['version'],
                assessment=assessment, verdict=verdict, label_vi=assessment['label_vi'],
                drivers=[] if verdict=='INSUFFICIENT_EVIDENCE' else supporting, risks=adverse,
                counter_evidence=counter, context_evidence=[point for point in points if point['direction'] in ('CONTEXT','NEUTRAL')],
                metadata_warnings=metadata_warnings, eligibility_issues=deepcopy(assessment['eligibility_issues']),
                skipped_evidence=skipped, peers=peer_explanations,
                publishable=assessment['publishable'], peers_change_verdict=False)
