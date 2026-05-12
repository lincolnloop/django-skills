# Django Code Review Recipe

A recipe for thorough Django code reviews. When installed and activated, Claude works through a
structured process: reading the PR description, applying focused playbooks for each area of the
codebase touched, and producing a graded findings report.

> **This is a recipe, not a tool.** It works as-is, but its real value is as a starting point.
> The `SKILL.md` contains a placeholder for your project's code standards — you should replace
> it with the actual conventions from your `CLAUDE.md`. The playbooks in `references/` are
> written for Django but reflect specific architectural choices (blue-green deployments, Celery,
> full-text search config) that may not match your setup. Adapt them to your stack.

## What it covers

Each playbook in `references/` applies to a specific area of the diff:

| Playbook | Covers |
|---|---|
| `correctness.md` | Logic errors, edge cases, data mutation safety, paired operations |
| `migrations.md` | Model/migration consistency, blue-green locking risks, rollback safety |
| `querysets.md` | N+1 queries, aggregation bugs, full-text search config mismatches |
| `signals.md` | Handler idempotency, connection placement, side-effect chains |
| `celery.md` | Task idempotency, stale data risks, queue flooding |
| `caching.md` | Key collisions, TTL appropriateness, stampede risks |
| `admin.md` | Custom save overrides, bulk action safety, user feedback |
| `security.md` | Input sanitisation, permission checks, sensitive data exposure |
| `tests.md` | Coverage, isolation, mock placement, edge cases |
| `performance.md` | N+1 queries, missing indexes, memory safety, hot-path API calls |
| `observability.md` | Exception handling, logging context, side-effect boundaries |

## Installation

```bash
npx skills add lincoln-loop/agent-skills --skill code-review
```

Or globally:

```bash
npx skills add lincoln-loop/agent-skills --skill code-review --global
```

Once installed, trigger it by asking Claude to:

> "Review this PR" / "Do a code review" / "Review these changes"

## Customising for your project

The most important customisation is **Step 2 of `SKILL.md`** — the code standards section.
Replace the example standards with the actual conventions from your project's `CLAUDE.md`.
Without this, Claude will apply generic heuristics rather than catching violations of your
specific patterns.

Beyond that:

- **Trim playbooks you don't need** — if you don't use Celery, remove `celery.md` from the
  table and delete the file.
- **Add project-specific playbooks** — create new files in `references/` for patterns that
  matter in your codebase (e.g. a REST API serializer playbook, a custom permissions playbook).
- **Tighten the migration playbook** — `references/migrations.md` covers blue-green deployment
  patterns. If your deployment strategy differs, revise the locking-risk section to match.

The best approach is to install the skill, use it on a few real reviews, note where it misses
things or raises irrelevant findings, and then edit your local copy to close those gaps.

## Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
