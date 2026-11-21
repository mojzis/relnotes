import subprocess
from pathlib import Path

import pytest

from relnotes.notes import Note, NoteError, check, collect, page, parse, release_body


def write(repo: Path, name: str, text: str) -> Path:
    path = repo / "release-notes" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def note(kind: str = "fixed", body: str = "`x run` no longer hangs.") -> str:
    return f"---\nkind: {kind}\n---\n\n{body}\n"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "root")
    return tmp_path


def commit(repo: Path, msg: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def test_parse_reads_date_slug_kind_and_body(tmp_path):
    n = parse(write(tmp_path, "2026-11-21-faster-check.md", note("added", "Body.")))
    assert (n.date, n.slug, n.kind, n.body) == (
        "2026-11-21",
        "faster-check",
        "added",
        "Body.",
    )


@pytest.mark.parametrize(
    ("name", "text", "error"),
    [
        ("faster.md", note(), "name must be"),
        ("2026-11-21-Faster.md", note(), "name must be"),
        ("2026-11-21-x.md", "no frontmatter\n", "frontmatter"),
        ("2026-11-21-x.md", note(kind="improved"), "kind must be"),
        ("2026-11-21-x.md", "---\nkind: fixed\ntool: x\n---\nBody.\n", "only `kind`"),
        ("2026-11-21-x.md", note(body=""), "empty"),
        ("2026-11-21-x.md", note(body="# Title"), "no headings"),
        ("2026-11-21-x.md", note(body="a" * 401), "limit is 400"),
    ],
)
def test_parse_rejects_malformed_notes(tmp_path, name, text, error):
    with pytest.raises(NoteError, match=error):
        parse(write(tmp_path, name, text))


def test_check_names_each_bad_file_and_skips_readme(tmp_path):
    write(tmp_path, "README.md", "# Notes\n")
    write(tmp_path, "2026-11-21-ok.md", note())
    write(tmp_path, "2026-11-21-bad.md", note(kind="nope"))
    assert check(tmp_path) == [
        "release-notes/2026-11-21-bad.md: kind must be one of"
        " added, changed, fixed, removed, got 'nope'"
    ]


def test_collect_assigns_the_first_tag_containing_the_note(repo):
    write(repo, "2026-11-01-one.md", note(body="One."))
    commit(repo, "one")
    git(repo, "tag", "v0.1.0")
    write(repo, "2026-11-02-two.md", note(body="Two."))
    commit(repo, "two")
    git(repo, "tag", "v0.2.0")
    write(repo, "2026-11-03-three.md", note(body="Three."))
    commit(repo, "three")
    write(repo, "2026-11-04-draft.md", note(body="Draft."))  # not committed

    versions = {n.slug: n.version for n in collect(repo)}

    assert versions == {"one": "v0.1.0", "two": "v0.2.0", "three": None, "draft": None}


def test_collect_sorts_tags_by_version_not_text(repo):
    write(repo, "2026-11-01-one.md", note())
    commit(repo, "one")
    git(repo, "tag", "v0.10.0")
    git(repo, "tag", "v0.9.0")
    assert collect(repo)[0].version == "v0.9.0"


def test_collect_outside_git_keeps_notes_unreleased(tmp_path):
    write(tmp_path, "2026-11-01-one.md", note())
    assert [n.version for n in collect(tmp_path)] == [None]


def n(slug: str, kind: str, version: str | None, body: str = "B.") -> Note:
    return Note(
        f"2026-11-01-{slug}.md", "2026-11-01", slug, kind, body, version, "2026-11-05"
    )


def test_release_body_groups_the_tags_notes_by_kind_in_fixed_order():
    notes = [
        n("a", "fixed", "v1", "Fix."),
        n("b", "added", "v1", "Add.\nMore."),
        n("c", "added", "v0"),
    ]
    assert (
        release_body(notes, "v1")
        == "### Added\n\n- Add.\n  More.\n\n### Fixed\n\n- Fix.\n"
    )
    assert release_body(notes, "v9") == ""


def test_page_puts_unreleased_first_then_newest_version():
    md = page(
        [n("a", "fixed", "v0.9.0"), n("b", "fixed", "v0.10.0"), n("c", "added", None)]
    )
    assert (
        md.index("## Not released yet")
        < md.index("## v0.10.0 · 2026-11-05")
        < md.index("## v0.9.0")
    )


def test_page_without_notes_says_so():
    assert "Nothing yet." in page([])
