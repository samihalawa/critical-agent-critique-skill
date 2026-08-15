# Critical Agent Critique Skill

This repository is the authoritative source for the global Codex finish critic. The Stop hook launches an
independent, read-only Codex subprocess before a turn can finish and requires a strict `PASS:` or `REVISE:`
verdict. The first revision for an exact session and turn blocks finalization with root-cause, sibling-sweep,
and right-layer verification guidance. The guard reviews the corrected response once more; a second revision
is recorded as `BOUNDED_REVISE (not PASS)` and does not create an unbounded finalization loop.

Install or update the global hook from this checkout:

```sh
python3 scripts/install-global-hook.py
```

The installer preserves unrelated hooks, replaces older copies of this managed Stop hook, enables the Codex
`hooks` feature, writes each target atomically, rolls back partial failures, and is idempotent.

Run the regression suite:

```sh
python3 -m unittest discover -s tests -v
```
