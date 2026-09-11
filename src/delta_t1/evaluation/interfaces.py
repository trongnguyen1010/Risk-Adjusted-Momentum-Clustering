from typing import Protocol


class StabilityEvaluator(Protocol):
    def compare(self, previous: list[dict], current: list[dict]) -> dict:
        """Return ARI, mapping, transitions, entered/exited and n_common.

        Preserve raw labels. Compare membership, not coordinates from separate PCA fits.
        """
        ...
