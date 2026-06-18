# LESSONS.md — AI Sims Creator (the desktop UI)

> Full prose for every lesson logged during work in `apps/desktop/`. The compact index lives in `apps/desktop/CLAUDE.md` "Lessons logged" table.
>
> **Lesson numbers are stable IDs.** New lessons get the next sequential number. Numbers may be referenced from code comments, commit messages, and cross-references between lessons. **Don't reorder; don't reuse a deleted number's slot.**
>
> **Lessons start at §1.** Each code area has its own lesson sequence — lessons don't carry across code areas.

---

## Lesson format

```markdown
## <a id="N"></a>N. <Short topic> — <one-line rule>

**Date:** YYYY-MM-DD.
**Source slice:** <slice-id or commit hash>.

<2-5 paragraphs explaining: what was discovered, why it matters, how to
apply the rule, what edge cases are still open. Cite file:line references
where applicable.>

**Rule:** <one-sentence summary, same as the heading subtitle>.
```

---

## <a id="1"></a>1. UI↔sidecar SSE transport — fetch-based streaming with a header-borne token; never native `EventSource` with a URL token

**Date:** 2026-06-17.
**Source slice:** 7.1 (`src/ipc/sse.ts`).

The per-launch loopback token (§4/§16) must ride **every** request to the sidecar, including the
SSE subscription — and it must **never** appear in a URL/query string (a server, proxy, or devtools
would log it, defeating the §16 local-process mitigation and tripping forbidden-pattern 3). Native
`EventSource` cannot set request headers, so the only way to authenticate it is to put the token in
the URL — which is exactly the leak we forbid. The browser's `EventSource` is therefore unusable for
this boundary.

The slice uses **`fetch` + a `ReadableStream` reader** instead: the token rides the `X-AISims-Token`
header on both the initial open and every reconnect, and we own the SSE frame parser (event/data/id
fields, comment-line heartbeats, CRLF/CR normalization, a §16 max-bytes buffer cap). Reconnect uses
`Last-Event-ID` with idle exponential backoff (an unbounded hot-spin on an immediately-closing stream
was a security-review finding). Replay safety is **defense-in-depth**: the reader drops events with
`id ≤ cursor` *and* the projection is idempotent on seen ids (set membership, ordering-agnostic) — so
even an inclusive server replay or a non-numeric id can't double-count or lose an event.

**Rule:** UI↔sidecar SSE is fetch-based streaming with the token in the `X-AISims-Token` header on open
*and* reconnect; never native `EventSource` with a URL/query token. Guard replay with both a
`Last-Event-ID` cursor-drop and an idempotent projection.

## <a id="2"></a>2. Runtime boundary is Zod; the *type* is the generated contract — pin them with a parity manifest

**Date:** 2026-06-17.
**Source slice:** 7.1 (`src/ipc/sse-schema.ts`).

The frozen contracts emit **TS types** (`packages/contracts/generated/contracts.ts`), not runtime
validators. The UI still needs a runtime boundary (Zod) to validate untrusted SSE frames. The trap is
re-declaring the shape in Zod and letting it silently drift from the generated type — a forbidden
duplicate of a contract type (root `CLAUDE.md` "import the generated type").

Resolution: the Zod schemas validate at runtime, but the **type comes from the generated contract** —
a compile-time **parity manifest** asserts `z.infer<typeof schema>` is type-equal to the generated
`SseEvent` members (and each domain-enum field equals its generated enum), plus a runtime check that
the schema's discriminant-tag set equals the generated union's member set. A future-added event tag or
a renamed field then fails `tsc`/the parity test rather than passing validation against a stale shape.
The same pattern backs the hand-authored endpoint catalog (`src/ipc/endpoints.ts`), which the 0.6
codegen does **not** emit (it emits model/enum types only) — a frozen-snapshot drift-guard pins the
catalog to `packages/contracts/tests/__snapshots__/ipc.schema.json` until the codegen is extended.

**Rule:** Zod is the runtime boundary; the generated contract is the type. Pin `z.infer` to the
generated members/enums with a compile-time parity manifest (and a runtime tag-set check) so the
validator cannot drift from the frozen contract.

## <a id="3"></a>3. Loopback token handoff — sync-IPC + a closure-getter `contextBridge`; never `process.argv`/`additionalArguments`

**Date:** 2026-06-17.
**Source slice:** 7.1 (`electron/token-handoff.ts`, `electron/main.ts`, `electron/preload.ts`).

