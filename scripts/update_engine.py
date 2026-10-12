"""Check or apply a safe fast-forward update of the public outlet engine."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "SilesiaCorp/outlet-photo-engine"


def git(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"Git {' '.join(args[:2])} nie zakończył się poprawnie; sprawdź dostęp i stan repo.")
    return result.stdout.strip()


def verify_remote(value: str):
    allowed = {f"https://github.com/{REPOSITORY}", f"https://github.com/{REPOSITORY}.git",
               f"git@github.com:{REPOSITORY}.git"}
    if value not in allowed:
        raise ValueError("Origin nie wskazuje kanonicznego publicznego silnika.")


def ensure_no_active_write(path: Path):
    if not path.is_file(): return
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        active = db.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('claimed','write_pending','needs_review')").fetchone()[0]
        if active:
            raise ValueError("Odnoga wykonuje wpis lub wynik jest niepewny. Zakończ/rozlicz tę operację przed aktualizacją.")
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Pobierz i zastosuj aktualizację po kontroli stanu")
    local = os.getenv("LOCALAPPDATA") or os.getenv("XDG_DATA_HOME")
    private = Path(local) if local else Path.home() / ".local" / "share"
    parser.add_argument("--queue-db", type=Path, default=private / "Codex" / "outlet-photo-engine" / "jobs.sqlite3")
    args = parser.parse_args()
    if not (ROOT / ".git").exists():
        raise ValueError("To kopia ZIP. Pobierz nowy ZIP do osobnego folderu albo użyj git clone; instrukcja w docs/UPDATING.md.")
    verify_remote(git("remote", "get-url", "origin"))
    if git("status", "--porcelain"):
        raise ValueError("Repo ma lokalne zmiany. Zachowaj i rozlicz je przed aktualizacją; skrypt ich nie nadpisze.")
    refs = git("ls-remote", "--symref", "origin", "HEAD")
    line = next((line for line in refs.splitlines() if line.startswith("ref: refs/heads/")), None)
    if not line:
        raise RuntimeError("Nie potwierdzono domyślnej gałęzi repo.")
    branch = line.split("\t", 1)[0].removeprefix("ref: refs/heads/")
    remote_sha = next(line.split()[0] for line in refs.splitlines() if line.endswith("\tHEAD") and not line.startswith("ref:"))
    before = git("rev-parse", "HEAD")
    if args.apply:
        ensure_no_active_write(args.queue_db)
        if git("branch", "--show-current") != branch:
            raise ValueError("Checkout jest na innej gałęzi niż wydanie. Przełącz ją świadomie po zachowaniu zmian.")
        git("fetch", "origin")
        git("merge", "--ff-only", f"origin/{branch}")
        after = git("rev-parse", "HEAD")
        # Remote can advance during the command; verify the fetched ref, not an old response.
        if after != git("rev-parse", f"origin/{branch}"):
            raise RuntimeError("Nie potwierdzono zgodnego SHA po aktualizacji.")
        if git("status", "--porcelain"):
            raise RuntimeError("Repo po aktualizacji nie jest czyste.")
        print(json.dumps({"updated": before != after, "verified": True, "commit": after}, ensure_ascii=False))
    else:
        print(json.dumps({"update_available": before != remote_sha, "current_commit": before,
                          "available_commit": remote_sha, "repository": f"https://github.com/{REPOSITORY}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError, sqlite3.Error) as error:
        print(f"Aktualizacja nieukończona: {error}", file=sys.stderr)
        raise SystemExit(1) from error
