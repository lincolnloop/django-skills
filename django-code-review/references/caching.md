# Caching Playbook

Apply whenever cache reads, writes, or invalidation logic is added or changed.

- Is the cache key unique enough to avoid collisions between environments or between different
  objects of the same type?
- Is the TTL appropriate? Is there explicit invalidation, or does the data rely solely on expiry?
- Is the cache invalidated on all paths that mutate the underlying data (including `post_save`,
  `post_delete`, bulk operations)?
- Could a cache stampede occur under high load (many simultaneous cache misses)?
