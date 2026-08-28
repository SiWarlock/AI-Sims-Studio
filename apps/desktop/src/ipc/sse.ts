/**
 * Fetch-based SSE subscription (§3/§4). Native EventSource can't set headers, so it would force the
 * token into the URL (logged by proxies/devtools → forbidden pattern 3 / §16). We own a minimal
 * fetch + ReadableStream reader instead: token rides the X-AISims-Token header on every open AND
 * reconnect, and we control `Last-Event-ID` for resumable replay. Replayed events at/under the
 * cursor are dropped (the projection also dedupes — defense in depth, Q4).
 */
import { TOKEN_HEADER } from "./endpoints";
import { parseSseEvent, type SseEvent } from "./sse-schema";

/** §16 boundary: cap the unframed buffer so a delimiter-less stream can't exhaust renderer memory. */
const MAX_BUFFER_BYTES = 1_048_576; // 1 MiB — frames are tiny; this is a generous abuse ceiling.
const BASE_BACKOFF_MS = 500;
const MAX_BACKOFF_MS = 30_000;

export interface SubscribeOptions {
  baseUrl: string;
  projectId: string;
  token: string;
  lastEventId?: string;
  fetchImpl?: typeof fetch;
  onEvent: (event: SseEvent) => void;
  signal?: AbortSignal;
  /** Max automatic reconnects after a stream ends (default: unbounded). */
  maxReconnects?: number;
  /** Backoff sleep between *idle* reconnects; injectable for tests. Default: abort-aware timer. */
  sleepImpl?: (ms: number) => Promise<void>;
}

/**
 * Compare event ids for the replay-drop. Monotonic numeric ids compare numerically; a non-numeric
 * id degrades to NO drop (never a mis-drop / data loss) — the idempotent projection then dedupes.
 */
function idLessOrEqual(id: string, cursor: string): boolean {
  const a = Number(id);
  const b = Number(cursor);
  if (Number.isFinite(a) && Number.isFinite(b)) return a <= b;
  return false;
}

function defaultSleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        resolve();
      },
      { once: true },
    );
  });
}

function parseFrame(raw: string): SseEvent | null {
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith(":")) continue; // comment / heartbeat — no payload
    if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
    // id:/event: framing lines are mirrored in the JSON payload; everything derives from `data`.
  }
  if (dataLines.length === 0) return null; // heartbeat / comment-only frame
  // Multiple data: lines join with LF per the SSE spec; LF is JSON whitespace, so a compact
  // single-line payload (what the sidecar emits) parses regardless.
  const payload: unknown = JSON.parse(dataLines.join("\n"));
  return parseSseEvent(payload); // Zod-validate (throws on unknown tag / malformed frame)
}

/** Reads one stream to EOF; returns the count of events delivered (0 ⇒ an idle/empty connection). */
async function readStream(
  body: ReadableStream<Uint8Array>,
  emit: (event: SseEvent) => boolean,
): Promise<number> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let delivered = 0;
  const drain = (): void => {
    let idx = buffer.indexOf("\n\n");
    while (idx !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const event = parseFrame(frame);
      if (event && emit(event)) delivered++;
      idx = buffer.indexOf("\n\n");
    }
    if (buffer.length > MAX_BUFFER_BYTES) {
      throw new Error("SSE frame exceeded max buffer size (§16 streaming cap)");
    }
  };
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    // Normalize SSE line terminators (CR, CRLF) to LF so frame splitting is transport-agnostic.
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    drain();
  }
  const trailing = (buffer + decoder.decode()).trim();
  if (trailing.length > 0) {
    const event = parseFrame(trailing);
    if (event && emit(event)) delivered++;
  }
  return delivered;
}

/**
 * Open the resumable SSE subscription and feed validated events to `onEvent`. Resolves when the
 * stream ends with no reconnects left (or the signal aborts). Reconnects re-present the cursor via
 * `Last-Event-ID`; consecutive *idle* (zero-delivered) reconnects back off exponentially so a
 * server that instantly closes the stream can't drive a hot reconnect loop.
 */
export async function subscribeEvents(opts: SubscribeOptions): Promise<void> {
  const fetchImpl = opts.fetchImpl ?? globalThis.fetch;
  const sleep = opts.sleepImpl ?? ((ms: number) => defaultSleep(ms, opts.signal));
  const url = `${opts.baseUrl}/projects/${encodeURIComponent(opts.projectId)}/events`;
  const maxReconnects = opts.maxReconnects ?? Number.POSITIVE_INFINITY;
  let cursor = opts.lastEventId;
  let reconnects = 0;
  let idleStreak = 0;

  for (;;) {
    const headers: Record<string, string> = {
      [TOKEN_HEADER]: opts.token,
      Accept: "text/event-stream",
    };
    if (cursor !== undefined) headers["Last-Event-ID"] = cursor;
    const init: RequestInit = { method: "GET", headers };
    if (opts.signal) init.signal = opts.signal;

    const resp = await fetchImpl(url, init);
    if (!resp.ok || !resp.body) {
      throw new Error(`SSE subscribe failed: HTTP ${resp.status}`);
    }

    const delivered = await readStream(resp.body, (event) => {
      if (cursor !== undefined && idLessOrEqual(event.id, cursor)) return false; // drop replayed
      cursor = event.id;
      opts.onEvent(event);
      return true;
    });

    if (opts.signal?.aborted) return;
    if (reconnects >= maxReconnects) return;
    reconnects++;

    if (delivered === 0) {
      idleStreak++;
      await sleep(Math.min(BASE_BACKOFF_MS * 2 ** (idleStreak - 1), MAX_BACKOFF_MS));
      if (opts.signal?.aborted) return;
    } else {
      idleStreak = 0;
    }
  }
}
