/**
 * RED — §18(1) per-provider test-call interpretation + controller. interpretProviderTest maps the
 * frozen TestProviderResponse to a UI ProviderTestResult; the failure path normalizes the code via
 * parseErrorCode (unknown/missing → SYSTEM, additive-enum tolerance, Lesson 13) and surfaces the
 * envelope's user-facing message. Framework-agnostic (pure fn + controller over a mock IpcClient,
 * Lesson 4); the visual API-key screen rides design-fixture review (D4), not these tests.
 */
import { describe, expect, it } from "vitest";

import type {
  ErrorCode,
  ErrorEnvelope,
  TestProviderResponse,
} from "../../../../packages/contracts/generated/contracts";
import type { IpcClient } from "../../src/ipc/client";
import {
  interpretProviderTest,
  testProviderConnectivity,
} from "../../src/onboarding/provider-test";

function envelope(code: string, creatorMessage: string): ErrorEnvelope {
  return {
    category: "provider",
    code: code as ErrorCode,
    creatorMessage,
    maintainerDetail: "internal maintainer detail",
    retryable: false,
  };
}

describe("provider test-call — §18(1) interpretation + controller", () => {
  it("test_interpret_ok_true_surfaces_latency — spec(§18)", () => {
    expect(interpretProviderTest({ ok: true, latencyMs: 42 })).toEqual({
      valid: true,
      latencyMs: 42,
    });
    // ok:true with no latency present ⇒ valid, no latency key (covers the absent-latency branch).
    expect(interpretProviderTest({ ok: true })).toEqual({ valid: true });
    // latencyMs:0 is a valid surfaced value — must NOT be dropped by a falsy check (!= null, not ?).
    expect(interpretProviderTest({ ok: true, latencyMs: 0 })).toEqual({ valid: true, latencyMs: 0 });
    // ok:true wins even if a stray error rides the response — error is ignored on success.
    expect(interpretProviderTest({ ok: true, error: envelope("SYSTEM", "ignored") })).toEqual({
      valid: true,
    });
  });

  it("test_interpret_ok_false_maps_known_error_code — spec(§18)", () => {
    const result = interpretProviderTest({
      ok: false,
      error: envelope("PROVIDER_AUTH_QUOTA", "Auth or quota check failed"),
    });
    if (result.valid) throw new Error("expected invalid");
    expect(result.code).toBe("PROVIDER_AUTH_QUOTA"); // recognized code preserved
    expect(result.message).toBe("Auth or quota check failed");
  });

  it("test_interpret_ok_false_unknown_code_to_system — spec(§17) Lesson 13", () => {
    const result = interpretProviderTest({
      ok: false,
      error: envelope("TOTALLY_OFF_CONTRACT", "weird"),
    });
    if (result.valid) throw new Error("expected invalid");
    expect(result.code).toBe("SYSTEM"); // unknown code → SYSTEM via parseErrorCode (additive tolerance)
  });

  it("test_interpret_ok_false_missing_error_defaults_system — spec(§18)", () => {
    const result = interpretProviderTest({ ok: false, error: null });
    if (result.valid) throw new Error("expected invalid");
    expect(result.code).toBe("SYSTEM"); // defensive: a failed probe is always actionable
    expect(result.message).toBe("Provider connectivity test failed."); // pinned generic, value-free message
  });

  it("test_interpret_preserves_error_message — spec(§18)", () => {
    const result = interpretProviderTest({
      ok: false,
      error: envelope("PROVIDER_OUTAGE", "Provider is currently unreachable"),
    });
    if (result.valid) throw new Error("expected invalid");
    expect(result.message).toBe("Provider is currently unreachable"); // creatorMessage surfaced
  });

  it("test_test_provider_connectivity_composes_client_then_interpret", async () => {
    const resp: TestProviderResponse = { ok: true, latencyMs: 7 };
    const mockClient = { testProvider: async () => resp } as unknown as IpcClient;
    expect(await testProviderConnectivity(mockClient, "openai")).toEqual({
      valid: true,
      latencyMs: 7,
    });
  });

  it("test_test_provider_connectivity_rejects_malformed_provider_id — spec(§18)", async () => {
    let called = false;
    const mockClient = {
      testProvider: async () => {
        called = true;
        return { ok: true } satisfies TestProviderResponse;
      },
    } as unknown as IpcClient;

    await expect(testProviderConnectivity(mockClient, "bad id!!")).rejects.toThrow(
      "Invalid provider id",
    );
    expect(called).toBe(false); // rejected before the probe fired
  });
});
