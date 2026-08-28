/**
 * Mock-sidecar SSE + fetch fixtures (Track A). No real sidecar, no wall-clock waits:
 * streams are driven by explicit chunk enqueue/close so tests stay deterministic.
 */

const enc = new TextEncoder();

/** Serialize an SSE event object into a wire frame (id/event/data lines + blank terminator). */
export function sseFrame(event: Record<string, unknown>): string {
  const id = String(event.id ?? "");
  const tag = String(event.event ?? "");
  return `id: ${id}\nevent: ${tag}\ndata: ${JSON.stringify(event)}\n\n`;
}

/** A heartbeat/comment frame (SSE keep-alive): a line starting with ':' carries no event. */
export function commentFrame(text = "heartbeat"): string {
  return `: ${text}\n\n`;
}

/** A ReadableStream that emits each chunk (already-serialized frames) then closes. */
export function streamFromChunks(chunks: readonly string[]): ReadableStream<Uint8Array> {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(enc.encode(chunk));
      controller.close();
    },
  });
}

/** A manually-driven stream: push frames and close on demand (drives the §21 interleaving). */
export interface ControllableStream {
  stream: ReadableStream<Uint8Array>;
  push: (chunk: string) => void;
  close: () => void;
}

export function controllableStream(): ControllableStream {
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const stream = new ReadableStream<Uint8Array>({
    start(c) {
      controller = c;
    },
  });
  return {
    stream,
    push: (chunk: string) => controller.enqueue(enc.encode(chunk)),
    close: () => controller.close(),
  };
}

/** Build an event-stream Response around a body stream (status 200, text/event-stream). */
export function eventStreamResponse(body: ReadableStream<Uint8Array>): Response {
  return new Response(body, {
    status: 200,
    headers: { "content-type": "text/event-stream" },
  });
}

/** A JSON ack Response (the immediate REST command-ack body). */
export function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export interface FetchCall {
  url: string;
  init: RequestInit | undefined;
}

export interface RecordingFetch {
  fetchImpl: typeof fetch;
  calls: FetchCall[];
  headerOf: (callIndex: number, name: string) => string | null;
}

/**
 * A fetch impl that returns the supplied responses in order (the last repeats if exhausted),
 * recording every (url, init) so a test can assert headers / URL / call order.
 */
export function recordingFetch(responses: readonly Response[]): RecordingFetch {
  const calls: FetchCall[] = [];
  const fetchImpl = (async (input: Parameters<typeof fetch>[0], init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init });
    const resp = responses[Math.min(calls.length - 1, responses.length - 1)];
    return resp;
  }) as typeof fetch;
  const headerOf = (callIndex: number, name: string): string | null => {
    const init = calls[callIndex]?.init;
    const h = new Headers(init?.headers);
    return h.get(name);
  };
  return { fetchImpl, calls, headerOf };
}
