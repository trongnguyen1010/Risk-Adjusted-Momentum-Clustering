"""Permutation-invariant temporal metrics and exact label alignment."""
from collections import Counter
from functools import lru_cache
import math


def alignment(cost: list[list[float]]) -> dict[int, int]:
    """Return current column -> previous row via exact subset assignment."""
    n = len(cost)
    if n > 10 or any(len(row) != n for row in cost):
        raise ValueError("alignment requires same k <= 10")

    @lru_cache(None)
    def solve(row, mask):
        if row == n:
            return 0.0, ()
        options = []
        for column in range(n):
            if not mask & (1 << column):
                value, path = solve(row + 1, mask | (1 << column))
                options.append((cost[row][column] + value, (column,) + path))
        return min(options)

    return {column: row for row, column in enumerate(solve(0, 0)[1])}


def membership_metrics(a: list[int], b: list[int]) -> tuple[float | None, float | None]:
    n = len(a)
    if n < 2:
        return None, None
    joint, counts_a, counts_b = Counter(zip(a, b)), Counter(a), Counter(b)
    pairs = lambda value: value * (value - 1) / 2
    observed = sum(pairs(value) for value in joint.values())
    sum_a, sum_b = sum(pairs(value) for value in counts_a.values()), sum(pairs(value) for value in counts_b.values())
    expected, bound = sum_a * sum_b / pairs(n), (sum_a + sum_b) / 2
    ari = (observed - expected) / (bound - expected) if abs(bound - expected) > 1e-12 else 1.0
    entropy_a, entropy_b = (-sum(value / n * math.log(value / n) for value in counts.values())
                            for counts in (counts_a, counts_b))
    mutual_information = sum(value / n * math.log(value * n / (counts_a[left] * counts_b[right]))
                             for (left, right), value in joint.items())
    nmi = 2 * mutual_information / (entropy_a + entropy_b) if entropy_a + entropy_b else 1.0
    return ari, nmi


def compare(previous: dict, current: dict) -> dict:
    previous_labels = {row["security_id"]: label
                       for row, label in zip(previous["rows"], previous["labels"])}
    current_labels = {row["security_id"]: label
                      for row, label in zip(current["rows"], current["labels"])}
    shared = sorted(previous_labels.keys() & current_labels.keys())
    k = len(previous["profiles"])
    if k != len(current["profiles"]):
        raise ValueError("changed k requires a separate stability experiment")
    counts = Counter((previous_labels[sid], current_labels[sid]) for sid in shared)
    if not shared:
        return dict(n_common=0, entered=sorted(current_labels), exited=sorted(previous_labels), mapping=None,
                    ari=None, nmi=None, membership_turnover=None, centroid_drift=None, transitions=[])
    mapping = alignment([[-counts[left, right] for right in range(k)] for left in range(k)])
    ari, nmi = membership_metrics([previous_labels[sid] for sid in shared],
                                  [current_labels[sid] for sid in shared])
    aligned = Counter((previous_labels[sid], mapping[current_labels[sid]]) for sid in shared)
    denominators = Counter(previous_labels[sid] for sid in shared)
    transitions = [dict(from_cluster=left, to_cluster=right, count=aligned[left, right],
                        denominator=denominators[left],
                        rate=aligned[left, right] / denominators[left] if denominators[left] else None)
                   for left in range(k) for right in range(k)]
    drift = {}
    for current_id, previous_id in mapping.items():
        before = previous["profiles"][previous_id]["centroid"]
        after = current["profiles"][current_id]["centroid"]
        drift[current_id] = {name: after[name] - before[name] for name in before}
    turnover = sum(previous_labels[sid] != mapping[current_labels[sid]] for sid in shared) / len(shared)
    return dict(n_common=len(shared), entered=sorted(current_labels.keys() - previous_labels.keys()),
                exited=sorted(previous_labels.keys() - current_labels.keys()), mapping=mapping,
                ari=ari, nmi=nmi, membership_turnover=turnover,
                persistence_probability=1 - turnover, migration_rate=turnover,
                centroid_drift=drift,
                cluster_size_change={current_id: current["profiles"][current_id]["size"] / len(current_labels)
                                     - previous["profiles"][previous_id]["size"] / len(previous_labels)
                                     for current_id, previous_id in mapping.items()}, transitions=transitions)
