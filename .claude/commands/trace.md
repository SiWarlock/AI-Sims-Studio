---
description: Pull a structured trace for a given id and format it for inspection. Usage: /trace <id>
allowed-tools: Bash, Read, Grep
argument-hint: "<id>"
---

Pull the structured trace for a given id and format the lifecycle for inspection.

Argument: `$ARGUMENTS` — the id of the run / item / request to inspect (a `runId`, `itemId`, or `traceRef`).

<!-- ▼ EXAMPLE BLOCK [id=trace-body]: /trace body — from the source project. Replace wholesale. ▼ -->

Observability here is **LangSmith over a thin tracing seam, fail-open and non-blocking** (`ARCHITECTURE.md §14`). The **authoritative** Trace summaries + ReviewEvents live in **Postgres (§12)**; LangSmith is the **derived mirror** for the dev/observability UX. Trace export is a background queue with a short export timeout + drop-on-timeout — so a span may be **legitimately missing** in LangSmith even though the run succeeded (a slow/offline LangSmith never stalls a generation run). Treat the Postgres/local record as ground truth and LangSmith as best-effort. The **redaction chokepoint (§16)** means no secrets/PII and no binaries leave — traces carry metadata + artifact *references* (paths) only, so expect `traceRef`s, not payloads.

## Procedure

1. **Local / authoritative lookup first** — grep the local structured-log output (the sidecar's structured logs, post-redaction) for the id; this matches the Postgres Trace summary, which is authoritative:
   ```bash
   grep "\"runId\":\"$ARGUMENTS\"\|\"itemId\":\"$ARGUMENTS\"\|\"traceRef\":\"$ARGUMENTS\"" <sidecar-log-path> | head -200
   ```

2. **Fallback to LangSmith (the derived mirror)** — if not in local logs, fetch the run from the configured LangSmith project by id (`LANGSMITH_API_KEY` + project from the env/Settings seam). If LangSmith is offline or the seam is opted-out (§18), say so — it is non-blocking by design, not an error.

3. **Format the lifecycle** for human inspection (the 5 ordered stages + their gates: plan → concept → mesh → overlay → export):
   ```
   id: <runId/itemId/traceRef>
   Lifecycle:
     [t=0ms]    plan:    <summary>          gate: <approved/pending>
     [t=Xms]    concept: <summary>          gate: <…>
     [t=Xms]    mesh:    <summary>          gate: <…>
     [t=Xms]    overlay: <summary>          gate: <…>
     [t=Xms]    export:  <DBPF round-trip result>   gate: <…>
     [total=Tms] <terminal item/run state>
   Cost / resource summary:
     <per-stage provider cost + tokens; ProviderJobRef ids; Blender/@s4tk wall-clock>
   Trace-loss:
     <count of dropped spans (fail-open export) surfaced in the dev panel, if any>
   Final outcome:
     <terminal state, or ErrorEnvelope {code, category, retryable, suggestedAction}>
   ```

4. **On a non-OK final status** — surface the `ErrorEnvelope` (§17): which stage emitted it (`code`, `category`, `retryable`), what the rest of the system saw, whether it was a cascading failure (e.g. provider terminal-config → run terminal), and the `suggestedAction`.

## Output

A single formatted trace block + (optionally) the raw tail if the user requests a deep dive. Flag explicitly when the LangSmith mirror is **incomplete vs the authoritative Postgres record** (dropped spans are expected under fail-open).

## Forbidden in this command

- **Fetching traces for ids outside this project's trace format** (a `runId`/`itemId`/`traceRef`). If an id doesn't match, say so; don't try to interpret a foreign trace.
- **Inferring stage output when spans are missing.** A dropped span is the fail-open design, not a failure to paper over — report "no trace (dropped under fail-open export)"; don't fabricate.
- **Treating the LangSmith mirror as authoritative** over the Postgres/local record, or surfacing any redacted secret/PII or binary payload (egress is metadata + references only, §16).

<!-- ▲ END EXAMPLE BLOCK [id=trace-body] ▲ -->
