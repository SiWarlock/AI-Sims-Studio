import { describe, expect, it, vi } from "vitest";

import { createFsBridge } from "../../electron/fs-bridge";
import { KeychainWriter, type KeychainEntryFactory } from "../../electron/keychain";
import {
  KEYCHAIN_CHANNEL,
  createKeychainBridge,
  dispatchKeychain,
  registerKeychainBridge,
} from "../../electron/keychain-bridge";
import { createLoopbackTokenChannel } from "../../electron/token-handoff";

const THREE_METHODS = ["deleteProviderKey", "hasProviderKey", "setProviderKey"];

/** A recording stand-in for the KeychainWriter (the bridge only needs these three methods). */
function recordingWriter() {
  const calls: string[][] = [];
  const writer = {
    setProviderKey: (p: string, k: string) => calls.push(["set", p, k]),
    hasProviderKey: (p: string) => {
      calls.push(["has", p]);
      return false;
    },
    deleteProviderKey: (p: string) => calls.push(["delete", p]),
  } as unknown as KeychainWriter;
  return { writer, calls };
}

describe("keychain IPC bridge — write-only, sender-gated (§3, safety rule 5, Lesson 6)", () => {
  it("test_bridge_surface_is_write_only_three_methods — rule 5 (no read-back) + Lesson 6", () => {
    const bridge = createKeychainBridge(() => ({ ok: true }));
    expect(Object.keys(bridge).sort()).toEqual(THREE_METHODS);
    expect((bridge as unknown as Record<string, unknown>).getProviderKey).toBeUndefined();

    // The channel dispatch rejects getProviderKey + any non-allowlisted method (default → reject).
    const { writer, calls } = recordingWriter();
    expect(dispatchKeychain(writer, "getProviderKey", "openai").ok).toBe(false);
    expect(dispatchKeychain(writer, "readSecret", "openai").ok).toBe(false);
    expect(dispatchKeychain(writer, "", "openai").ok).toBe(false);
    expect(calls).toEqual([]); // rejected methods never touch the writer
    // Allowlisted methods dispatch.
    expect(dispatchKeychain(writer, "setProviderKey", "openai", "sk").ok).toBe(true);
    expect(dispatchKeychain(writer, "hasProviderKey", "openai").value).toBe(false);
    expect(dispatchKeychain(writer, "deleteProviderKey", "openai").ok).toBe(true);
    expect(calls).toEqual([["set", "openai", "sk"], ["has", "openai"], ["delete", "openai"]]);
  });

  it("test_error_codes_are_specific — renderer-facing redacted code contract", () => {
    const inMemory: KeychainEntryFactory = () => ({
      setPassword: () => undefined,
      getPassword: () => null,
      deletePassword: () => undefined,
    });
    const lockedFactory: KeychainEntryFactory = () => ({
      setPassword: () => {
        throw new Error("locked");
      },
      getPassword: () => {
        throw new Error("locked");
      },
      deletePassword: () => {
        throw new Error("locked");
      },
    });
    const writer = new KeychainWriter(inMemory);
    expect(dispatchKeychain(writer, "getProviderKey", "openai").error).toBe("unknown-method");
    expect(dispatchKeychain(writer, "setProviderKey", "openai").error).toBe("missing-key"); // no key
    expect(dispatchKeychain(writer, "setProviderKey", "openai", "").error).toBe("missing-key"); // empty
    expect(dispatchKeychain(writer, "setProviderKey", "bad id", "k").error).toBe("invalid-id");
    expect(dispatchKeychain(new KeychainWriter(lockedFactory), "hasProviderKey", "openai").error).toBe(
      "unavailable",
    );
  });

  it("test_sender_frame_gated — Lesson 6 (renderer↔main boundary)", () => {
    let handler:
      | ((event: { senderFrame: unknown; returnValue: unknown }, ...args: unknown[]) => void)
      | undefined;
    const fakeIpcMain = {
      on: (_ch: string, fn: typeof handler) => {
        handler = fn;
      },
    };
    const { writer, calls } = recordingWriter();
    registerKeychainBridge(fakeIpcMain as never, writer);
    expect(handler).toBeDefined();

    // Sub-frame sender → rejected, writer untouched.
    const subEvent = { senderFrame: { parent: {} }, returnValue: undefined as unknown };
    handler?.(subEvent, "setProviderKey", "openai", "sk");
    expect((subEvent.returnValue as { ok: boolean }).ok).toBe(false);
    expect(calls).toEqual([]);

    // Top-frame sender → dispatched.
    const topEvent = { senderFrame: { parent: null }, returnValue: undefined as unknown };
    handler?.(topEvent, "setProviderKey", "openai", "sk");
    expect((topEvent.returnValue as { ok: boolean }).ok).toBe(true);
    expect(calls).toEqual([["set", "openai", "sk"]]);
  });

  it("test_bridge_input_never_leaks — safety rule 5 (full renderer→main path)", () => {
    const SECRET = "sk-BRIDGE-CANARY-1a2b3c";
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((m) =>
      vi.spyOn(console, m).mockImplementation(() => undefined),
    );
    const { writer } = recordingWriter();

    // Pure dispatch: the IPC response never echoes the key.
    const res = dispatchKeychain(writer, "setProviderKey", "openai", SECRET);
    expect(res.ok).toBe(true);
    expect(JSON.stringify(res)).not.toContain(SECRET);

    // Registered handler: returnValue never echoes the key.
    let handler:
      | ((event: { senderFrame: unknown; returnValue: unknown }, ...args: unknown[]) => void)
      | undefined;
    registerKeychainBridge({ on: (_c: string, fn: typeof handler) => (handler = fn) } as never, writer);
    const ev = { senderFrame: { parent: null }, returnValue: undefined as unknown };
    handler?.(ev, "setProviderKey", "openai", SECRET);
    expect(JSON.stringify(ev.returnValue)).not.toContain(SECRET);

    // No console sink saw the key anywhere along the bridge path.
    for (const spy of spies) {
      for (const call of spy.mock.calls) {
        expect(JSON.stringify(call)).not.toContain(SECRET);
      }
      spy.mockRestore();
    }
  });

  it("test_token_fs_keychain_all_exposed — Lesson 6, no 7.1/7.2c regression", () => {
    const exposed: { key: string; api: Record<string, unknown> }[] = [];
    const fakeBridge = {
      exposeInMainWorld: (key: string, api: Record<string, unknown>) => exposed.push({ key, api }),
    };
    const fs = createFsBridge(() => null);
    const keychain = createKeychainBridge(() => ({ ok: true }));

    createLoopbackTokenChannel({ getToken: () => "tok" }, fakeBridge, { fs, keychain });

    const api = exposed[0].api;
    expect(typeof api.getToken).toBe("function");
    expect(api.fs).toBeDefined();
    expect(Object.keys(api.keychain as object).sort()).toEqual(THREE_METHODS);
  });
});

// KEYCHAIN_CHANNEL is the single narrow channel name (asserted present for the contract).
it("keychain channel constant is defined", () => {
  expect(typeof KEYCHAIN_CHANNEL).toBe("string");
});
