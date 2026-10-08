# Import Skill (maintainers only)

Keeps this collection growing from real use. Projects that install `django-development`,
`celery` and `django-code-review` refine their local copies as they go: rules mined from code
review, incidents and corrections made during agent sessions. This skill compares a project's
copies against this collection and proposes the general improvements back here as a pull
request.

It isn't installable. It lives outside the skill directories and is marked
`metadata.internal: true`, so `npx skills add` neither lists nor installs it.

## How it works

1. **The project mines.** Rules are found and sharpened inside the project, with its own
   context and review. This skill doesn't read pull requests, issues or application code.
2. **This skill harvests.** It reads only the project's general skills, matches rules by ID, and
   classifies each one as new, sharpened, the same, diverged or project-bound.
3. **Rules are generalised.** Project specifics in evidence and examples are replaced by the
   framework mechanism and neutral examples, in the style of the existing rules.
4. **A maintainer reviews.** The skill reports every candidate and every rewrite, and waits for
   confirmation before opening a PR here.

## Usage

From a checkout of this repository, ask your agent:

> Follow `maintainers/import-skill/SKILL.md` to import from `../some-project`.

To make it available as a slash command in your own checkout, symlink it into a local skills
directory. Dot-directories are git-ignored here, so the link stays on your machine:

```bash
mkdir -p .claude/skills && ln -s ../../maintainers/import-skill .claude/skills/import-skill
```
