"""DBSCAN comparator boundary pending approved density protocol."""


def validate_config(config: dict) -> None:
    raise ValueError("DBSCAN is not enabled until eps/min_samples and noise-handling methodology are approved")


def fit_snapshot(rows: list[dict], config: dict) -> dict:
    validate_config(config)
    raise AssertionError("unreachable")
