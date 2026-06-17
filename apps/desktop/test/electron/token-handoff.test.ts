import { describe, expect, it, vi } from "vitest";

import {
  TOKEN_BRIDGE_KEY,
  createLoopbackTokenChannel,
  type TokenBridge,
} from "../../electron/token-handoff";

const TOKEN = "loopback-tok-xyz-789";

describe("loopback token handoff — parent→child channel only (§4/§16)", () => {
  it("test_token_handoff_exposes_to_renderer_only — spec(§16)", () => {
    const exposed: { key: string; api: TokenBridge }[] = [];
    const bridge = {
      exposeInMainWorld: (key: string, api: TokenBridge) => exposed.push({ key, api }),
    };
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((m) =>
      vi.spyOn(console, m).mockImplementation(() => undefined),
    );

    createLoopbackTokenChannel({ getToken: () => TOKEN }, bridge);

    // Exposed exactly once, under the agreed key, and the bridge yields the token via its getter.
    expect(exposed).toHaveLength(1);
    expect(exposed[0].key).toBe(TOKEN_BRIDGE_KEY);
    expect(exposed[0].api.getToken()).toBe(TOKEN);

    // The token is closure-captured, never a plain enumerable property (no serialization leak).
    expect(JSON.stringify(exposed[0].api)).not.toContain(TOKEN);

    // Never leaked onto the global object…
    for (const value of Object.values(globalThis as Record<string, unknown>)) {
      expect(value).not.toBe(TOKEN);
    }
    // …and never to any log sink.
    for (const spy of spies) {
      for (const callArgs of spy.mock.calls) {
        expect(JSON.stringify(callArgs)).not.toContain(TOKEN);
      }
      spy.mockRestore();
    }
  });
});
