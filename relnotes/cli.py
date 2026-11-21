"""relnotes command line.

Stdlib argparse on purpose: every tool repo runs this in CI through
`uvx relnotes`, so it carries no runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path

from relnotes import __version__
from relnotes.notes import NOTES_DIR, check, collect, note_paths, page, release_body


def guide_text() -> str:
    return files("relnotes").joinpath("guide.md").read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="relnotes",
        description="Release notes as one small file per user-visible change, in "
        f"{NOTES_DIR}/. Run `relnotes guide` before writing one.",
    )
    ap.add_argument("--version", action="version", version=f"relnotes {__version__}")
    ap.add_argument("--repo", type=Path, default=Path(), help="repo root (default: .)")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")
    sub.add_parser("guide", help="when and how to write a note (read this first)")
    sub.add_parser("check", help="exit 1 if any note is malformed")
    b = sub.add_parser("body", help="GitHub release body for a tag")
    b.add_argument("tag", help="the release tag, e.g. v1.2.3")
    pg = sub.add_parser("page", help="docs page: every note, newest release first")
    pg.add_argument("--out", type=Path, help="write here instead of stdout")
    pg.add_argument("--title", default="Release notes")
    sub.add_parser("json", help="every note with its version, as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo: Path = args.repo
    if args.cmd == "guide":
        sys.stdout.write(guide_text())
        return 0
    if args.cmd == "check":
        errors = check(repo)
        for e in errors:
            print(e, file=sys.stderr)
        if errors:
            print(
                "run `relnotes guide` for the format and wording rules", file=sys.stderr
            )
            return 1
        print(f"{len(note_paths(repo))} release notes ok")
        return 0
    notes = collect(repo)
    if args.cmd == "body":
        sys.stdout.write(release_body(notes, args.tag))
    elif args.cmd == "page":
        text = page(notes, args.title)
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
    else:
        json.dump([asdict(n) for n in notes], sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
