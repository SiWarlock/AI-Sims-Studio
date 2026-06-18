/**
 * Mods-path validation (§18 onboarding item 2). Hard-fails (blocking) on a path that is missing /
 * not a directory / not writable; warns (non-blocking) on a writable directory that doesn't match
 * the canonical …/The Sims 4/Mods shape — custom Mods locations are allowed, not blocked. Pure over
 * the injected FsProbe.
 */
import type { FsProbe } from "./fs-probe";

export interface ModsPathVerdict {
  valid: boolean;
  warnings: string[];
  /** Present iff `valid` is false: the blocking reason. */
  blocking?: string;
}

const STANDARD_SUFFIX = "/The Sims 4/Mods";

export function validateModsPath(fs: FsProbe, path: string): ModsPathVerdict {
  if (!fs.exists(path)) {
    return { valid: false, blocking: "Path does not exist.", warnings: [] };
  }
  if (!fs.isDirectory(path)) {
    return { valid: false, blocking: "Path is not a directory.", warnings: [] };
  }
  if (!fs.isWritable(path)) {
    return { valid: false, blocking: "Path is not writable.", warnings: [] };
  }
  const warnings: string[] = [];
  // Normalize a trailing slash (Finder/OS often appends one) and compare case-insensitively
  // (macOS filesystems are case-insensitive) so the canonical location isn't falsely flagged.
  const normalized = path.replace(/\/+$/, "").toLowerCase();
  if (!normalized.endsWith(STANDARD_SUFFIX.toLowerCase())) {
    warnings.push("Non-standard Mods location — expected a path ending in …/The Sims 4/Mods.");
  }
  return { valid: true, warnings };
}
