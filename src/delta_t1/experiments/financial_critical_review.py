"""Replay exact PDF/API diagnostic comparisons; never repair or accept API cells."""
from collections import Counter
from decimal import Decimal
import json

from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read, put


def source_cell(payload, case):
    if case['mode'] != ('NAM' if case['quarter'] == 0 else 'QUY'):
        raise ValueError('incompatible provider period')
    value = payload['value']
    templates = [g for g in value['templace'] if g['code'] == case['group']]
    if len(templates) != 1:
        raise ValueError('ambiguous source template group')
    labels = [r['name'] for r in templates[0]['data'] if str(r['code']) == case['raw_code']]
    if len(labels) > 1:
        raise ValueError('ambiguous source label')
    label = labels[0] if labels else None
    if label != case['expected_api_label']:
        raise ValueError('provider label differs from reviewed evidence')
    cells = []
    for group in value['data']:
        if group['code'] != case['group']:
            continue
        for period in group['data']:
            if (period['symbol'], period['year'], period['quater'], period['type']) != (
                    case['symbol'], case['year'], case['quarter'], case['provider_type']):
                continue
            cells += [r for r in period['data'] if str(r['code']) == case['raw_code']]
    if len(cells) != 1:
        raise ValueError('ambiguous or missing exact source cell')
    number = Decimal(str(cells[0]['value']))
    if not number.is_finite():
        raise ValueError('nonfinite source number')
    return number, label


def compare(payload, case):
    number, label = source_cell(payload, case)
    if case['source_report_year'] != case['year']:
        raise ValueError('critical review requires original same-year report')
    if label is None:
        if case['pdf_value'] is not None or case.get('field') is not None:
            raise ValueError('unlabelled code cannot be assigned PDF semantics')
        return dict(case_id=case['id'], status='UNRESOLVED_NONZERO_UNLABELLED' if number else
                    'UNRESOLVED_ZERO_UNLABELLED', api_value=str(number), pdf_value=None,
                    accepted=False, automatic_override=False)
    if not case.get('field') or not case.get('row_label') or type(case['pdf_page']) is not int or case['pdf_page'] < 1:
        raise ValueError('explicit reviewed PDF field, row and physical page required')
    pdf = Decimal(case['pdf_value'])
    if not pdf.is_finite():
        raise ValueError('nonfinite PDF number')
    status = ('RAW_NUMERIC_MATCH_REFERENCE_ONLY' if pdf == number else
              'PDF_NONZERO_API_ZERO' if number == 0 and pdf != 0 else 'RAW_NUMERIC_DIFFERENCE')
    return dict(case_id=case['id'], status=status, api_value=str(number), pdf_value=str(pdf),
                difference=str(number-pdf), field=case['field'], pdf_page=case['pdf_page'],
                unit_acceptance=False, accepted=False, automatic_override=False)


def run(root, config_path, action):
    config = read(inside(root, config_path)); pins = {}
    if config.get('version') != 'financial-critical-review-v1' or config.get('accepted_facts_allowed') is not False:
        raise ValueError('diagnostic-only critical review contract required')
    def pin(path, expected=None):
        raw = inside(root, path).read_bytes(); sha = digest(raw)
        if expected is not None and sha != expected:
            raise ValueError('critical evidence changed: '+path)
        pins[path] = sha
        return raw
    for p in [config_path, 'src/delta_t1/experiments/financial_critical_review.py',
              'scripts/financial_critical_review.py']:
        pin(p)
    review = json.loads(pin(config['review']['path'], config['review']['sha256']))
    if review['review_method'] != 'AGENT_VISUAL_REVIEW_OF_PINNED_PDF_PAGES' or review['pit_ready'] is not False:
        raise ValueError('explicit visual review required')
    cases = review['cases']
    if not 1 <= len(cases) <= 100 or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('bounded distinct comparisons required')
    for e in review['evidence']:
        pin(e['path'], e['sha256'])
    results = []
    for case in cases:
        payload = json.loads(pin(case['source_path'], case['source_sha256']))
        for name in ['pdf', 'image']:
            pin(case[name+'_path'], case[name+'_sha256'])
        results.append(compare(payload, case))
    holds = review['partition_holds']
    for hold in holds:
        if hold['accepted'] is not False or hold['automatic_override'] is not False:
            raise ValueError('API source quarantine cannot accept or repair')
        matching = [r for c, r in zip(cases, results) if all(c[k] == hold[k] for k in
                    ['symbol', 'year', 'quarter', 'mode', 'provider_type', 'statement'])]
        if not any(r['status'] in ['RAW_NUMERIC_DIFFERENCE', 'PDF_NONZERO_API_ZERO',
                                  'UNRESOLVED_NONZERO_UNLABELLED'] for r in matching):
            raise ValueError('partition hold lacks exact finding evidence')
    summary = dict(status='CRITICAL_SOURCE_PARTITIONS_QUARANTINED', comparisons=len(results),
                   comparison_statuses=dict(Counter(r['status'] for r in results)), partition_holds=len(holds),
                   accepted_facts=0, automatic_repairs=0, strict_pit_metrics=0, next50_allowed=False)
    products = {'summary.json': encoded(summary), 'comparisons.json': encoded(results),
                'partition-quarantine.json': encoded(holds), 'input-pins.json': encoded(pins)}
    manifest = {p: digest(b) for p, b in products.items()}
    out = inside(root, config['output_root']) / digest(encoded(manifest))[:20]
    if action == 'verify':
        if read(out/'manifest.json') != manifest:
            raise ValueError('critical review manifest changed')
        for p, sha in manifest.items():
            if digest((out/p).read_bytes()) != sha:
                raise ValueError('critical review output changed')
    else:
        for p, b in products.items():
            put(out/p, b)
        put(out/'manifest.json', manifest)
    return dict(summary, output=out.relative_to(root).as_posix())
