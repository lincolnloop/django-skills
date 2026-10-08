# QuerySets and Full-Text Search Playbook

Apply whenever ORM queries or search functionality is added or changed. Rule shape follows
`django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### Flag a loop that filters or follows a relation without `select_related`/`prefetch_related` `querysets/n-plus-one`
- **Do:** check any loop that calls `.filter()` again per iteration, or accesses a related
  object's attributes, for a missing `select_related()`/`prefetch_related()` on the base
  queryset.
- **Why:** querysets are lazily evaluated per relation access by default — each iteration
  without a prefetch issues its own query, turning one request into N+1 queries that only shows
  up as a performance problem under real data volume, not in a small test fixture.
- **Evidence:** Django docs, "Database access optimization" — `select_related`/
  `prefetch_related`.

### Check `annotate()` aggregates for join-multiplication double-counting `querysets/annotate-double-counting`
- **Do:** when an `annotate()` aggregates across a joined relation, check whether the join can
  multiply rows before the aggregate runs, and whether `distinct=True` is needed on the
  aggregate.
- **Why:** annotating a `Count`/`Sum` across a one-to-many join counts once per joined row, not
  once per base row — joining two one-to-many relations in the same query compounds this further
  and produces a silently inflated total.
- **Evidence:** Django docs, "Aggregation" — "Combining multiple aggregations" warns explicitly
  about this join-multiplication effect.

### Flag raw SQL strings and `.extra()` for injection risk `querysets/raw-sql-injection-risk`
- **Do:** check any `.raw()`, `.extra()`, or string-interpolated query fragment for unescaped
  user input.
- **Why:** these bypass the ORM's parameterized-query escaping, so string-interpolated user
  input in any of them is a SQL injection vector.
- **Except:** parameters passed through `.raw(sql, params)`'s own parameter-binding (not string
  interpolation) are safe — the risk is specifically interpolation, not raw SQL itself.
- **Evidence:** Django docs, "Performing raw SQL queries" — explicit warning on passing
  parameters, not interpolating them.

### Check `.first()` vs `.get()` matches the intent `querysets/first-vs-get`
- **Do:** check whether `.first()` is used where exactly one result is actually expected (use
  `.get()` instead), or `.get()` is used where zero-or-more results are possible (use `.first()`
  or keep the queryset).
- **Why:** `.get()` raises `DoesNotExist`/`MultipleObjectsReturned` when the assumption of
  exactly one row is wrong, surfacing a bug immediately; `.first()` silently returns `None` or an
  arbitrary row instead, which can mask the same bug.
- **Evidence:** Django docs, `QuerySet.get()` vs `QuerySet.first()`.

### A `tsvector` built with an explicit search config must be queried with the same config `querysets/search-config-consistency`
- **Do:** when a stored `tsvector` column is built with an explicit `config` argument (e.g.
  `to_tsvector('english', ...)` in a management command, signal, or migration), check that every
  `SearchQuery`/`SearchVector`/`SearchRank` that queries it passes the same `config=` argument
  explicitly.
- **Why:** omitting `config=` on either the build or query side falls back to the database's
  `default_text_search_config`, which is not guaranteed to match across environments — a search
  that works locally can silently return no results in an environment with a different default.
- **Evidence:** PostgreSQL docs, `default_text_search_config`; Django docs, `contrib.postgres`
  search — `SearchVector`/`SearchQuery` `config` parameter.
