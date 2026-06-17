// Phase-0 skeleton entry for the DBPF export worker (@s4tk).
//
// The real modules (donor/clone/serialize/write/validate per the area module layout) and
// the atomic temp-write → fsync → DBPF round-trip validate → atomic rename pipeline land in
// the export track's first phase. This placeholder only gives the strict TS toolchain an
// input so `tsc --noEmit`, ESLint, and Vitest run clean while the area is empty.
export {};
