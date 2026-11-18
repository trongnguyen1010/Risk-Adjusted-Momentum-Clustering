from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

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


AssessmentContext = Literal['SIMULATED_AS_OF', 'CURRENT_AS_OF']
AssessmentAvailability = Literal['READY', 'HISTORICAL_ONLY', 'STALE', 'NOT_ELIGIBLE', 'NOT_FOUND', 'DATA_MISSING']
AssessmentStatus = Literal['RESEARCH_FAVORABLE', 'WATCH', 'CAUTION', 'INSUFFICIENT_EVIDENCE']
FeatureId = Literal[
    'roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover', 'revenue_growth', 'cfo_to_ni',
    'mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21', 'downside_vol_63',
]
FEATURE_IDS = frozenset(FeatureId.__args__)


class AssessmentClusterProfile(BaseModel):
    id: int
    model_version: str
    date_or_fy: str
    profile: str | None
    quality_flags: list[str] = Field(default_factory=list)
    source_revision: str


class AssessmentPeerComparison(BaseModel):
    peer_basis: str
    peer_count: int = Field(ge=0)
    peer_median: float | None
    p25: float | None
    p75: float | None


class AssessmentFeature(BaseModel):
    feature_id: FeatureId
    category: Literal['MARKET', 'FINANCIAL']
    value: float | None
    status: str
    unit: str
    period: str | None
    usable_from_date: str | None
    peer: AssessmentPeerComparison | None
    evidence_ref: str | None


class AssessmentEvidence(BaseModel):
    feature_id: FeatureId
    direction: Literal['FAVORABLE', 'CAUTION', 'COUNTER_EVIDENCE']
    message: str
    value: float | None
    status: str | None
    evidence_ref: str | None


class AssessmentHistoryPoint(BaseModel):
    feature_id: FeatureId
    period: str
    value: float | None
    status: str
    usable_from_date: str | None
    source: str


class AssessmentReferences(BaseModel):
    release_revision: str
    policy_revision: str
    manifest_sha256: str
    deterministic_content_sha256: str
    source_hashes: dict[str, str]


class AssessmentResponse(BaseModel):
    ticker: str
    request_time: str
    as_of: str
    required_price_session: str
    evidence_cutoff_at: str | None
    assessment_context: AssessmentContext
    availability_status: AssessmentAvailability
    assessment_status: AssessmentStatus
    rationale: str
    market_cluster: AssessmentClusterProfile | None
    financial_cluster: AssessmentClusterProfile | None
    features: list[AssessmentFeature] = Field(min_length=18, max_length=18)
    drivers: list[AssessmentEvidence] = Field(default_factory=list)
    risks: list[AssessmentEvidence] = Field(default_factory=list)
    counter_evidence: list[AssessmentEvidence] = Field(default_factory=list)
    history: list[AssessmentHistoryPoint] = Field(default_factory=list)
    references: AssessmentReferences
    scope: Literal['AS_OF_ASSESSMENT_ONLY']

    @model_validator(mode='after')
    def require_exact_feature_whitelist(self):
        if {feature.feature_id for feature in self.features} != FEATURE_IDS:
            raise ValueError('features must contain the Assessment whitelist exactly once')
        return self


class AssessmentQuery(BaseModel):
    """Public query parameters deliberately omit as_of and release context."""

    model_config = ConfigDict(extra='forbid')

    lookback_years: Literal[5, 10] = 10
