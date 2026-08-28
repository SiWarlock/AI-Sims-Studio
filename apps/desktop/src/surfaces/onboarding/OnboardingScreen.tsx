/**
 * Onboarding / Settings surface (§3/§18) — the functional wiring over the tested onboarding logic
 * (detect / validate / load / persist). Visual polish is a design-fixture-review follow-up (D4),
 * not /tdd. Server-driven (fp-2): settings are read on demand, never cached as authority.
 */
import { useEffect, useState } from "react";

import type { SettingsResponse } from "../../../../../packages/contracts/generated/contracts";
import type { IpcClient } from "../../ipc/client";
import { detectSimsInstall, type SimsInstall } from "../../onboarding/detect";
import type { FsProbe } from "../../onboarding/fs-probe";
import { validateModsPath, type ModsPathVerdict } from "../../onboarding/mods-path";
import { loadSettings, persistModsPath } from "../../settings/settings";

export interface OnboardingScreenProps {
  client: IpcClient | null;
  fs: FsProbe;
}

export function OnboardingScreen({ client, fs }: OnboardingScreenProps): React.ReactElement {
  const [install, setInstall] = useState<SimsInstall | null>(null);
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [modsPath, setModsPath] = useState("");
  const [verdict, setVerdict] = useState<ModsPathVerdict | null>(null);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Detect the install once on mount and pre-fill the default Mods path (before the user types).
  // Mount-only on purpose: `fs` is a stable module-level probe; re-running would clobber input.
  useEffect(() => {
    const detected = detectSimsInstall(fs);
    setInstall(detected);
    if (detected.defaultModsPath) setModsPath(detected.defaultModsPath);
  }, []);

  useEffect(() => {
    if (!client) return;
    let active = true;
    void loadSettings(client).then(
      (s) => {
        if (!active) return;
        setSettings(s);
        // Seed only an empty field — never clobber an in-progress user edit.
        if (s.simsModsPath) setModsPath((cur) => (cur === "" ? (s.simsModsPath ?? "") : cur));
      },
      () => undefined,
    );
    return () => {
      active = false;
    };
  }, [client]);

  const onValidate = (): void => setVerdict(validateModsPath(fs, modsPath));

  const onSave = (): void => {
    const v = validateModsPath(fs, modsPath);
    setVerdict(v);
    setSaveError(null);
    setSaved(false);
    if (!v.valid || !client) return;
    void persistModsPath(client, modsPath).then(
      (s) => {
        setSettings(s);
        setSaved(true);
      },
      () => setSaveError("Could not save the Mods folder. Please try again."),
    );
  };

  return (
    <section aria-labelledby="onboarding-title">
      <h2 id="onboarding-title">Set up your Sims 4 Mods folder</h2>
      <p>
        {install?.detected
          ? "The Sims 4 install detected."
          : "The Sims 4 install not detected — enter your Mods folder manually."}
      </p>
      <label htmlFor="mods-path">Mods folder</label>
      <input
        id="mods-path"
        value={modsPath}
        onChange={(e) => setModsPath(e.target.value)}
        placeholder="…/The Sims 4/Mods"
      />
      <button type="button" onClick={onValidate}>
        Validate
      </button>
      <button type="button" onClick={onSave} disabled={!client}>
        Save
      </button>
      {verdict && !verdict.valid ? <p role="alert">{verdict.blocking}</p> : null}
      {verdict && verdict.warnings.length > 0 ? (
        <div role="status">
          {verdict.warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
        </div>
      ) : null}
      {saveError ? <p role="alert">{saveError}</p> : null}
      {settings?.simsModsPath ? <p>Current saved path: {settings.simsModsPath}</p> : null}
      {saved ? <p role="status">Saved.</p> : null}
    </section>
  );
}
