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
    variants:dict[str,list[dict[str,Any]]]={}

class SnapshotResponse(BaseModel):
    points_included:bool=True
    snapshot:dict[str,Any]
    points:list[dict[str,Any]]
    profiles:list[dict[str,Any]]
    definitions:dict[str,Any]
    peer_examples:list[dict[str,Any]]=[]

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
    history_versions:dict[str,str]|None=None

Availability=Literal['SOURCE_REPORTED','AVAILABLE_REVIEWED','AVAILABLE_NOT_CONNECTED','MISSING_INPUT','NOT_COMPUTED','REVIEW_PENDING','NOT_APPLICABLE','SOURCE_UNAVAILABLE']

class IndicatorMetric(BaseModel):
    family:Literal['EPS','PE','PB','F_SCORE','M_SCORE','Z_SCORE']
    value:str|None
    status:str
    availability:Availability
    variant:str|None
    unit:str
    year:str|None=None
    input_period:str|None=None
    input_scope:str|None=None
    price_date:str|None=None
    reference_date:str|None=None
    period_kind:str|None=None
    price_basis:str|None=None
    balance_date:str|None=None
    share_basis:str|None=None
    temporal_status:str|None=None
    missing_inputs:str|None=None
    dependency_ids:str|None=None
    formula_version:str|None=None
    evidence_ref:str
    pdf_sha256:str|None=None
    components:dict[str,Any]|None=None
    strict_pit_ready:Literal[False]=False
    production_ready:Literal[False]=False

class IndicatorGroup(BaseModel):
    id:str
    source_id:str
    source_label:str
    cohort:str
    year:str
    metrics:list[IndicatorMetric]
    source_path:str
    source_sha256:str

class IndicatorResponse(BaseModel):
    ticker:str
    available:bool
    groups:list[IndicatorGroup]
    default_group_id:str|None
    sources:list[dict[str,Any]]
    coverage:dict[str,Any]
    unavailable_cohorts:int
    scope:str
    missing_reason:str|None
    note:str
