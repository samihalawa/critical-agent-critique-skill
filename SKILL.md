---
name: critical-agent-critique-skill
description: "Analyze prior agent work for a target repo across local code, recent commits, Codex history, Claude history, and repo-local notes; identify only severe, obviously context-broken or hallucinated implementations; and fix those critical issues immediately. Use when a repo appears polluted by off-track agent work and the user wants a strict critique-plus-repair pass rather than a broad cleanup."
---

# Critical Agent Critique Skill

Use this skill when the user suspects a repo contains clearly off-track agent work and wants only the critical failures corrected.

This is not a general polish pass. The goal is to find and fix only the severe cases where prior agent work obviously drifted from user intent, repo context, or system reality.

Example target shape:

- analyze prior work around a repo such as `/Users/samihalawa/git/PROJECTS_ON_PROCESS/2026-MANUS-oulang`
- read local evidence from the repo plus `~/.codex` and `~/.claude`
- detect over-engineered, unrelated, broken, fabricated, or contextless implementations
- fix the truly critical ones immediately

## Hard Rules

- Work from real local evidence, not summaries alone.
- Read the current repo first so critique is grounded in the actual architecture.
- Use Codex and Claude histories as evidence of intent, constraints, and prior mistakes, not as truth.
- Focus only on critical issues that are obvious and high-confidence.
- Do not open a giant speculative cleanup backlog.
- Ignore minor style drift, harmless duplication, or debatable design choices.
- A change qualifies only if it clearly shows hallucination, loss of context, or severe off-track execution.
- Verify that a suspected issue is still present in the current code before touching it.
- Prefer direct repair over long critique reports.
- If a bad implementation should be removed, confirm the surrounding workflow so the removal does not break valid current behavior.
- When multiple agents touched the same area, treat the current code plus verified behavior as higher-signal than any single conversation.

## Critical-Issue Standard

Only escalate items that meet at least one of these standards:

- implements functionality unrelated to the user's actual request
- invents flows, data, APIs, or UI states that do not exist in the repo or product
- breaks a working workflow because the agent forced a guessed architecture
- adds severe over-engineering that blocks or distorts the intended feature
- contradicts explicit user constraints from prior conversation history
- claims completion while leaving an obviously broken or disconnected implementation
- wires code that cannot possibly work in the current stack, config, or runtime model

Do not treat these as critical by default:

- naming preferences
- ordinary refactor disagreements
- low-risk dead code unless it actively causes confusion or breakage
- imperfect abstractions that still match the real feature

## Required Source Order

For the target repo, inspect sources in this order:

1. current repo context
   - `tree -I node_modules -L 2`
   - `AGENTS.md`, `README.md`, package manifests, router or app entry points
   - current dirty worktree
   - recent commits and diffs
2. repo-local notes that may show prior agent narratives
3. Codex history tied to the repo cwd
   - `~/.codex/sessions/**/*.jsonl`
4. Claude history tied to the repo cwd
   - `~/.claude/projects/<derived-project>/*.jsonl`
5. current implementation hotspots
   - the exact files and functions implicated by the suspected drift

Do not start editing until the issue is supported by both code evidence and at least one source of prior-intent evidence when available.

## Workflow

### 1. Ground In The Current Repo

- read the real repo structure first
- inspect current status, recent commits, and touched files
- identify the workflows or subsystems most likely affected by prior agent drift
- ignore broad areas with no concrete evidence of harm

### 2. Build A Critique Ledger

For each candidate issue, record:

- affected workflow
- implicated files and functions
- commit(s) or local changes involved
- supporting conversation or note evidence if available
- why it appears hallucinated, unrelated, or context-broken
- why it is critical rather than merely imperfect

If you cannot explain the issue crisply, it is not ready for repair.

### 3. Read Prior Agent History Selectively But Directly

- filter Codex and Claude history by the target repo cwd
- prioritize sessions near the suspect commits or feature area
- read original conversation files directly, sequentially
- extract:
  - what the user actually asked for
  - explicit constraints
  - later corrections
  - places where the assistant clearly invented scope or architecture

Do not overread unrelated sessions once the critical issue is proven.

### 4. Confirm The Issue In Current Code

Before editing, prove the current repo still contains the problem:

- inspect the exact files and call paths
- verify whether the implementation is wired, broken, or dead
- check whether later commits already fixed or replaced it
- determine the safest repair:
  - remove
  - simplify
  - reconnect properly
  - replace with a direct implementation that matches the real request

### 5. Fix Critical Issues Immediately

For each validated critical issue:

- implement the smallest complete repair that restores alignment with the real request
- remove unrelated or fabricated behavior when necessary
- preserve valid surrounding work
- avoid rewriting unrelated areas just because the original implementation was messy

### 6. Verify Aggressively

Use the fastest real checks that prove the fix:

- targeted build, test, or typecheck commands
- route or handler inspection
- runtime logs
- browser or UI checks when the issue is user-facing
- direct data-path verification when DB or API wiring is involved

Do not mark the issue fixed without concrete verification.

### 7. Return A Tight Repair Report

Report only:

1. the critical issues found
2. why each one qualified as obvious agent drift or hallucination
3. what was fixed
4. how it was verified
5. any remaining suspected issues that were intentionally not touched because they were not high-confidence critical failures

## Decision Standard

A candidate should be fixed in this pass only when all are true:

- the current code still contains the problem
- the problem is severe enough to justify intervention now
- the problem is clearly connected to off-track or contextless prior agent work
- the correct repair can be made with high confidence from current repo evidence

If any of those are missing, leave it out of this skill's scope.
