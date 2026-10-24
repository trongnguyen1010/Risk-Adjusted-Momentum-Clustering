"""Indexed, parameterized read access. No ingestion, feature calculation or fitting."""
from contextlib import contextmanager
from collections import Counter
from functools import lru_cache
from datetime import date as calendar_date
from .alignment import maximum_overlap
import json
import hashlib
from pathlib import Path
import sqlite3

KINDS = {'market','financial','combined'}


class MissingData(ValueError): pass
class InvalidQuery(ValueError): pass
class AmbiguousIdentity(ValueError): pass


class TerminalRepository:
    def __init__(self, bundle):
        self.bundle=Path(bundle).resolve()
        self.database=self.bundle/'terminal.sqlite'
        self.manifest=json.loads((self.bundle/'manifest.json').read_bytes())
        if self.manifest.get('version')!='delta-intelligence-v1' or not self.database.is_file():
            raise MissingData('Build the DELTA presentation bundle first.')
        with self.database.open('rb') as source:
            digest=hashlib.file_digest(source,'sha256').hexdigest()
        if digest != self.manifest.get('database_sha256'):
            raise MissingData('Presentation database checksum mismatch. Rebuild from verified sources.')
        with self.connect() as db:
            self.meta=json.loads(db.execute("SELECT value FROM metadata WHERE key='overview'").fetchone()[0])

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.database.as_uri()+'?mode=ro',uri=True)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        try:yield db
        finally:db.close()

    def query(self, sql, args=()):
        with self.connect() as db:return [dict(r) for r in db.execute(sql,args).fetchall()]

    def kind(self,kind):
        if kind not in KINDS:raise InvalidQuery('Unknown experiment family.')
        return kind

    def catalog(self):
        datasets={}
        for kind in sorted(KINDS):
            history=self.query('SELECT * FROM snapshots WHERE kind=? ORDER BY date',(kind,))
            for r in history:
                r['sizes']=json.loads(r['sizes']);r['metrics']=json.loads(r['metrics'])
            datasets[kind]=dict(history=history,dates=[r['date'] for r in history],latest=history[-1],**self.meta['model_configs'][kind])
        return dict(metadata=dict(self.meta,bundle_revision=self.manifest['database_sha256']),datasets=datasets,
                    provenance=[dict(path=p,sha256=v['sha256'],bytes=v['size']) for p,v in self.manifest['sources'].items()])

    def resolve_snapshot(self,kind,date=None):
        self.kind(kind)
        sql='SELECT * FROM snapshots WHERE kind=?'
        args=[kind]
        if date:sql+=' AND date=?';args.append(date)
        found=self.query(sql+' ORDER BY date DESC LIMIT 1',args)
        if not found:raise MissingData('No stored model for the selected date. Choose an available snapshot.')
        r=found[0];r['sizes']=json.loads(r['sizes']);r['metrics']=json.loads(r['metrics'])
        return r

    @staticmethod
    def observation(r):
        value=dict(r)
        value['features']=json.loads(value['features']) if isinstance(value.get('features'),str) else value.get('features',{})
        return value

    @lru_cache(maxsize=160)
    def snapshot(self,kind,date=None):
        snap=self.resolve_snapshot(kind,date)
        points=[self.observation(r) for r in self.query('''SELECT o.*,s.name,s.exchange FROM observations o
             LEFT JOIN securities s ON s.ticker=o.ticker WHERE o.kind=? AND o.date=? ORDER BY o.ticker''',(kind,snap['date']))]
        profiles=self.query('SELECT * FROM profiles WHERE kind=? AND date=? ORDER BY cluster',(kind,snap['date']))
        for p in profiles:
            for f in ['means','medians','quartiles']:p[f]=json.loads(p[f])
        return dict(snapshot=snap,points=points,profiles=profiles,definitions={k:self.meta['definitions'][k] for k in self.meta['model_configs'][kind]['features']})

    def members(self,kind,date=None,q='',cluster=None,exchange=None,page=1,page_size=25,sort='ticker',direction='asc',matrix_market=None,matrix_financial=None):
        snap=self.resolve_snapshot(kind,date)
        fields=self.meta['model_configs'][kind]['features']
        if sort not in ['ticker','name','cluster']+fields:raise InvalidQuery('Unsupported sort column.')
        if direction not in ('asc','desc') or page<1 or not 1<=page_size<=100:raise InvalidQuery('Invalid pagination/sort.')
        clauses=['o.kind=?','o.date=?'];args=[kind,snap['date']]
        if q:
            clauses.append('(o.ticker LIKE ? OR s.name LIKE ?)');args += ['%'+q[:80]+'%']*2
        if cluster is not None:clauses.append('o.cluster=?');args.append(cluster)
        if exchange:clauses.append('s.exchange=?');args.append(exchange)
        if matrix_market is not None or matrix_financial is not None:
            if kind!='financial':raise InvalidQuery('Matrix filter applies to financial fiscal-year view.')
            exists=['r.ticker=o.ticker',"substr(r.date,1,4)=o.date","r.coverage='BOTH'"]
            if matrix_market is not None:exists.append('r.market_cluster=?');args.append(matrix_market)
            if matrix_financial is not None:exists.append('r.financial_cluster=?');args.append(matrix_financial)
            clauses.append('EXISTS(SELECT 1 FROM relations r WHERE '+' AND '.join(exists)+')')
        base=' FROM observations o LEFT JOIN securities s ON s.ticker=o.ticker WHERE '+' AND '.join(clauses)
        count=self.query('SELECT count(*) AS n'+base,args)[0]['n']
        field="json_extract(o.features,'$."+sort+"')" if sort in fields else 's.name' if sort=='name' else 'o.'+sort
        order=f' ORDER BY ({field} IS NULL),{field} {direction.upper()},o.ticker ASC LIMIT ? OFFSET ?'
        result=[self.observation(r) for r in self.query('SELECT o.*,s.name,s.exchange'+base+order,args+[page_size,(page-1)*page_size])]
        return dict(items=result,total=count,page=page,page_size=page_size,snapshot=snap,columns=fields)

    def search(self,q='',limit=12):
        return self.query('SELECT * FROM securities WHERE ticker LIKE ? OR name LIKE ? ORDER BY CASE WHEN ticker=? THEN 0 ELSE 1 END,ticker LIMIT ?',('%'+q[:80]+'%','%'+q[:80]+'%',q.upper(),limit))

    def security(self,ticker):
        found=self.query('SELECT * FROM securities WHERE ticker=?',(ticker.upper(),))
        if not found:raise MissingData('Ticker is not in the research universe.')
        if found[0]['ambiguous']:raise AmbiguousIdentity('Multiple provisional security identities: cannot merge ticker history safely.')
        return found[0]

    def stock(self,ticker,kind='market',date=None):
        security=self.security(ticker)
        snap=self.resolve_snapshot(kind,date)
        current=self.query('SELECT * FROM observations WHERE kind=? AND date=? AND ticker=?',(kind,snap['date'],security['ticker']))
        history={k:[self.observation(r) for r in self.query('SELECT * FROM observations WHERE ticker=? AND kind=? ORDER BY date',(security['ticker'],k))] for k in KINDS}
        price_coverage=self.query('SELECT min(date) AS start,max(date) AS end,count(*) AS rows FROM prices WHERE ticker=?',(security['ticker'],))[0]
        return dict(security=security,current=self.observation(current[0]) if current else None,current_snapshot=snap,
                    current_missing_reason=None if current else 'Not eligible / no stored membership at this exact snapshot.',
                    history=history,price_coverage=price_coverage,financial_scope='Annual fiscal reference; publication timing not verified.',
                    price_scope='Historical provider-adjusted proxy or raw close in VND/share; not live.')

    def prices(self,ticker,end=None,basis='adj_close'):
        self.security(ticker)
        if end:
            try:
                if calendar_date.fromisoformat(end).isoformat()!=end:raise ValueError
            except ValueError:raise InvalidQuery('Invalid ISO price date.')
        if basis not in ['adj_close','raw_close']:raise InvalidQuery('Unknown price basis.')
        args=[ticker.upper()];where='ticker=?'
        if end:where+=' AND date<=?';args.append(end)
        result=self.query(f'SELECT date,{basis} AS close,volume,basis,conflict FROM prices WHERE {where} ORDER BY date',args)
        if len({r['date'] for r in result})!=len(result):raise AmbiguousIdentity('Overlapping price identities are held; no ticker splice.')
        available=any(r['close'] is not None for r in result)
        return dict(ticker=ticker.upper(),basis=basis,unit='VND/share',points=result,
                    available=available,missing_reason=None if available else 'No usable observations for the selected price basis and period.')

    def compare(self,tickers,kind,date=None):
        if not 1<=len(tickers)<=4:raise InvalidQuery('Compare one to four tickers.')
        snap=self.resolve_snapshot(kind,date)
        records=[]
        for ticker in tickers:
            security=self.security(ticker)
            found=self.query('SELECT * FROM observations WHERE kind=? AND date=? AND ticker=?',(kind,snap['date'],security['ticker']))
            records.append(dict(security=security,observation=self.observation(found[0]) if found else None,
                                missing_reason=None if found else 'No observation at this exact comparison date.'))
        return dict(snapshot=snap,items=records,features=self.meta['model_configs'][kind]['features'])

    def matrix(self,year):
        if not year.isdigit() or len(year)!=4:raise InvalidQuery('Invalid fiscal year.')
        dates=self.query("SELECT DISTINCT date FROM relations WHERE substr(date,1,4)=? ORDER BY date",(year,))
        if not dates:return dict(available=False,date=None,year=year,total=0,cells=[],scope='EX_POST_NOT_PIT',reason='Year-end market × financial overlap is available only for 2019–2025.')
        day=dates[-1]['date']
        cells=self.query("SELECT market_cluster,financial_cluster,count(*) AS n FROM relations WHERE date=? AND coverage='BOTH' GROUP BY market_cluster,financial_cluster",(day,))
        return dict(available=True,date=day,year=year,total=sum(r['n'] for r in cells),cells=cells,
                    market_labels=sorted({int(x) for x in self.resolve_snapshot('market',day)['sizes']}|{r['market_cluster'] for r in cells}),
                    financial_labels=sorted({int(x) for x in self.resolve_snapshot('financial',year)['sizes']}|{r['financial_cluster'] for r in cells}),scope='EX_POST_SAME_FISCAL_YEAR_NOT_PIT',
                    reason='Financial FY may be published after this market date; exploratory reference only.')

    def migration(self,kind,source,target):
        a=self.snapshot(kind,source);b=self.snapshot(kind,target)
        left={r['ticker']:r['cluster'] for r in a['points']};right={r['ticker']:r['cluster'] for r in b['points']}
        common=sorted(set(left)&set(right))
        counts=Counter((left[t],right[t]) for t in common if left[t]>=0 and right[t]>=0)
        source_labels=sorted(set(left.values())|{int(x) for x in a['snapshot']['sizes']})
        target_labels=sorted(set(right.values())|{int(x) for x in b['snapshot']['sizes']})
        mapping,unmatched_source,unmatched_target=maximum_overlap(counts,source_labels,target_labels)
        next_id=max([0]+source_labels+target_labels)+1
        for label in unmatched_target:
            mapping[label]=next_id;next_id+=1
        for label in target_labels:
            if label<0:mapping[label]=label
        cells=Counter((left[t],mapping[right[t]]) for t in common)
        return dict(source=source,target=target,kind=kind,common=len(common),entered=len(set(right)-set(left)),exited=len(set(left)-set(right)),
                    stayed=sum(n for (i,j),n in cells.items() if i==j and i>=0),mapping={str(i):value for i,value in mapping.items()},
                    source_labels=source_labels,target_labels=target_labels,display_target_labels=sorted(set(mapping.values())),
                    unmatched_source=unmatched_source,unmatched_target=unmatched_target,
                    cells=[dict(source=i,target=j,n=n) for (i,j),n in sorted(cells.items())],
                    alignment='Pairwise maximum-overlap label alignment for display; not economic regime identity. Raw stored assignments are preserved.')
