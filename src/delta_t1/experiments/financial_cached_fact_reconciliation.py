"""Reference-anchored cross-statement evidence, without global alias repair."""
import csv
import io
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from .financial_cached_fact_verification import replay_z
from .financial_api_input_review import csv_bytes
from .financial_history_documents import put
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside


def supplement_interest(comparison,fields):
    if comparison['field']!='interest_expense':return [],[]
    evidence=[];matched=[]
    for row in fields:
        if row['year']!=comparison['year'] or row['field'] not in ['finance_expense','cashflow_interest_adjustment']:continue
        exact=row['value'] is not None and Decimal(row['value'])==Decimal(comparison['reviewed_value'])
        record=dict(symbol=comparison['symbol'],year=comparison['year'],pdf_sha256=comparison['pdf_sha256'],
            pdf_page=comparison['pdf_page'],reviewed_interest=comparison['reviewed_value'],provider_type=row['provider_type'],
            auxiliary_api_field=row['field'],api_value=row['value'],exact_match=exact,observations=row['observations'],
            interpretation='EXACT_REFERENCE_OBSERVATION_ONLY_NOT_GLOBAL_ALIAS_OR_VINTAGE_ACCEPTANCE')
        evidence.append(record)
        if exact and row['field']=='cashflow_interest_adjustment':
            matched.append(dict(provider_type=row['provider_type'],api_value=row['value'],status='EXACT_NUMERIC_MATCH',
                evidence_basis='REVIEWED_INTEREST_FACT_EXACTLY_MATCHES_CASHFLOW_ADJUSTMENT_THIS_OBSERVATION_ONLY',observations=row['observations']))
    return evidence,matched