The first implementation passed the per-launch token from the Electron main to the renderer via
`webPreferences.additionalArguments` → renderer `process.argv`. A security review caught that
`process.argv` is **enumerable by other local processes** — the *exact* §16 local-process attack the
token exists to mitigate. Handing a secret over argv re-opens the boundary it was meant to close.

The fix: the main process holds the token in a **closure** and serves it to the preload over a
**synchronous IPC** request (`ipcRenderer.sendSync`); the preload exposes it to the renderer through a
`contextBridge` **closure-getter** (not enumerable on `window`/`globalThis`, never logged). The token
never touches argv, the command line, or any log sink. 7.2's real sidecar→renderer handshake **must
preserve this no-argv posture** when the token starts being minted by the sidecar.

**Rule:** Serve the loopback token to the renderer via synchronous IPC + a closure-getter
`contextBridge`; never via `process.argv`/`additionalArguments` (enumerable by other local processes).

## <a id="4"></a>4. Onboarding/UI logic is framework-agnostic + tested over injected ports; the React screen is a thin design-fixture view

**Date:** 2026-06-17.
**Source slice:** 7.2a (`src/onboarding/*`, `src/settings/settings.ts`).

The deterministic core of a UI surface — detection, validation, persistence, projection — is **framework-
agnostic TypeScript tested over injected ports** (an `FsProbe` interface, the IPC client, a mock sidecar), with
**no React in the test path** (the Vitest env stays `node`). The React screen is a **thin view** that wires the
already-tested logic; its *visual* design ships through **design-fixture review (D4)**, not `/tdd`. So a slice's
`/tdd` RED surface is the logic (detect/validate/load/persist), and the rendered screen is a `not-tested-because:
visual/wiring` entry on the coverage map (covered by `tsc` + the fixture review).

This keeps the deterministic surface fully pinned without pulling `@testing-library`/`jsdom` into the slice, and
keeps the visual workstream on its own (design-fixture) cadence. The injected-port shape also lets the real
backing (e.g. a `node:fs`-backed `FsProbe` via the Electron preload) land later as pure wiring without touching
the tested logic — until it does, the resolver **shape-guards + safe-defaults** rather than trusting an
arbitrary global.

**Rule:** Test UI logic framework-agnostically over injected ports (`node` env, no React); the React screen is a
thin view whose visuals ride design-fixture review (D4), mapped as `not-tested-because: visual/wiring`.

## <a id="5"></a>5. A conflated GET/PUT endpoint's read/write split lives in the client via a GATED method override + effective-method idempotency

**Date:** 2026-06-17.
**Source slice:** 7.2a (`src/ipc/client.ts`).

