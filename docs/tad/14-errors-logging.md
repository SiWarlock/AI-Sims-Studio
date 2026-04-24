# TAD — Error Handling, Logging, and Observability

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §16

> Error taxonomy, error flow, structured logging, observable events, no-telemetry policy.

---

## 16. Error Handling, Logging, Observability

### 16.1 Error Taxonomy

Errors are categorized:

- **USER_INPUT_ERROR** — user input invalid (e.g., prompt empty)
- **CONFIG_ERROR** — configuration missing or invalid (e.g., Sims install not found)
- **DEPENDENCY_ERROR** — external dependency unavailable (Anthropic API down, Blender not installed)
- **GENERATION_ERROR** — AI call failed after retries
- **VALIDATION_ERROR** — project state failed validation
- **BUILD_ERROR** — DBPF build or tuning clone failed
- **INSTALL_ERROR** — file copy to Mods folder failed
- **INTERNAL_ERROR** — unexpected exception, bug

Every error has a unique code and both user-facing and admin-facing messages.

### 16.2 Error Flow

Within the sidecar, errors are caught at stage boundaries and converted to structured error responses. The frontend displays the user message; admin mode shows the admin message and stack trace.

### 16.3 Logging

Structured logging with `structlog`:

- Every log entry has timestamp, level, module, event name, and context fields
- Sensitive data (API keys, user prompts) is redacted in logs by default; admin mode can toggle verbose logging for debugging
- Log files rotate per session (one file per app launch)
- Log files older than 30 days are auto-deleted on startup

### 16.4 Observable Events

Key events logged at INFO level or above:

- App startup / shutdown
- Project create / open / close
- Generation job start / progress / complete / failed
- AI API call dispatched / completed / retried / failed
- Blender invocation
- DBPF package built
- Validation run
- Export completed
- Install completed
- Admin mode entered / exited

### 16.5 No Telemetry

Per PRD §8 and §19.9: no logs, metrics, or data are sent to any remote server. All observability is local.

---
