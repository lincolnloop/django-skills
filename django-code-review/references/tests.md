# Test Quality Playbook

Apply to all test files, and to any change that does not include tests. Rule shape follows
`django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### Tests must cover the important failure modes, not only the happy path `tests/failure-mode-coverage`
- **Do:** check that tests exercise the failure modes a reviewer would expect for this change,
  not only the success case.
- **Why:** a change with only happy-path coverage can regress its error handling silently — the
  tests stay green while the failure behaviour quietly breaks.
- **Evidence:** see `django-development`'s `tests/exercise-enabled-branch` for the specific case
  of a fix whose regression test only covers the disabled/absent branch.

### Edge cases need their own test, not implicit coverage from the happy path `tests/edge-case-coverage`
- **Do:** check for explicit tests of empty inputs, `None`, zero counts, boundary values, and
  concurrent access where relevant — not just an assumption that the happy-path test would catch
  them too.
- **Why:** a happy-path test by construction doesn't exercise these inputs, so their behaviour
  is simply untested unless a test targets them directly.
- **Evidence:** see `references/correctness.md`'s `correctness/edge-cases`.

### A test must assert on the thing that actually matters `tests/asserts-the-right-thing`
- **Do:** check that an assertion would fail if the code under test were wrong — not just that
  it happens to pass given the current (possibly incomplete) implementation.
- **Why:** a test asserting a count started at zero, rather than checking the specific object
  exists with the right attributes, passes whether or not the code under test actually works —
  it's worse than no test, because it looks like coverage that isn't there.
- **Evidence:** general test-quality concern — a passing test is only meaningful if it would
  have failed against a plausible wrong implementation.

### Tests must not depend on state left by another test or on execution order `tests/test-isolation`
- **Do:** check that a test doesn't rely on database state, cache state, or ordering effects
  from another test having already run.
- **Why:** test frameworks don't guarantee ordering, and parallel test execution actively breaks
  it — a test that passes only in one ordering fails unpredictably as the suite grows or runs in
  parallel.
- **Evidence:** pytest-django docs on test database isolation per test.

### A mock must be applied where the code under test actually looks up the name `tests/mock-placement`
- **Do:** check that `mock.patch('module.func')` targets the name as the code under test
  resolves it — a local `from module import func` done before the patch is applied binds its own
  reference that the patch on `module.func` won't intercept.
- **Why:** Python's `from x import y` copies a reference into the importing module's namespace at
  import time; patching `x.y` afterward doesn't change what the importing module's `y` already
  points to.
- **Except:** patching `importing_module.func` (the name as used by the code under test, not its
  original module) works regardless of which import style was used — this is the usual fix.
- **Evidence:** `unittest.mock` docs, "where to patch" — "patch() works by (temporarily)
  changing the object that a name points to with another one. … The key is to patch where the
  thing is looked up."

### New management commands, signal handlers, and admin actions need tests beyond the happy path `tests/non-view-code-coverage`
- **Do:** check that management commands, signal handlers, admin actions, and cache
  invalidation paths have their own tests — not just the view/model code that's easiest to
  reach from an HTTP test client.
- **Why:** these code paths are triggered differently (a cron job, a signal, an admin action, a
  cache miss) from the request/response cycle most test tooling defaults to covering, so they're
  the ones most likely to be skipped if tests are only written for what's convenient to trigger.
- **Evidence:** general test-coverage-gap concern, specific to Django's non-view entry points.

### A test must clean up the external/shared state it touches `tests/cleanup`
- **Do:** check that a test clears any cache keys, temp files, or other external state it wrote,
  rather than relying on the next test run starting from a clean slate by coincidence.
- **Why:** state left behind by one test run can make a later, unrelated test pass or fail for
  the wrong reason — a classic source of flaky tests that are hard to reproduce in isolation.
- **Evidence:** general test-isolation concern, extended to state outside the test database
  (which pytest-django resets automatically) to state the framework doesn't know about.
