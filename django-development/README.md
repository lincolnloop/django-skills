# Django Development Recipe

A recipe of general Django idioms: how the framework actually behaves and how to use it,
independent of any one project. Each rule is stated as a **Do/Don't**, a **Why** (citing Django
source or docs), and an **Except** where it stops applying, organised by the layer you're
writing — models, views, templates, tests.

> **This is a recipe, not a tool.** It works as-is, but its value grows when you layer your own
> project's conventions on top. The skill itself documents a precedence model: project
> conventions and package-specific skills (e.g. a `celery` skill) override what's here. Treat
> this as the baseline layer, not the last word.

## What it covers

| Layer | Rules |
|---|---|
| Models and the ORM | Cascade deletion audits, constraint-backed uniqueness, model instances vs. dicts |
| Views and template context | What context processors already add, and when they don't run |
| Templates and template tags | Per-template `{% load %}`, filter-argument lookup failures, presentation in model properties, removed builtins |
| Tests | Exercising the branch a fix enables, destructive round-trip coverage |

## Installation

```bash
npx skills add lincoln-loop/agent-skills --skill django-development
```

Or globally:

```bash
npx skills add lincoln-loop/agent-skills --skill django-development --global
```

Once installed, it's consulted automatically before or while Claude writes Django code —
models, views, templates, forms, admin, signals, management commands, or tests.

## Adapting for your project

- **Add a project layer.** Create your own `project-conventions` skill (or an `AGENTS.md`) for
  choices specific to your codebase — this skill explicitly defers to it.
- **Add package layers.** If you use Celery, DRF, or another library with its own idioms, add a
  skill for it; this recipe's precedence rules already expect one.
- **Version-specific rules.** A few rules only apply above a given Django version (see the
  **Applies:** field). Check your pinned Django version before assuming one holds.
- **Extend, don't just trim.** As you hit new framework gotchas, add rules in the same
  Do/Why/Except shape so they stay consistent with the rest of the skill.

## Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
