"""Run offline research against a checksummed canonical pipeline run."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.pipeline import run_canonical
from delta_t1.experiments.runner import experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_run")
    parser.add_argument("--config", required=True)
    parser.add_argument("--canonical-feature-config", help="First run shared QC/features on a promotion directory")
    args = parser.parse_args()
    try:
        data_run = Path(args.data_run)
        if args.canonical_feature_config:
            data_run, manifest = run_canonical(data_run, args.canonical_feature_config, ROOT)
            if manifest["status"] != "complete":
                raise ValueError("canonical QC failed: " + str(data_run))
        target, manifest = experiment(data_run, Path(args.config), ROOT)
        print(f"{manifest['status']}: {target / 'manifest.json'}")
        raise SystemExit(0 if manifest["status"] == "complete" else 2)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
