/**
 * Injected filesystem probe (§18). Onboarding detection/validation is pure over this seam so it
 * unit-tests with no real FS; the Electron main/preload supplies a real implementation (node:fs)
 * when the screen mounts.
 */
export interface FsProbe {
  exists(path: string): boolean;
  isDirectory(path: string): boolean;
  isWritable(path: string): boolean;
  homeDir(): string;
}
