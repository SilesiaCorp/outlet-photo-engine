"""Generate or verify an approved sheet-entry plan; never send a write itself."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outlet_engine.sheet import assert_preimage, build_plan, verify_readback  # noqa: E402


def private_path(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return resolved
    raise ValueError("Manifest, snapshot, plan i receipt muszą pozostać poza repozytorium.")


def load(path: Path):
    return json.loads(private_path(path).read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("plan")
    build.add_argument("--manifest", type=Path, required=True)
    build.add_argument("--snapshot", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    for command in ["preflight", "verify"]:
        action = commands.add_parser(command)
        action.add_argument("--plan", type=Path, required=True)
        action.add_argument("--snapshot", type=Path, required=True)
        if command == "verify":
            action.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        result = build_plan(load(args.manifest), load(args.snapshot))
    elif args.command == "preflight":
        assert_preimage(load(args.plan), load(args.snapshot))
        print("Aktualny wiersz i struktura zgadzają się z planem.")
        return 0
    else:
        result = verify_readback(load(args.plan), load(args.snapshot))
    destination = private_path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    print(f"{args.command}: {result['range']}; OP {result['operation_id']}; wynik zapisano prywatnie.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as error:
        print(f"Plan/weryfikacja nieukończone: {error}", file=sys.stderr)
        raise SystemExit(1) from error
