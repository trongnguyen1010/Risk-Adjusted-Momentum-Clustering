/** Small descriptive statistics for one snapshot (no model fitting). */

/** Average ranks (1..n) of the finite values; other entries stay null. */
export function ranks(values: (number | null | undefined)[]): (number | null)[] {
  const idx = values
    .map((v, i) => [v, i] as const)
    .filter((p): p is readonly [number, number] => typeof p[0] === "number" && Number.isFinite(p[0]))
    .sort((a, b) => a[0] - b[0]);
  const out: (number | null)[] = values.map(() => null);
  for (let i = 0; i < idx.length; ) {
    let j = i;
    while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    const r = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) out[idx[k][1]] = r;
    i = j + 1;
  }
  return out;
}

/** Percentile in [0, 1] of each value within the column (ties share the average rank). */
export function percentiles(values: (number | null | undefined)[]): (number | null)[] {
  const r = ranks(values);
  const n = r.filter((v) => v !== null).length;
  return r.map((v) => (v === null ? null : n > 1 ? (v - 1) / (n - 1) : 0.5));
}

/** Spearman rank correlation on rows where both values exist; null if fewer than 10 pairs. */
export function spearman(a: (number | null | undefined)[], b: (number | null | undefined)[]): number | null {
  const pairs = a
    .map((v, i) => [v, b[i]] as const)
    .filter((p): p is readonly [number, number] => typeof p[0] === "number" && typeof p[1] === "number");
  if (pairs.length < 10) return null;
  const ra = ranks(pairs.map((p) => p[0])) as number[];
  const rb = ranks(pairs.map((p) => p[1])) as number[];
  const mean = (pairs.length + 1) / 2;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < pairs.length; i++) {
    num += (ra[i] - mean) * (rb[i] - mean);
    da += (ra[i] - mean) ** 2;
    db += (rb[i] - mean) ** 2;
  }
  return da && db ? num / Math.sqrt(da * db) : null;
}

export function median(values: (number | null | undefined)[]): number | null {
  const v = values.filter((x): x is number => typeof x === "number" && Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}
