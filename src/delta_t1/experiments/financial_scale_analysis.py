"""Measured scale diagnostics; candidate arithmetic is never accepted financial data."""
import hashlib
import json
import subprocess
import sys
import unicodedata
from collections import Counter
from decimal import Decimal
from pathlib import Path

from .financial_scale_probe import CLOSED, verify
from ..features.financial_reference import calculate
from ..features.financial_vas_reference import calculate_vas_f_score, calculate_vas_m_score
from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside, seal
from ..ingestion.financial_crawl_candidates import csv_bytes

TERMS={
    'BALANCE':['can doi ke toan','bao cao tinh hinh tai chinh','balance sheet'],
    'INCOME':['ket qua hoat dong kinh doanh','income statement','statement of income'],
    'CASHFLOW':['luu chuyen tien te','cash flows'],
    'EPS_SHARES':['lai co ban tren co phieu','lai tren co phieu','earnings per share','weighted average','binh quan gia quyen'],
    'DEBT':['vay va no thue tai chinh','borrowings','den han tra','current portion'],
    'PPE':['tai san co dinh huu hinh','tangible fixed assets','depreciation'],
    'PUBLICATION':['cong bo thong tin','disclosed on','published on'],
    'UNITS':['don vi tinh','don vi:','currency:','vnd','trieu dong'],
}


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower().replace('đ','d')) if not unicodedata.combining(c))


def hints(pages):
    result=[]
    for p in pages:
        text=normalize(p['text'])
        matched=[k for k,terms in TERMS.items() if any(t in text for t in terms)]
        if matched:result.append(dict(pdf_page=p['pdf_page'],categories=matched))
    return result


def candidate_math(requirements, symbol, year, company_type):
    """Preserve missing notes. Only existing formulas are used as diagnostics.

    EBIT arithmetic hypothesis EBT+interest is explicitly unreviewed; it is not
    stored as a reconciled fact. Units/scope/vintage/PIT remain unaccepted.
    """
    mapping={}
    for r in requirements:
        if r['symbol']!=symbol or len(r.get('candidate_values',[]))!=1:continue
        v=Decimal(r['candidate_values'][0])
        if v.is_finite():mapping[r['field'],r['year']-year]=v
    base=dict(symbol=symbol,year=year,acceptance='UNREVIEWED_PROVIDER_DIAGNOSTIC_ONLY',
              unit_scope_vintage_status='NOT_ACCEPTED',publication_status='NOT_ACCEPTED',**CLOSED)
    if company_type!='Regular':
        return dict(base,status='SECTOR_TEMPLATE_REQUIRED',f_signals=None,m_value=None,z_arithmetic=None,
                    vendor_basic_eps=None,missing_notes=['SECTOR_SPECIFIC_DEFINITION'])
    f=calculate_vas_f_score(mapping)
    m=calculate_vas_m_score(mapping,'GROSS_SHORT_TERM_TRADE')
    fields=['current_assets','current_liabilities','total_assets','total_liabilities','total_equity',
            'retained_earnings','profit_before_tax','interest_expense']
    missing=[k for k in fields if (k,0) not in mapping]
    balance=None;z=None
    if not missing:
        v={k:mapping[k,0] for k in fields}
        balance=abs(v['total_assets']-v['total_liabilities']-v['total_equity'])
        if balance<=Decimal('1'):
            # Formula input only, never a reviewed EBIT fact or PIT claim.
            v['document_reconciled_ebit']=v['profit_before_tax']+v['interest_expense']
            result=calculate('Z_SCORE',v)
            z=result['value']['em_z_double_prime_reference'] if result['value'] else None
    return dict(base,status='CANDIDATE_DIAGNOSTICS_EVALUATED',f_signals=f['signals'],
        f_known_signals=f['known_signals'],f_full_value=f['value'],m_value=m['value'],m_missing=m.get('missing',[]),
        z_arithmetic=z,z_missing_fields=missing,balance_arithmetic_residual=str(balance) if balance is not None else None,
        z_basis='EBT_PLUS_INTEREST_UNREVIEWED_INPUT_HYPOTHESIS_HOMOGENEOUS_UNITS_UNVERIFIED',
        vendor_basic_eps=str(mapping['vendor_basic_eps',0]) if ('vendor_basic_eps',0) in mapping else None,
        recomputed_eps=None,pe_ttm=None,pb_current=None,
        missing_notes=['WEIGHTED_SHARES_NUMERATOR_DILUTION','DEBT_CURRENT_PORTION','OWNED_PPE_DEPRECIATION',
                       'SHARE_EVENTS_PARENT_EQUITY','EXACT_PUBLICATION_REVISION'])


def exact_prices(root,path,expected,symbols,day):
    sha=hashlib.sha256();rows=[]
    with inside(root,path).open('rb') as stream:
        for line in stream:
            sha.update(line)
            if day.encode() not in line:continue
            r=json.loads(line)
            if r['ticker'] in symbols and r['trade_date']==day and r['available_at'][:10]<=day:rows.append(r)
    if sha.hexdigest()!=expected:raise ValueError('market raw-price snapshot checksum mismatch')
    if len({r['ticker'] for r in rows})!=len(rows):raise ValueError('ambiguous raw prices')
    return rows


