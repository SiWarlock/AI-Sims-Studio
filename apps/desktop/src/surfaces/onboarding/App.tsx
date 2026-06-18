/**
 * The app root surface (§3). 7.2a renders the onboarding/settings screen; the remaining creator
 * screens (UI-001…011) land in 7.3 on this same React/Vite toolchain.
 */
import type { IpcClient } from "../../ipc/client";
import type { FsProbe } from "../../onboarding/fs-probe";
import { OnboardingScreen } from "./OnboardingScreen";

export interface AppProps {
  client: IpcClient | null;
  fs: FsProbe;
}

export function App({ client, fs }: AppProps): React.ReactElement {
  return (
    <main>
      <h1>AI Sims Creator</h1>
      <OnboardingScreen client={client} fs={fs} />
    </main>
  );
}
