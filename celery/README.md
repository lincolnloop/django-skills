# Celery Recipe

A recipe of Celery idioms for Django projects, independent of any one project. It sits in the
same precedence model as [`django-development`](../django-development/): a **package** layer
that overrides general Django rules where Celery's constraints require it, and defers to your
own `project-conventions`.

> **This is a recipe, not a tool.** It works as-is, but its value grows alongside
> `django-development` — install both, and let your own project conventions sit above them.

## What it covers

| Area | Rules |
|---|---|
| Task arguments | Passing primary keys instead of model instances, and why that's a correctness rule, not just an optimisation |
| Concurrency | Pointing back to `django-development`'s constraint-over-precheck rule, which applies directly to concurrently-run tasks |

## Installation

```bash
npx skills add lincoln-loop/django-skills --skill celery
```

Or globally:

```bash
npx skills add lincoln-loop/django-skills --skill celery --global
```

Install alongside `django-development` for the full precedence chain:

```bash
npx skills add lincoln-loop/django-skills --skill django-development
npx skills add lincoln-loop/django-skills --skill celery
```

## Using it

Like `django-development`, this is a **background** skill. It applies while the agent writes
task definitions (`@shared_task`) or call sites (`.delay()`, `.apply_async()`), without being
asked for. Add the pointer from the
[root README](../README.md#make-background-skills-dependable) to your project's instructions
file to make that dependable.

A prompt where it should apply:

> "Send the welcome email from a Celery task when a user signs up."

Here the skill steers the call to `send_welcome_email.delay(user.pk)`, with the task re-fetching
the user, rather than passing the `User` instance.

## Adapting for your project

- **Add a project layer.** Your own `project-conventions` skill (or `AGENTS.md`) sits above
  this one — use it for things specific to your task queue setup (routing, retry policy,
  broker choice) that this recipe deliberately leaves out.
- **Extend, don't just trim.** As you hit new Celery gotchas, add rules in the same
  Do/Why/Except shape so they stay consistent with `django-development`.

## Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
