/**
 * §18(1) per-provider test-call interpretation + controller. interpretProviderTest maps the frozen
 * TestProviderResponse to a UI-facing ProviderTestResult; testProviderConnectivity composes the
 * token-bearing client probe with it (validating the providerId first, so a malformed id never
 * fires the probe). The failure path normalizes the code via parseErrorCode (unknown/missing →
 * SYSTEM — additive-enum tolerance, Lesson 13) and surfaces ONLY the rule-5-safe creatorMessage
 * (never maintainerDetail). The visual API-key entry screen rides design-fixture review (D4).
 */
import type {
  ErrorCode,
  TestProviderRequest,
  TestProviderResponse,
} from "../../../../packages/contracts/generated/contracts";
import { parseErrorCode } from "../../../../packages/contracts/generated/helpers";
import type { IpcClient } from "../ipc/client";
import { sanitizeProviderId } from "../keychain/provider-keys";

export type ProviderTestResult =
  | { valid: true; latencyMs?: number }
  | { valid: false; code: ErrorCode; message: string };

/** A failed probe with no envelope still yields an actionable, value-free message. */
const GENERIC_FAILURE_MESSAGE = "Provider connectivity test failed.";

/**
 * Pure interpretation of the connectivity probe. ok:true → valid (+ latency when present);
 * ok:false → invalid with a parseErrorCode-normalized code + the creatorMessage (or a generic
 * message when the envelope is absent). Never reads maintainerDetail (rule 5).
 */
export function interpretProviderTest(resp: TestProviderResponse): ProviderTestResult {
  if (resp.ok) {
    return resp.latencyMs != null ? { valid: true, latencyMs: resp.latencyMs } : { valid: true };
  }
  const error = resp.error;
  if (!error) {
    return { valid: false, code: "SYSTEM", message: GENERIC_FAILURE_MESSAGE };
  }
  return { valid: false, code: parseErrorCode(error.code), message: error.creatorMessage };
}

/**
 * The production entry point (Step 7.5): the onboarding API-key flow calls this after a key is
 * written (7.2b-1) to validate it. Validates the providerId (reusing the keychain client's
 * sanitizer) before the probe fires, then composes the client call with the interpretation.
 */
export async function testProviderConnectivity(
  client: IpcClient,
  providerId: string,
  body?: TestProviderRequest,
): Promise<ProviderTestResult> {
  const id = sanitizeProviderId(providerId);
  const resp = await client.testProvider(id, body);
  return interpretProviderTest(resp);
}
