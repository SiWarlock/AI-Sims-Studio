/**
 * Renderer bootstrap (§3): wire the IPC client + the SSE subscription + the state projection into a
 * thin observer. This is the renderer's production entry — `renderer-entry.ts` calls it with the
 * bridged loopback token; the visible screens (7.3) read `getState()`.
 */
import { createIpcClient, type IpcClient } from "./ipc/client";
import { subscribeEvents, type SubscribeOptions } from "./ipc/sse";
import { initialState, projectEvent, type ObserverState } from "./state/projection";

export interface BootstrapOptions {
  /** When set, the observer opens the SSE stream for this project (first-run has none → idle). */
  projectId?: string;
  fetchImpl?: typeof fetch;
  maxReconnects?: number;
  signal?: AbortSignal;
  onState?: (state: ObserverState) => void;
}

export interface ObserverHandle {
  client: IpcClient;
  getState(): ObserverState;
  /** Resolves when the SSE stream ends (immediately resolved if no project is subscribed). */
  done: Promise<void>;
}

export function bootstrapObserver(
  token: string,
  baseUrl: string,
  opts: BootstrapOptions = {},
): ObserverHandle {
  const client = createIpcClient({
    baseUrl,
    token,
    ...(opts.fetchImpl ? { fetchImpl: opts.fetchImpl } : {}),
  });

  let state = initialState();
  let done = Promise.resolve();

  if (opts.projectId !== undefined) {
    const sub: SubscribeOptions = {
      baseUrl,
      projectId: opts.projectId,
      token,
      onEvent: (event) => {
        state = projectEvent(state, event);
        opts.onState?.(state);
      },
      ...(opts.fetchImpl ? { fetchImpl: opts.fetchImpl } : {}),
      ...(opts.maxReconnects !== undefined ? { maxReconnects: opts.maxReconnects } : {}),
      ...(opts.signal ? { signal: opts.signal } : {}),
    };
    done = subscribeEvents(sub);
  }

  return {
    client,
    getState: () => state,
    done,
  };
}
