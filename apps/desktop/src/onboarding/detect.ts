/**
 * Sims 4 install detection (§18 onboarding item 2). Probes the standard macOS user-data location
 * for The Sims 4 and derives the default Mods path. Pure over the injected FsProbe; a missing
 * install yields `detected:false` with no throw (graceful first-run).
 */
import type { FsProbe } from "./fs-probe";

export interface SimsInstall {
  detected: boolean;
  userDataDir?: string;
  defaultModsPath?: string;
}

/** Standard macOS Sims 4 user-data dir, relative to the home directory. */
const USER_DATA_SUBPATH = "Documents/Electronic Arts/The Sims 4";

export function detectSimsInstall(fs: FsProbe): SimsInstall {
  const userDataDir = `${fs.homeDir()}/${USER_DATA_SUBPATH}`;
  if (fs.exists(userDataDir) && fs.isDirectory(userDataDir)) {
    return { detected: true, userDataDir, defaultModsPath: `${userDataDir}/Mods` };
  }
  return { detected: false };
}
