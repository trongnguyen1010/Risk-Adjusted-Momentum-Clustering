from typing import Protocol


class SignalPolicy(Protocol):
    def make_targets(self, snapshot: dict, config: dict) -> dict:
        """Return decision_time, weights, cash_weight and selection reasons."""
        ...


class BacktestEngine(Protocol):
    def run(self, targets: list[dict], raw_prices: list[dict], actions: list[dict], calendar: list[dict], config: dict) -> dict:
        """Return trades, holdings, cash, gross/net NAV, rejects and provenance.

        Execute after signal availability. Raw prices only for quantities/cash.
        Corporate actions require explicit handling; never drop unresolved holdings.
        """
        ...
