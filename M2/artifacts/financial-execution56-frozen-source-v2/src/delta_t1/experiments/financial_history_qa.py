"""Offline diagnostics on sealed history candidates; never accepts financial facts."""
import argparse
import csv
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside

VERSION = 'financial-history-qa-v1'


def load(path):
    return json.loads(path.read_bytes())


def norm(label):
    text = unicodedata.normalize('NFD', label or '').lower().replace('đ', 'd')
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'^\s*(?:\d+|[ivx]+|[abcd])\s*[.)]\s*', '', text)
    return ' '.join(re.findall(r'[a-z0-9]+', text))


# Exact provider code AND normalized label. These are diagnostic aliases, not
# canonical acceptance or VAS code assumptions. Provider KQKD 21 is not finance income.
ALIASES = [
    ('CDKT', 'TN', '100', 'current_assets', 'TÀI SẢN NGẮN HẠN'),
    ('CDKT', 'TN', '200', 'noncurrent_assets', 'TÀI SẢN DÀI HẠN'),
    ('CDKT', 'TN', '270', 'total_assets', 'TỔNG CỘNG TÀI SẢN'),
    ('CDKT', 'NV', '300', 'total_liabilities', 'NỢ PHẢI TRẢ'),
    ('CDKT', 'NV', '310', 'current_liabilities', 'Nợ ngắn hạn'),
    ('CDKT', 'NV', '330', 'noncurrent_liabilities', 'Nợ dài hạn'),
    ('CDKT', 'NV', '400', 'total_equity', 'D VỐN CHỦ SỞ HỮU'),
    ('CDKT', 'NV', '400', 'total_equity', 'VỐN CHỦ SỞ HỮU'),
    ('CDKT', 'NV', '440', 'total_capital', 'TỔNG CỘNG NGUỒN VỐN'),
    ('CDKT', 'NV', '319', 'other_short_term_payables', 'Phải trả ngắn hạn khác'),
    ('CDKT', 'NV', '320', 'short_term_loans_and_finance_leases', 'Vay và nợ thuê tài chính ngăn hạn'),
    ('CDKT', 'NV', '320', 'short_term_loans_and_finance_leases', 'Vay và nợ thuê tài chính ngắn hạn'),
    ('CDKT', 'NV', '338', 'noncurrent_loans_and_finance_leases', 'Vay và nợ thuê tài chính dài hạn'),
    ('CDKT', 'NV', '421', 'retained_earnings', 'Lợi nhuận sau thuế chưa phân phối'),
    ('KQKD', 'KQKD', '10', 'net_revenue', 'Doanh thu thuần về bán hàng và cung cấp dịch vụ'),
    ('KQKD', 'KQKD', '11', 'cost_of_goods_sold', 'Giá vốn hàng bán'),
    ('KQKD', 'KQKD', '20', 'gross_profit', 'Lợi nhuận gộp về bán hàng và cung cấp dịch vụ'),
    ('KQKD', 'KQKD', '24', 'interest_expense', '- Trong đó :Chi phí lãi vay'),
    ('KQKD', 'KQKD', '25', 'selling_expense', 'Chi phí bán hàng'),
    ('KQKD', 'KQKD', '26', 'administrative_expense', 'Chi phí quản lý doanh nghiệp'),
    ('KQKD', 'KQKD', '50', 'profit_before_tax', 'Tổng lợi nhuận kế toán trước thuế'),
    ('KQKD', 'KQKD', '60', 'net_profit', 'Lợi nhuận sau thuế thu nhập doanh nghiệp'),
    ('KQKD', 'KQKD', '61', 'parent_net_profit', '- Lợi nhuận sau thuế của cổ đông của Công ty mẹ'),
    ('KQKD', 'KQKD', '70', 'vendor_basic_eps', 'Lãi cơ bản trên cổ phiếu (Đồng/1 cổ phiếu)'),
    ('LCTT', 'HDKD', 'HDKD_20', 'operating_cash_flow', 'Lưu chuyển tiền thuần từ hoạt động kinh doanh'),
]
MAPPING = {(s, g, c, norm(label)): field for s, g, c, field, label in ALIASES}


