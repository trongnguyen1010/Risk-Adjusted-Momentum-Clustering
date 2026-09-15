"""Read-only product projection over immutable research artifacts."""

from .builder import build_company_detail, export_product_bundle
from .repository import ProductRepository

__all__ = ["ProductRepository", "build_company_detail", "export_product_bundle"]
