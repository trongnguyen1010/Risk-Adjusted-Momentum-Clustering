from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from .repository import TerminalRepository, MissingData, InvalidQuery, AmbiguousIdentity
from .schemas import Kind, HealthResponse, CatalogResponse, SnapshotResponse, MembersResponse, StockResponse
from .indicators import IndicatorReferences

ROOT=Path(__file__).resolve().parents[3]

def create_app(repository=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.repository=repository or TerminalRepository(os.environ.get('DELTA_BUNDLE',str(ROOT/'data/web/delta-intelligence-v1')))
        app.state.indicators=IndicatorReferences(ROOT)
        yield
    app=FastAPI(title='DELTA Intelligence · Read-only Research API',version='1.0.0',lifespan=lifespan)
    def repo(request:Request):return request.app.state.repository
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
    def snapshot(request:Request,kind:Kind,date:str|None=None):return repo(request).snapshot(kind,date)
    @app.get('/api/v2/members/{kind}',response_model=MembersResponse)
    def members(request:Request,kind:Kind,date:str|None=None,q:str='',cluster:int|None=None,exchange:str|None=None,
                page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),sort:str='ticker',direction:str='asc',
                matrix_market:int|None=None,matrix_financial:int|None=None):
        return repo(request).members(kind,date,q,cluster,exchange,page,page_size,sort,direction,matrix_market,matrix_financial)
    @app.get('/api/v2/search')
    def search(request:Request,q:str='',limit:int=Query(12,ge=1,le=30)):return dict(items=repo(request).search(q,limit))
    @app.get('/api/v2/stocks/{ticker}',response_model=StockResponse)
    def stock(request:Request,ticker:str,kind:Kind='market',date:str|None=None):return repo(request).stock(ticker,kind,date)
    @app.get('/api/v2/prices/{ticker}')
    def prices(request:Request,ticker:str,end:str|None=None,basis:str='adj_close'):return repo(request).prices(ticker,end,basis)
    @app.get('/api/v2/indicators/{ticker}')
    def indicators(request:Request,ticker:str):
        security=repo(request).security(ticker)
        return request.app.state.indicators.stock(security['ticker'])
    @app.get('/api/v2/compare')
    def compare(request:Request,tickers:str,kind:Kind='market',date:str|None=None):return repo(request).compare([t.strip() for t in tickers.split(',') if t.strip()],kind,date)
    @app.get('/api/v2/matrix/{year}')
    def matrix(request:Request,year:str):return repo(request).matrix(year)
    @app.get('/api/v2/migration/{kind}')
    def migration(request:Request,kind:Kind,source:str,target:str):return repo(request).migration(kind,source,target)
    return app

app=create_app()