def semantic_field(candidate):
    return MAPPING.get((candidate['statement'], candidate['group'],
                        candidate['raw_code'], norm(candidate.get('label'))))


def number(value):
    if value is None:
        return None
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('nonfinite candidate')
    return result


def structural_header(candidate, payload):
    """Exclude only a proven root group zero, never an unexplained orphan/amount."""
    if candidate.get('label') or number(candidate.get('value')) != 0:
        return False
    for group in payload.get('value', {}).get('templace', []):
        if group.get('code') != candidate['group'] or 'data' not in group:
            continue
        expected = str(group['code']) + '_' + str(group.get('number'))
        children = {str(child.get('code')) for child in group['data']}
        if expected == candidate['raw_code'] and expected not in children:
            return True
    return False


def observation(candidate):
    return {k: candidate.get(k) for k in (
        'source_path', 'source_sha256', 'template_sha256', 'raw_code', 'label',
        'value', 'provider_type', 'header', 'interval')}


def unique_value(candidates):
    # Retain every observation in output; identical numbers are not vintage proof.
    values = {number(c['value']) for c in candidates}
    if None in values or len(values) != 1:
        return None
    return next(iter(values))


def displacement(annual, quarterly):
    """Two distinct nonzero amounts on shifted neighboring codes; flag, never repair."""
    matches = []
    for shift in (-2, -1, 1, 2):
        pairs = [(code, code + shift, value) for code, value in annual.items()
                 if value is not None and value != 0 and value == quarterly.get(code + shift)
                 and value != quarterly.get(code)]
        if len({v for _, _, v in pairs}) >= 2:
            matches.append(dict(offset=shift, pairs=[dict(annual_code=a, quarter_code=b,
                                                        value=str(v)) for a, b, v in pairs]))
    return matches


def csv_body(rows):
    if not rows:
        return b'status\n'
    columns = list(dict.fromkeys(k for row in rows for k in row))
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                         if isinstance(v, (list, dict)) else v for k, v in row.items()})
    return out.getvalue().encode('utf-8')


def classify_gap(row, candidates):
    h1 = [c for c in candidates if c['symbol'] == row['symbol']
          and c['year'] == int(row['year']) and c['statement'] == row['statement']
          and c['mode'] == 'LUYKE' and c.get('quarter') == 2]
    return dict(row, reason='ABSENT_IN_ACQUIRED_PROVIDER_PAGES_NOT_PROOF_OF_NONPUBLICATION',
                h1_candidate_cells=len(h1),
                h1_action='REVIEW_H1_SOURCE_AND_INTERVAL_NO_AUTOMATIC_Q2_SUBSTITUTION' if h1 else '',
                next_action='CACHE_DOCUMENT_LOOKUP_THEN_TARGETED_PDF', accepted=False, pit_ready=False)


