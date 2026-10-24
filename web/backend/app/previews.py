"""Versioned, non-promoted presentation sidecar. Read saved labels; never transform/fit."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from .repository import MissingData, InvalidQuery
from .alignment import maximum_overlap


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


class PreviewRepository:
    def __init__(self,base,root,config='configs/product/model_previews_v1.json'):
        self.base=base;self.root=Path(root).resolve();self.meta=base.meta;self.manifest=base.manifest
        pointer=json.loads(self.inside(config).read_bytes())
        manifest_path=self.inside(pointer['manifest']);file=self.inside(pointer['file'])
        if digest(manifest_path)!=pointer['manifest_sha256'] or digest(file)!=pointer['file_sha256']:raise MissingData('Research preview checksum mismatch.')
        seal=json.loads(manifest_path.read_bytes());data=json.loads(file.read_bytes())
        if seal['version']!='delta-r1-preview-v1' or seal['data_sha256']!=pointer['file_sha256'] or seal['database_sha256']!=base.manifest['database_sha256']:raise MissingData('Preview schema or baseline revision mismatch.')
        if data['default']!='BASELINE_UNCHANGED' or data['promotion_status']!='NOT_PROMOTED':raise MissingData('Preview promotion policy changed.')
        self.variants=data['variants'];self.preview_manifest=seal;self.pointer=pointer
        self.revision=hashlib.sha256((base.manifest['database_sha256']+pointer['manifest_sha256']).encode()).hexdigest()
        for kind,variants in self.variants.items():
            for version,item in variants.items():
                if item['status']!='NOT_PROMOTED' or item['features']!=self.meta['model_configs'][kind]['features']:raise MissingData('Preview variant contract mismatch.')
                for day,model in item['snapshots'].items():
                    counts=Counter(model['labels'])
                    if len(model['symbols'])!=len(model['labels']) or len(set(model['symbols']))!=len(model['symbols']) or counts!={int(k):v for k,v in model['snapshot']['sizes'].items()}:raise MissingData('Preview assignment counts mismatch.')
                    if len(model['security_ids'])!=len(model['symbols']) or model['snapshot']['n']!=len(model['symbols']) or {p['cluster']:p['size'] for p in model['profiles']}!=dict(counts):raise MissingData('Preview profile/identity counts mismatch.')

    def inside(self,relative):
        path=(self.root/relative).resolve()
        if not path.is_relative_to(self.root):raise MissingData('Preview path outside project.')
        return path

    def __getattr__(self,name):return getattr(self.base,name)

    def supports(self,kind,version):
        return version in (None,self.meta['model_configs'].get(kind,{}).get('version')) or version in self.variants.get(kind,{})

    def variant(self,kind,version):
        self.base.kind(kind)
        if version in (None,self.meta['model_configs'][kind]['version']):return None
        if version not in self.variants.get(kind,{}):raise InvalidQuery('Unknown model version; no fallback labels were substituted.')
        return self.variants[kind][version]

    def catalog(self):
        result=self.base.catalog();result['metadata']=dict(result['metadata'],bundle_revision=self.revision,
            database_sha256=self.base.manifest['database_sha256'],presentation_version='delta-r1-preview-v1',preview_status='NOT_PROMOTED')
        variants={}
        for kind,items in self.variants.items():
            variants[kind]=[]
            for item in items.values():
                history=[]
                for day,model in sorted(item['snapshots'].items()):
                    snapshot=model['snapshot'];metrics={k:v for k,v in snapshot['metrics'].items() if isinstance(v,(int,float,str,bool)) or v is None}
                    history.append(dict(snapshot,metrics=metrics))
                variants[kind].append({k:v for k,v in item.items() if k!='snapshots'}|dict(history=history,dates=[r['date'] for r in history],latest=history[-1]))
        result['variants']=variants
        result['provenance']=result['provenance']+[dict(path=self.pointer['manifest'],sha256=self.pointer['manifest_sha256'],bytes=self.inside(self.pointer['manifest']).stat().st_size),dict(path=self.pointer['file'],sha256=self.pointer['file_sha256'],bytes=self.inside(self.pointer['file']).stat().st_size)]
        return result

    @lru_cache(maxsize=240)
    def snapshot(self,kind,date=None,version=None):
        item=self.variant(kind,version)
        if item is None:return self.base.snapshot(kind,date)
        day=date or max(item['snapshots'])
        if day not in item['snapshots']:raise MissingData('No stored preview model for this exact date.')
        model=item['snapshots'][day];raw=self.base.snapshot(kind,day)
        if [p['ticker'] for p in raw['points']]!=model['symbols'] or [p['security_id'] for p in raw['points']]!=model['security_ids']:raise MissingData('Preview cohort/identity mismatch; no join fallback.')
        points=[dict(p,cluster=label,scope=model['snapshot']['scope'],version=version) for p,label in zip(raw['points'],model['labels'])]
        return dict(snapshot=model['snapshot'],points=points,profiles=model['profiles'],definitions=raw['definitions'],peer_examples=model['peer_examples'])

    def members(self,kind,date=None,q='',cluster=None,exchange=None,page=1,page_size=25,sort='ticker',direction='asc',matrix_market=None,matrix_financial=None,version=None,matrix_market_version=None):
        item=self.variant(kind,version)
        if item is None and (matrix_market_version is None or self.variant('market',matrix_market_version) is None):return self.base.members(kind,date,q,cluster,exchange,page,page_size,sort,direction,matrix_market,matrix_financial)
        data=self.snapshot(kind,date,version);fields=self.meta['model_configs'][kind]['features']
        if sort not in ['ticker','name','cluster']+fields or direction not in ('asc','desc') or page<1 or not 1<=page_size<=100:raise InvalidQuery('Invalid preview sort/pagination.')
        rows=list(data['points'])
        if q:rows=[r for r in rows if q.casefold() in r['ticker'].casefold() or q.casefold() in (r.get('name') or '').casefold()]
        if cluster is not None:rows=[r for r in rows if r['cluster']==cluster]
        if exchange:rows=[r for r in rows if r.get('exchange')==exchange]
        if matrix_market is not None or matrix_financial is not None:
            if kind!='financial':raise InvalidQuery('Matrix filter applies to financial fiscal-year view.')
            _,left,right=self.matrix_maps(data['snapshot']['date'],matrix_market_version,version)
            allowed={t for t in set(left)&set(right) if (matrix_market is None or left[t]==matrix_market) and (matrix_financial is None or right[t]==matrix_financial)}
            rows=[r for r in rows if r['ticker'] in allowed]
        key=lambda r:r['features'].get(sort) if sort in fields else r.get(sort)
        rows.sort(key=lambda r:r['ticker']);present=[r for r in rows if key(r) is not None];missing=[r for r in rows if key(r) is None]
        present.sort(key=key,reverse=direction=='desc');rows=present+missing
        return dict(items=rows[(page-1)*page_size:page*page_size],total=len(rows),page=page,page_size=page_size,snapshot=data['snapshot'],columns=fields)

    def stock(self,ticker,kind='market',date=None,version=None):
        if self.variant(kind,version) is None:return self.base.stock(ticker,kind,date)
        result=self.base.stock(ticker,kind,date);data=self.snapshot(kind,date,version)
        current=next((p for p in data['points'] if p['ticker']==ticker.upper()),None)
        history={};versions={}
        for family in self.meta['model_configs']:
            chosen=version if version in self.variants.get(family,{}) else None
            versions[family]=chosen or self.meta['model_configs'][family]['version']
            if chosen:
                history[family]=[]
                for observation in result['history'][family]:
                    model=self.variants[family][chosen]['snapshots'].get(observation['date'])
                    if not model or ticker.upper() not in model['symbols']:continue
                    index=model['symbols'].index(ticker.upper())
                    if model['security_ids'][index]!=observation['security_id']:raise MissingData('Historical preview identity mismatch.')
                    history[family].append(dict(observation,cluster=model['labels'][index],scope=model['snapshot']['scope'],version=chosen))
            else:history[family]=result['history'][family]
        return dict(result,current=current,current_snapshot=data['snapshot'],current_missing_reason=None if current else 'No stored membership in this exact preview cohort.',history=history,history_versions=versions)

    def compare(self,tickers,kind,date=None,version=None):
        if self.variant(kind,version) is None:return self.base.compare(tickers,kind,date)
        if not 1<=len(tickers)<=4:raise InvalidQuery('Compare one to four tickers.')
        data=self.snapshot(kind,date,version);by={p['ticker']:p for p in data['points']}
        return dict(snapshot=data['snapshot'],features=self.meta['model_configs'][kind]['features'],items=[dict(security=self.base.security(t),observation=by.get(t.upper()),missing_reason=None if t.upper() in by else 'No observation at this exact model/date.') for t in tickers])

    def matrix_maps(self,year,market_version=None,financial_version=None):
        if not str(year).isdigit() or len(str(year))!=4:raise InvalidQuery('Invalid fiscal year.')
        days=[r['date'] for r in self.base.catalog()['datasets']['market']['history'] if r['date'].startswith(str(year))]
        if not days:return None,{},{}
        day=max(days)
        left={p['ticker']:p['cluster'] for p in self.snapshot('market',day,market_version)['points']}
        right={p['ticker']:p['cluster'] for p in self.snapshot('financial',str(year),financial_version)['points']}
        return day,left,right

    def matrix(self,year,version=None,market_version=None):
        if self.variant('financial',version) is None and self.variant('market',market_version) is None:return self.base.matrix(year)
        self.variant('financial',version);self.variant('market',market_version)
        day,left,right=self.matrix_maps(year,market_version,version)
        if day is None:return self.base.matrix(year)
        cells=Counter((left[t],right[t]) for t in set(left)&set(right))
        return dict(available=True,date=day,year=year,total=sum(cells.values()),cells=[dict(market_cluster=a,financial_cluster=b,n=n) for (a,b),n in sorted(cells.items())],
            market_labels=sorted(set(left.values())),financial_labels=sorted(set(right.values())),market_version=market_version or self.meta['model_configs']['market']['version'],financial_version=version or self.meta['model_configs']['financial']['version'],
            scope='EX_POST_PREVIEW_COMPARISON_NOT_PROMOTED_NOT_PIT',reason='Saved candidate assignments; original fiscal timing/identity limitations remain. Versions are explicit; no model was promoted.')

    def migration(self,kind,source,target,version=None):
        if self.variant(kind,version) is None:return self.base.migration(kind,source,target)
        a=self.snapshot(kind,source,version);b=self.snapshot(kind,target,version)
        left={r['ticker']:r['cluster'] for r in a['points']};right={r['ticker']:r['cluster'] for r in b['points']};common=sorted(set(left)&set(right))
        source_labels=sorted(set(left.values()));target_labels=sorted(set(right.values()))
        mapping,unmatched_source,unmatched_target=maximum_overlap(Counter((left[t],right[t]) for t in common if left[t]>=0 and right[t]>=0),source_labels,target_labels)
        next_id=max([0]+source_labels+target_labels)+1
        for label in unmatched_target:mapping[label]=next_id;next_id+=1
        for label in target_labels:
            if label<0:mapping[label]=label
        cells=Counter((left[t],mapping[right[t]]) for t in common)
        return dict(source=source,target=target,kind=kind,version=version,common=len(common),entered=len(set(right)-set(left)),exited=len(set(left)-set(right)),stayed=sum(n for (i,j),n in cells.items() if i==j and i>=0),mapping={str(k):v for k,v in mapping.items()},source_labels=source_labels,target_labels=target_labels,display_target_labels=sorted(set(mapping.values())),unmatched_source=unmatched_source,unmatched_target=unmatched_target,cells=[dict(source=i,target=j,n=n) for (i,j),n in sorted(cells.items())],alignment='Maximum-overlap display alignment within the same preview version; stored labels unchanged.')
