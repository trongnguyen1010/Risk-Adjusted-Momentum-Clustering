"""Daily portfolio metrics and paired moving-block bootstrap uncertainty."""
import math
import random
from statistics import covariance, mean, stdev, variance

from ..features.preprocessing import quantile


def metrics(returns: list[float], benchmark: list[float], rf_annual: float, turnover: list[float]) -> dict:
    if len(returns) < 2 or len(returns) != len(benchmark) or len(turnover) != len(returns):
        raise ValueError("aligned returns/benchmark/turnover with at least two sessions required")
    if not math.isfinite(rf_annual) or rf_annual <= -1 or any(
            not math.isfinite(value) or value <= -1 for value in returns + benchmark):
        raise ValueError("invalid return/risk-free input")
    risk_free = (1 + rf_annual) ** (1 / 252) - 1
    excess = [value - risk_free for value in returns]
    active = [value - baseline for value, baseline in zip(returns, benchmark)]
    equity, peak, worst = 1.0, 1.0, 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1)
    annual = equity ** (252 / len(returns)) - 1
    deviation, excess_deviation, tracking = stdev(returns), stdev(excess), stdev(active)
    downside = math.sqrt(mean(min(value, 0) ** 2 for value in excess))
    beta = covariance(returns, benchmark) / variance(benchmark) if variance(benchmark) > 1e-16 else None
    return dict(n_sessions=len(returns), cumulative_return=equity - 1, annualized_return=annual,
                annualized_volatility=deviation * math.sqrt(252),
                sharpe=mean(excess) / excess_deviation * math.sqrt(252) if excess_deviation > 1e-12 else None,
                sortino=mean(excess) / downside * math.sqrt(252) if downside > 1e-12 else None,
                maximum_drawdown=worst, calmar=annual / abs(worst) if worst < 0 else None,
                hit_rate=sum(value > 0 for value in returns) / len(returns), turnover=sum(turnover),
                annualized_turnover=sum(turnover) * 252 / len(returns), beta=beta,
                alpha_annual=(mean(excess) - beta * mean(value - risk_free for value in benchmark)) * 252
                if beta is not None else None,
                information_ratio=mean(active) / tracking * math.sqrt(252) if tracking > 1e-12 else None)


def bootstrap(returns: list[float], benchmark: list[float], seed: int, samples: int, block_length: int) -> dict:
    n = len(returns)
    if n != len(benchmark) or samples < 20 or not 1 <= block_length <= n:
        raise ValueError("invalid paired bootstrap configuration")
    generator, estimates = random.Random(seed), []
    for _ in range(samples):
        indices = []
        while len(indices) < n:
            start = generator.randrange(n - block_length + 1)
            indices.extend(range(start, start + block_length))
        selected = indices[:n]
        estimates.append(math.prod(1 + returns[index] for index in selected)
                         - math.prod(1 + benchmark[index] for index in selected))
    return dict(method="paired moving-block bootstrap",
                statistic="strategy minus benchmark cumulative return",
                lower_95=quantile(estimates, .025), upper_95=quantile(estimates, .975),
                samples=samples, block_length=block_length, seed=seed,
                note="Conditional on fixed selected strategy; excludes model-selection uncertainty; not a significance claim")
