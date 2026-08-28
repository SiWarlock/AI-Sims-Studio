/**
 * KeychainWriter — the provider-key secret-handling core (§18, safety rule 5). Writes each key to a
 * login-keychain generic-password entry at service="AISimsCreator", account=providerId, over an
 * INJECTED keyring boundary (mock-first; no real keychain in unit tests). The real @napi-rs/keyring
 * Entry is wired in as the prod factory by main.ts (interop proven by spike 7.2b-0).
 *
 * RULE 5: the key value never lands in a log, the writer's repr, or an error — ANY boundary failure
 * is re-thrown as a fresh, REDACTED KeychainUnavailableError (never the raw error, which could echo
 * the secret). Write-only by construction: there is deliberately no getProviderKey (the Python
 * sidecar reads the secret, 7.2b-2; the same (service, account) contract).
 */

/** The locked-in keychain service name — shared verbatim with the Python read accessor (7.2b-2). */
export const KEYCHAIN_SERVICE = "AISimsCreator";

/**
 * One keychain entry's operations (the injected boundary). `getPassword` returns null when the
 * entry is absent (NOT an error); all three throw ONLY on a real keychain failure (locked /
 * unavailable). The prod factory (main.ts) maps @napi-rs/keyring's not-found into null / no-op.
 */
export interface KeychainEntry {
  setPassword(password: string): void;
  getPassword(): string | null;
  deletePassword(): void;
}

export type KeychainEntryFactory = (service: string, account: string) => KeychainEntry;

/** A locked / unavailable keychain — typed + REDACTED (carries no key and no raw cause chain). */
export class KeychainUnavailableError extends Error {
  constructor() {
    super("The OS keychain is locked or unavailable.");
    this.name = "KeychainUnavailableError";
  }
}

/** A malformed providerId / empty key — a caller-input error (NOT a keychain failure; no secret). */
export class InvalidProviderIdError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidProviderIdError";
  }
}

// Keep in sync with src/keychain/provider-keys.ts's renderer-side sanitizer (this writer is the
// authoritative gate; the client copy is an early-UX pre-check).
const PROVIDER_ID_RE = /^[a-z0-9][a-z0-9._-]*$/i;

/** Reject empty/whitespace/control/malformed providerIds before they reach the keychain (rule 5). */
function assertValidProviderId(providerId: string): void {
  if (!PROVIDER_ID_RE.test(providerId)) {
    throw new InvalidProviderIdError("Invalid provider id.");
  }
}

export class KeychainWriter {
  readonly #entryFactory: KeychainEntryFactory;

  constructor(entryFactory: KeychainEntryFactory) {
    this.#entryFactory = entryFactory;
  }

  setProviderKey(providerId: string, key: string): void {
    assertValidProviderId(providerId);
    if (key.length === 0) {
      throw new InvalidProviderIdError("Provider key must not be empty.");
    }
    this.#guard(() => this.#entryFactory(KEYCHAIN_SERVICE, providerId).setPassword(key));
  }

  hasProviderKey(providerId: string): boolean {
    assertValidProviderId(providerId);
    return this.#guard(
      () => this.#entryFactory(KEYCHAIN_SERVICE, providerId).getPassword() !== null,
    );
  }

  deleteProviderKey(providerId: string): void {
    assertValidProviderId(providerId);
    this.#guard(() => this.#entryFactory(KEYCHAIN_SERVICE, providerId).deletePassword());
  }

  /** Run a boundary op; ANY failure → a fresh redacted KeychainUnavailableError (rule 5: the raw
   *  error — which may echo the secret — is never propagated). */
  #guard<T>(op: () => T): T {
    try {
      return op();
    } catch {
      throw new KeychainUnavailableError();
    }
  }
}
