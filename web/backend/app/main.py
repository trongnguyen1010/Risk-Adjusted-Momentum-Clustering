from contextlib import asynccontextmanager
import os
from pathlib import Path
import sqlite3
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from .repository import TerminalRepository, MissingData, InvalidQuery, AmbiguousIdentity
from .schemas import Kind, HealthResponse, CatalogResponse, SnapshotResponse, MembersResponse, StockResponse
from .indicators import IndicatorReferences
from .schemas import IndicatorResponse
from .previews import PreviewRepository
from .fundamentals import FundamentalsRepository

ROOT=Path(__file__).resolve().parents[3]

def create_app(repository=None,fundamentals=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.repository=repository or TerminalRepository(os.environ.get('DELTA_BUNDLE',str(ROOT/'data/web/delta-intelligence-v4')))
        preview_config=ROOT/'configs/product/model_previews_v1.json'
        if repository is None and preview_config.is_file():
            # R1 previews are pinned to the v1 bundle; another bundle serves without them.
            try:app.state.repository=PreviewRepository(app.state.repository,ROOT)
            except (MissingData,OSError):pass  # Not published with this bundle.
        app.state.indicators=IndicatorReferences(ROOT)
        app.state.fundamentals=fundamentals
        if fundamentals is None:
            try:app.state.fundamentals=FundamentalsRepository.from_config(ROOT)
            except (MissingData,FileNotFoundError):app.state.fundamentals=None  # Endpoints answer 404 until built.
        yield
    app=FastAPI(title='DELTA Intelligence · Read-only Research API',version='1.0.0',lifespan=lifespan)
    def repo(request:Request):return request.app.state.repository
    def read(request,method,*args,version=None,**kwargs):
        selected=repo(request)
        if isinstance(selected,PreviewRepository):return getattr(selected,method)(*args,version=version,**kwargs)
        return getattr(selected,method)(*args)
    @app.middleware('http')
    async def require_matching_revision(request:Request,call_next):
        if request.url.path.startswith('/api/v2/') and request.url.path not in ('/api/v2/catalog','/api/v2/health'):
            revision=request.query_params.get('revision')
            if revision and revision!=getattr(repo(request),'revision',repo(request).manifest['database_sha256']):
                return JSONResponse(status_code=409,content={'detail':'Gói dữ liệu đã đổi phiên bản. Tải lại workspace để tránh trộn model, nhãn và hồ sơ.'})
            version=request.query_params.get('version')
            parts=request.url.path.split('/')
            kind=parts[4] if len(parts)>4 and parts[3] in ('snapshots','members','migration') else 'financial' if len(parts)>3 and parts[3]=='matrix' else request.query_params.get('kind','market')
            expected=repo(request).meta['model_configs'].get(kind,{}).get('version')
            supported=repo(request).supports(kind,version) if isinstance(repo(request),PreviewRepository) else version==expected
            if version and expected and not supported:
                return JSONResponse(status_code=409,content={'detail':'Model version trong yêu cầu không khớp artifact đang phục vụ; không thay thế bằng nhãn khác.'})
            for key in ('market_version','matrix_market_version'):
                value=request.query_params.get(key)
                if value and not (repo(request).supports('market',value) if isinstance(repo(request),PreviewRepository) else value==repo(request).meta['model_configs']['market']['version']):
                    return JSONResponse(status_code=409,content={'detail':'Market model version mismatch; no cross-version fallback.'})
        return await call_next(request)
    @app.exception_handler(MissingData)
    async def missing(request,error):return JSONResponse(status_code=404,content={'detail':str(error)})
    @app.exception_handler(InvalidQuery)
    async def invalid(request,error):return JSONResponse(status_code=400,content={'detail':str(error)})
    @app.exception_handler(AmbiguousIdentity)
    async def ambiguous(request,error):return JSONResponse(status_code=409,content={'detail':str(error)})
    @app.api_route('/api/v2/health',methods=['GET','HEAD'],response_model=HealthResponse)
    def health(request:Request):return dict(status='ok',version=repo(request).meta['version'],read_only=True)
    @app.get('/api/v2/catalog',response_model=CatalogResponse)
    def catalog(request:Request):return repo(request).catalog()
    @app.get('/api/v2/snapshots/{kind}',response_model=SnapshotResponse)
    def snapshot(request:Request,kind:Kind,date:str|None=None,include_points:bool=True,version:str|None=None):
        stored=read(request,'snapshot',kind,date,version=version)
        return dict(stored,points=stored['points'] if include_points else [],points_included=include_points)
    @app.get('/api/v2/members/{kind}',response_model=MembersResponse)
    def members(request:Request,kind:Kind,date:str|None=None,q:str='',cluster:int|None=None,exchange:str|None=None,
                page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),sort:str='ticker',direction:str='asc',
                matrix_market:int|None=None,matrix_financial:int|None=None,version:str|None=None,matrix_market_version:str|None=None):
        return read(request,'members',kind,date,q,cluster,exchange,page,page_size,sort,direction,matrix_market,matrix_financial,version=version,matrix_market_version=matrix_market_version)
    @app.get('/api/v2/search')
    def search(request:Request,q:str='',limit:int=Query(12,ge=1,le=30)):return dict(items=repo(request).search(q,limit))
    @app.get('/api/v2/stocks/{ticker}',response_model=StockResponse)
    def stock(request:Request,ticker:str,kind:Kind='market',date:str|None=None,version:str|None=None):return read(request,'stock',ticker,kind,date,version=version)
    def fund(request):
        found=request.app.state.fundamentals
        if found is None:raise MissingData('Bộ chỉ số tài chính chưa sẵn sàng trên máy chủ này.')
        return found
    def closes(request,ticker):
        rows=repo(request).query('SELECT date,raw_close,adj_close FROM prices WHERE ticker=? ORDER BY date DESC LIMIT 400',(ticker.upper(),))
        return [(r['date'],r['raw_close'],r['adj_close']) for r in reversed(rows)]
    def cluster_members(request,ticker):
        for kind in ('combined','market'):
            latest=repo(request).query('SELECT date FROM snapshots WHERE kind=? ORDER BY date DESC LIMIT 1',(kind,))
            if not latest:continue
            own=repo(request).query('SELECT cluster FROM observations WHERE kind=? AND date=? AND ticker=?',(kind,latest[0]['date'],ticker.upper()))
            if own:
                members=repo(request).query('SELECT ticker FROM observations WHERE kind=? AND date=? AND cluster=?',(kind,latest[0]['date'],own[0]['cluster']))
                return [r['ticker'] for r in members],f'CLUSTER_{kind.upper()}:{latest[0]["date"]}'
        return None,None
    @app.get('/api/v2/fundamentals-coverage')
    def fundamentals_coverage(request:Request):return fund(request).coverage()
    @app.get('/api/v2/stocks/{ticker}/overview')
    def stock_overview(request:Request,ticker:str):
        source=fund(request);company=source.company(ticker)
        body=source.overview(company['ticker'],closes(request,company['ticker']))
        try:
            found=repo(request).query("SELECT date,liquidity FROM observations WHERE kind='market' AND ticker=? ORDER BY date DESC LIMIT 1",(company['ticker'],))
        except sqlite3.OperationalError:found=[]  # Bundles before v3 have no liquidity column.
        body['liquidity']=dict(status=found[0]['liquidity'],date=found[0]['date']) if found and found[0]['liquidity'] else None
        body['groups']=stock_groups(request,company['ticker'])
        return body
    def stock_groups(request,ticker):
        """The ticker's cluster in the latest snapshot of each model, with its plain-language name (bundle v4+)."""
        out=[]
        for kind in ('market','financial','combined'):
            latest=repo(request).query('SELECT date FROM snapshots WHERE kind=? ORDER BY date DESC LIMIT 1',(kind,))
            if not latest:continue
            day=latest[0]['date']
            own=repo(request).query('SELECT cluster FROM observations WHERE kind=? AND date=? AND ticker=?',(kind,day,ticker))
            if not own:continue
            try:
                story=repo(request).query('SELECT name,description FROM profiles WHERE kind=? AND date=? AND cluster=?',(kind,day,own[0]['cluster']))
            except sqlite3.OperationalError:story=[]  # Bundles before v4 have no names.
            out.append(dict(kind=kind,date=day,cluster=own[0]['cluster'],
                            name=story[0]['name'] if story else None,description=story[0]['description'] if story else None))
        return out
    @app.get('/api/v2/stocks/{ticker}/fundamentals')
    def stock_fundamentals(request:Request,ticker:str,start:int=Query(2016,alias='from'),end:int=Query(2025,alias='to')):
        return fund(request).fundamentals(ticker,start,end)
    @app.get('/api/v2/stocks/{ticker}/scores/{year}')
    def stock_scores(request:Request,ticker:str,year:int):return fund(request).scores(ticker,year)
    @app.get('/api/v2/stocks/{ticker}/peers')
    def stock_peers(request:Request,ticker:str,limit:int=Query(9,ge=1,le=20)):
        source=fund(request);company=source.company(ticker)
        members,basis=cluster_members(request,company['ticker'])
        return source.peers(company['ticker'],members,basis,limit)
    @app.get('/api/v2/prices/{ticker}')
    def prices(request:Request,ticker:str,end:str|None=None,basis:str='adj_close'):return repo(request).prices(ticker,end,basis)
    @app.get('/api/v2/indicator-coverage')
    def indicator_coverage(request:Request):return request.app.state.indicators.coverage()
    @app.get('/api/v2/indicators/{ticker}',response_model=IndicatorResponse)
    def indicators(request:Request,ticker:str):
        security=repo(request).security(ticker)
        return request.app.state.indicators.stock(security['ticker'])
    @app.get('/api/v2/compare')
    def compare(request:Request,tickers:str,kind:Kind='market',date:str|None=None,version:str|None=None):return read(request,'compare',[t.strip() for t in tickers.split(',') if t.strip()],kind,date,version=version)
    @app.get('/api/v2/matrix/{year}')
    def matrix(request:Request,year:str,version:str|None=None,market_version:str|None=None):return read(request,'matrix',year,version=version,market_version=market_version)
    @app.get('/api/v2/migration/{kind}')
    def migration(request:Request,kind:Kind,source:str,target:str,version:str|None=None):return read(request,'migration',kind,source,target,version=version)
    return app

app=create_app()
