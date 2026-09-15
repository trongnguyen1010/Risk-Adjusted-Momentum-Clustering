"""Versioned feature metadata; names alone never imply research eligibility."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    family: str
    version: str
    formula: str
    required_source: tuple[str, ...]
    lookback: str
    point_in_time_rule: str
    missing_policy: str
    transform: str
    cluster_eligible: bool
    reference: str


class FeatureRegistry:
    def __init__(self, definitions: Iterable[FeatureDefinition] = ()):
        self._definitions: dict[str, FeatureDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: FeatureDefinition) -> None:
        if not definition.name or definition.name in self._definitions:
            raise ValueError("feature name must be nonempty and unique: " + definition.name)
        if not all((definition.family, definition.version, definition.formula,
                    definition.point_in_time_rule, definition.missing_policy,
                    definition.transform, definition.reference)):
            raise ValueError("feature metadata is incomplete: " + definition.name)
        if not definition.required_source:
            raise ValueError("feature required_source is empty: " + definition.name)
        self._definitions[definition.name] = definition

    def get(self, name: str) -> FeatureDefinition:
        try:
            return self._definitions[name]
        except KeyError:
            raise ValueError("unregistered feature: " + name) from None

    def resolve(self, names: Iterable[str]) -> list[FeatureDefinition]:
        names = list(names)
        if not names or len(names) != len(set(names)):
            raise ValueError("feature list must be nonempty and unique")
        return [self.get(name) for name in names]

    def require_cluster_eligible(self, names: Iterable[str]) -> list[FeatureDefinition]:
        names = list(names)
        explicitly_prohibited = [name for name in names if name in PROHIBITED_CLUSTER_INPUTS]
        if explicitly_prohibited:
            raise ValueError(
                "Sharpe/ROI are portfolio-only and prohibited as clustering inputs: "
                + ", ".join(explicitly_prohibited)
            )
        definitions = self.resolve(names)
        prohibited = [item.name for item in definitions if not item.cluster_eligible]
        if prohibited:
            raise ValueError(
                "Sharpe/ROI and other non-cluster features are prohibited as clustering inputs: "
                + ", ".join(prohibited)
            )
        return definitions

    def names(self, *, family: str | None = None, cluster_eligible: bool | None = None) -> tuple[str, ...]:
        items = self._definitions.values()
        if family is not None:
            items = (item for item in items if item.family == family)
        if cluster_eligible is not None:
            items = (item for item in items if item.cluster_eligible is cluster_eligible)
        return tuple(sorted(item.name for item in items))


PIT_MARKET = "Source row available_at phải không sau decision_at; basis phải nhất quán."
NO_FILL = "Thiếu bất kỳ observation bắt buộc nào thì trả None; không fill hoặc đổi thành zero."
INTERNAL_BASELINE = "DELTA market baseline 1.4; cần literature lock trước final methodology."
PROHIBITED_CLUSTER_INPUTS = {"sharpe_63", "sharpe_126", "roi"}


def _market(name: str, formula: str, lookback: str, *, cluster_eligible: bool = True,
            source: tuple[str, ...] = ("prices_daily", "trading_calendar"),
            transform: str = "winsorize_then_snapshot_scale") -> FeatureDefinition:
    return FeatureDefinition(name=name, family="market" if cluster_eligible else "portfolio_legacy",
                             version="1.4.0", formula=formula, required_source=source,
                             lookback=lookback, point_in_time_rule=PIT_MARKET,
                             missing_policy=NO_FILL, transform=transform,
                             cluster_eligible=cluster_eligible, reference=INTERNAL_BASELINE)


DEFAULT_FEATURES = (
    _market("mom_21", "P_t / P_(t-21) - 1", "22 usable price observations"),
    _market("mom_63", "P_t / P_(t-63) - 1", "64 usable price observations"),
    _market("mom_126", "P_t / P_(t-126) - 1", "127 usable price observations"),
    _market("mom_252", "P_t / P_(t-252) - 1", "253 usable price observations"),
    _market("vol_63", "sample_std(daily_returns) * sqrt(252)", "63 consecutive returns"),
    _market("vol_126", "sample_std(daily_returns) * sqrt(252)", "126 consecutive returns"),
    _market("downside_vol_63", "sqrt(mean(min(r,0)^2) * 252)", "63 consecutive returns"),
    _market("mdd_126", "min(P / running_max(P) - 1)", "126 consecutive prices"),
    _market("beta_126", "cov(stock, benchmark) / var(benchmark)", "126 paired returns",
            source=("prices_daily", "benchmark_daily", "trading_calendar")),
    _market("liquidity_21", "mean(traded_value)", "21 consecutive values"),
    _market("ram_63", "mom_63 / vol_63", "mom_63 and vol_63"),
    FeatureDefinition(name="roi", family="portfolio_metric", version="prohibited",
                      formula="Không phải feature của DELTA.", required_source=("portfolio_returns",),
                      lookback="experiment-defined", point_in_time_rule="Chỉ sau portfolio simulation.",
                      missing_policy="Không đưa vào feature snapshot.", transform="none",
                      cluster_eligible=False, reference="DELTA research invariant"),
)


FEATURE_REGISTRY = FeatureRegistry(DEFAULT_FEATURES)


def validate_required_features(names: Iterable[str]) -> tuple[str, ...]:
    return tuple(item.name for item in FEATURE_REGISTRY.require_cluster_eligible(names))
