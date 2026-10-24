"""Polynomial, rectangular maximum-overlap matching for display labels only."""


def maximum_overlap(counts, sources, targets):
    # Square Hungarian assignment with dummy rows/columns. Noise is never aligned.
    sources = sorted(x for x in sources if x >= 0)
    targets = sorted(x for x in targets if x >= 0)
    size = max(len(sources), len(targets))
    if not size:
        return {}, sources, targets
    weights = [[counts.get((sources[i], targets[j]), 0)
                if i < len(sources) and j < len(targets) else 0
                for j in range(size)] for i in range(size)]
    u, v, p, way = [[0] * (size + 1) for _ in range(4)]
    for i in range(1, size + 1):
        p[0] = i
        j0 = 0
        minimum, used = [float('inf')] * (size + 1), [False] * (size + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], float('inf'), 0
            for j in range(1, size + 1):
                if not used[j]:
                    cur = -weights[i0-1][j-1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j], way[j] = cur, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(size + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if not j0:
                break
    mapping = {}
    for j in range(1, size + 1):
        i = p[j] - 1
        if i < len(sources) and j <= len(targets) and weights[i][j-1] > 0:
            mapping[targets[j-1]] = sources[i]
    return mapping, [x for x in sources if x not in mapping.values()], [x for x in targets if x not in mapping]
