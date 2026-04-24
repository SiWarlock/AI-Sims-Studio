---
description: Run the full Python and TypeScript test suites and report results. Optionally scope to a specific module by passing a path.
argument-hint: [optional module path]
allowed-tools: Bash, Read
---

Run the project test suites.

If `$ARGUMENTS` is provided, scope tests to that module. Examples:
- `/run-tests sidecar/aisc/storage` → only storage tests
- `/run-tests frontend/src/components/CollectionBoard` → only that component's tests
- `/run-tests` (no args) → full suite

Execute:

1. **Python tests:**
   - If args indicate a Python path: `!cd sidecar && pytest -q <path>`
   - Otherwise: `!cd sidecar && pytest -q`
   - Include coverage: append `--cov=aisc --cov-report=term-missing` if no specific path
2. **TypeScript tests:**
   - If args indicate a TS path: `!cd frontend && npm test -- --run <path>`
   - Otherwise: `!cd frontend && npm test -- --run`
3. **Integration tests** (only if running full suite without args):
   - `!cd sidecar && pytest -q -m integration`

Report:

- Pass/fail counts per suite
- Any skipped tests with reasons
- Coverage summary (if computed)
- Any flaky tests that failed then passed on retry — flag explicitly, these need investigation
- Total runtime

If any tests fail, show the failing test names and first few lines of error output. Do not attempt to fix failures — this command only reports.
