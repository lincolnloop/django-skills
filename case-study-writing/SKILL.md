---
name: case-study-writing
description: "Writes Lincoln Loop B2B case studies from the project open in the current workspace. Explores the codebase, parses git history, optionally runs the project locally, interviews the user for missing details, gathers visuals from Figma frames and screenshots, researches industry benchmarks, and produces a visually rich case study following the Lincoln Loop Case Study Template 2024 and house style. Use when the user asks to write, draft, or update a case study for a client project."
disable-model-invocation: true
---

# Case Study Writing

## Trigger

The user wants a Lincoln Loop case study for the client project open in the current workspace. The user worked on this project and is available to answer questions: treat them as the interview subject.

Steps may be skipped when they add nothing (e.g. skip running locally or web research when the codebase, git history, and user answers already provide enough material).

## Resuming a Previous Run

Before starting from scratch, check `docs/case-studies/` for an existing case study markdown for this client. If one exists, ask the user whether to resume instead of redoing the research and interview:

- **Recompile only**: the markdown is approved and only the .docx needs regenerating (e.g. after a skill, style, or reference.docx update). Jump straight to the Output step.
- **Revise**: the user wants changes to specific sections. Jump to Step 7 for those sections only, then re-run Step 8 and the Output step.
- **Start over**: treat the existing file as stale input and run the full workflow.

The markdown file and its assets folder are the durable state; everything needed to recompile lives there.

## Dependencies

Check availability early and tell the user about any gaps instead of failing mid-workflow:

- `git` (required): project history, Step 2
- `gh` (recommended), authenticated against the project's repo: PR descriptions, Step 2. Without it, fall back to commit history alone.
- Figma MCP server (recommended): frame screenshots, Step 5. Without it, request exported screenshots.
- `pandoc` (required for the final .docx): Output. Ask before installing.

## Workflow

Copy this checklist and track progress:

```
Case Study Progress:
- [ ] Step 1: Explore the project
- [ ] Step 2: Parse git and PR history
- [ ] Step 3: Run locally (if needed)
- [ ] Step 4: Interview the user
- [ ] Step 5: Gather visuals
- [ ] Step 6: Research benchmarks
- [ ] Step 7: Draft section-by-section
- [ ] Step 8: Self-review, then final checklist
```

### Step 1: Explore the Project

The current workspace IS the client project. Explore it to understand:

- **What the product does**: read READMEs, landing pages, config files, routes, and models to understand the product from a user/business perspective
- **Scope of work**: how many apps/services, what integrations exist, what user-facing features were built
- **Problem indicators**: comments, docs, or issues that reveal what pain points the solution addresses

This is for **context only**. Mention technologies at the level the template asks (e.g. "Django, Python, AWS") but do NOT include implementation details (architecture, code patterns) in the case study body.

### Step 2: Parse Git and PR History

Use git and GitHub PRs to reconstruct the project story:

```bash
# Project duration and timeline
git log --reverse --format='%ad %s' --date=short | head -5
git log -1 --format='%ad' --date=short

# Major phases and milestones (merges, releases, tags)
git log --merges --format='%ad %s' --date=short
git tag --sort=creatordate

# Scope: contributors and volume
git shortlog -sn
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
```

**Enrich the commit timeline with PR descriptions.** Work is incremental, so each PR carries a small, human-readable description of what changed and why, written in context at the time. The commit history remains the backbone (duration, milestones, phases); PR descriptions add the context and intent behind those changes:

```bash
# Merged PRs, oldest first
gh pr list --state merged --limit 200 --json number,title,mergedAt --jq 'sort_by(.mergedAt)[] | "\(.mergedAt[:10]) #\(.number) \(.title)"'

# Full description of a notable PR
gh pr view <number> --json title,body
```

Read the full descriptions of the most significant PRs (features, migrations, redesigns) and use their framing when describing the work in the Solution section.

