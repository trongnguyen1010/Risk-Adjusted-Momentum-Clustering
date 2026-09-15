"""Interface guard for a future explicitly approved temporal clustering method."""
from abc import ABC, abstractmethod


class DynamicClusteringMethod(ABC):
    """No implementation may be added before the methodology review is APPROVED."""

    @abstractmethod
    def fit_sequence(self, snapshots: list[list[dict]], config: dict) -> dict:
        raise NotImplementedError
