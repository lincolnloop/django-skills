# Test Quality Playbook

Apply to all test files, and to any change that does not include tests.

- Do tests cover the happy path and the important failure modes?
- Are edge cases tested: empty inputs, `None`, zero counts, boundary values, concurrent access
  where relevant?
- Do tests assert on the right thing? A test that passes for the wrong reason (e.g. asserting a
  count that starts at zero rather than checking the specific object) is worse than no test.
- Are tests isolated? Do they rely on database state left by other tests, or on a specific
  ordering?
- Are mocks applied at the right point in the import chain? A mock on `module.func` will not
  intercept a local `from module import func` made before the mock is applied.
- Are there tests for new management commands, signal handlers, admin actions, and cache
  invalidation paths — not just the happy-path function?
- Do tests clean up after themselves (cache, files, external state)?