def analyze(root,collection,output,price_config,worker):
    root=Path(root).resolve();verify(root,collection)
    source=inside(root,collection,'data');c=json.loads((source/'config.json').read_bytes())
    r=json.loads((source/'results.json').read_bytes());trial=inside(root,c['trial_run'],'data')
    members=json.loads((trial/'plan.json').read_bytes())['members'];requirements=json.loads((trial/'requirements.json').read_bytes())
    out=inside(root,output,'data');out.mkdir(parents=True,exist_ok=False)
    pdfs=[];by_sha={};pages_used=0
    for d in r['documents']:
        a=d['acquisition'];item=dict(symbol=d['symbol'],year=d['year'],provider_report=d['provider_report'],
            acquisition_status=a['status'],pdf_path=a.get('path'),pdf_sha256=a.get('sha256'))
        if a['status'] not in ['DOWNLOADED','CACHED']:
            item['extraction_status']='ACQUISITION_UNAVAILABLE';pdfs.append(item);continue
        if a['sha256'] in by_sha:
            item.update(by_sha[a['sha256']]);item['extraction_reused']=True;pdfs.append(item);continue
        dest=out/'text'/(a['sha256']+'.json');dest.parent.mkdir(exist_ok=True)
        try:
            limit=min(c['max_pdf_pages'],1800-pages_used)
            if limit<=0:raise ValueError('global text-page budget reached')
            subprocess.run([sys.executable,str(worker),'--worker-pdf',str(inside(root,a['path'],'data')),
                            '--worker-output',str(dest),'--max-pages',str(limit)],check=True,timeout=90,capture_output=True)
            text=json.loads(dest.read_bytes());pages=text['pages'];pages_used+=len(pages)
            meta=dict(extraction_status=text['status'],text_path=dest.relative_to(root).as_posix(),
                text_sha256=digest(dest.read_bytes()),total_pdf_pages=text['total_pages'],text_pages=len(pages),
                low_text_pages=sum(len(''.join(p['text'].split()))<80 for p in pages),page_hints=hints(pages))
            meta['readability']='MOSTLY_SCANNED_OR_UNREADABLE' if meta['low_text_pages']>len(pages)/2 else 'TEXT_EXTRACTABLE'
            item.update(meta);by_sha[a['sha256']]=meta
        except (ValueError,OSError,subprocess.SubprocessError) as e:
            item.update(extraction_status='EXTRACTION_FAILED',error=str(e))
        pdfs.append(item)
    diagnostics=[candidate_math(requirements,m['ticker'],year,m['proposed_company_type'])
                 for m in members for year in [2023,2024,2025]]
    pc=json.loads(inside(root,price_config,'configs').read_bytes())
    prices=exact_prices(root,pc['price_path'],pc['price_sha256'],set(c['symbols']),'2026-08-28')
    lookup={p['ticker']:p for p in prices}
    for d in diagnostics:
        price=lookup.get(d['symbol']);eps=d['vendor_basic_eps']
        d['raw_price']=price['raw_close'] if price else None
        d['pe_annual_vendor_diagnostic']=(str(Decimal(str(price['raw_close']))/Decimal(eps))
            if price and eps and Decimal(eps)>0 else None)
        d['pe_basis']='RAW_CLOSE_2026_08_28_OVER_PRINTED_ANNUAL_VENDOR_EPS_UNVERIFIED_PIT_NOT_TTM'
    discovery={d['symbol']:d for d in r['discoveries'] if d['year']==2025}
    per_symbol=[]
    for m in members:
        s=m['ticker'];ds=[d for d in diagnostics if d['symbol']==s];ps=[p for p in pdfs if p['symbol']==s]
        per_symbol.append(dict(symbol=s,proposed_company_type=m['proposed_company_type'],
            annual2025_document_candidates=len(discovery[s]['candidates']),discovery_status=discovery[s]['status'],
            z_arithmetic_diagnostic_years=sum(d['z_arithmetic'] is not None for d in ds),
            printed_vendor_eps_years=sum(d['vendor_basic_eps'] is not None for d in ds),
            pe_annual_vendor_diagnostic_years=sum(d['pe_annual_vendor_diagnostic'] is not None for d in ds),
            sampled_pdf_count=len(ps),text_readable_pdf_count=sum(p.get('readability')=='TEXT_EXTRACTABLE' for p in ps),
            scanned_pdf_count=sum(p.get('readability')=='MOSTLY_SCANNED_OR_UNREADABLE' for p in ps),
            accepted_new_metrics=0,financial_cluster_allowed=False))
    result=dict(version='financial-scale-analysis-v1',collection=collection,
        collection_manifest_sha256=digest((source/'manifest.json').read_bytes()),
        trial_run=c['trial_run'],price_path=pc['price_path'],price_sha256=pc['price_sha256'],
        price_decision_date='2026-08-28',price_rows=len(prices),
        discovery_status_counts=dict(Counter(p['discovery_status'] for p in per_symbol)),
        sample_pdf_records=len(pdfs),unique_text_extractions=len(by_sha),text_pages_used=pages_used,
        readability_counts=dict(Counter(p.get('readability','UNAVAILABLE') for p in pdfs)),
        candidate_z_arithmetic_rows=sum(d['z_arithmetic'] is not None for d in diagnostics),
        printed_vendor_eps_rows=sum(d['vendor_basic_eps'] is not None for d in diagnostics),
        candidate_pe_annual_vendor_rows=sum(d['pe_annual_vendor_diagnostic'] is not None for d in diagnostics),
        accepted_new_metrics=0,**CLOSED)
    for name,obj in [('results.json',result),('pdf-index.json',pdfs),('candidate-diagnostics.json',diagnostics),
                     ('per-symbol.json',per_symbol),('price-excerpt.json',prices)]:immutable_write(out/name,encoded(obj))
    immutable_write(out/'per-symbol.csv',csv_bytes(per_symbol,list(per_symbol[0])))
    immutable_write(out/'analyzer.py',Path(__file__).read_bytes());immutable_write(out/'worker.py',Path(worker).read_bytes())
    seal(out);return result
