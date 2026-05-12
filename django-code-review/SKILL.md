---
name: django-code-review
description: Performs a thorough Django code review catching real bugs, design problems, and project standard violations. Use when the user asks to "review this code", "review these changes", "review this PR", "do a code review", or asks for feedback on a diff or pull request.
version: 1.0.0
---

# Django Code Review

Perform a detailed, thorough code review. The goal is to catch real bugs, design problems, and
violations of project standards — not to nitpick style or flag issues the linter will catch
automatically.

Do not raise issues that are intentionally out of scope for the stated change.

---

## Step 1 — Understand the change

Before reviewing any code:

- Read the PR description, ticket, or commit messages to understand the intended purpose.
- Identify which parts of the codebase are affected: models, signals, views, tasks, templates,
  migrations, tests, settings, management commands.
- Note any explicit constraints mentioned by the author (e.g. "deliberately not handling X",
  "follow-up ticket for Y").

---

## Step 2 — Apply the relevant playbooks

Work through each playbook that applies to the changes being reviewed. Skip playbooks for areas
the diff does not touch.

| Area | Playbook | Apply when… |
|---|---|---|
| Logic and edge cases | `references/correctness.md` | Any code change |
| Models and migrations | `references/migrations.md` | Any `models.py` or `migrations/` change |
| QuerySets and full-text search | `references/querysets.md` | Any ORM or search change |
| Signals | `references/signals.md` | Any signal definition or handler |
| Celery tasks | `references/celery.md` | Any task definition or `.delay()` / `.apply_async()` call |
| Caching | `references/caching.md` | Any cache read/write/invalidation |
| Django admin | `references/admin.md` | Any `admin.py` change |
| Security | `references/security.md` | Any view, form, query, or file-handling change |
| Tests | `references/tests.md` | Any test file, or any change that lacks tests |
| Performance | `references/performance.md` | Any queryset, bulk operation, or hot-path change |
| Error handling | `references/observability.md` | Any exception handling, logging, or task code |

Also verify project code standards from `CLAUDE.md`.

> **Customise this section** — replace the example standards below with your own project's
> conventions. These are illustrative only.
>
> Example:
> - Single quotes for strings.
> - 100-character line length limit.
> - Imports sorted with `isort` (standard library → third-party → local). No star imports except
>   in settings files.
> - Explicit type hints on function signatures. `ClassVar` for class-level attributes that are
>   not instance fields.
> - Modern Python 3.12 syntax (`X | Y` unions, `match`, f-strings).
> - No helpers or abstractions for one-time use.
> - No backwards-compatibility shims for removed code.

---

## Step 3 — Write the review

See `references/output-format.md` for the required output structure.

Do not report:
- Pre-existing issues not introduced by this change.
- Issues the linter or type checker will catch automatically.
- Nitpicks that a senior engineer would not raise in a review.
- Speculative problems with no concrete evidence in the diff.