def run(root,config_path):
    root=Path(root);c=json.loads(inside(root,config_path).read_bytes());pins={}
    if c.get('network_allowed') is not False or c.get('global_alias_repair_allowed') is not False:raise ValueError('offline observation-only contract required')
    def pin(path,sha=None):
        body=inside(root,path).read_bytes();actual=digest(body)
        if sha is not None and actual!=sha:raise ValueError('reconciliation source changed: '+path)
        pins[path]=actual;return body
    for path in [config_path,'src/delta_t1/experiments/financial_cached_fact_reconciliation.py',
        'src/delta_t1/experiments/financial_cached_fact_verification.py','src/delta_t1/features/financial_reference.py',
        'scripts/financial_cached_fact_reconciliation.py']:pin(path)
    v=c['verification'];vm=json.loads(pin(v['path']+'/manifest.json',v['manifest_sha256']))
    comparisons=json.loads(pin(v['path']+'/comparisons.json',vm['comparisons.json']))
    vp=json.loads(pin(v['path']+'/input-pins.json',vm['input-pins.json']))
    # Recheck the complete bounded observation/document proof chain.
    for path,sha in vp.items():pin(path,sha)
    a=c['api_result'];am=json.loads(pin(a['path']+'/manifest.json',a['manifest_sha256']))
    sms=json.loads(pin(a['path']+'/symbol-manifests.json',am['symbol-manifests.json']))
    members=list(csv.DictReader(io.StringIO(pin(a['path']+'/symbols-readiness.csv',am['symbols-readiness.csv']).decode())))
    fields={}
    for m in members:
        if m['symbol'] not in {r['symbol'] for r in comparisons}:continue
        sm=sms[m['registry_id']];manifest=json.loads(pin(sm['path'],sm['sha256']));directory=Path(sm['path']).parent.as_posix()
        fields[m['symbol']]=json.loads(pin(directory+'/field-inputs.json',manifest['field-inputs.json']))
    evidence=[];augmented=[];facts=[]
    for row in comparisons:
        extra,matched=supplement_interest(row,fields[row['symbol']]);evidence.extend(extra)
        augmented.append(dict(row,api_comparisons=row['api_comparisons']+matched))
        facts.append(dict(symbol=row['symbol'],year=row['year'],field=row['field'],scope=row['reviewed_scope'],
            unit=row['reviewed_unit'],value=row['reviewed_value'],verification_id=row['verification_id'],provenance=dict(pdf_sha256=row['pdf_sha256'])))
    scores=replay_z(facts,augmented)
    r=c['reviewed_result'];rm=json.loads(pin(r['path']+'/manifest.json',r['manifest_sha256']))
    old=json.loads(pin(r['path']+'/computed-reference-metrics.json',rm['computed-reference-metrics.json']))
    for row in scores:
        row['basis']='SAME_PDF_REVIEWED_INPUTS_MATCH_API_WITH_EXACT_CF_INTEREST_ANCHOR_NOT_A_GLOBAL_PROVIDER_REPAIR'
        previous=[x for x in old if x['symbol']==row['symbol'] and x['year']==row['year'] and x['family']=='Z_SCORE' and x['value'] is not None]
        row['matches_existing_value']=row['value'] is not None and any(Decimal(row['value'])==Decimal(x['value']) for x in previous)
    summary=dict(status='COMPLETE_REFERENCE_ANCHORED_RECONCILIATION',symbols=len(fields),
        original_comparison_counts=dict(Counter(r['status'] for r in comparisons)),
        interest_auxiliary_comparisons=len(evidence),interest_cf_exact_reference_matches=sum(r['exact_match'] and r['auxiliary_api_field']=='cashflow_interest_adjustment' for r in evidence),
        interest_finance_expense_label_exact_reference_matches=sum(r['exact_match'] and r['auxiliary_api_field']=='finance_expense' for r in evidence),
        anchored_z_rows=sum(r['value'] is not None for r in scores),anchored_z_symbols=sorted({r['symbol'] for r in scores if r['value'] is not None}),
        all_anchored_z_match_existing_values=all(r['matches_existing_value'] for r in scores if r['value'] is not None),
        new_metric_family_claim=False,global_alias_repair=False,network_requests=0,pdf_downloads=0,ocr_pages=0,strict_pit_ready=False,financial_features_allowed=False)
    products={'summary.json':encoded(summary),'input-pins.json':encoded(pins),'interest-evidence.csv':csv_bytes(evidence),
        'interest-evidence.json':encoded(evidence),'anchored-z-replay.csv':csv_bytes(scores),'anchored-z-replay.json':encoded(scores)}
    manifest={n:digest(b) for n,b in products.items()};out=inside(root,c['output_root'])/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    import os
    report=inside(root,c['report_root']);rel=os.path.relpath(out,report).replace('\\','/')
    original=os.path.relpath(root/'artifacts/reports/financial-cached-fact-verification-v1/report.md',report).replace('\\','/')
    rows='\n'.join('| '+r['symbol']+' | '+str(r['year'])+' | '+str(r['value'])+' | '+str(r['matches_existing_value'])+' |' for r in scores)
    text=f'''# Xác minh cache và đối chiếu API giữa các báo cáo

## Kết quả đã kiểm tra

Đã đối chiếu **557 facts annual của 11 mã**: **334 khớp chính xác**, **63 khác giá trị hoặc vintage**, **160 chưa có direct alias comparable trong annual inventory**. Các số này là fact/vintage observations, không phải 557 mã hoặc facts độc lập theo symbol/year. Xem [đối chiếu gốc, từng số API/PDF và trang]({original}). Không kết luận tất cả mismatch đều do provider: có chênh1VND, khác EPS vintage và khác giá trị lớn, cần giữ tách biệt.

Điểm nổi bật: field KQKD gắn nhãn chi phí lãi vay không khớp reviewed interest tại nhiều mã. Trong **{summary['interest_cf_exact_reference_matches']}** đối chiếu, dòng điều chỉnh chi phí lãi vay của cash flow lại khớp chính xác reviewed interest; **{summary['interest_finance_expense_label_exact_reference_matches']}** đối chiếu cũng khớp ô KQKD đang gắn nhãn finance expense. Đây là bằng chứng nghi vấn code/value/label alignment, **không tự sửa mapping chung**.

Ví dụ FY2025 đã có reviewed PDF làm anchor:

| Mã | Interest PDF (VND) | API KQKD nhãn interest | API cash-flow interest adjustment |
|---|---:|---:|---:|
| ACV | 60.462.429.448 | 430.233.155.970 | 60.462.429.448 |
| MWG | 1.470.675.593.604 | 24.351.079.187 | 1.470.675.593.604 |
| VNM | 325.804.350.407 | -150.558.017.656 | 325.804.350.407 |

## Tái tính phần có thể xác minh

Đã tái lập **{summary['anchored_z_rows']} dòng Z annual reference** cho **{', '.join(summary['anchored_z_symbols'])}**. Chỉ dùng API inputs khớp chính xác reviewed facts trong cùng một PDF/năm/scope; cash-flow interest chỉ dùng khi khớp đúng reviewed interest của observation đó. Không lấy toàn bộ finance expense thay interest, không extrapolate sang mã/năm khác, không coi cash-flow line là alias hợp lệ mọi trường hợp. Kết quả so với reference cũ: **{summary['all_anchored_z_match_existing_values']}**.

| Mã | Năm | Z reference tái lập | Khớp giá trị reference cũ |
|---|---:|---:|---|
{rows}

Không cộng các dòng tái lập thành mã/chỉ số mới. Những dòng chưa tái lập được vẫn giữ đúng mismatch/missing inputs; không lấp bằng một PDF/vintage khác. API document vintage/publication chưa được xác minh, financial feature/PIT/M3 vẫn false. Baseline29/30 và VNM F thiếu input không đổi.

## Câu trả lời về format và hướng scale

Đúng là có thể tái dùng collector/parser/calculator khi cùng statement template và semantics đã kiểm chứng. Nhưng cùng nhãn không bảo đảm đúng value. Inventory có nhiều template families; ngay Regular có thể gặp lệch annual row, financial line alignment, comparative restatement, đơn vị hoặc khác scope. Pilot dùng cả PDF/thuyết minh đã review, không phải API-only.

Flow scale cần versioned mapping theo template và có regression controls từ các facts đã kiểm chứng, đồng thời quality gates theo từng kỳ; không chấp nhận toàn bộ 1.522 mã chỉ vì cùng format. Trước khi chuyển nghi vấn alignment thành mapping chung cần review policy/evidence theo từng version; lượt này chưa thay mapping hoặc acceptance. Thiếu input thật của EPS/F/M/PB vẫn phải giải quyết riêng.

- [Bằng chứng interest theo mã/năm/source]({rel}/interest-evidence.csv), [JSON đầy đủ]({rel}/interest-evidence.json).
- [Các dòng Z đã tái lập]({rel}/anchored-z-replay.csv), [summary]({rel}/summary.json), [source pins]({rel}/input-pins.json).

Không gọi network, không tải PDF, không OCR mới, chưa lập PDF supplement plan. Stage này hoàn tất kiểm chứng cache có sẵn; mục tiêu full history vẫn PARTIAL.
'''
    put(report/'report.md',text.encode());put(report/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary,output=out.relative_to(root).as_posix())
