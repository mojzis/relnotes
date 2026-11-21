"""Read release notes and render them.

A note is `release-notes/YYYY-MM-DD-short-slug.md` with a `kind:` frontmatter
field and a one- or two-sentence body. The version a note ships in is the
first `v*` tag that contains the commit which added the file, so nothing is
moved or edited at release time.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

NOTES_DIR = "release-notes"
KINDS = ("added", "changed", "fixed", "removed")
KIND_TITLES = {
    "added": "Added",
    "changed": "Changed",
    "fixed": "Fixed",
    "removed": "Removed",
}
MAX_CHARS = 400

_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
_FRONT = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


@dataclass
class Note:
    file: str
    date: str
    slug: str
    kind: str
    body: str
    version: str | None = None
    released: str | None = None


class NoteError(ValueError):
    pass


def parse(path: Path) -> Note:
    """Read one note; raise NoteError naming what is wrong."""
    m = _NAME.match(path.name)
    if not m:
        raise NoteError("name must be YYYY-MM-DD-short-slug.md (lowercase, hyphens)")
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    front = _FRONT.match(text)
    if not front:
        raise NoteError("must start with a --- frontmatter block holding `kind:`")
    fields = {}
    for line in front.group(1).splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise NoteError(f"frontmatter line is not `key: value`: {line!r}")
        fields[key.strip()] = value.strip()
    if set(fields) != {"kind"}:
        raise NoteError(
            f"frontmatter takes only `kind`, got: {', '.join(sorted(fields))}"
        )
    kind = fields["kind"]
    if kind not in KINDS:
        raise NoteError(f"kind must be one of {', '.join(KINDS)}, got {kind!r}")
    body = front.group(2).strip()
    if not body:
        raise NoteError("body is empty")
    if body.startswith("#"):
        raise NoteError("no headings: the body is one or two plain sentences")
    if len(body) > MAX_CHARS:
        raise NoteError(f"body is {len(body)} characters, the limit is {MAX_CHARS}")
    return Note(file=path.name, date=m.group(1), slug=m.group(2), kind=kind, body=body)


def note_paths(repo: Path) -> list[Path]:
    d = repo / NOTES_DIR
    return (
        sorted(p for p in d.glob("*.md") if p.name.lower() != "readme.md")
        if d.is_dir()
        else []
    )


def check(repo: Path) -> list[str]:
    errors = []
    for p in note_paths(repo):
        try:
            parse(p)
        except NoteError as e:
            errors.append(f"{NOTES_DIR}/{p.name}: {e}")
    return errors


def _git(repo: Path, *args: str) -> str:
    # Fixed git subcommands, no shell; git comes from PATH as in any CI.
    cmd = ["git", *args]
    return subprocess.run(  # noqa: S603
        cmd, cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def _added_in(repo: Path) -> dict[str, str]:
    """Note file name -> hash of the oldest commit that added it."""
    out = _git(
        repo, "log", "--reverse", "--no-renames", "--diff-filter=A",
        "--format=%x00%H", "--name-only", "--", NOTES_DIR,
    )  # fmt: skip
    added: dict[str, str] = {}
    commit = ""
    for line in out.splitlines():
        if line.startswith("\0"):
            commit = line[1:]
        elif line.strip():
            added.setdefault(Path(line).name, commit)
    return added


def _tag_dates(repo: Path) -> dict[str, str]:
    out = _git(
        repo,
        "for-each-ref",
        "refs/tags/v*",
        "--format=%(refname:short) %(creatordate:short)",
    )
    return dict(line.split(" ", 1) for line in out.splitlines() if " " in line)


def _first_tag(repo: Path, commit: str) -> str | None:
    out = _git(
        repo, "tag", "--contains", commit, "--list", "v*", "--sort=version:refname"
    )
    tags = out.split()
    return tags[0] if tags else None


def collect(repo: Path) -> list[Note]:
    """Every well-formed note, with the version it shipped in (None = unreleased).

    Malformed notes are skipped here; `check` is what reports them.
    """
    notes = []
    for p in note_paths(repo):
        try:
            notes.append(parse(p))
        except NoteError:
            continue
    if not notes:
        return notes
    try:
        added = _added_in(repo)
        dates = _tag_dates(repo)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return notes
    first: dict[str, str | None] = {}
    for n in notes:
        commit = added.get(n.file)
        if not commit:
            continue  # not committed yet
        if commit not in first:
            first[commit] = _first_tag(repo, commit)
        n.version = first[commit]
        n.released = dates.get(n.version) if n.version else None
    return notes


def _item(n: Note) -> str:
    return "- " + n.body.replace("\n", "\n  ")


def _by_kind(notes: list[Note]) -> list[str]:
    lines: list[str] = []
    for kind in KINDS:
        group = sorted((n for n in notes if n.kind == kind), key=lambda n: n.file)
        if group:
            lines += [f"### {KIND_TITLES[kind]}", "", *map(_item, group), ""]
    return lines


def release_body(notes: list[Note], tag: str) -> str:
    """Markdown for the GitHub release of `tag`; empty when no note shipped in it."""
    lines = _by_kind([n for n in notes if n.version == tag])
    return "\n".join(lines).strip() + "\n" if lines else ""


def _version_key(tag: str) -> tuple:
    return tuple(
        int(x) if x.isdigit() else x for x in re.split(r"[.\-+]", tag.lstrip("v"))
    )


def page(notes: list[Note], title: str = "Release notes") -> str:
    """Docs page: unreleased first, then each release, newest first."""
    lines = [
        f"# {title}",
        "",
        "What changed for users, release by release. Each entry is one change you can "
        "notice. Dependency bumps and internal clean-ups are left out.",
        "",
    ]
    unreleased = [n for n in notes if not n.version]
    if unreleased:
        lines += ["## Not released yet", "", *_by_kind(unreleased)]
    versions = sorted(
        {n.version for n in notes if n.version}, key=_version_key, reverse=True
    )
    for v in versions:
        group = [n for n in notes if n.version == v]
        date = group[0].released
        lines += [f"## {v}" + (f" · {date}" if date else ""), "", *_by_kind(group)]
    if not notes:
        lines += ["Nothing yet.", ""]
    return "\n".join(lines).rstrip() + "\n"
