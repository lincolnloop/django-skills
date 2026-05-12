# Review Output Format

Group findings by severity:

**Bugs / correctness issues** — things that will cause incorrect behaviour or data loss.

**Design concerns** — things that will cause problems at scale or are structurally fragile.

**Standards violations** — clear violations of project conventions from `CLAUDE.md` or
documented patterns.

**Observations** — non-blocking notes worth mentioning but not requiring changes.

For each finding, state:
1. What the problem is.
2. Where it is (file and line reference).
3. Why it matters.
4. A suggested fix or direction, where one is clear.

Omit any severity section that has no findings.
