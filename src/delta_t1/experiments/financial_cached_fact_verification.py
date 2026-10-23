"""Compare sealed API observations with existing reviewed document facts offline.

Exact numeric matches validate this observation against this reference only;
they never identify an API document vintage or validate other issuers/years.
"""
import csv
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from .financial_api_input_review import csv_bytes
from .financial_history_documents import put, read
from .financial_reviewed_batch import validate_fact
from .financial_acquisition_overnight import state_file
from ..features.financial_reference import calculate
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

VERSION='financial-cached-fact-verification-v1'
API_FIELD_NAMES={'noncontrolling_equity':'noncontrolling_interests'}
Z_FIELDS={'current_assets','current_liabilities','total_assets','retained_earnings','total_equity','total_liabilities'}
CODE=['src/delta_t1/experiments/financial_cached_fact_verification.py',
      'scripts/financial_cached_fact_verification.py',
      'src/delta_t1/experiments/financial_api_input_review.py',
      'src/delta_t1/experiments/financial_reviewed_batch.py',
      'src/delta_t1/features/financial_reference.py']


def normalize_reviewed_schema(fact):
    """Spelling/schema compatibility for reviewed packages, never an API multiplier."""
    result=dict(fact)
    if result['unit'] in {'VND_PER_SHARE','shares'}:
        result['original_reviewed_unit']=result['unit']
        result['unit']={'VND_PER_SHARE':'VND/share','shares':'SHARES'}[result['unit']]
    if result['field']=='weighted_basic_shares':
        result['original_reviewed_field']=result['field']
        result['field']='weighted_average_basic_shares'
    return result


def compare_fact(fact, rows):
    field=API_FIELD_NAMES.get(fact['field'],fact['field'])
    cells=[r for r in rows if (r['year'],r['field'])==(fact['year'],field)]
    result=[]
    for cell in cells:
        exact=cell['value'] is not None and Decimal(cell['value'])==Decimal(fact['value'])
        result.append(dict(provider_type=cell['provider_type'],api_value=cell['value'],
            status='EXACT_NUMERIC_MATCH' if exact else 'API_VALUE_AMBIGUOUS_OR_MISSING' if cell['value'] is None else 'NUMERIC_DIFFERENCE_OR_VINTAGE',
            difference=str(Decimal(cell['value'])-Decimal(fact['value'])) if cell['value'] is not None else None,
            observations=cell['observations']))
    return result


def replay_z(facts, comparisons):
    """Same reviewed PDF/year/scope only, and every API input must match exactly."""
    groups=defaultdict(list);result=[]
    for fact in facts:
        groups[fact['symbol'],fact['year'],fact['scope'],fact['provenance']['pdf_sha256']].append(fact)
    for (symbol,year,scope,pdf),fs in sorted(groups.items()):
        if scope=='COMPANY_REPORTED':continue
        by_field=defaultdict(list)
        for f in fs:by_field[f['field']].append(f)
        # No selection when a reviewed package itself contains conflicting values.
        unique={f:rs[0]['value'] for f,rs in by_field.items() if len({(Decimal(r['value']),r['unit']) for r in rs})==1}
        if not Z_FIELDS<=unique.keys():continue
        if Decimal(unique['total_assets'])!=Decimal(unique['total_equity'])+Decimal(unique['total_liabilities']):continue
        bridge={'profit_before_tax','interest_expense'}<=unique.keys()
        direct='document_reconciled_ebit' in unique
        if not bridge and not direct:continue
        required=Z_FIELDS|({'profit_before_tax','interest_expense'} if bridge else {'document_reconciled_ebit'})
        ids={f['verification_id'] for f in fs if f['field'] in required}
        by_provider=defaultdict(set)
        for comparison in comparisons:
            if comparison['verification_id'] in ids:
                for item in comparison['api_comparisons']:
                    if item['status']=='EXACT_NUMERIC_MATCH':by_provider[item['provider_type']].add(comparison['field'])
        for provider,fields in sorted(by_provider.items(),key=str):
            if not required<=fields:continue
            values={f:unique[f] for f in Z_FIELDS}
            ebit=str(Decimal(unique['profit_before_tax'])+Decimal(unique['interest_expense'])) if bridge else unique['document_reconciled_ebit']
            if direct and Decimal(ebit)!=Decimal(unique['document_reconciled_ebit']):continue
            values['document_reconciled_ebit']=ebit
            score=calculate('Z_SCORE',values)
            result.append(dict(symbol=symbol,year=year,input_scope=scope,pdf_sha256=pdf,provider_type=provider,
                family='Z_SCORE',value=score['value']['em_z_double_prime_reference'] if score['value'] else None,
                status='API_VALUES_REPRODUCE_SAME_PDF_REVIEWED_REFERENCE' if score['value'] else score['status'],
                verification_ids=sorted(ids),api_document_vintage_verified=False,new_metric_family_claim=False,
                strict_pit_ready=False,financial_features_allowed=False))
    return result


