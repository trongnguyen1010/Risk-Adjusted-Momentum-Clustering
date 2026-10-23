"""Replay reviewed primary facts without accepting API candidates or PIT dates."""
import json
from decimal import Decimal
from pathlib import Path

from ..features.financial_reference import calculate
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_cafef_pilot import required_keys
from .financial_history_documents import put, read


def check_quarter(review):
    values = {}
    for f in review['facts']:
        if f['unit'] != 'VND' or f['scope'] != 'CONSOLIDATED' or f['framework'] != 'VAS':
            raise ValueError('quarter unit/scope mismatch')
        if f['review_status']!='REVIEWED_REFERENCE_ONLY' or f['interval'] not in ['INSTANT','Q2_STANDALONE','H1_YTD']:
            raise ValueError('unreviewed quarter interval')
        key=(f['interval'],f['field'])
        if key in values:raise ValueError('duplicate quarter field interval')
        values[key]=Decimal(f['value'])
    checks=[]
    equations=[('INSTANT','total_assets',['total_liabilities','total_equity']),
               ('INSTANT','total_assets',['current_assets','noncurrent_assets']),
               ('Q2_STANDALONE','net_revenue',['cost_of_goods_sold','gross_profit']),
               ('H1_YTD','net_revenue',['cost_of_goods_sold','gross_profit'])]
    for interval,left,right in equations:
        delta=values[interval,left]-sum(values[interval,k] for k in right)
        if delta:raise ValueError('quarter reviewed accounting mismatch')
        checks.append(dict(interval=interval,left=left,right=right,difference=str(delta),passed=True))
    if review['quarter_cfo'] is not None:
        raise ValueError('unreviewed H1-to-quarter CFO bridge')
    return checks


def compute_review(facts):
    if len({f['id'] for f in facts}) != len(facts):
        raise ValueError('duplicate reviewed fact ID')
    values = {}
    for f in facts:
        if f['review_status'] != 'REVIEWED_REFERENCE_ONLY' or f['unit'] != 'VND' or f['scope'] != 'CONSOLIDATED' or f['framework'] != 'VAS':
            raise ValueError('review unit/scope/framework mismatch')
        if f.get('pit_ready') is not False or f.get('available_at') is not None:
            raise ValueError('this review has no publication acceptance')
        key = (f['symbol'], f['year'], f['field'])
        if key in values:
            raise ValueError('ambiguous reviewed comparison key')
        values[key] = Decimal(f['value'])
    metrics, checks, gaps = [], [], []
    for symbol, year in sorted({(f['symbol'], f['year']) for f in facts}):
        current = {field: str(v) for (s,y,field),v in values.items() if (s,y)==(symbol,year)}
        for name, left, right in [('BALANCE', 'total_assets',['total_liabilities','total_equity']),
                                  ('GROSS_PROFIT','net_revenue',['cost_of_goods_sold','gross_profit'])]:
            if not all(k in current for k in [left]+right):
                continue
            delta=Decimal(current[left])-sum(Decimal(current[k]) for k in right)
            checks.append(dict(symbol=symbol,year=year,check=name,difference=str(delta),passed=delta==0))
            if delta:
                raise ValueError('review accounting difference: '+name)
        # Same declared document-reconciled EBIT bridge used by the FY2025 baseline.
        if 'profit_before_tax' in current and 'interest_expense' in current:
            current['document_reconciled_ebit']=str(Decimal(current['profit_before_tax'])+Decimal(current['interest_expense']))
        result=calculate('Z_SCORE',current)
        metrics.append(dict(symbol=symbol,year=year,family='Z_SCORE',variant='ANNUAL_EM_Z_DOUBLE_PRIME_PLUS_3_25_REFERENCE',
            result=result,dependency_ids=[f['id'] for f in facts if f['symbol']==symbol and f['year']==year],
            ebit_derivation=dict(operation='profit_before_tax + interest_expense',value=current.get('document_reconciled_ebit')),
            temporal_status='FY2015_DOCUMENT_CURRENT_OR_COMPARATIVE_REFERENCE_NOT_PIT',pit_ready=False))
        for family in ['EPS','PE','PB','F_SCORE','M_SCORE']:
            missing=[dict(field=field,year=year+offset) for field,offset in sorted(required_keys(family))
                     if (symbol,year+offset,field) not in values]
            gaps.append(dict(symbol=symbol,year=year,family=family,value=None,missing=missing,
                reason='MISSING_REVIEWED_DEPENDENCIES_OR_VALUATION_EVIDENCE',pit_ready=False))
    return dict(metrics=metrics,accounting_checks=checks,missing_inputs=gaps,new_reference_facts=len(facts),
                new_reference_metrics=sum(m['result']['value'] is not None for m in metrics),
                baseline_2025_metrics_unchanged=True,pit_ready=False,financial_features_allowed=False)


