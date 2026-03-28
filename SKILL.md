---
name: critical-agent-critique-skill
description: "Perform a forensic critique of prior agent work for a target repo across the current thread, local code, recent commits, Codex history, Claude history, and repo-local notes; ingest the conversation evidence in detail, identify only severe context-broken or hallucinated implementations, and either return a structured analytical critique or repair the highest-confidence critical failures immediately."
---

# Critical Agent Critique Skill

Use this skill when the user suspects a repo contains clearly off-track agent work and wants a strict critique of the most severe failures, not a broad cleanup.

This skill is intentionally narrow. It should find only the high-confidence cases where prior agent work clearly drifted from user intent, repo context, or system reality.

Do not turn this into a general polish pass or a vague architectural review.

## Mode Selection

Choose the mode from the user's wording before touching code:

- `forensic-critique mode`
  - Use when the user asks for critique, analysis, root-cause review, conversation forensics, or a report.
  - Stay text-only. Never write code.
- `critical-repair mode`
  - Use when the user wants the same critique work plus immediate correction of the proven critical failures.
  - Complete the critique first, then fix only the validated critical issues.

If the user does not clearly ask for repair, default to `forensic-critique mode`.

## Hard Rules

- Work from real local evidence, not summaries alone.
- Read the current active thread first when it is relevant to the repo or issue under critique.
- Read the current repo before judging whether prior agent work was bad.
- Use Codex and Claude histories as evidence of intent, constraints, and prior mistakes, not as truth.
- Perform both message-by-message micro-analysis and thematic macro-analysis before final judgment.
- List the actual messages in order for the selected scope when the user asks for conversation critique.
- Report total messages, approximate word count, approximate character count, and key thematic blocks.
- Base conclusions only on the actual source text plus current repo evidence.
- Focus only on critical issues that are obvious and high-confidence.
- Do not open a giant speculative cleanup backlog.
- Ignore minor style drift, harmless duplication, or debatable design choices.
- A change qualifies only if it clearly shows hallucination, loss of context, or severe off-track execution.
- Verify that a suspected issue is still present in the current code before touching it.
- If prior agent work looks wrong but the current code is already corrected, critique it but do not reopen it as an implementation target.
- Prefer direct repair over long reports only in `critical-repair mode`.
- If a bad implementation should be removed, confirm the surrounding workflow so the removal does not break valid current behavior.
- When multiple agents touched the same area, treat the current code plus verified behavior as higher-signal than any single conversation.

## Critical-Issue Standard

Only escalate items that meet at least one of these standards:

- implements functionality unrelated to the user's actual request
- invents flows, data, APIs, or UI states that do not exist in the repo or product
- breaks a working workflow because the agent forced a guessed architecture
- adds severe over-engineering that blocks or distorts the intended feature
- contradicts explicit user constraints from conversation history
- claims completion while leaving an obviously broken or disconnected implementation
- wires code that cannot possibly work in the current stack, config, or runtime model
- repeats the same failure across turns after the user corrected it

Do not treat these as critical by default:

- naming preferences
- ordinary refactor disagreements
- low-risk dead code unless it actively causes confusion or breakage
- imperfect abstractions that still match the real feature
- missing polish that does not distort the requested workflow

## Required Source Order

For the target repo, inspect sources in this order:

1. current active conversation or thread
   - current user and assistant messages in this thread
   - message order, corrections, frustrations, and repeated asks
2. current repo context
   - `tree -I node_modules -L 2`
   - `AGENTS.md`, `README.md`, package manifests, router or app entry points
   - current dirty worktree
   - recent commits and diffs
3. repo-local notes that may show prior agent narratives
4. Codex history tied to the repo cwd
   - `~/.codex/sessions/**/*.jsonl`
5. Claude history tied to the repo cwd
   - `~/.claude/projects/<derived-project>/*.jsonl`
6. current implementation hotspots
   - the exact files and functions implicated by the suspected drift

Do not start editing until the issue is supported by both code evidence and at least one source of prior-intent evidence when available.

## Forensic Critique Workflow

### Phase 1. Forensic Context Ingestion And Metadata Reporting

- State the active mode: `forensic-critique` or `critical-repair`.
- Build a source ledger before deep analysis.
- Record every selected source with:
  - source type
  - file or conversation identifier
  - why it was selected
  - planned coverage level
- Open one real sample from each source type first and confirm it is readable.
- For the selected conversation scope, report:
  - total selected conversations
  - total messages
  - approximate word count
  - approximate character count
  - key thematic blocks
