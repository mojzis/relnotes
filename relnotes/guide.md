# relnotes guide: writing release notes

This repo keeps its release notes as small files in `release-notes/`, one
file per change a user can notice. The agent that makes the change writes the
note in the same PR. The release workflow puts the notes into the GitHub
release (`relnotes body <tag>`), the docs list them (`relnotes page`), and for
the aesop tools the aesop site shows the newest ones.

Readers are developers who use the tool, and the agents working for them. They
have not seen the code, the PR or the issue. Each note must make sense to them
on its own.

## When to write a note

Write one when a user would notice the change: a new command, flag or config
key; different output, defaults or exit codes; a bug they could hit that is now
fixed; something faster or slower in a way they would feel; something removed.

Don't write one for dependency bumps, CI and release changes, refactors, tests,
internal docs, or a fix to something that was never released.

One note per change. A PR with two user-visible changes adds two files. A PR
with none adds no file. That's fine; nothing forces a note on every PR.

## The file

`release-notes/YYYY-MM-DD-short-slug.md`, with the date you write it and a slug
of two to five lowercase words joined by hyphens:

```markdown
---
kind: fixed
---

`madoqua run` no longer hangs when a check prints more than 64 KB of output.
```

- `kind` is the only field: `added`, `changed`, `fixed` or `removed`.
- The tool comes from the repo, the date from the file name, the version from
  the release tag. Don't write any of them in the note.
- The body is one or two sentences, at most 400 characters. No headings, no
  lists.
- `uvx --from git+https://github.com/mojzis/relnotes relnotes check` validates every note.

## How to write the body

The test: someone who uses the tool but has never opened its code reads the
note once and knows what is different for them, and whether they need to do
anything.

1. **Say what the user sees, not what you changed in the code.** Name the
   command, flag, config key or output they deal with. No function names,
   module names, file paths inside the repo, or internal concepts.
2. **Lead with the effect.** First the thing that is different now, then, if
   it matters, when it happens or why.
3. **Use plain words.** Short sentences, active voice, everyday verbs. Explain
   or drop any term a user of the tool would not know. No jargon: no "refactor",
   "plumbing", "codepath", "regression", "edge case", "robustness".
4. **Be concrete.** "Checks a 2 000-file repo in 0.4 s instead of 3 s" beats
   "faster checks". "Exits with code 2 when the config file is missing" beats
   "better error handling".
5. **Say what the user has to do, if anything.** A renamed flag, a new
   default, a removed command: say what to use or change instead.
6. **No hype, no filler.** No "now", "improved", "enhanced", "various",
   "better", "seamless", "robust", "minor" unless the sentence would be wrong
   without it. No emoji, no exclamation marks.
7. **No PR or issue numbers, no author names.** GitHub adds the PR list under
   the notes in the release.
8. **Present tense, about the tool.** "`zorilla check` reports tests that
   never assert anything." Not "I added", "we fixed", "this PR".
9. **Code in backticks.** Commands, flags, config keys, file names the user
   types or sees.

### Per kind

- **added**: what it is and what it is for. "`gerenuk audit --json` prints the
  unused symbols as JSON, for scripts and CI."
- **changed**: what was before, what is now, and what to do about it.
  "`biston scan` ignores files under `.venv/` by default. Add them back with
  `--include .venv`."
- **fixed**: the symptom the user saw, not the cause. "`ty-find refs` no longer
  misses references inside f-strings."
- **removed**: what is gone and what to use instead. "The `madoqua
  timings` command is gone; `madoqua stats` shows the same numbers."

### Bad, then good

- Bad: "Refactored the staged-file resolver to use a single git invocation."
  Good: "`madoqua run` starts about twice as fast in large repos."
- Bad: "Fix edge case in config parsing (#42)."
  Good: "A `pyproject.toml` with an empty `[tool.biston]` table no longer makes
  `biston scan` crash."
- Bad: "Improved output."
  Good: "`pycoati` prints the test file and line next to every finding, so you
  can jump straight to it."

## Commands

- `relnotes check`: exit 1 if a note is malformed (name, `kind`, length).
- `relnotes body v1.2.3`: Markdown for that release, grouped by kind.
- `relnotes page --out docs/src/release-notes.md`: every note, newest release
  first, plus the ones not released yet.
- `relnotes json`: every note with its version and release date.

## Before you commit

Read the note as someone who only knows the tool's `--help` and docs. If they
would have to ask "what does that mean?" or "so what?", rewrite it.
