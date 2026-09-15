"""GMM comparator boundary pending dependency and covariance protocol approval."""


def validate_config(config: dict) -> None:
    raise ValueError("GMM is not enabled until covariance, initialization and dependency methodology are approved")


def fit_snapshot(rows: list[dict], config: dict) -> dict:
    validate_config(config)
    raise AssertionError("unreachable")
