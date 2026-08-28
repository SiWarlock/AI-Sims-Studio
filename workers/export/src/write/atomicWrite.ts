// 🔒 S1b-clone — the SAFETY-RULE-4 atomic validated write. The sole publish path for an export
// artifact; its own security-reviewed commit.
//
// Sequence (rule 4 — §9): write bytes to a TEMP path in the sidecar scratch dir → fsync(file)+fsync(dir)
// → re-read from disk and RUN THE VALIDATE → only on a PASS, atomic rename(temp → final) → fsync(dir).
// On a validate FAIL: unlink the temp, return `failed`, NO rename, NO partial file left behind.
//
// Invariants this choke point enforces:
//   - rule 4: never a half-written / unvalidated package is published; donors are never opened here at
//     all (no donor handle — read-only by construction);
//   - rule 3 / rule 4: writes go ONLY under the provided sidecar scratch dir; a path under a live Sims
//     "Mods" folder is REFUSED before any byte is written (defensive belt — the worker never builds into
//     the live Mods folder).

import { randomBytes } from "node:crypto";
import { open, readFile, rename, unlink } from "node:fs/promises";
import { join, sep } from "node:path";

/** The live Sims 4 Mods folder name — a path segment the publish path must never write under. */
const MODS_SEGMENT = "Mods";

export interface AtomicWriteInput {
  /** Sidecar-provided scratch dir (e.g. a randomized mkdtemp). The ONLY place bytes are written. */
  scratchDir: string;
  /** Final package filename within `scratchDir` (e.g. "clone.package"). */
  filename: string;
  /** The serialized DBPF bytes to publish. */
  buffer: Buffer;
  /** Round-trip validation run against the bytes AS WRITTEN TO DISK; rename happens only on `true`. */
  validate: (writtenBytes: Buffer) => boolean | Promise<boolean>;
}

export interface AtomicWriteResult {
  status: "succeeded" | "failed";
  /** The published package path (under `scratchDir`) on success; null on failure. */
  packagePath: string | null;
  reason: string;
}

/** True if any path segment equals `segment` (e.g. a live Sims "Mods" folder). */
function pathHasSegment(p: string, segment: string): boolean {
  return p.split(sep).includes(segment);
}

/** fsync a directory entry (best-effort — durability nicety; some filesystems reject dir-fsync). */
async function fsyncDir(dir: string): Promise<void> {
  let dh;
  try {
    dh = await open(dir, "r");
    await dh.sync();
  } catch {
    // best-effort: the atomic rename is still correct; dir-fsync only hardens durability.
  } finally {
    await dh?.close();
  }
}

/** Atomically publish a validated package into the scratch dir. Never throws; never leaves a partial. */
export async function atomicValidatedWrite(input: AtomicWriteInput): Promise<AtomicWriteResult> {
  const { scratchDir, filename, buffer, validate } = input;

  // rule 4 defensive belt: never publish into a live Sims "Mods" folder.
  if (pathHasSegment(scratchDir, MODS_SEGMENT)) {
    return {
      status: "failed",
      packagePath: null,
      reason: `refused: scratchDir is under a "${MODS_SEGMENT}" folder (rule 4) — ${scratchDir}`,
    };
  }

  const finalPath = join(scratchDir, filename);
  const tempPath = join(scratchDir, `.${filename}.tmp-${randomBytes(8).toString("hex")}`);

  try {
    // 1. write to TEMP (owner-only) → 2. fsync(file) → 3. fsync(dir)
    const tempFh = await open(tempPath, "w", 0o600);
    try {
      await tempFh.writeFile(buffer);
      await tempFh.sync();
    } finally {
      await tempFh.close();
    }
    await fsyncDir(scratchDir);

    // 4. re-read the ON-DISK bytes + validate (round-trip from disk, not an in-memory model)
    let ok: boolean;
    try {
      const onDisk = await readFile(tempPath);
      ok = await validate(onDisk);
    } catch {
      ok = false; // a thrown validator is fail-closed
    }

    // 5a. FAIL → discard the temp; NO rename, NO partial file
    if (!ok) {
      await unlink(tempPath).catch(() => undefined);
      return {
        status: "failed",
        packagePath: null,
        reason: "round-trip validation failed — temp discarded, no package published",
      };
    }

    // 5b. PASS → atomic rename into place + harden the directory entry
    await rename(tempPath, finalPath);
    await fsyncDir(scratchDir);
    return { status: "succeeded", packagePath: finalPath, reason: "validated package published" };
  } catch (e) {
    // any I/O failure (open/write/sync/rename) → clean up the temp, never leave a partial, never throw.
    await unlink(tempPath).catch(() => undefined);
    return {
      status: "failed",
      packagePath: null,
      reason: `atomic write I/O failure — temp discarded, no package published: ${
        e instanceof Error ? e.message : String(e)
      }`,
    };
  }
}
