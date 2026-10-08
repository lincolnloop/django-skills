---
name: import-skill
description: 'Maintainer tool for this repository. Use when asked to "import from <project>", "harvest rules from <path>", or "check <project> for new django-development rules": compares the general skills in a local project checkout against this collection and proposes generalised additions as a pull request here. Never writes to the source project.'
version: 0.1.0
metadata:
  internal: true
---

# Import Skill

Brings rules that a project has already distilled into its own general skills
(`django-development`, package skills such as `celery`, review playbooks) into this collection.

This skill **harvests, it doesn't mine.** Finding rules in pull requests, incidents and session
corrections is the project's own job, done in the project with the context needed to judge them.
This skill only reads rules that have already been through that process, and turns them into
general recipes.

## Step 1: Confirm the source and what identifies it

Ask for, and don't infer:

- **The source:** a path to a local checkout of the project. Never write to it, commit to it, or
  run anything in it other than reading files.
- **The scope:** which skills to compare. The default is the general layers only:
  `django-development`, package skills, and review playbooks (mapped to `django-code-review`).
  A project's own conventions layer (`project-conventions`, `AGENTS.md`, memory directories) is
  out of scope. Rules there are true only because of that project's choices.
- **Identifying terms:** the project's name, the client's name, domains, and distinctive model
  or app names. Step 4 searches the result for these.

Don't record the source path or any identifying term in this repository: not in files, branch
names, commit messages, or the PR.

## Step 2: Compare rule by rule

Rules carry a stable ID (e.g. `templates/filter-argument-lookups`). Match source rules to this
collection's rules by ID, falling back to the heading text, and classify each one:

| Class | Meaning | Action |
|---|---|---|
| **New** | No equivalent here | Candidate to add, under the matching layer |
| **Sharpened** | Exists here, but the source adds an **Except:** case, an **Applies:** version, or a clearer **Why:** | Candidate to merge the addition only |
| **Same** | Equivalent here | Skip |
| **Diverged** | Both changed and they now disagree | Show both; the maintainer decides |
| **Project-bound** | True only because of the project's choices, or can't be stated without its specifics | Skip, and list it in the report |

Source rules with an **Overrides:** line pointing at a project-only skill are project-bound by
definition. The rule they override may still be worth checking.

## Step 3: Generalise

For each candidate, rewrite anything that ties it to the project. Follow the existing rules in
this collection as the house style:

- **Evidence:** replace issue and PR numbers, incident or error-tracker IDs, file paths, URLs and
  names with the framework mechanism. Cite the Django or library source, the docs, or the release
  notes, ideally with a minimal example using neutral models (`Author`, `Book`, `Article`). Compare
  `django-development`'s `models/cascade-audit`, whose evidence describes Django's deletion
  collector and an `Author`/`Book` cascade. Verify any cited source exists before citing it.
- **Examples:** rename project models, apps, settings and business terms.
- **Overrides:** remove lines that point at project-only skills.

Keep the **Why:** and **Except:** lines; they're the valuable part. If a rule can't stand
without project specifics, reclassify it as project-bound.

## Step 4: Check and report

Before showing anything, search the proposed changes for every identifying term from Step 1, and
for patterns that commonly leak:
- `#<digits>` and `<owner>/<repo>#<digits>`;
- error-tracker IDs such as `ABC-1F2`;
- `apps/` and other repository paths;
- domains.

Fix anything found.

Then present a report: each candidate with its class, the proposed text, and what was rewritten
or removed and why. List skipped project-bound rules by ID only. Wait for confirmation.

## Step 5: Write here

On confirmation, create a branch in this repository with a neutral name (e.g.
`import-template-rules`), apply the changes, bump each changed skill's `version` in `SKILL.md`
and `package.json`, and open a PR. Describe the PR by what the rules cover, not by where they
came from.

## Do not

- Read beyond the scoped skills: no PR threads, issues, incident reports or application code from
  the source project.
- Copy text verbatim without the Step 3 rewrite.
- Mention the source project anywhere in this repository or its PRs.
