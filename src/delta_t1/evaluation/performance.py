"""Daily simple-return metrics and paired moving-block bootstrap uncertainty."""
import math
import random
from statistics import mean, stdev, variance, covariance

from ..clustering.kmeans import quantile


def metrics(returns: list[float], benchmark: list[float], rf_annual: float, turnover: list[float]) -> dict:
    if len(returns) < 2 or len(returns) != len(benchmark) or len(turnover) != len(returns):
        raise ValueError("aligned returns/benchmark/turnover with at least two sessions required")
    if not math.isfinite(rf_annual) or rf_annual <= -1 or any(not math.isfinite(r) or r <= -1 for r in returns + benchmark):
        raise ValueError("invalid return/risk-free input")
    rf = (1 + rf_annual) ** (1 / 252) - 1
    excess = [r - rf for r in returns]
    active = [r - b for r, b in zip(returns, benchmark)]
    equity, peak, worst = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1)
    annual = equity ** (252 / len(returns)) - 1
    sd, excess_sd, tracking = stdev(returns), stdev(excess), stdev(active)
    downside = math.sqrt(mean(min(x, 0) ** 2 for x in excess))
    beta = covariance(returns, benchmark) / variance(benchmark) if variance(benchmark) > 1e-16 else None
    return dict(n_sessions=len(returns), cumulative_return=equity - 1, annualized_return=annual,
                annualized_volatility=sd * math.sqrt(252), sharpe=mean(excess) / excess_sd * math.sqrt(252) if excess_sd > 1e-12 else None,
                sortino=mean(excess) / downside * math.sqrt(252) if downside > 1e-12 else None,
                maximum_drawdown=worst, calmar=annual / abs(worst) if worst < 0 else None,
                hit_rate=sum(r > 0 for r in returns) / len(returns), turnover=sum(turnover),
                annualized_turnover=sum(turnover) * 252 / len(returns), beta=beta,
                alpha_annual=(mean(excess) - beta * mean(b - rf for b in benchmark)) * 252 if beta is not None else None,
                information_ratio=mean(active) / tracking * math.sqrt(252) if tracking > 1e-12 else None)


def bootstrap(returns: list[float], benchmark: list[float], seed: int, samples: int, block_length: int) -> dict:
    n = len(returns)
    if n != len(benchmark) or samples < 20 or not 1 <= block_length <= n:
        raise ValueError("invalid paired bootstrap configuration")
    rng, estimates = random.Random(seed), []
    for _ in range(samples):
        indices = []
        while len(indices) < n:
            start = rng.randrange(n - block_length + 1)
            indices.extend(range(start, start + block_length))
        selected = indices[:n]
        estimates.append(math.prod(1 + returns[i] for i in selected) - math.prod(1 + benchmark[i] for i in selected))
    return dict(method="paired moving-block bootstrap", statistic="strategy minus benchmark cumulative return",
                lower_95=quantile(estimates, .025), upper_95=quantile(estimates, .975), samples=samples,
                block_length=block_length, seed=seed, note="Conditional on fixed selected strategy; excludes model-selection uncertainty; not a significance claim")
