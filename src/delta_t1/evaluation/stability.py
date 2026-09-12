"""Permutation-invariant metrics and exact minimum-cost label alignment."""
from collections import Counter
from functools import lru_cache
import math


def alignment(cost: list[list[float]]) -> dict[int, int]:
    """Exact assignment via subset DP, O(k² 2^k), bounded to research k<=10.

    Returns current column -> previous row. Same objective as Hungarian matching.
    """
    n = len(cost)
    if n > 10 or any(len(row) != n for row in cost):
        raise ValueError("alignment requires same k <= 10")
    @lru_cache(None)
    def solve(row, mask):
        if row == n:
            return 0.0, ()
        options = []
        for col in range(n):
            if not mask & (1 << col):
                value, path = solve(row + 1, mask | (1 << col))
                options.append((cost[row][col] + value, (col,) + path))
        return min(options)
    return {col: row for row, col in enumerate(solve(0, 0)[1])}


def membership_metrics(a: list[int], b: list[int]) -> tuple[float | None, float | None]:
    n = len(a)
    if n < 2:
        return None, None
    joint, ca, cb = Counter(zip(a, b)), Counter(a), Counter(b)
    pairs = lambda x: x * (x - 1) / 2
    observed = sum(pairs(v) for v in joint.values())
    sa, sb = sum(pairs(v) for v in ca.values()), sum(pairs(v) for v in cb.values())
    expected, bound = sa * sb / pairs(n), (sa + sb) / 2
    ari = (observed - expected) / (bound - expected) if abs(bound - expected) > 1e-12 else 1.0
    ha, hb = (-sum(v / n * math.log(v / n) for v in c.values()) for c in (ca, cb))
    mi = sum(v / n * math.log(v * n / (ca[x] * cb[y])) for (x, y), v in joint.items())
    return ari, 2 * mi / (ha + hb) if ha + hb else 1.0


def compare(previous: dict, current: dict) -> dict:
    p = {r["security_id"]: c for r, c in zip(previous["rows"], previous["labels"])}
    c = {r["security_id"]: label for r, label in zip(current["rows"], current["labels"])}
    shared = sorted(p.keys() & c.keys())
    k = len(previous["profiles"])
    if k != len(current["profiles"]):
        raise ValueError("changed k requires a separate stability experiment")
    # Align on common membership, avoiding distances between independently fitted scalers.
    counts = Counter((p[s], c[s]) for s in shared)
    if not shared:
        return dict(n_common=0, entered=sorted(c.keys()), exited=sorted(p.keys()), mapping=None,
                    ari=None, nmi=None, membership_turnover=None, centroid_drift=None, transitions=[])
    mapping = alignment([[-counts[i, j] for j in range(k)] for i in range(k)])
    ari, nmi = membership_metrics([p[s] for s in shared], [c[s] for s in shared])
    aligned = Counter((p[s], mapping[c[s]]) for s in shared)
    denominators = Counter(p[s] for s in shared)
    transitions = [dict(from_cluster=i, to_cluster=j, count=aligned[i, j], denominator=denominators[i],
                        rate=aligned[i, j] / denominators[i] if denominators[i] else None) for i in range(k) for j in range(k)]
    # Drift is per-feature in raw feature units, not incomparable scaler coordinates.
    drift = {}
    for current_id, previous_id in mapping.items():
        a, b = previous["profiles"][previous_id]["centroid"], current["profiles"][current_id]["centroid"]
        drift[current_id] = {name: b[name] - a[name] for name in a}
    turnover = sum(p[s] != mapping[c[s]] for s in shared) / len(shared)
    return dict(n_common=len(shared), entered=sorted(c.keys() - p.keys()), exited=sorted(p.keys() - c.keys()),
                mapping=mapping, ari=ari, nmi=nmi, membership_turnover=turnover, persistence_probability=1 - turnover,
                migration_rate=turnover, centroid_drift=drift,
                cluster_size_change={j: current["profiles"][j]["size"] / len(c) - previous["profiles"][i]["size"] / len(p) for j, i in mapping.items()}, transitions=transitions)
