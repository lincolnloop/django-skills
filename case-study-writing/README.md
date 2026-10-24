# case-study-writing

An agent skill that writes Lincoln Loop B2B case studies from a client project, following the Case Study Template 2024 and the house style of published studies at [lincolnloop.com/work](https://lincolnloop.com/work/).

## How to Use It

1. Open your coding agent in the client project you want a case study for. The skill treats the current workspace as the project.
2. Invoke the skill explicitly with `/case-study-writing` (it never auto-triggers).
3. Stay available: the agent interviews you one question at a time, with a recommended answer for each, but only about things it could not figure out from the repo itself.
4. Share Figma URLs for the frames that best showcase the work when asked. The agent verifies Figma MCP access and captures screenshots; if that is not possible, it asks for exported screenshots instead.
5. Approve the draft section-by-section. Nothing is finalized in one dump.

### Re-running

The markdown in `docs/case-studies/` is the durable state. Invoking the skill again in a project that already has a case study offers to resume: recompile only the .docx (e.g. after a template/branding update), revise specific sections, or start over. To just recompile, say so explicitly: "/case-study-writing: the markdown is approved, only recompile the .docx".

## What It Does

- Explores the codebase to understand the product from a business perspective
- Reconstructs the project story from commit history, enriched with PR descriptions (`gh`)
- Optionally runs the project locally for screenshots
- Researches industry benchmarks with cited sources
- Gathers visuals generously: the result should be near-final public-facing marketing material
- Self-reviews for leftover placeholders, LLM markup tells (arrows, em dashes), inconsistencies, and ambiguity before you see each draft

## What You Get at the End

All artifacts are written to `docs/case-studies/` inside the client project (not committed unless you ask):

| Artifact | Path |
|----------|------|
| Markdown case study | `docs/case-studies/YYYY-MM-DD-<client-slug>.md` |
| Image assets | `docs/case-studies/assets/<client-slug>/` |
| Compiled Word document | `docs/case-studies/YYYY-MM-DD-<client-slug>.docx` |

The .docx is compiled with pandoc, complete with embedded imagery and working hyperlinks, ready to hand to marketing.

## Files in This Skill

- `SKILL.md`: the 8-step workflow, guardrails, and output spec
- `template.md`: the Lincoln Loop Case Study Template 2024 (interview script + section structure), verbatim
- `style.md`: house style distilled from published case studies (title formula, voice, section conventions, hero stats, quote and visuals rules)
- `reference.docx`: branded pandoc reference document (Lincoln Loop fonts, headings, header/footer) used by the .docx compilation; its styles import cleanly into Google Docs
- `scripts/build_reference_docx.py`: regenerates `reference.docx` from the Word/Google Docs case study template; run it if the template's branding changes:

```bash
python3 scripts/build_reference_docx.py "Case Study Template 2024.docx" reference.docx
```

- `tests/test_skill.py`: validates skill structure (frontmatter, file references, no LLM markup), the reference builder (completeness, idempotency), and the pandoc pipeline (branded styles in compiled output):

```bash
python3 -m unittest discover tests -v
```

## Requirements

- `gh` CLI authenticated against the client repo (for PR descriptions)
- Figma MCP server configured in your agent (for frame screenshots)
- `pandoc` for the .docx compilation
