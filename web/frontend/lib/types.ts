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