def run(root,config_path):
    root=Path(root);c=read(inside(root,config_path));pins={}
    if c['version']!=VERSION or any(c.get(k) is not False for k in ['network_allowed','pdf_download_allowed','ocr_allowed','cross_issuer_acceptance_allowed']):
        raise ValueError('explicit offline same-observation verification contract required')
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('verification input changed: '+path)
        pins[path]=sha;return body
    for p in CODE+[config_path]:pin(p)
    def sealed(item):
        manifest=json.loads(pin(item['path']+'/manifest.json',item['manifest_sha256']))
        def get(name):return json.loads(pin(item['path']+'/'+name,manifest[name]))
        return manifest,get
    rm,ref=sealed(c['reviewed_result']);review_pins=ref('input-pins.json')
    am,api=sealed(c['api_result']);symbol_manifests=api('symbol-manifests.json')
    members=list(csv.DictReader(io.StringIO(pin(c['api_result']['path']+'/symbols-readiness.csv',am['symbols-readiness.csv']).decode('utf-8'))))
    by_symbol={r['symbol']:r for r in members}
    facts=[];excluded=Counter()
    for item in c['fact_sources']:
        if item['path'] not in review_pins:raise ValueError('fact source not pinned by previous reviewed replay')
        package=json.loads(pin(item['path'],review_pins[item['path']]))
        if item['kind']=='MANIFEST_FACTS':
            package=json.loads(pin(str(Path(item['path']).parent/'facts.json').replace('\\','/'),package['facts.json']))
        elif item['kind']=='PILOT':package=package['facts']
        elif item['kind']=='SCALE_REVIEWED_CONFIG':
            normalized=[]
            for doc in package['documents']:
                if doc['months']!=12 or doc['scope']!='CONSOLIDATED' or doc['framework']!='VAS':raise ValueError('scale scope/interval differs')
                for f in doc['facts']:
                    if f['review_status']!='VISUALLY_VERIFIED_REFERENCE_ONLY':raise ValueError('unreviewed scale fact')
                    normalized.append(dict(f,id=doc['symbol']+':'+str(doc['year'])+':'+f['field'],symbol=doc['symbol'],year=doc['year'],
                        scope=doc['scope'],framework=doc['framework'],review_status='REVIEWED_REFERENCE_ONLY',
                        provenance=dict(pdf_path=doc['pdf_path'],pdf_sha256=doc['pdf_sha256'],pdf_page=f['pdf_page'],
                                        source_review_status=f['review_status'])))
            package=normalized
        else:raise ValueError('unknown reviewed source kind')
        for f in package:
            if f.get('interval') or not 2012<=f['year']<=2025:
                excluded['nonannual_or_outside_range']+=1;continue
            f=normalize_reviewed_schema(f)
            validate_fact(f,f['scope'])
            p=f['provenance']
            if not p.get('pdf_path') or not p.get('pdf_sha256'):
                excluded['no_pdf_provenance']+=1;continue
            # Scale PDFs are hash-declared directly by the already pinned review
            # config; other bundles use the replay's transitive source pins.
            if item['kind']!='SCALE_REVIEWED_CONFIG' and review_pins.get(p['pdf_path'])!=p['pdf_sha256']:
                raise ValueError('reviewed document not in frozen source chain')
            if p['pdf_path'] not in pins:pin(p['pdf_path'],p['pdf_sha256'])
            image=p.get('image_path')
            if image:
                expected=p.get('image_sha256') or review_pins.get(image)
                if not expected:raise ValueError('reviewed image has no hash')
                if image not in pins:pin(image,expected)
            f=dict(f,source_package=item['path'])
            f['verification_id']=digest(encoded({k:f[k] for k in ['symbol','year','field','value','unit','scope','provenance']}))[:24]
            facts.append(f)
    # Preserve vintages, remove only identical repeated fact records.
    facts=list({f['verification_id']:f for f in facts}.values())
    fields={};comparisons=[]
    for symbol in sorted({f['symbol'] for f in facts}):
        m=symbol_manifests[by_symbol[symbol]['registry_id']];manifest=json.loads(pin(m['path'],m['sha256']))
        directory=Path(m['path']).parent.as_posix()
        fields[symbol]=json.loads(pin(directory+'/field-inputs.json',manifest['field-inputs.json']))
        # Revalidate exact raw bytes used by these observations (not just derived CSV).
        for row in fields[symbol]:
            for obs in row['observations']:
                if obs['source_path'] not in pins:pin(obs['source_path'],obs['source_sha256'])
    for f in facts:
        items=compare_fact(f,fields[f['symbol']]);statuses={r['status'] for r in items}
        status='EXACT_VALUE_MATCH_WITH_COMPETING_PARTITION_DIFFERENCE' if 'EXACT_NUMERIC_MATCH' in statuses and len(statuses)>1 else 'EXACT_VALUE_MATCH_TO_REVIEWED_DOCUMENT' if 'EXACT_NUMERIC_MATCH' in statuses else 'NUMERIC_DIFFERENCE_OR_VINTAGE' if items else 'NO_COMPARABLE_DIRECT_ALIAS_IN_ANNUAL_INVENTORY'
        p=f['provenance'];comparisons.append(dict(verification_id=f['verification_id'],fact_id=f['id'],symbol=f['symbol'],year=f['year'],field=f['field'],
            reviewed_value=f['value'],reviewed_unit=f['unit'],reviewed_scope=f['scope'],pdf_sha256=p['pdf_sha256'],pdf_path=p['pdf_path'],pdf_page=p.get('pdf_page'),
            image_path=p.get('image_path'),source_package=f['source_package'],status=status,api_comparisons=items,
            verified_observation_only='EXACT_VALUE_MATCH' in status,cross_issuer_year_acceptance_allowed=False,
            api_document_vintage_verified=False,strict_pit_ready=False,financial_features_allowed=False))
    scores=replay_z(facts,comparisons)
    old=ref('computed-reference-metrics.json')
    for score in scores:
        previous=[r for r in old if r['symbol']==score['symbol'] and r['year']==score['year'] and r['family']=='Z_SCORE' and r['value'] is not None]
        score['matches_existing_value']=any(Decimal(r['value'])==Decimal(score['value']) for r in previous) if score['value'] is not None else False
    symbol_summary=[]
    for symbol in sorted(fields):
        rs=[r for r in comparisons if r['symbol']==symbol]
        symbol_summary.append(dict(symbol=symbol,comparison_rows=len(rs),status_counts=dict(Counter(r['status'] for r in rs)),
            reproduced_z_rows=sum(r['symbol']==symbol and r['value'] is not None for r in scores)))
    summary=dict(status='COMPLETE_CACHED_FACT_VERIFICATION',financial_delivery='PARTIAL_REFERENCE_OBSERVATION_VALIDATION_ONLY',
        symbols=len(fields),reviewed_annual_facts=len(facts),comparison_statuses=dict(Counter(r['status'] for r in comparisons)),
        reproduced_z_rows=sum(r['value'] is not None for r in scores),reproduced_z_symbols=len({r['symbol'] for r in scores if r['value'] is not None}),
        new_z_keys=sorted({(r['symbol'],r['year']) for r in scores if r['value'] is not None and not any(x['symbol']==r['symbol'] and x['year']==r['year'] and x['family']=='Z_SCORE' and x['value'] is not None for x in old)}),
        excluded_facts=dict(excluded),network_requests=0,pdf_downloads=0,ocr_pages=0,
        full10y_six_family_verified=0,api_scope_or_vintage_auto_accepted=False,financial_features_allowed=False)
    products={'summary.json':encoded(summary),'input-pins.json':encoded(pins),'comparisons.json':encoded(comparisons),
        'comparisons.csv':csv_bytes(comparisons),'symbols.csv':csv_bytes(symbol_summary),
        'api-anchored-z-replay.json':encoded(scores),'api-anchored-z-replay.csv':csv_bytes(scores)}
    manifest={n:digest(b) for n,b in products.items()};out=inside(root,c['output_root'])/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    import os
    report=inside(root,c['report_root']);relative=os.path.relpath(out,report).replace('\\','/')
    rows='\n'.join('| '+r['symbol']+' | '+str(r['comparison_rows'])+' | '+str(sum(n for k,n in r['status_counts'].items() if k.startswith('EXACT_VALUE_MATCH')))+' | '+str(r['reproduced_z_rows'])+' |' for r in symbol_summary)
    text=f'''# Xác minh API bằng input reviewed đã cache

Đã đối chiếu **{len(facts)} facts annual**, **{len(fields)} mã**, từng mã–năm–field với số PDF/thuyết minh đã review. Hash nguồn/API/PDF/image được kiểm lại, không tải PDF/OCR mới. Kết quả: **{summary['comparison_statuses']}**. Mismatch là khác giá trị hoặc vintage, chưa tự kết luận toàn bộ là provider nhập sai.

| Mã | Facts đối chiếu | Facts có ít nhất một partition khớp chính xác | Dòng Z tái lập từ API khớp reference |
|---|---:|---:|---:|
{rows}

## Cùng format có tái dùng được không?

Cùng collector và exact code/label cho phép tái dùng parser/công thức. Không chứng minh cùng đơn vị, scope, vintage hoặc ô giá trị đúng. Trong inventory trước có Regular1429/Securities42/Bank29/UNKNOWN22 (diagnostic classification, không phải historical sector acceptance). Pilot29/30 dùng reviewed PDF/note inputs bổ sung; không phải kết quả API-only. Chỉ chốt khớp cho đúng observation đối chiếu, không tự mở acceptance cho mã hoặc năm khác.

Các fact không có direct alias vẫn được giữ trong report: EPS numerator/weighted shares, parent issuance/current debt portion và pure depreciation thường nằm ở thuyết minh; có tiền vốn góp, aggregate D&A hoặc EPS công bố không đủ thay thế. API field có giá trị nhưng khác reviewed PDF/vintage được giữ cả hai để review, không repair/shift/average hoặc chọn latest.

## Tính lại phần có đủ bằng chứng

Tái lập **{summary['reproduced_z_rows']} dòng Z annual reference / {summary['reproduced_z_symbols']} mã** chỉ khi các input API cùng provider partition khớp chính xác facts cùng một PDF/năm/scope; EBIT dùng bridge PBT+interest đã có reviewed facts. Không trộn các PDF/vintages để lấp input. Source PDF/note là anchor của numerical reference; chưa chứng minh API report identity/publication, không mở PIT/backtest. Keys Z reference chưa xuất hiện trong stage33: **{summary['new_z_keys']}**. Dòng trùng metric/key không cộng thành mã mới.

## Bằng chứng và bước sau

- [Comparisons có giá trị API/PDF, trang, scope và vintage]({relative}/comparisons.csv), [JSON đầy đủ]({relative}/comparisons.json).
- [Tổng theo mã]({relative}/symbols.csv), [Z đã tái lập]({relative}/api-anchored-z-replay.csv), [summary]({relative}/summary.json).
- [Pins]({relative}/input-pins.json): exact document và API hashes, không suy đơn vị từ magnitude.

Xác minh này mở rộng bằng chứng field-level cho phần cache hiện có, không tuyên bố 1.522 mã đều đúng hay thiếu. Việc tăng số mã verified cần đủ evidence riêng của các mã/kỳ đó. Ưu tiên cache/API mapping trước; phần thiếu cần tài liệu mới phải báo owner trước khi lập bổ sung PDF plan. Lượt này không lập plan hoặc acquire tài liệu mới. Financial delivery vẫn PARTIAL.
'''
    put(report/'report.md',text.encode('utf-8'));put(report/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    state_file(inside(root,c['output_root'])/'pipeline-status.json',summary['status'],output=out.relative_to(root).as_posix(),report=(report/'report.md').relative_to(root).as_posix())
    return dict(summary,output=out.relative_to(root).as_posix())
