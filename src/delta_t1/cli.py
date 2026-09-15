import argparse
from pathlib import Path
from .io import read_json
from .pipeline import run


def main(argv=None):
    parser = argparse.ArgumentParser(description="Delta T1 data foundation")
    commands = parser.add_subparsers(dest="command", required=True)
    pipeline = commands.add_parser("run", help="Download, QC and compute monthly features")
    pipeline.add_argument("--config", required=True)
    pipeline.add_argument("--root", default=".", help="Resolve data paths under this project directory")
    pipeline.add_argument("--resume", help="Resume the exact same config/code/raw snapshot")
    inspect = commands.add_parser("inspect", help="Print run status and artifact counts")
    inspect.add_argument("manifest")
    product = commands.add_parser("product-build", help="Build an immutable company-intelligence bundle")
    product.add_argument("--canonical", required=True)
    product.add_argument("--features", required=True)
    product.add_argument("--experiment", required=True)
    product.add_argument("--output", required=True)
    serve = commands.add_parser("serve", help="Serve a product bundle and the web shell")
    serve.add_argument("--bundle", required=True)
    serve.add_argument("--web-root", default="web")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            directory, manifest = run(Path(args.config), Path(args.root), args.resume)
            print(f"run_id={manifest['run_id']} status={manifest['status']} synthetic={manifest['synthetic']}")
            print(f"manifest={directory / 'manifest.json'}")
            if manifest['status'] != 'complete':
                print("Inspect manifest jobs and quality/issues.jsonl before retrying.")
            return 0 if manifest["status"] == "complete" else 2
        if args.command == "product-build":
            from .product import export_product_bundle
            manifest = export_product_bundle(args.canonical, args.features, args.experiment, args.output)
            print(f"product_bundle={args.output} companies={manifest['company_count']} status={manifest['status']}")
            return 0
        if args.command == "serve":
            from .product.server import serve
            serve(args.bundle, args.web_root, args.host, args.port)
            return 0
        manifest = read_json(args.manifest)
        for key in ("run_id", "status", "synthetic", "data_hash", "clean_rows", "feature_rows"):
            print(f"{key}: {manifest.get(key)}")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 2
