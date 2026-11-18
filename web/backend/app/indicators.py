"""Presentation adapter for existing reviewed six-family results. Never compute scores."""
import csv
from contextlib import closing
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import json
import sqlite3
from pathlib import Path
from .repository import MissingData

FAMILIES=('EPS','PE','PB','F_SCORE','M_SCORE','Z_SCORE')

def availability(row):
    if row.get('status') == 'PROVIDER_REPORTED' and row.get('value') not in ('', None):return 'SOURCE_REPORTED'
    if row.get('value') not in ('', None):return 'AVAILABLE_REVIEWED'
    status=row.get('status','')
    if status in ('NOT_COMPUTED','NOT_APPLICABLE','SOURCE_UNAVAILABLE','REVIEW_PENDING'):return status
    if row.get('missing_inputs') not in ('',None,'[]') or 'MISSING' in status:return 'MISSING_INPUT'
    return 'REVIEW_PENDING'  # An absent family alone does not establish a missing-input reason.

def cohort_key(row):
    cohort=row.get('cohort_id') or (f"PDF:{row['pdf_sha256']}:{row['year']}" if row.get('pdf_sha256') else f"PILOT5_FY{row['year']}:{row['symbol']}:{row['year']}")
    if row.get('source_adapter')=='FPT_CACHE_FLOW':cohort+=' · snapshot='+row.get('snapshot_date','UNSPECIFIED')
    if row.get('period_kind') not in ('ANNUAL','',None):cohort+=' · period='+row['period_kind']
    return cohort

