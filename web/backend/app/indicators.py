"""Presentation adapter for existing reviewed six-family results. Never compute scores."""
import csv
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from .repository import MissingData

FAMILIES=('EPS','PE','PB','F_SCORE','M_SCORE','Z_SCORE')

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
            with csv_path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            for row in rows:
                if row['family'] not in FAMILIES:raise MissingData('Unknown indicator family in reviewed source.')
                value=row.get('value','')
                if value:
                    try:
                        if not Decimal(value).is_finite():raise InvalidOperation
                    except InvalidOperation:raise MissingData('Non-finite indicator value in reviewed source.')
            sources.append(dict(source=source,rows=rows,numeric=sum(bool(r.get('value')) for r in rows),symbols=len({r['symbol'] for r in rows if r.get('value')})))
        return sources

    def stock(self,ticker):
        groups=[];unavailable=0;summaries=[]
        for package in self.load():
            source=package['source'];cohorts={}
            summaries.append(dict(id=source['id'],label=source['label'],numeric_values=package['numeric'],symbols=package['symbols'],path=source['file'],sha256=source['file_sha256']))
            for row in package['rows']:
                if row['symbol']!=ticker.upper():continue
                cohort=row.get('cohort_id') or f"PILOT5_FY{row['year']}:{ticker.upper()}:{row['year']}"
                if row.get('source_adapter')=='FPT_CACHE_FLOW':
                    cohort+=' · snapshot='+row.get('snapshot_date','UNSPECIFIED')
                if row.get('period_kind') not in ('ANNUAL','',None):
                    cohort+=' · period='+row['period_kind']
                cohorts.setdefault(cohort,[]).append(row)
            for cohort,rows in cohorts.items():
                if not any(r.get('value') for r in rows):unavailable+=1;continue
                by_family={}
                for r in rows:
                    if r['family'] in by_family:raise MissingData('Duplicate family in one source cohort; cannot choose a vintage implicitly.')
                    by_family[r['family']]=r
                metrics=[]
                for family in FAMILIES:
                    r=by_family.get(family,{})
                    value=r.get('value') or None
                    metrics.append(dict(family=family,value=value,status=r.get('status') or 'UNAVAILABLE',
                        variant=r.get('variant') or None,unit=r.get('unit') or ('VND/share' if family=='EPS' else 'points/9' if family=='F_SCORE' else 'ratio'),
                        year=r.get('year'),input_period=r.get('input_period') or '/'.join(filter(None,[r.get('period_start'),r.get('period_end')])),input_scope=r.get('input_scope'),
                        price_date=(r.get('price_date') or r.get('snapshot_date') or None) if family in ('PE','PB') else None,
                        reference_date=r.get('snapshot_date') or None,period_kind=r.get('period_kind') or None,price_basis=r.get('price_basis') or None,
                        balance_date=r.get('balance_date'),share_basis=r.get('share_basis'),temporal_status=r.get('temporal_status'),
                        missing_inputs=r.get('missing_inputs') or None,strict_pit_ready=False,production_ready=False))
                groups.append(dict(id=source['id']+':'+cohort,source_id=source['id'],source_label=source['label'],
                    cohort=cohort,year=rows[0]['year'],metrics=metrics,source_path=source['file'],source_sha256=source['file_sha256']))
        groups.sort(key=lambda g:(g['source_id']!='pilot5',-int(g['year']),g['id']))
        return dict(ticker=ticker.upper(),available=bool(groups),groups=groups,sources=summaries,
                    unavailable_cohorts=unavailable,scope='REVIEWED_REFERENCE_NOT_CURRENT_NOT_PIT',
                    missing_reason=None if groups else 'Chưa có bộ chỉ số đã review cho mã này trong các gói dữ liệu đã nối.',
                    note='Chọn một gói/kỳ cụ thể; không trộn vintage, không dùng giá ngày chọn để tính lại P/E/P/B, không thay thế sáu core ratios của mô hình B/C.')
