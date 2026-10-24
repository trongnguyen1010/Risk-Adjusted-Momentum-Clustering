import dictionary from "./vi.json";

const messages: Record<string, string> = dictionary;
export function vi(value: string): string {
  return messages[value] ?? value;
}

// Translate presentation strings only. Source identifiers, numeric values and
// the original experiment protocol stay intact for reproducibility.
export function localizePayload<T>(value: T): T {
  const identifiers = new Set([
    "protocol",
    "components",
    "version",
    "bundle_revision",
    "sha256",
    "source_sha256",
    "source_path",
    "source_id",
    "security_id",
    "registry_id",
    "ticker",
    "kind",
    "date",
    "year",
    "cohort",
    "id",
    "family",
    "availability",
    "value",
    "variant",
    "formula_version",
    "features",
    "unit",
    "status",
    "input_period",
    "input_scope",
    "price_date",
    "reference_date",
    "period_kind",
    "price_basis",
    "balance_date",
    "share_basis",
    "temporal_status",
    "missing_inputs",
    "dependency_ids",
    "evidence_ref",
    "pdf_sha256",
  ]);
  function visit(node: unknown, key = ""): unknown {
    if (identifiers.has(key)) return node;
    if (typeof node === "string") return vi(node);
    if (Array.isArray(node)) return node.map((item) => visit(item));
    if (node !== null && typeof node === "object") {
      return Object.fromEntries(
        Object.entries(node).map(([k, v]) => [k, visit(v, k)]),
      );
    }
    return node;
  }
  return visit(value) as T;
}
