from typing import Protocol


class SnapshotClusterer(Protocol):
    def fit_snapshot(self, eligible_features: list[dict], config: dict) -> dict:
        """Return assignments, profiles, metrics and fitted scaler/PCA/model bundle.

        Fit one cross-section only. Save fit_as_of, feature/data versions and seed.
        The implementation must validate assignments against the shared contract.
        """
        ...