class IndicatorReferences:
    def __init__(self, root, config='configs/product/indicator_reference_v1.json'):
        self.root=Path(root).resolve()
        self.config=config

    def inside(self, relative):
        path=(self.root/relative).resolve()
        if not path.is_relative_to(self.root):raise MissingData('Indicator source escapes the project directory.')
        return path

    @lru_cache(maxsize=1)
    def load(self):
        path=self.inside(self.config)
        if not path.is_file():return []
        config=json.loads(path.read_bytes())
        sources=[]
        for source in config['sources']:
            manifest_path=self.inside(source['manifest']);csv_path=self.inside(source['file'])
            if not manifest_path.is_file() or not csv_path.is_file():
                continue  # Missing local artifacts remain explicitly unavailable.
            digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            if digest(manifest_path)!=source['manifest_sha256'] or digest(csv_path)!=source['file_sha256']:
                raise MissingData('Reviewed indicator source checksum mismatch; no values were substituted.')
            manifest=json.loads(manifest_path.read_bytes())
            pins=manifest.get('files',manifest)
            if pins.get(csv_path.name)!=source['file_sha256']:
                raise MissingData('Indicator CSV is not pinned by its result manifest.')
            if source.get('format') == 'sqlite':
                with closing(sqlite3.connect(csv_path.as_uri()+'?mode=ro',uri=True)) as db:
                    summary=json.loads(db.execute("SELECT value FROM metadata WHERE key='summary'").fetchone()[0])
                    if source.get('hide_unconfirmed_zero'):
                        numeric,symbols=db.execute("SELECT COUNT(*),COUNT(DISTINCT symbol) FROM observations WHERE CAST(json_extract(payload,'$.value') AS REAL) != 0").fetchone()
                    else:numeric,symbols=summary['numeric_reported_eps'],summary['symbols_with_reported_eps']
                sources.append(dict(source=source,rows=[],numeric=numeric,symbols=symbols,quoted_numeric=summary['numeric_reported_eps']))
                continue
            with csv_path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            supplements={}
            for item in source.get('supplements',[]):
                extra=self.inside(item['file'])
                if not extra.is_file() or digest(extra)!=item['sha256'] or pins.get(extra.name)!=item['sha256']:
                    raise MissingData('Indicator supplementary evidence absent or checksum mismatch.')
                supplements[item['kind']]=json.loads(extra.read_bytes())
            if supplements:
                details={(r['symbol'],r['family']):r for r in supplements.get('calculation_details',[])}
                dependencies={(r['symbol'],r['family']):r for r in supplements.get('dependencies',[])}
                for row in rows:
                    key=row['symbol'],row['family']
                    if key in dependencies and dependencies[key].get('missing'):
                        row['missing_inputs']=json.dumps(dependencies[key]['missing'],ensure_ascii=False)
                    if key in details:row['components']=details[key].get('result')
            for row in rows:
                if row['family'] not in FAMILIES:raise MissingData('Unknown indicator family in reviewed source.')
                value=row.get('value','')
                if value:
                    try:
                        if not Decimal(value).is_finite():raise InvalidOperation
                    except InvalidOperation:raise MissingData('Non-finite indicator value in reviewed source.')
            if source.get('row_filter'):
                rows=[r for r in rows if all(r.get(k)==v for k,v in source['row_filter'].items())]
            sources.append(dict(source=source,rows=rows,numeric=sum(bool(r.get('value')) for r in rows),symbols=len({r['symbol'] for r in rows if r.get('value')})))
        return sources

    def coverage(self):
        packages=[]
        for package in self.load():
            if package['source'].get('format')=='sqlite':
                packages.append(dict(id=package['source']['id'],numeric_values=package['numeric'],quoted_numeric_values=package['quoted_numeric'],symbols=package['symbols'],families={f:package['numeric'] if f=='EPS' else 0 for f in FAMILIES},full6_cohorts=0))
                continue
            cohorts={}
            for row in package['rows']:cohorts.setdefault((row['symbol'],cohort_key(row)),[]).append(row)
            packages.append(dict(id=package['source']['id'],numeric_values=package['numeric'],symbols=package['symbols'],
                families={f:sum(r['family']==f and bool(r.get('value')) for r in package['rows']) for f in FAMILIES},
                full6_cohorts=sum({r['family'] for r in rows if r.get('value')}==set(FAMILIES) for rows in cohorts.values())))
        configured=json.loads(self.inside(self.config).read_bytes())['sources'] if self.inside(self.config).is_file() else []
        return dict(packages=packages,unavailable_sources=[s['id'] for s in configured if s['id'] not in {p['id'] for p in packages}],
                    denominator='Numeric observations per package, including distinct periods/vintages; pilot5 is a subset of reviewed85. Do not sum package counts.',
                    default_policy='pilot5 first, then newest FY within one reviewed source cohort; never merge families across vintages.',strict_pit_ready=False)

    def stock(self,ticker):
        groups=[];unavailable=0;summaries=[]
        for package in self.load():
            source=package['source'];cohorts={}
            summaries.append(dict(id=source['id'],label=source['label'],numeric_values=package['numeric'],symbols=package['symbols'],path=source['file'],sha256=source['file_sha256']))
            rows=package['rows']
            if source.get('format')=='sqlite':
                with closing(sqlite3.connect(self.inside(source['file']).as_uri()+'?mode=ro',uri=True)) as db:
                    rows=[json.loads(r[0]) for r in db.execute('SELECT payload FROM observations WHERE symbol=? ORDER BY year DESC',(ticker.upper(),))]
                for row in rows:
                    row['year']=str(row['year'])
                    # A provider zero can be a placeholder. Preserve the raw zero in
                    # evidence; do not present it as confirmed EPS without source proof.
                    if source.get('hide_unconfirmed_zero') and Decimal(row['value']) == 0:
                        row['components']={'source_reported_value':row['value'],'reason':'UNCONFIRMED_PROVIDER_ZERO'}
                        row['value']=None;row['status']='UNCONFIRMED_PROVIDER_ZERO'
            for row in rows:
                if row['symbol']!=ticker.upper():continue
                cohort=cohort_key(row)
                cohorts.setdefault(cohort,[]).append(row)
            for cohort,rows in cohorts.items():
                if not any(r.get('value') for r in rows):unavailable+=1
                by_family={}
                for r in rows:
                    if r['family'] in by_family:raise MissingData('Duplicate family in one source cohort; cannot choose a vintage implicitly.')
                    by_family[r['family']]=r
                metrics=[]
                for family in FAMILIES:
                    r=by_family.get(family,{})
                    value=r.get('value') or None
                    metrics.append(dict(family=family,value=value,status=r.get('status') or 'UNKNOWN',availability=availability(r),
                        variant=r.get('variant') or source.get('variant') or None,unit=r.get('unit') or ('VND/share' if family=='EPS' else 'points/9' if family=='F_SCORE' else 'ratio'),
                        year=r.get('year'),input_period=r.get('input_period') or '/'.join(filter(None,[r.get('period_start'),r.get('period_end')])),input_scope=r.get('input_scope'),
                        price_date=(r.get('price_date') or r.get('snapshot_date') or None) if family in ('PE','PB') else None,
                        reference_date=r.get('snapshot_date') or None,period_kind=r.get('period_kind') or None,price_basis=r.get('price_basis') or None,
                        balance_date=r.get('balance_date'),share_basis=r.get('share_basis'),temporal_status=r.get('temporal_status'),
                        missing_inputs=r.get('missing_inputs') or None,evidence_ref=r.get('evidence_ref') or source['file'],
                        components=r.get('components'),
                        dependency_ids=r.get('dependency_ids') or r.get('verification_ids') or None,formula_version=r.get('formula_version') or None,
                        pdf_sha256=r.get('pdf_sha256') or r.get('primary_pdf_sha256') or None,strict_pit_ready=False,production_ready=False))
                groups.append(dict(id=source['id']+':'+cohort,source_id=source['id'],source_label=source['label'],
                    cohort=cohort,year=rows[0]['year'],metrics=metrics,source_path=source['file'],source_sha256=source['file_sha256']))
        groups.sort(key=lambda g:(not any(m['value'] is not None for m in g['metrics']),g['source_id']!='pilot5',-int(g['year']),g['source_id']=='provider_eps',g['id']))
        return dict(ticker=ticker.upper(),available=any(m['value'] is not None for g in groups for m in g['metrics']),groups=groups,sources=summaries,
                    default_group_id=groups[0]['id'] if groups else None,coverage=self.coverage(),
                    unavailable_cohorts=unavailable,scope='REVIEWED_REFERENCE_NOT_CURRENT_NOT_PIT',
                    missing_reason=None if groups else 'Chưa có bộ chỉ số đã review cho mã này trong các gói dữ liệu đã nối.',
                    note='Chọn một gói/kỳ cụ thể; không trộn vintage, không dùng giá ngày chọn để tính lại P/E/P/B, không thay thế sáu core ratios của mô hình B/C.')