Extract from all of this: project **duration**, **key milestones**, **major features shipped** (commit/merge messages cross-referenced with their PR descriptions), and **phases of work** (migration, redesign, performance, etc.). These feed the Background, Solution, and snapshot fields.

### Step 3: Run Locally (If Needed)

If understanding the user-facing product requires seeing it, run the project locally (check README/Makefile/justfile for setup) and browse it. Take screenshots of notable features; they are candidates for the Visuals section. Skip this step if the codebase and git history already give enough context.

### Step 4: Interview the User

The user is here to help. Draw questions from the interview script in [template.md](template.md), but:

- **Explore first**: if a question can be answered by exploring the codebase or git history, explore instead of asking.
- **One question at a time**: never a batch of topics in a single message.
- **Provide a recommended answer** with each question, based on what you inferred from steps 1-3, so the user can confirm or correct rather than start from scratch.
- When the answer options are discrete, you MUST present them as structured multiple choice using the agent's question tool (the tool for collecting structured multiple-choice answers from the user), not as options listed in plain chat text. Fall back to conversational questions only when no such tool exists or the question is genuinely open-ended.

Prioritize the gaps you could NOT fill yourself:

1. Client pain points and goals at project start
2. Why Lincoln Loop was the right fit (previous experience, approach, services)
3. Innovative approaches or unique problem-solving
4. Challenges faced along the way
5. Value-add beyond expectations
6. **Metrics and stats**: before/after numbers, timeframes (push for these; they make the case study)
7. Client quotes or testimonials with full attribution
8. Future plans / next steps
9. Visual ideas and which Figma frames showcase the work best

### Step 5: Gather Visuals

The case study must be close to final public-facing marketing material, so include **more visuals than usual**. Lincoln Loop has a strong design team; their materials are the best source.

- **Request Figma access**: whenever a section would benefit from a visual, ask the user for the relevant Figma frames (a figma.com URL).
- **Verify Figma MCP access**: when a Figma URL is shared, first confirm the Figma MCP server is available and authenticated (run a lightweight read against the shared file). If it fails with an auth error, authenticate and retry once. Then use the Figma tooling to capture screenshots of the frames.
- **Fall back to screenshots**: if the Figma MCP is unavailable or access to the file is denied, report that to the user and ask them (or the designer through them) for exported screenshots instead.
- **Capture from the running app**: reuse or take screenshots from Step 3 for before/after pairs and feature highlights.
- Save every gathered visual to `docs/case-studies/assets/<client-slug>/` with descriptive filenames; the markdown and .docx outputs reference them from there.
- **Resolution matters in the .docx**: export Figma frames at 2x and capture screenshots at full window size. Never use an image narrower than ~1200px for full-width placement; a small image stretched across the page renders blurry in Word and Google Docs.
- Aim for a visual per major section (Challenge, Solution, Results) plus before/after pairs, each with a descriptive caption per [style.md](style.md).
- Do not proceed to drafting a section that clearly needs a visual without first requesting one.

### Step 6: Research Benchmarks

Search the web for:

