"""Manage the private child-thread queue without starting tasks or making writes."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outlet_engine.queue import JobQueue  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    local = os.getenv("LOCALAPPDATA") or os.getenv("XDG_DATA_HOME")
    private_root = Path(local) if local else Path.home() / ".local" / "share"
    parser.add_argument("--db", type=Path, default=private_root / "Codex" / "outlet-photo-engine" / "jobs.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    enqueue = commands.add_parser("enqueue")
    enqueue.add_argument("--manifest", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("--operation", required=True)
    worker = commands.add_parser("worker")
    worker.add_argument("--resource", required=True)
    worker.add_argument("--thread")
    worker.add_argument("--host", default="local")
    claim = commands.add_parser("claim")
    claim.add_argument("--resource", required=True)
    claim.add_argument("--thread", required=True)
    claim.add_argument("--manifest-output", type=Path, help="Zapisz pobrany manifest prywatnie poza repo")
    update = commands.add_parser("update")
    update.add_argument("--operation", required=True)
    update.add_argument("--thread", required=True)
    update.add_argument("--state", choices=["write_pending", "verified", "needs_data", "needs_review", "failed"], required=True)
    update.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    queue = JobQueue(args.db)
    try:
        if args.command == "enqueue":
            result = queue.enqueue(json.loads(args.manifest.read_text(encoding="utf-8-sig")))
        elif args.command == "status":
            result = queue.get(args.operation)
        elif args.command == "worker":
            if args.thread:
                queue.register_worker(args.resource, args.thread, args.host)
            result = queue.worker(args.resource)
        elif args.command == "claim":
            result = queue.claim(args.resource, args.thread)
            if result and args.manifest_output:
                output = args.manifest_output.resolve()
                try:
                    output.relative_to(ROOT)
                except ValueError:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(result["manifest"] + "\n", encoding="utf-8")
                else:
                    raise ValueError("Manifest produkcyjny musi pozostać poza repozytorium.")
        else:
            receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig")) if args.receipt else None
            queue.update(args.operation, args.thread, args.state, receipt)
            result = queue.get(args.operation)
        # Do not dump purchase/customer data or the full manifest into the conversation.
        print(json.dumps({key: value for key, value in (result or {}).items()
                          if key in {"operation_id", "resource", "proposal_sha256", "state", "worker", "thread_id", "host_id", "updated_at"}},
                         ensure_ascii=False, indent=2))
    finally:
        queue.close()
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as error:
        print(f"Kolejka nieukończona: {error}", file=sys.stderr)
        raise SystemExit(1) from error