The frozen §4 catalog models `GET/PUT /settings` as **one** endpoint id (classified mutating; the drift-guard
pins this — it can't be split client-side). The UI needs both the GET (load) and the PUT (persist), so the
read/write split lives in the **client**. The trap a security review caught: a `method` override that was
**type-allowed on any endpoint** plus a **post-hoc `Idempotency-Key` strip** — a caller could GET a mutating
path or diverge from §4 R9, silently widening the frozen surface.

The fix: **gate** the override to the one conflated endpoint (`GET/PUT /settings` only; throw otherwise) and
**derive idempotency from the effective method** (a GET carries the token but omits `Idempotency-Key`; a PUT
carries both) — never strip the key after the fact. The override is a narrow, asserted exception, not a general
escape hatch; the frozen mutating/read classification is otherwise honored verbatim.

**Rule:** When a frozen endpoint conflates GET/PUT under one id, put the split in the client behind a **gated**
method override (throws outside the named endpoint) with idempotency **derived from the effective method** —
never a type-open override or a strip-after-the-fact.

## <a id="6"></a>6. Renderer↔main access is a narrow read-only bridge — `sendSync`, an allowlisted single channel, and a top-frame sender gate

**Date:** 2026-06-17.
**Source slice:** 7.2c (`electron/fs-bridge.ts`, `electron/main.ts`, `electron/preload.ts`).

When the renderer needs a host capability (filesystem probes, etc.), do **not** hand it a raw `node:fs`/Node
handle. Expose a **narrow, read-only bridge**: the main process performs the operation; the preload exposes a
small fixed method set under `window.aisims` over a **synchronous** `sendSync` channel (keeps a sync consumer
interface unrippled — same posture as the token handoff, Lesson 3). Three reinforcing guards, all test-pinned:
(1) a **single IPC channel with a method allowlist** — a `dispatch(method, …) → handler | null` with `default →
null`, so an arbitrary method string sent on the channel executes nothing (pin the reject path, not just the
cooperative surface); (2) **read-only only** — no content read, no write, no arbitrary `fs` method; `isWritable`
is a non-destructive `fs.access(W_OK)`, never a temp write; (3) a **top-frame-only sender-frame gate** on every
`ipcMain` handler (`senderFrame` is the top frame), so a sub-frame/embedded context can't drive the bridge.

`contextBridge.exposeInMainWorld` **cannot expose the same key twice**, so multiple bridges (token + fs) compose
into **one** `window.aisims` object through a single helper (spread the closure-getter member **last** so a data
member can't shadow it) — keep that helper the sole composition point rather than exposing inline (which would
orphan it). The sender-frame gate is load-bearing enough that retrofitting it onto an earlier handler (the 7.1
token handler shared the gap) is worth folding into the slice whose crux it is. Exact-renderer-URL origin pinning
(beyond top-frame) is a later hardening.

**Rule:** Renderer↔main host access is a narrow read-only bridge — `sendSync`, a single allowlisted channel with
a `default→null` reject, read-only ops only (`fs.access` for writability), and a top-frame sender gate on every
handler; compose multiple bridges into one `window.aisims` via the single helper (closure-getter last).

## <a id="7"></a>7. Provider secrets — a WRITE-ONLY main-process keychain bridge (no read-back to the renderer)

**Date:** 2026-06-18.
**Source slice:** 7.2b-1 (`electron/keychain.ts`, `electron/keychain-bridge.ts`).

Provider API keys live in the OS keychain (rule 5; revised D3 = a shared NAMED entry, interop proven by spike
7.2b-0). The renderer needs to **store, check, and clear** a key — but it must **never read one back**. So the
keychain bridge is **write-only**: `window.aisims.keychain = {setProviderKey, hasProviderKey, deleteProviderKey}`
with **no `getProviderKey`** — `has` returns a boolean only, and the secret is consumed by the **sidecar** (Python
`keyring`, 7.2b-2), never re-entering the renderer. The entry is named `(service="AISimsCreator",
account=providerId)`; that constant pair is the ui-owned secret-name contract shared **verbatim** with the sidecar
read — keep both sides identical. The write path reuses the Lesson-6 narrow bridge (single allowlisted channel,
`default→reject`, top-frame sender gate, single-`window.aisims` composition). The native `@napi-rs/keyring` import
stays in `main.ts` (typecheck-only); its `Entry` is verified to return `getPassword→string|null` /
`deletePassword→bool` (neither throws on not-found) — so the factory is a trivial pass-through and no fragile
not-found classifier is needed.

**Rule:** Provider secrets go through a **write-only** main-process keychain bridge (`set`/`has`(bool)/`delete`,
**no `get`**) named `(service="AISimsCreator", account=providerId)`; the sidecar reads, the renderer never reads
back. Keep the secret-name constants identical on both ends.

## <a id="8"></a>8. Rule-5 redaction discipline — fail-safe typed errors, coarse redacted codes, secret-canary on every layer

**Date:** 2026-06-18.
**Source slice:** 7.2b-1 (`electron/keychain.ts`, `electron/keychain-bridge.ts`).

A secret-handling boundary's own error can **echo the secret** (a keychain lib may put the attempted value in its
message). So never propagate a raw boundary error: catch it and throw a **fresh typed error with no `cause` chain**
(`KeychainUnavailableError`) — fail-safe redaction beats diagnostic granularity. For remediation you still want
*some* signal, so the IPC layer maps to **coarse, value-free redacted codes** (`invalid-id` / `unavailable` /
`missing-key` / `unknown-method` / `sender` / `failed`) — never the raw error. Reject an **empty/missing key**
before the keychain (an empty `set` silently clobbers a real key). And pin it with a **secret-canary**: feed a
known secret through *every* layer that touches it — the writer AND the bridge dispatch/handler — and assert it
appears in **no** console sink, no `repr`/`toString`, no error message/stack, and no IPC response. One layer's pin
isn't the guarantee; the full renderer→main→keychain path is.

**Rule:** At a secret boundary, throw a fresh typed error (no raw `cause`) + map to coarse redacted codes; reject
empty/missing secrets before the store; pin redaction with a secret-canary on **every** layer that touches the
value, not just the innermost one.

<!-- next lesson: §9 -->