- If the history is large, use a two-pass method:
  - pass 1: metadata, timestamps, cwd confirmation, repeated failure signals
  - pass 2: full sequential reads for the most relevant or contradictory sessions

### Phase 2. Micro-Analysis: Message-By-Message Reading

Process every selected message in order.

For each user message, extract:

- raw wording when nuance matters
- normalized plain-language restatement
- explicit request
- implicit intent
- constraints and preferences
- frustration or correction signals
- success criteria implied by the user

For each assistant message, extract:

- what was actually done
- what was only promised
- what evidence was provided
- what assumptions were made without proof
- what was skipped, contradicted, or abandoned
- whether the assistant ignored corrections or relied on summary instead of source

Tag messages or turns when useful:

- `[OK]`
- `[PARTIAL]`
- `[FAIL]`
- `[CORRECTED]`
- `[IGNORED]`

If the user had to repeat or correct the same point after an earlier completion claim, classify that earlier claim as `[FAIL]`.

### Phase 3. Macro-Analysis: Thematic Re-Read

Re-read the material by theme, not only chronology.

Recommended themes:

- request understanding
- repo grounding
- implementation quality
- verification quality
- instruction loss
- agent trust failures

For each theme, answer:

- what the user consistently wanted
- where the agent drifted
- which constraints were lost
- whether the repo ever matched the claims
- what the root cause was

### Phase 4. Comprehensive Problem Identification

Build a problem inventory with these buckets:

- explicit user problems
  - bugs
  - UX frustrations
  - broken flows
  - errors
- agent-driven frustrations
  - miscommunication
  - ignored feedback
  - false completion claims
  - scope invention
  - plan-without-execution loops
- implicit problems
  - contradictory reporting
  - unreported failures
  - abandoned tasks
  - contradictory concurrent edits

For each problem, capture:

- source evidence
- earliest appearance
- latest appearance
- whether it is still present now
- why it qualifies as critical or does not

### Phase 5. Analytical Protocol

In `forensic-critique mode`:

- never write code
- stay strictly analytical
- base conclusions only on the provided text plus verifiable current repo evidence

In `critical-repair mode`:

- keep the same analytical discipline first
- only then verify the current repo and repair the highest-confidence critical failures

### Phase 6. Confirm Critical Issues In Current Code

Only perform this phase in `critical-repair mode`.

Before editing, prove the current repo still contains the problem:

- inspect the exact files and call paths
- verify whether the implementation is wired, broken, or dead
- check whether later commits already fixed or replaced it
- determine the safest repair:
  - remove
  - simplify
  - reconnect properly
  - replace with a direct implementation that matches the real request

### Phase 7. Fix Critical Issues Immediately

Only perform this phase in `critical-repair mode`.

For each validated critical issue:

- implement the smallest complete repair that restores alignment with the real request
- remove unrelated or fabricated behavior when necessary
- preserve valid surrounding work
- avoid rewriting unrelated areas just because the original implementation was messy

### Phase 8. Self-Validation

Before returning results, verify the critique itself.

Checklist:

- Did you read the selected messages sequentially?
- Did you perform both micro-analysis and macro-analysis?
- Did you report counts and key blocks?
- Did you separate explicit, agent-driven, and implicit problems?
- Did you tie conclusions to source evidence instead of intuition?
- In `critical-repair mode`, did you verify the current code before editing?
- Did you avoid labeling low-confidence issues as critical?

If any answer is no, narrow the claims and say so explicitly.

## Output Format

Unless the user requests a different format, return:

1. `Forensic Analysis & Context Ingestion`
2. `Analysis Summary`
3. `Problem Inventory`
4. `Root Cause Analysis`
5. `Critique of Agent Behavior`
6. `Strategic Recommendations`
7. `Success Criteria`

In `forensic-critique mode`, also include:

8. `Best Recovery Prompt`
   - write the strongest follow-on prompt that would force the next agent to address the critical issues correctly

In `critical-repair mode`, append:

8. `Current Repo Verification`
9. `Critical Issues Fixed`
10. `Verification Evidence`
11. `Remaining Suspected Issues Not Touched`
12. `Best Recovery Prompt`

## Decision Standard

A candidate should be fixed in this pass only when all are true:

- the current code still contains the problem
- the problem is severe enough to justify intervention now
- the problem is clearly connected to off-track or contextless prior agent work
- the correct repair can be made with high confidence from current repo evidence

If any of those are missing, leave it out of this skill's repair scope.