- Industry benchmarks (average metrics in the client's industry)
- Competitor landscape (why the client chose this solution)
- Supporting statistics (market data reinforcing the challenge)

Record the source URL for every benchmark or statistic so claims can be cited or verified.

### Step 7: Draft Section-by-Section

Write the case study following the structure in [template.md](template.md) and the house style in [style.md](style.md).

Do NOT dump the full draft at once. Present it **section-by-section** (Subtitle + snapshot, Background, Challenge, The Right Fit for the Job, Solution, Results, Looking Forward, then the supporting sections) and get the user's approval on each before moving on. Revise in place when the user pushes back.

Writing guidance (STAR maps onto the template):

- **Background + Challenge** = Situation/Task: client context, then the quantified problem and desired outcomes
- **Solution** = Action: approach, collaboration, key features, timeline; highlight anything innovative
- **Results** = Result: data-driven, before/after metrics with timeframes

Target 800-1200 words for the narrative sections. Keep it skimmable: headers, bold, bullets. Embed the visuals gathered in Step 5 inline (markdown image references with captions) where they support the narrative. Give every image an explicit pandoc width attribute so sizing in the .docx is deliberate: `![Caption](assets/<client-slug>/shot.png){width=6in}` for landscape, ~3-4in for portrait shots.

End each snapshot field line with a backslash so the line breaks survive the .docx conversion (soft line breaks collapse into spaces):

```markdown
**Client:** Wharton Generative AI Labs\
**Project URL:** gail.wharton.upenn.edu\
**Duration:** 4 weeks, part of an ongoing relationship\
**Industries:** Higher Education, EdTech, AI Research\
**Services:** Design Systems, Next.js / React Development\
**Technology:** Next.js, React, TypeScript, Tailwind CSS
```

### Step 8: Review

First run a **self-review** pass and fix issues inline before showing the user:

1. **Placeholder scan**: no leftover `[Enter ...]` template brackets, TBDs, or incomplete sections
2. **LLM markup scan**: no arrows (→), em dashes (—), or similar typographic tells; rewrite with commas, colons, or parentheses
3. **Internal consistency**: do sections contradict each other? Do snapshot fields match the narrative?
4. **Ambiguity check**: could any claim be read two ways? Make it explicit.

Then verify the final checklist:

- [ ] Title follows "[Service/outcome] for [Client]" (see style.md)
- [ ] Subtitle follows the "When [client] needed to [challenge]..." formula
- [ ] All snapshot fields filled (Client, URL, Duration, Industries, Services, Technology)
- [ ] All template sections present
- [ ] Challenge is quantified, not vague
- [ ] Results are data-driven with before/after metrics and timeframes
- [ ] 1-3 hero stats identified for the Stats and Metrics section
- [ ] Exactly one client quote with full attribution (name, title, company)
- [ ] Visuals embedded with captions in every major section, including at least one before/after pair when applicable
- [ ] No deep technical details in the narrative
- [ ] 800-1200 words for narrative sections
- [ ] Skimmable (headers, bold, bullets)

## Guardrails

- **Evidence only**: base all claims exclusively on commit history, PR descriptions, diffs, repo contents, the user's answers, or cited web sources. Never invent metrics, and never infer client motivation; ask instead.
- **Omit cosmetic work**: when summarizing shipped work from git, skip formatting, imports, and minor renames.
- **Cite benchmarks**: every industry statistic must carry a source URL.
- **Confidentiality**: the case study is public-facing. Confirm with the user which client names, metrics, and details are publishable. Never copy secrets, internal URLs, credentials, or PII from the repo into the draft.

## Output

All artifacts live in the current project under `docs/case-studies/` (create it if needed). Confirm the filename with the user before writing, and do not commit anything unless asked.

1. **Markdown source**: `docs/case-studies/YYYY-MM-DD-<client-slug>.md`, the final approved case study.
2. **Image assets**: save all gathered visuals (Figma exports, screenshots) to `docs/case-studies/assets/<client-slug>/` and reference them from the markdown with relative paths, so the document is self-contained.
3. **Compiled .docx**: convert the markdown to a complete Word document with embedded imagery and working hyperlinks, using the branded `reference.docx` bundled in this skill's directory (it carries the Lincoln Loop fonts, heading styles, header/footer, and Google Docs-compatible style definitions):

```bash
pandoc "docs/case-studies/YYYY-MM-DD-<client-slug>.md" \
  --from markdown-auto_identifiers \
  --resource-path="docs/case-studies" \
  --reference-doc="<this-skill-directory>/reference.docx" \
  -o "docs/case-studies/YYYY-MM-DD-<client-slug>.docx"
```

Verify pandoc printed no `Could not fetch resource` warnings; each one means a missing image in the .docx.

If pandoc is missing, ask the user before installing it with the system's package manager (e.g. `brew install pandoc` on macOS, `apt install pandoc` on Debian/Ubuntu, `winget install pandoc` on Windows). After compiling, open or point the user to the .docx so they can verify images and links rendered correctly.
