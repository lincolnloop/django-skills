# QuerySets and Full-Text Search Playbook

Apply whenever ORM queries or search functionality is added or changed.

---

## QuerySet patterns

- Are querysets evaluated at the right point? Lazy evaluation can cause N+1 queries. Look for
  loops that call `.filter()` or access related object attributes without `select_related()` /
  `prefetch_related()`.
- Does an `annotate()` produce the correct aggregate? Watch for double-counting with `distinct=True`
  missing.
- Are raw SQL strings or `.extra()` used? Flag these for injection risk.
- Is `.first()` used where `.get()` is more appropriate (and vice versa)?

---

## Full-text search

When a stored `tsvector` column is built with an explicit `config` argument (e.g.
`to_tsvector('english', ...)` in a management command, signal, or migration), every `SearchQuery`
and `SearchVector` that queries it must pass the same `config=` argument explicitly. Omitting
`config=` falls back to the database's `default_text_search_config`, which is not guaranteed to
match across environments, causing searches to silently return no results.

Check that all places that build search vectors (management commands, signals, ORM expressions)
use the same config string, and that all query-side uses (`SearchQuery`, `SearchVector`,
`SearchRank`) match it.
