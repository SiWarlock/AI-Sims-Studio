// S1b-clone — re-serialize the cloned DBPF via @s4tk into an uncompressed package buffer.
//
// Thin seam over `Package.getBuffer()` so the serialize step is an explicit, testable stage of the
// pipeline (and the one place a future compression/minify policy would live). The output buffer is
// what the atomic-write path durably writes + round-trip-validates.

import type { Package } from "@s4tk/models";

/** Serialize a cloned package to an uncompressed DBPF buffer. */
export function serializeClone(pkg: Package): Buffer {
  return pkg.getBuffer();
}