def run(root, action):
    source='data/financial/history_document_supplement_v2/review/01-gmd2015-reference-review.json'
    conflicts='data/financial/history_document_supplement_v2/review/02-cache-conflict-disposition.json'
    quarter_path='data/financial/history_document_supplement_v2/review/03-fpt2024q2-reference-review.json'
    review=read(inside(root,source));disposition=read(inside(root,conflicts));quarter=read(inside(root,quarter_path))
    pins={p:digest(inside(root,p).read_bytes()) for p in [source,conflicts,quarter_path,quarter['date_policy'],
        'src/delta_t1/experiments/financial_history_review.py','scripts/financial_history_review.py',
        'src/delta_t1/features/financial_reference.py','src/delta_t1/experiments/financial_cafef_pilot.py']}
    for f in review['facts'] + disposition['rows'] + quarter['facts']:
        p=f.get('provenance',f)
        for name in ['pdf','image']:
            relative=p[name+'_path'];sha=digest(inside(root,relative).read_bytes())
            if sha!=p[name+'_sha256']:raise ValueError('review evidence changed: '+relative)
            pins[relative]=sha
    result=compute_review(review['facts'])
    from ..ingestion.financial_date_pit import next_session
    calendar=inside(root,quarter['calendar_path']);raw=calendar.read_bytes()
    if digest(raw)!=quarter['calendar_sha256']:raise ValueError('date policy calendar changed')
    pins[quarter['calendar_path']]=digest(raw)
    pub=quarter['publication'];e=pub['evidence']
    if any(f['provenance']['pdf_sha256']!=pub['pdf_sha256'] for f in quarter['facts']):
        raise ValueError('publication is not linked to exact fact document')
    if pub['publication_date'] <= max(f['period_end'] for f in quarter['facts']):
        raise ValueError('publication before quarter completion')
    if digest(inside(root,e['image_path']).read_bytes())!=e['image_sha256']:
        raise ValueError('publication image changed')
    pins[e['image_path']]=e['image_sha256']
    if pub['validation_status']!='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED' or pub['precision']!='DATE_ONLY':
        raise ValueError('unreviewed publication evidence')
    usable,status=next_session(pub['publication_date'],'HOSE',[json.loads(line) for line in raw.splitlines()])
    if (usable,status)!=(pub['usable_from_date'],pub['date_pit_status']):raise ValueError('date overlay changed')
    result.update(quarter_reference_facts=len(quarter['facts']),quarter_accounting_checks=check_quarter(quarter),
        quarter_publication=pub,quarter_cfo=None,quarter_cfo_reason=quarter['quarter_cfo_reason'],
        total_new_reviewed_reference_facts=len(review['facts'])+len(quarter['facts']),
        complete_new_pit_metrics=0)
    result.update(cache_conflicts_reconfirmed=len(disposition['rows']),status='PARTIAL',
        source_publication_date=None,source_signature_dates_are_not_publication=True)
    products={'input-pins.json':encoded(pins),'reference-results.json':encoded(result),
        'report.md':('# Financial history — bổ sung PDF/OCR và reference review\n\n'
        'GMD FY2015: tải PDF hợp nhất kiểm toán từ issuer,13 MB; text layer không có. '
        'OCR CPU vie+eng tự động đúng8trang được chọn, xuất text/TSV/confidence; visual review xác nhận40facts '
        '(20fields ×2015/2014 comparative). Bốn accounting checks PASS; tính lại2Z annual EM Z″ +3,25 bằng calculator cũ.\n\n'
        'Các facts 2014 là comparative trong vintage2015, không áp ngược làm original2014/PIT. '
        'Không dùng EPS reported thay EPS tính lại; F/M/EPS/PE/PB còn missing dependencies trong reference-results.json.\n\n'
        '12conflicts trước đây đã đối chiếu lại7ảnh trang cache, giữ reviewed PDF reference và quarantine API. '
        'Không thay baseline29/30 hoặc sửa raw. VNM F vẫn thiếu original-maturity current portion.\n\n'
        'FPT H1/2024 observed URL trả404 một lần, đã seal receipt; không retry hoặc coi H1=Q2. '
        'Sau đó tìm được original Q2/2024 PDF trong cache: review23facts, giữ INSTANT/Q2_STANDALONE/H1_YTD riêng, '
        '4accounting checks PASS. Explicit publication18/07/2024 → usable19/07/2024 theo existing observed-calendar policy; '
        'chưa có complete PIT metrics, không annualize lợi nhuận quý hoặc dùng H1 CFO thay Q2. '
        'Dữ liệu lịch sử và PIT vẫn PARTIAL; chưa batch20 hoặc backtest.\n').encode('utf-8')}
    manifest={n:digest(b) for n,b in sorted(products.items())}
    out=inside(root,'data/financial/history_reference_review_v1')/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=manifest:raise ValueError('reference manifest differs')
        for n,h in manifest.items():
            if digest((out/n).read_bytes())!=h:raise ValueError('reference result changed')
    else:
        for n,b in products.items():put(out/n,b)
        put(out/'manifest.json',manifest)
    return dict(status='VERIFIED' if action=='verify' else 'PARTIAL',output=out.relative_to(root).as_posix(),
        new_reference_facts=result['new_reference_facts'],new_reference_metrics=result['new_reference_metrics'],
        cache_conflicts_reconfirmed=result['cache_conflicts_reconfirmed'],pit_ready=False)
