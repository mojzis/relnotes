# relnotes

Release notes as one small file per user-visible change.

Each PR that changes something a user would notice adds a file to
`release-notes/`, written by whoever (usually an agent) made the change:

```markdown
<!-- release-notes/2026-11-21-faster-staged-check.md -->
---
kind: changed
---

`madoqua run` checks only the staged files, so a commit in a large repo takes 0.3 s instead of 2 s.
```

No release-time editing: a note ships in the first `v*` tag that contains the
commit which added it.

```
uvx relnotes@latest guide          # when to write a note and how to word it
uvx relnotes check                 # exit 1 if a note is malformed
uvx relnotes body v1.2.3           # GitHub release body for a tag
uvx relnotes page --out FILE       # docs page, newest release first
uvx relnotes json                  # every note with its version, for other sites
```

## In a repo

Release workflow (needs the full history to see the previous tag):

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 0
- uses: astral-sh/setup-uv@v10.4.0
- run: uvx relnotes check && uvx relnotes body "$GITHUB_REF_NAME" > release-body.md
- uses: softprops/action-gh-release@v3
  with:
    body_path: release-body.md
    generate_release_notes: true   # GitHub's PR list goes under the notes
```

In the repo's `CLAUDE.md`:

```markdown
## Release notes
A user-visible change adds a note in `release-notes/`. Run `uvx relnotes@latest guide` before writing one.
```

Runtime dependencies: none (stdlib only), so `uvx relnotes` is quick in CI.