def analyze(root, config):
    pins = {}

    def pinned(relative, expected=None):
        path = inside(root, relative)
        raw = path.read_bytes()
        sha = digest(raw)
        if expected is not None and sha != expected:
            raise ValueError('input hash mismatch: ' + relative)
        pins[relative] = sha
        return raw

    report = config['input_report']
    manifest = json.loads(pinned(report + '/manifest.json', config['input_manifest_sha256']))
    # Verify all sealed report products, not just candidate data.
    for name, sha in manifest.items():
        pinned(report + '/' + name, sha)
    candidates = [json.loads(line) for line in pinned(report + '/candidates.jsonl').splitlines()]
    facts = json.loads(pinned(config['reviewed_inputs'], config['reviewed_inputs_sha256']))
    coverage = list(csv.DictReader(io.StringIO(pinned(report + '/financial_coverage.csv').decode('utf-8'))))
    metrics = list(csv.DictReader(io.StringIO(pinned(report + '/metrics.csv').decode('utf-8'))))
    payloads, structural, unresolved, mapped, buckets, raw_buckets = {}, [], [], [], defaultdict(list), defaultdict(list)
    for c in candidates:
        source = c['source_path']
        if source not in payloads:
            payloads[source] = json.loads(pinned(source, c['source_sha256']))
        elif pins[source] != c['source_sha256']:
            raise ValueError('conflicting raw hash: ' + source)
        base = dict(symbol=c['symbol'], year=c['year'], quarter=c['quarter'], mode=c['mode'],
                    statement=c['statement'], group=c['group'], **observation(c))
        if structural_header(c, payloads[source]):
            structural.append(dict(**base, status='STRUCTURAL_GROUP_HEADER_ZERO', accepted=False))
            continue
        if not c.get('label'):
            unresolved.append(dict(**base, status='UNEXPLAINED_ORPHAN', accepted=False))
        if not 2012 <= c['year'] <= 2025:
            continue  # observed extra years stay in sealed acquisition, outside target QA
        raw_key = (c['symbol'], c['year'], c['quarter'], c['mode'], c['provider_type'], c['statement'], c['group'], c['raw_code'])
        raw_buckets[raw_key].append(c)
        field = semantic_field(c)
        if field:
            mapped.append(dict(**base, field=field, status='EXACT_CODE_LABEL_CANDIDATE', accepted=False, pit_ready=False))
            key = (c['symbol'], c['year'], c['quarter'], c['mode'], c['provider_type'], field)
            buckets[key].append(c)
    conflicts = []
    for key, cells in sorted(raw_buckets.items()):
        if len({number(c['value']) for c in cells}) > 1:
            conflicts.append(dict(key=list(key), observations=[observation(c) for c in cells],
                                  status='MULTIPLE_PROVIDER_VALUES_NO_VINTAGE_SELECTION'))
    arithmetic = []
    formulas = [('ASSETS_EQUALS_CAPITAL', 'total_assets', ['total_capital']),
                ('ASSETS_EQUALS_LIABILITIES_EQUITY', 'total_assets', ['total_liabilities', 'total_equity']),
                ('ASSET_PARTS', 'total_assets', ['current_assets', 'noncurrent_assets']),
                ('LIABILITY_PARTS', 'total_liabilities', ['current_liabilities', 'noncurrent_liabilities']),
                ('GROSS_PROFIT', 'net_revenue', ['cost_of_goods_sold', 'gross_profit'])]
    periods = sorted({key[:5] for key in buckets})
    for period in periods:
        for name, lhs, rhs in formulas:
            inputs = {field: buckets.get(period + (field,), []) for field in [lhs] + rhs}
            if not all(inputs.values()):
                continue
            values = {field: unique_value(cells) for field, cells in inputs.items()}
            delta = None if None in values.values() else values[lhs] - sum(values[f] for f in rhs)
            arithmetic.append(dict(period=list(period), check=name,
                status='AMBIGUOUS_OR_MISSING_VALUE' if delta is None else ('RAW_EQUALITY' if delta == 0 else 'RAW_DIFFERENCE'),
                difference=None if delta is None else str(delta),
                observations={f: [observation(c) for c in cs] for f, cs in inputs.items()},
                interpretation='SAME_UNIT_SCOPE_HYPOTHESIS_ONLY_NO_ACCEPTANCE'))
    annual_q4, shifts = [], []
    for period in sorted({key[:5] for key in raw_buckets}):
        symbol, year, quarter, mode, provider_type = period
        if mode != 'NAM' or quarter != 0:
            continue
        annual_codes, quarter_sets = {}, defaultdict(dict)
        for key, cells in sorted(raw_buckets.items()):
            if key[0] != symbol or key[1] != year or key[5] != 'CDKT':
                continue
            if key[2:4] == (0, 'NAM') and key[4] == provider_type:
                annual_codes[(key[6], key[7])] = cells
            elif key[2:4] == (4, 'QUY'):
                quarter_sets[key[4]][(key[6], key[7])] = cells
        # Restrict displacement detector to known short liability row neighborhood.
        def debt_codes(codes):
            return {int(code): unique_value(cs) for (group, code), cs in codes.items()
                    if group == 'NV' and code.isdigit() and 311 <= int(code) <= 324}
        # Annual audit flags often differ from Q4 provider flags (e.g. K versus N).
        # Preserve both partitions and compare diagnostically; never equate scopes.
        for quarter_type, quarter_codes in sorted(quarter_sets.items()):
            for code in sorted(annual_codes.keys() & quarter_codes.keys()):
                a, q = annual_codes[code], quarter_codes[code]
                av, qv = unique_value(a), unique_value(q)
                annual_q4.append(dict(symbol=symbol, year=year,
                    annual_provider_type=provider_type, q4_provider_type=quarter_type,
                    group=code[0], raw_code=code[1],
                    status='AMBIGUOUS_OR_MISSING_VALUE' if av is None or qv is None else ('RAW_EQUALITY' if av == qv else 'RAW_DIFFERENCE'),
                    annual=[observation(c) for c in a], q4=[observation(c) for c in q],
                    interpretation='CLOSING_BALANCE_CANDIDATES_VINTAGE_SCOPE_UNIT_UNVERIFIED'))
            for match in displacement(debt_codes(annual_codes), debt_codes(quarter_codes)):
                shifts.append(dict(symbol=symbol, year=year,
                    annual_provider_type=provider_type, q4_provider_type=quarter_type,
                    annual_sources=sorted({c['source_path'] for cs in annual_codes.values() for c in cs}),
                    q4_sources=sorted({c['source_path'] for cs in quarter_codes.values() for c in cs}),
                    status='POSSIBLE_ROW_DISPLACEMENT_REVIEW_NO_REPAIR', **match))
    reference = []
    for fact in facts:
        if fact.get('review_status') != 'REVIEWED_REFERENCE_ONLY':
            continue
        for key, cells in sorted(buckets.items()):
            if key[0] != fact['symbol'] or key[1] != fact['year'] or key[2:4] != (0, 'NAM') or key[5] != fact['field']:
                continue
            value, target = unique_value(cells), number(fact['value'])
            reference.append(dict(symbol=key[0], year=key[1], field=key[5], provider_type=key[4],
                status='AMBIGUOUS_OR_MISSING_VALUE' if value is None or target is None else (
                    'RAW_SAME_UNIT_HYPOTHESIS_MATCH' if value == target else 'RAW_SAME_UNIT_HYPOTHESIS_CONFLICT'),
                api=[observation(c) for c in cells], pdf_fact=fact,
                accepted=False, pit_ready=False))
    gaps = [classify_gap(r, candidates) for r in coverage if r['status'] == 'NO_CANDIDATE_IN_ACQUIRED_PAGES']
    queue = {}

    def enqueue(symbol, year, period, priority, reason, evidence):
        item = queue.setdefault((symbol, year, period), dict(symbol=symbol, year=year, period=period,
            priority=priority, reasons=[], evidence=[], cached_pdf_candidates=[],
            action='REUSE_CACHE_THEN_DISCOVER_TARGETED_PRIMARY_PDF_TEXT_FIRST',
            accepted=False, pit_ready=False, publication_status='EVIDENCE_REQUIRED'))
        item['priority'] = min(item['priority'], priority)
        if reason not in item['reasons']:
            item['reasons'].append(reason)
        item['evidence'].append(evidence)

    for gap in gaps:
        enqueue(gap['symbol'], int(gap['year']), 'FY' if gap['mode'] == 'NAM' else 'Q' + gap['quarter'],
                2, 'MISSING_PROVIDER_PERIOD', dict(statement=gap['statement'], h1_candidate_cells=gap['h1_candidate_cells']))
    for item in shifts:
        enqueue(item['symbol'], item['year'], 'FY', 1, 'POSSIBLE_ROW_DISPLACEMENT', item)
    for item in reference:
        if item['status'] == 'RAW_SAME_UNIT_HYPOTHESIS_CONFLICT':
            enqueue(item['symbol'], item['year'], 'FY', 1, 'REVIEWED_PDF_VALUE_CONFLICT', dict(field=item['field'], fact_id=item['pdf_fact']['id']))
    for item in arithmetic:
        if item['status'] == 'RAW_DIFFERENCE':
            symbol, year, quarter, mode, _ = item['period']
            period = 'FY' if mode == 'NAM' else ('H1' if mode == 'LUYKE' else 'Q' + str(quarter))
            enqueue(symbol, year, period, 2, 'RAW_ACCOUNTING_DIFFERENCE', dict(check=item['check'], difference=item['difference']))
    for item in queue.values():
        # Annual cache suggestions for quarterly gaps are not declared equivalent.
        item['cached_pdf_candidates'] = sorted({f['provenance']['pdf_path'] for f in facts
            if f['symbol'] == item['symbol'] and f['year'] == item['year'] and f.get('provenance', {}).get('pdf_path')})
    queue = sorted(queue.values(), key=lambda x: (x['priority'], x['symbol'], x['year'], x['period']))
    summary = dict(version=VERSION, status='PARTIAL', candidate_cells=len(candidates),
        structural_group_header_zeros=len(structural), unexplained_orphans=len(unresolved),
        nonstructural_candidate_cells=len(candidates) - len(structural), mapped_diagnostic_cells=len(mapped),
        conflicting_observation_keys=len(conflicts), raw_accounting_checks=dict(Counter(x['status'] for x in arithmetic)),
        annual_q4_checks=dict(Counter(x['status'] for x in annual_q4)), possible_displacements=len(shifts),
        reviewed_pdf_comparisons=dict(Counter(x['status'] for x in reference)),
        missing_coverage_slots=len(gaps), missing_slots_by_symbol=dict(Counter(x['symbol'] for x in gaps)),
        selective_document_queue_periods=len(queue), accepted_new_facts=0, pit_eligible_new_facts=0,
        reference_metrics_verified=sum(m['status'] == 'RECOMPUTED_REFERENCE' and bool(m['value']) for m in metrics),
        reference_metrics_target=len(metrics), batch20_allowed=False,
        diagnostic_year_range=[2012, 2025], candidate_count_includes_observed_extra_years=True,
        financial_features_allowed=False, research_ready=False,
        limitations=['API field unit, fiscal scope and report vintages unverified',
                     'Arithmetic and PDF raw-value matches do not accept facts or prove PIT',
                     'H1 flow is not Q2 standalone; absent pages are not proof of nonpublication',
                     'No network, PDF download, OCR or row repair in offline QA'])
    products = {'summary.json': encoded(summary), 'structural_headers.csv': csv_body(structural),
        'unexplained_orphans.csv': csv_body(unresolved)}
    # JSONL has one compact JSON object per line; preserve all observation lineage.
    products['mapped_candidates.jsonl'] = b''.join((json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8') for x in mapped)
    for name, value in [('observation_conflicts', conflicts), ('accounting_checks', arithmetic),
                        ('annual_q4_checks', annual_q4), ('possible_row_displacements', shifts),
                        ('reviewed_pdf_comparisons', reference), ('document_queue', queue)]:
        products[name + '.json'] = encoded(value)
    products['missing_coverage.csv'] = csv_body(gaps)
    products['reviewed_pdf_conflicts.csv'] = csv_body([
        dict(symbol=x['symbol'], year=x['year'], field=x['field'],
             api_raw_value=str(unique_value(x['api'])),
             reviewed_pdf_value=x['pdf_fact']['value'], reviewed_pdf_unit=x['pdf_fact']['unit'],
             pdf_page=x['pdf_fact']['provenance'].get('pdf_page'),
             pdf_path=x['pdf_fact']['provenance'].get('pdf_path'),
             fact_id=x['pdf_fact']['id'], provider_type=x['provider_type'], status=x['status'])
        for x in reference if x['status'] == 'RAW_SAME_UNIT_HYPOTHESIS_CONFLICT'])
    return products, pins, summary


def run(root, config_path, action):
    config = load(inside(root, config_path))
    if config.get('version') != VERSION:
        raise ValueError('unknown QA version')
    products, pins, summary = analyze(root, config)
    pins[config_path] = digest(inside(root, config_path).read_bytes())
    for relative in ['src/delta_t1/experiments/financial_history_qa.py',
                     'scripts/financial_history_qa.py', 'scripts/financial_history_qa.ps1']:
        pins[relative] = digest(inside(root, relative).read_bytes())
    products['input-pins.json'] = encoded(pins)
    report = ('# QA financial history pilot5 — PARTIAL\n\n'
        + f"Đã kiểm {summary['candidate_cells']:,} candidate cells; xác nhận {summary['structural_group_header_zeros']:,} "
          'zero placeholders là tiêu đề nhóm từ template gốc, giữ raw và không coi là financial fact.\n\n'
        + f"Còn {summary['missing_coverage_slots']} coverage slots không có candidate; "
          f"queue {summary['selective_document_queue_periods']} issuer-periods ưu tiên cache/PDF chọn lọc.\n\n"
        + 'Các phép so chỉ là raw-value diagnostics: chưa xác nhận unit/scope/vintage. Không sửa lệch hàng, '
          'không lấy H1 thay Q2, không accept từ việc tổng cân. Xem summary.json và các file lineage.\n\n'
        + f"0 new accepted/PIT facts; baseline FY2025 giữ {summary['reference_metrics_verified']}/{summary['reference_metrics_target']}, VNM F còn thiếu input. "
          'Batch20 và research gates vẫn đóng. Không network/PDF/OCR trong QA offline.\n')
    report += ('\n| Kiểm tra | Kết quả |\n|---|---|\n'
        + f"| Code/label mappings dùng cho diagnostic | {summary['mapped_diagnostic_cells']} |\n"
        + f"| Raw accounting | {json.dumps(summary['raw_accounting_checks'], sort_keys=True)} |\n"
        + f"| Annual–Q4 closing raw comparison | {json.dumps(summary['annual_q4_checks'], sort_keys=True)} |\n"
        + f"| Dấu hiệu lệch hàng cần review | {summary['possible_displacements']} |\n"
        + f"| Reviewed PDF input raw comparison | {json.dumps(summary['reviewed_pdf_comparisons'], sort_keys=True)} |\n"
        + '\nXem [field conflicts và vị trí PDF](reviewed_pdf_conflicts.csv), '
          '[raw observations và provenance đầy đủ](reviewed_pdf_comparisons.json), '
          '[missing coverage](missing_coverage.csv), [queue ưu tiên](document_queue.json). '
          'Số trang PDF trong CSV là trang file (1-based); đơn vị API chưa accepted.\n')
    products['report.md'] = report.encode('utf-8')
    manifest = {name: digest(raw) for name, raw in sorted(products.items())}
    output = inside(root, config['output_root']) / digest(encoded(manifest))[:20]
    if action == 'verify':
        if not output.exists() or load(output / 'manifest.json') != manifest:
            raise ValueError('QA output absent or manifest differs')
        for name, sha in manifest.items():
            if digest((output / name).read_bytes()) != sha:
                raise ValueError('QA product changed: ' + name)
    else:
        for name, raw in {**products, 'manifest.json': encoded(manifest)}.items():
            path = output / name
            if path.exists():
                if path.read_bytes() != raw:
                    raise ValueError('immutable output differs: ' + str(path))
            else:
                immutable_write(path, raw)
    return dict(status='VERIFIED' if action == 'verify' else 'PARTIAL',
                output=output.relative_to(root).as_posix(), **{k: v for k, v in summary.items() if k != 'status'})


def cli(root):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'verify'])
    parser.add_argument('--config', default='configs/data/financial_history_qa_v1.json')
    args = parser.parse_args()
    try:
        print(json.dumps(run(root, args.config, args.action), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED', error=str(error)), ensure_ascii=False))
        raise SystemExit(2)
