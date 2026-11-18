"""Small shared evidence/policy helpers for D-ASS-01 component rules.

Pure evaluation after S1 supplies verified cells. Does not load features, fit models,
verify raw-source files, or activate the existing Assessment builder.
"""
from collections.abc import Mapping
import json
import math
from numbers import Real
import operator
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[4] / 'configs/product/assessment_policy_v1.json'
OPS = {'>': operator.gt, '<': operator.lt, '==': operator.eq}


def load_policy(policy=None):
    if policy is None:
        policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    if not isinstance(policy, Mapping) or policy.get('policy_id') != 'D-ASS-01':
        raise ValueError('A versioned D-ASS-01 policy is required')
    if len(policy['features']['whitelist']) != 18 or len(set(policy['features']['whitelist'])) != 18:
        raise ValueError('Policy must contain exactly 18 unique features')
    return policy


def read_evidence(name, cell, *, rule_id, policy, categorical_values=None, as_metadata=False):
    cell = cell if isinstance(cell, Mapping) else {}
    source_status = cell.get('status', 'MISSING_INPUT')
    value = cell.get('value')
    result = dict(rule_id=rule_id, value=value, status=source_status, unit=cell.get('unit'),
                  period=cell.get('period'), evidence_ref=cell.get('evidence_ref'))
    metadata_cell = as_metadata or categorical_values is not None
    result['metadata' if metadata_cell else 'metric'] = name
    reason = None
    if value is None:
        reason = 'MISSING_INPUT'
    elif categorical_values is not None:
        if not any(type(value) is type(allowed) and value == allowed for allowed in categorical_values):
            reason = 'INVALID_METADATA'
            result['value'] = None
    elif isinstance(value, bool) or not isinstance(value, Real):
        reason = 'INVALID_VALUE'
        result['value'] = None
    elif not math.isfinite(float(value)):
        reason = 'NON_FINITE_VALUE'
        result['value'] = None
    else:
        result['value'] = float(value)
    if reason is None and source_status not in policy['eligibility']['accept_only_statuses']:
        reason = 'UNUSABLE_STATUS'
    if reason is None and source_status == 'IMPUTED_MEDIAN':
        approved = policy['imputed_policy']
        if metadata_cell:
            reason = 'IMPUTED_METADATA_NOT_ALLOWED'
        elif name not in policy['features']['financial']:
            reason = 'IMPUTATION_NOT_ALLOWED_FOR_MARKET'
        elif not (approved.get('allowed_for_rulebook') is True
                  and approved.get('approval', {}).get('status') == 'APPROVED_BY_USER'
                  and 'RULEBOOK' in approved['approval'].get('scope', [])):
            reason = 'UNAPPROVED_IMPUTATION'
        elif cell.get('cell_lineage_verified') is not True:
            reason = 'UNVERIFIED_IMPUTATION_LINEAGE'
    if reason is None and any(not isinstance(result[k], str) or not result[k].strip()
                              for k in ('unit','period','evidence_ref')):
        reason = 'MISSING_EVIDENCE'
    if reason is None and (cell.get('source_hash_verified') is not True or cell.get('provenance_verified') is not True):
        reason = 'UNVERIFIED_EVIDENCE'
    result.update(validation_status=reason or 'VALID', usable=reason is None,
                  is_observed=source_status == 'OK', cell_lineage_verified=cell.get('cell_lineage_verified') is True,
                  source_hash_verified=cell.get('source_hash_verified') is True,
                  provenance_verified=cell.get('provenance_verified') is True)
    return result


def evaluate_expression(expression, cells, *, metadata=None, rules=None):
    """Three-valued expressions: None is unknown evidence, never a numerical zero."""
    metadata = {} if metadata is None else metadata
    if 'all' in expression or 'any' in expression:
        key = 'all' if 'all' in expression else 'any'
        values = [evaluate_expression(item,cells,metadata=metadata,rules=rules) for item in expression[key]]
        if key == 'all':
            return False if False in values else None if None in values else True
        return True if True in values else None if None in values else False
    if 'not' in expression:
        value = evaluate_expression(expression['not'],cells,metadata=metadata,rules=rules)
        return None if value is None else not value
    if 'rule_ref' in expression:
        if rules is None:
            raise ValueError('No policy rules supplied for rule reference')
        node = rules
        for key in expression['rule_ref'].split('.'):
            node = node[key]
        return evaluate_expression(node,cells,metadata=metadata,rules=rules)
    if 'always' in expression:
        return expression['always']
    if 'feature' in expression:
        cell = cells.get(expression['feature'])
    elif 'metadata' in expression:
        cell = metadata.get(expression['metadata'])
    else:
        raise ValueError('Unsupported rule expression')
    if not cell or not cell['usable']:
        return None
    if expression['op'] not in OPS:
        raise ValueError('Unsupported comparison operator')
    return bool(OPS[expression['op']](cell['value'],expression['value']))


def rule_result(rule_id, matched, *, evidence=(), qualifiers=()):
    return dict(rule_id=rule_id,status='UNKNOWN' if matched is None else 'MATCH' if matched else 'NO_MATCH',
                matched=matched,evidence=[dict(item,rule_id=rule_id) for item in evidence],
                qualifiers=[dict(item,rule_id=rule_id) for item in qualifiers])
