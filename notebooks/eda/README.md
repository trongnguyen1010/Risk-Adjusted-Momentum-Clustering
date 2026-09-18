# notebooks/eda

## Purpose

This folder contains inspection-only notebooks for the M1 Scale EDA.

**Important distinctions:**

| Layer | Role |
|---|---|
| `M1_SCALE_EDA.ipynb` | **Inspection layer** — reads pre-generated artifacts, no business logic |
| `data/derived/m1_scale_quality/<report_id>/` | **Source of truth** — generated offline by `scripts/report_m1_scale_quality.py` |

## Rules

- Notebooks perform **zero network requests**.
- Notebooks do **not** crawl, do not modify raw/canonical/derived artifacts.
- Do not put gate rules, feature formulas, or research business logic inside notebooks.
- Always point to an **explicit artifact ID**, not "latest".

## Quick start

```bash
pip install -e ".[research]"
```

Open `M1_SCALE_EDA.ipynb` using VS Code Jupyter, JupyterLab, or another compatible notebook environment.

Edit `QUALITY_REPORT_DIR` in Cell 1 to point to the desired quality artifact.
