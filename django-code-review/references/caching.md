# Caching Playbook

Apply whenever cache reads, writes, or invalidation logic is added or changed. Rule shape
follows `django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### A cache key must be unique per object and per environment `caching/key-collisions`
- **Do:** check that the cache key includes enough identifying information (object ID, type,
  relevant parameters) to avoid colliding with a different object of the same type, or with the
  same key used by a different environment sharing the same cache backend.
- **Why:** a collision silently serves one object's (or one environment's) cached value in place
  of another's — there's no error, just wrong data.
- **Evidence:** general cache-key design concern; shared cache backends (e.g. one Redis instance
  used by staging and production) make the environment half of this especially easy to miss.

### Check that the TTL matches how long the data is allowed to be stale `caching/ttl-appropriateness`
- **Do:** check whether the TTL is appropriate for the data's actual staleness tolerance, and
  whether invalidation is explicit or the code relies solely on expiry.
- **Why:** a TTL that's too long serves stale data for longer than acceptable; one that's too
  short defeats the purpose of caching by re-fetching almost immediately. Relying solely on
  expiry (no explicit invalidation) means every write is stale-visible for up to the full TTL.
- **Evidence:** general cache-design tradeoff between staleness and cache effectiveness.

### Invalidate the cache on every path that mutates the underlying data `caching/invalidation-coverage`
- **Do:** check that cache invalidation happens on every mutation path for the cached data —
  including `post_save`, `post_delete`, and bulk operations (`.update()`, `.delete()`), not just
  the "normal" single-object save path.
- **Why:** `.update()` and `.delete()` on a queryset don't fire `post_save`/`post_delete` signals
  at all, so invalidation logic that only lives in a signal handler silently misses bulk
  mutations.
- **Evidence:** Django docs, `QuerySet.update()`/`QuerySet.delete()` — explicit note that these
  do not call model `save()`/`delete()` or send signals.

### Check whether a cache stampede is possible under load `caching/stampede-risk`
- **Do:** check whether many concurrent requests can simultaneously miss the same cache key
  (e.g. right after it expires, or on first access to a newly-popular key) and all regenerate
  the cached value at once.
- **Why:** a stampede turns a single expensive operation into N concurrent copies of that same
  operation, hitting whatever it's protecting (usually the database) with a spike proportional
  to concurrent traffic instead of the one computation the cache was meant to absorb.
- **Except:** a cheap-to-regenerate value, or traffic low enough that simultaneous misses are
  implausible, doesn't need stampede protection.
- **Evidence:** general cache-stampede failure mode; mitigations include jittered TTLs,
  locking around regeneration, or serving stale-while-revalidating.
