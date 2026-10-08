# Performance and Scalability Playbook

Apply whenever querysets, bulk operations, or hot-path code is added or changed. Rule shape
follows `django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### Check behaviour against production data volumes, not fixture-sized ones `performance/production-scale`
- **Do:** consider actual table sizes and likely query plans, not just whether the change works
  against a small local/test dataset.
- **Why:** a query plan that uses a sequential scan is invisible in a test with a few hundred
  rows and can be a serious regression against a production table with millions.
- **Evidence:** general performance-review concern — correctness and performance are different
  axes, and a change can pass every test while still regressing at scale.

### A new filter/sort field needs an index, or an explicit reason it doesn't `performance/missing-index`
- **Do:** check whether a new field used in `.filter()`/`.order_by()` (especially one exposed to
  user-controlled sorting or filtering) has a matching database index.
- **Why:** without an index, filtering or sorting on that field forces a sequential scan that
  gets slower in direct proportion to table size — fine today, a production incident once the
  table grows.
- **Except:** a field only ever filtered on a tiny, bounded table doesn't need an index purely
  for this reason.
- **Evidence:** Django docs, `Field.db_index`; PostgreSQL query planner behaviour on unindexed
  filter/sort columns.

### Flag an entire queryset loaded into memory where iteration or pagination would do `performance/unbounded-memory-load`
- **Do:** check for `list(queryset)`, template loops over an un-paginated queryset, or any
  pattern that materializes an entire table's worth of rows at once.
- **Why:** memory use grows with table size with no upper bound — a pattern that's fine at
  launch becomes an OOM risk as the table grows, often well before CPU or query time become
  problems.
- **Evidence:** Django docs, `QuerySet.iterator()` — exists specifically to bound memory use
  for large querysets.

### Check whether an external API call sits in a hot path `performance/external-call-in-hot-path`
- **Do:** check whether a call to an external service (an LLM API, a third-party data API) runs
  synchronously inside a request or a tight loop, and whether it's rate-limited or cached.
- **Why:** an external call's latency and availability are outside this codebase's control —
  putting one in a hot path means every request pays that latency, and an outage or rate limit on
  the external side becomes an outage here too.
- **Except:** a call that's already behind a cache with a reasonable TTL, or is genuinely
  infrequent (e.g. an admin-triggered one-off action), doesn't need further guarding.
- **Evidence:** general dependency-isolation concern — see `references/caching.md` for the
  caching half of the mitigation.

### Check whether a task (or the code enqueuing it) can flood the queue `performance/queue-flooding`
- **Do:** check whether a new Celery task, or code that enqueues one, is bounded against
  triggering an unexpectedly large number of further tasks (e.g. one task per row of a queryset
  with no size limit).
- **Why:** an unbounded fan-out can overwhelm the queue and starve other work, with the failure
  mode scaling directly with whatever input triggered it.
- **Evidence:** see `references/celery.md`'s `celery/cascade-and-queue-flooding`, which covers
  the same concern from the task-review angle.
