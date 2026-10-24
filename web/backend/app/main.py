from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from .repository import TerminalRepository, MissingData, InvalidQuery, AmbiguousIdentity
from .schemas import Kind, HealthResponse, CatalogResponse, SnapshotResponse, MembersResponse, StockResponse
from .indicators import IndicatorReferences
from .schemas import IndicatorResponse
from .previews import PreviewRepository

ROOT=Path(__file__).resolve().parents[3]

def create_app(repository=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.repository=repository or TerminalRepository(os.environ.get('DELTA_BUNDLE',str(ROOT/'data/web/delta-intelligence-v1')))
        preview_config=ROOT/'configs/product/model_previews_v1.json'
        if repository is None and preview_config.is_file():app.state.repository=PreviewRepository(app.state.repository,ROOT)
        app.state.indicators=IndicatorReferences(ROOT)
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
