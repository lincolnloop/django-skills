# Lincoln Loop Case Study House Style

Distilled from published case studies at [lincolnloop.com/work](https://lincolnloop.com/work/) (Firefox.com, LCvista, NOLS, GBI). Match these patterns.

## Title and Subtitle

- **Title**: service-led, client-anchored: "[Service/outcome] for [Client]".
  - "CMS Replatforming for NOLS"
  - "Test suite audit and optimization for LCvista"
  - "Green tech web app development for GBI"
  - NOT "[Project Name] Case Study"
- **Subtitle**: the "When [client] needed to [challenge], Lincoln Loop [high-level solution]." formula, used as the lede paragraph.

## Voice

- First-person plural: "we built", "our team", "we began by".
- Confident and concrete; no hedging, no superlatives without evidence.
- Narrative sections total roughly 700-1100 words.
- **No LLM markup artifacts**: never use arrows (→), em dashes (—), or similar typographic tells in the case study. Rewrite around them: use commas, colons, parentheses, or split the sentence.

## Section Conventions

- **Background**: opens with a one-paragraph client identity (who they are, mission, scale). E.g. "LCvista, a SaaS provider of accounting compliance solutions..." / "NOLS is a nonprofit that teaches outdoor skills, leadership, and environmental ethics...". End with why the project became necessary.
- **Challenge**: prose paragraph setting the stage, then a bulleted list introduced by "Key challenges included:" or "[Client] needed a platform that:". Quantify wherever possible ("CI build times stretching to 75 minutes", "more than 60 million users across five languages").
- **Solution**: chronological/phased narrative ("We began by...", "The next step was...", "Throughout the project..."). Name technologies at brand level only (Django, Wagtail, HTMX, Highcharts); no architecture detail. Include training, documentation, and handoff work when it happened; published studies consistently feature it.
- **The Right Fit for the Job**: placement is flexible; published studies often put it AFTER Solution (LCvista, NOLS, GBI). Lead with what the client needed in a partner, then why Lincoln Loop matched.
- **Results**: bullets in `**Bold label:** outcome` form, mixing hard metrics, qualitative wins, and longevity claims:
  - "**CI Time Reduction:** Improved test suite build time by 87%."
  - "**Empowered staff:** Editors can now publish content independently, speeding up internal workflows."
  - "**Long-term solution:** Ten years later, the site remains in production..."
- **Looking Forward**: short; reinforces partnership longevity and the foundation laid for future work.

## Stats, Quotes, Visuals

- **Hero stats**: pick 1-3 headline numbers for the Stats and Metrics section, formatted as big callouts: "60M weekly visitors", "41 documented components", "$28,000 estimated annual savings". Not a stats dump.
- **Quotes**: exactly one client quote, used as a pull-quote blockquote, with full attribution (name, title, company). E.g. Dan Brown, Director, Websites & Marketing Technology at Mozilla.
- **Visuals**: be generous; the case study should read as near-final marketing material. Source visuals from the designer's Figma frames first, then app screenshots. Favor before/after pairs with descriptive captions, e.g. "Screens from the original Net Zero Calculator, an Excel-based tool" / "Screens from the redesigned Net Zero Calculator, a modern Django web application". Every major section (Challenge, Solution, Results) should carry at least one captioned visual.

## Snapshot Field Phrasing

- **Duration**: "9 months, plus ongoing support" / "Multi-phase, spanning March to August 2024" / "1 year". Include ongoing-support framing when true.
- **Industries**: short list, e.g. "Technology, SaaS, Compliance" / "Environmental Services, Nonprofit, Education".
- **Services**: Lincoln Loop service names, e.g. "Design Research & Strategy, Design Systems, Django Development, CMS Replatforming".
- **Technology**: brand-level list, e.g. "Django, Alpine.js, HTMX, Figma, Highcharts".

## Example Excerpt (LCvista Results)

> - **CI Time Reduction:** Improved test suite build time by 87%.
> - **Cost Savings:** Estimated annual savings of $28,000 in testing costs.
> - **Developer Efficiency:** 20 developers gained consistent, reliable CI feedback, allowing faster deployments.
> - **Sustainable Testing Culture:** LCvista's team was empowered to independently maintain high-quality testing standards through training and documentation.

## Example Excerpt (Firefox.com Challenge bullets)

> Several factors made the replatform particularly complex:
>
> - **High-volume release publishing:** Firefox ships major updates every six weeks. Within days of a release, these pages can reach more than 60 million users across five languages.
> - **Legacy browser support:** Because firefox.com is where users download the browser itself, the site needed to remain functional on Internet Explorer and legacy versions of Safari.
