export type Kind = "market" | "financial" | "combined";
export type Values = Record<string, number | null>;
export interface Definition {
  label: string;
  formula: string;
  unit: "percent" | "ratio" | "vnd";
  family: string;
}
export interface Observation {
  kind: Kind;
  date: string;
  ticker: string;
  security_id: string;
  cluster: number;
  features: Values;
  scope: string;
  name?: string;
  exchange?: string;
  liquidity?: "LIQUID" | "ILLIQUID" | null;
}
export interface Snapshot {
  kind: Kind;
  date: string;
  n: number;
  k: number;
  sizes: Record<string, number>;
  metrics: Record<string, unknown>;
  scope: string;
}
export interface Profile {
  kind: Kind;
  date: string;
  cluster: number;
  size: number;
  means: Values;
  medians: Values;
  quartiles: Record<string, number[] | null>;
  name?: string | null;
  description?: string | null;
}
export interface Dataset {
  label?: string;
  status?: string;
  history: Snapshot[];
  dates: string[];
  latest: Snapshot;
  k: number;
  scaling: string;
  frequency: string;
  features: string[];
  version: string;
  protocol?: Record<string, unknown>;
  liquidity_filter?: string;
  stability_note?: string;
}
export interface Catalog {
  metadata: {
    bundle_revision?: string;
    candidates: number;
    market_snapshots: number;
    financial_periods: number;
    combined_snapshots: number;
    scope: string;
    financial_rows: number;
    financial_publication_rows: number;
    price_rows: number;
    price_conflicts_held: number;
    generated_at: string;
    version: string;
    definitions: Record<string, Definition>;
    validations: Record<string, { status: string; quality_status: string }>;
    full_suite: { status: string; reason: string };
    limitations: string[];
  };
  datasets: Record<Kind, Dataset>;
  variants?: Partial<Record<Kind, Dataset[]>>;
  provenance: { path: string; sha256: string; bytes: number }[];
}
export interface SnapshotData {
  peer_examples?: {
    ticker: string;
    cluster: number;
    rule: string;
    peers: { ticker: string; distance: number }[];
  }[];
  snapshot: Snapshot;
  points: Observation[];
  profiles: Profile[];
  definitions: Record<string, Definition>;
}
export interface Members {
  items: Observation[];
  total: number;
  page: number;
  page_size: number;
  snapshot: Snapshot;
  columns: string[];
}
export interface Security {
  ticker: string;
  name: string;
  exchange: string;
  security_id: string;
  ambiguous: number;
}
export interface Stock {
  history_versions?: Record<Kind, string> | null;
  security: Security;
  current: Observation | null;
  current_snapshot: Snapshot;
  current_missing_reason: string | null;
  history: Record<Kind, Observation[]>;
  price_coverage: { start: string | null; end: string | null; rows: number };
  financial_scope: string;
  price_scope: string;
}
export interface PriceData {
  ticker: string;
  basis: string;
  unit: string;
  available: boolean;
  missing_reason: string | null;
  points: {
    date: string;
    close: number | null;
    volume: number | null;
    conflict: number;
  }[];
}
export interface Migration {
  source: string;
  target: string;
  kind: Kind;
  common: number;
  entered: number;
  exited: number;
  stayed: number;
  mapping: Record<string, number>;
  cells: { source: number; target: number; n: number }[];
  alignment: string;
}
export interface Matrix {
  market_labels?: number[];
  financial_labels?: number[];
  available: boolean;
  date: string | null;
  year: string;
  total: number;
  cells: { market_cluster: number; financial_cluster: number; n: number }[];
  scope: string;
  reason: string;
}
export interface Comparison {
  snapshot: Snapshot;
  features: string[];
  items: {
    security: Security;
    observation: Observation | null;
    missing_reason: string | null;
  }[];
}

