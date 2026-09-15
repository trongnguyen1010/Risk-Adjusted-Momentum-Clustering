"""Validated file repository consumed by the HTTP product edge."""

from pathlib import Path

from ..io import read_json


class ProductRepository:
    def __init__(self, bundle_dir):
        self.bundle_dir = Path(bundle_dir).resolve()
        manifest_path = self.bundle_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError(f"missing product manifest: {manifest_path}")
        self.manifest = read_json(manifest_path)
        if self.manifest.get("status") != "complete":
            raise ValueError("product bundle is not complete")

    def list_companies(self):
        return read_json(self.bundle_dir / "companies.json")

    def get_company(self, ticker):
        normalized = str(ticker).strip().upper()
        if not normalized or not normalized.replace("-", "").isalnum():
            raise ValueError("ticker must contain only letters, numbers or hyphen")
        path = self.bundle_dir / "companies" / f"{normalized}.json"
        if not path.is_file():
            raise KeyError(normalized)
        return read_json(path)
