// Phase 0 bootstrap stub. The real IPC client lands in Task 0.2 once the
// Tauri↔Python stdio JSON-RPC transport is in place.
//
// The final shape, per frontend/CLAUDE.md:
//   class IPCClient {
//     async request<TParams, TResult>(method: string, params: TParams): Promise<TResult>;
//     subscribe(eventType: string, handler: (params: unknown) => void): () => void;
//   }

export const ipc = {
  async request(_method: string, _params: unknown): Promise<never> {
    throw new Error("IPC client not yet implemented (Phase 0 Task 0.2).");
  },
};