// Indicators v1 (D-IND-01): /api/v2/stocks/{ticker}/overview|fundamentals|scores|peers
export type CellStatus =
  | "OK"
  | "MISSING_INPUT"
  | "NOT_APPLICABLE"
  | "NEGATIVE_EARNINGS"
  | "NEGATIVE_EQUITY"
  | "NO_PRICE";
export type MetricUnit = "vnd" | "percent" | "times" | "points" | "score";
export interface IndicatorCell {
  value: number | null;
  status: CellStatus;
  reason?: "NO_ANNUAL_REPORT";
}
export interface MetricDefinition {
  group: string;
  label: string;
  unit: MetricUnit;
  description: string;
}
export interface StockCard extends IndicatorCell, MetricDefinition {
  metric: string;
  year: number;
  rating: string | null;
}
export interface StockOverview {
  ticker: string;
  name: string | null;
  exchange: string | null;
  sector_group: string;
  sector_label: string;
  financial_sector: boolean;
  latest_fiscal_year: number | null;
  price: {
    close: number;
    date: string;
    change_1d: number | null;
    change_1m: number | null;
    change_ytd: number | null;
  } | null;
  market_cap: number | null;
  shares: number | null;
  cards: StockCard[];
  summary: string[];
  liquidity?: { status: "LIQUID" | "ILLIQUID"; date: string } | null;
  groups?: { kind: Kind; date: string; cluster: number; name: string | null; description: string | null }[];
}
export interface StockFundamentals {
  ticker: string;
  financial_sector: boolean;
  years: number[];
  run_id: string | null;
  price_basis: string | null;
  metrics: Record<string, Record<string, IndicatorCell>>;
  definitions: Record<string, MetricDefinition>;
  groups: { name: string; metrics: string[] }[];
}
export interface ScoreHead {
  value: number | null;
  status: CellStatus;
  rating: string | null;
  missing: string[];
  flags: string[];
}
export interface StockScores {
  ticker: string;
  year: number;
  applicable: boolean;
  f_score: ScoreHead & {
    known_signals: number;
    signals: { name: string; passed: boolean | null; text: string }[];
  };
  m_score: ScoreHead & {
    variables: { name: string; value: number | null; text: string }[];
  };
  z_score: ScoreHead & {
    components: { name: string; value: number | null; text: string }[];
  };
  z_score_dp: ScoreHead;
}
export interface PeerRow {
  ticker: string;
  name: string | null;
  exchange: string | null;
  sector_group: string;
  latest_fiscal_year: number | null;
  pe: number | null;
  pb: number | null;
  roe: number | null;
  eps: number | null;
  market_cap: number | null;
}
export interface StockPeers {
  ticker: string;
  basis: string;
  items: PeerRow[];
}

// Investment Assessment response (S4). Keep the nullable fields nullable: a missing
// value/status is evidence state, not a value to fill from a fixture or another release.
export type AssessmentContext = "SIMULATED_AS_OF" | "CURRENT_AS_OF";
export type AssessmentAvailabilityStatus =
  | "READY"
  | "HISTORICAL_ONLY"
  | "STALE"
  | "NOT_ELIGIBLE"
  | "NOT_FOUND"
  | "DATA_MISSING";
export type AssessmentStatus =
  | "RESEARCH_FAVORABLE"
  | "WATCH"
  | "CAUTION"
  | "INSUFFICIENT_EVIDENCE";
export type AssessmentFeatureId =
  | "roe"
  | "roa"
  | "gross_margin"
  | "net_margin"
  | "debt_to_equity"
  | "current_ratio"
  | "asset_turnover"
  | "revenue_growth"
  | "cfo_to_ni"
  | "mom_21"
  | "mom_63"
  | "mom_126"
  | "mom_252"
  | "vol_63"
  | "mdd_126"
  | "beta_126"
  | "liquidity_21"
  | "downside_vol_63";
export type AssessmentFeatureCategory = "MARKET" | "FINANCIAL";
export type AssessmentFeatureValueStatus = "OK" | "DATA_MISSING";

export interface AssessmentPeerComparison {
  peer_basis: string;
  peer_count: number;
  peer_median: number | null;
  p25: number | null;
  p75: number | null;
}

