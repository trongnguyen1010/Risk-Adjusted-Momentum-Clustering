"""Prepare/verify folder consolidation; physical operations use checked PowerShell."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.layout import make_plan, verify_plan


def wrappers(plan):
    for entry in plan["entries"]:
        if entry["old"].startswith("scripts/") and entry["kind"] == "MOVE_FILE_KEEP_HARDLINK":
            name = Path(entry["old"]).name
            code = ('"""Entrypoint tương thích cho runner corporate actions đã lưu."""\n'
                'from pathlib import Path\nimport runpy\nimport sys\n'
                'ROOT = Path(__file__).resolve().parents[2]\n'
                'sys.path.insert(0, str(ROOT / "scripts"))\n'
                'if __name__ == "__main__":\n'
                f'    runpy.run_path(str(ROOT / "scripts" / {name!r}), run_name="__main__")\n')
            with (ROOT / "scripts/corporate_actions" / name).open("x", encoding="utf-8") as stream:
                stream.write(code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        plan = json.loads((args.output / "plan.json").read_text(encoding="utf-8"))
        result = verify_plan(ROOT, plan)
        with (args.output / "verification.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False))
    else:
        plan = make_plan(ROOT)
        args.output.mkdir(parents=True, exist_ok=False)
        with (args.output / "plan.json").open("x", encoding="utf-8") as stream:
            json.dump(plan, stream, ensure_ascii=False, indent=2)
        wrappers(plan)
        from collections import Counter
        print(json.dumps({"entries": len(plan["entries"]), "counts": dict(Counter(e["kind"] for e in plan["entries"]))}))
