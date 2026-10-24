from typing import Any, Literal
from pydantic import BaseModel

Kind=Literal['market','financial','combined']

class HealthResponse(BaseModel):
    status:str
    version:str
    read_only:bool

class CatalogResponse(BaseModel):
    metadata:dict[str,Any]
    datasets:dict[str,Any]
    provenance:list[dict[str,Any]]

class SnapshotResponse(BaseModel):
    snapshot:dict[str,Any]
    points:list[dict[str,Any]]
    profiles:list[dict[str,Any]]
    definitions:dict[str,Any]

class MembersResponse(BaseModel):
    items:list[dict[str,Any]]
    total:int
    page:int
    page_size:int
    snapshot:dict[str,Any]
    columns:list[str]

class StockResponse(BaseModel):
    security:dict[str,Any]
    current:dict[str,Any]|None
    current_snapshot:dict[str,Any]
    current_missing_reason:str|None
    history:dict[str,list[dict[str,Any]]]
    price_coverage:dict[str,Any]
    financial_scope:str
    price_scope:str