export interface AssessmentFeature {
  feature_id: AssessmentFeatureId;
  category: AssessmentFeatureCategory;
  value: number | null;
  status: AssessmentFeatureValueStatus;
  unit: string;
  period: string | null;
  usable_from_date: string | null;
  peer: AssessmentPeerComparison | null;
  evidence_ref: string | null;
}

export interface AssessmentClusterProfile {
  id: number;
  model_version: string;
  date_or_fy: string;
  profile: string | null;
  quality_flags: string[];
  source_revision: string;
}

export interface AssessmentEvidence {
  feature_id: AssessmentFeatureId | null;
  direction: "FAVORABLE" | "CAUTION" | "COUNTER_EVIDENCE";
  message: string;
  value: number | null;
  status: string | null;
  evidence_ref: string | null;
}

export interface AssessmentHistoryPoint {
  feature_id: AssessmentFeatureId;
  period: string;
  value: number | null;
  status: string;
  usable_from_date: string | null;
  source: string;
}

export interface AssessmentReferences {
  release_revision: string;
  policy_revision: string;
  manifest_sha256: string;
  deterministic_content_sha256: string;
  source_hashes: Record<string, string>;
}

export interface AssessmentResponse {
  ticker: string;
  request_time: string;
  as_of: string;
  required_price_session: string;
  evidence_cutoff_at: string | null;
  assessment_context: AssessmentContext;
  availability_status: AssessmentAvailabilityStatus;
  assessment_status: AssessmentStatus;
  rationale: string;
  market_cluster: AssessmentClusterProfile | null;
  financial_cluster: AssessmentClusterProfile | null;
  features: AssessmentFeature[];
  drivers: AssessmentEvidence[];
  risks: AssessmentEvidence[];
  counter_evidence: AssessmentEvidence[];
  history: AssessmentHistoryPoint[];
  references: AssessmentReferences;
  scope: "AS_OF_ASSESSMENT_ONLY";
}

export interface AssessmentQuery {
  lookback_years?: 5 | 10;
}

export type BacktestMetrics = {
  periods: number;
  total_return: number | null;
  cagr: number | null;
  volatility_annual: number | null;
  max_drawdown: number | null;
  avg_turnover: number | null;
  avg_cash_after_trading: number | null;
  failed_buys: number;
  failed_sells: number;
  scaled_buys: number;
  price_stale?: number;
  limit_data_missing?: number;
};
export type BacktestSegment = {
  segment: "development" | "holdout";
  run_id: string;
  start: string;
  end: string;
  status: string;
  financial_source: string;
  git_commit: string;
  config: string;
  config_sha256: string;
  counts: Record<string, { decisions: number; executed: number; too_small: number; not_executed_segment_end: number }>;
  seal: { path: string; sha256: string; sealed_at: string; status: string };
  inputs_sha256: Record<string, string>;
  metrics: Record<string, BacktestMetrics>;
  adj_glitches_repaired: number | null;
  sources: { path: string; sha256: string }[];
};
export type BacktestSummary = {
  version: string;
  strategies: string[];
  benchmark: string;
  final_status: string;
  source_commit: string;
  config_sha256: string;
  outputs_manifest: { path: string; sha256: string };
  segments: BacktestSegment[];
};
type BacktestLines = { dates: string[]; series: Record<string, number[]> };
export type BacktestSeries = { segment: string; run_id: string; nav: BacktestLines; drawdown: BacktestLines; turnover: BacktestLines };
export type BacktestPeriod = {
  date: string;
  decision_date: string;
  candidates: number;
  status: string;
  executed: boolean;
  cash: number | null;
  items: { ticker: string; weight: number; rank: number | null }[];
};
export type BacktestHoldings = {
  segment: string;
  run_id: string;
  strategy: string;
  periods: { date: string; decision_date: string; status: string; executed: boolean; n: number }[];
  period: BacktestPeriod;
};
