# LESSONS.md — AI Sims Creator (the Sims DBPF export worker)

> Full prose for every lesson logged during work in `workers/export/`. The compact index lives in `workers/export/CLAUDE.md` "Lessons logged" table.
>
> **Lesson numbers are stable IDs.** New lessons get the next sequential number. Numbers may be referenced from code comments, commit messages, and cross-references between lessons. **Don't reorder; don't reuse a deleted number's slot.**
>
> **Lessons start at §1.** Each code area has its own lesson sequence — lessons don't carry across code areas.

---

## Lesson format

```markdown
## <a id="N"></a>N. <Short topic> — <one-line rule>

**Date:** YYYY-MM-DD.
**Source slice:** <slice-id or commit hash>.

<2-5 paragraphs explaining: what was discovered, why it matters, how to
apply the rule, what edge cases are still open. Cite file:line references
where applicable.>

**Rule:** <one-sentence summary, same as the heading subtitle>.
```

---

<a id="1"></a>
## 1. `@s4tk` reads EA-App-macOS FullBuild donors via the buffer path — `extractResources` filter+limit, not `Package.from`; read-only

**Date:** 2026-06-17.
**Source slice:** 1.1 / S1b donor-scan (`src/donor/scan.ts`).

`@s4tk/models@0.6.14` reads the EA-App-macOS Sims 4 donors fine on Apple Silicon (install
`/Applications/EA Games/The Sims 4.app`; donors `Contents/Data/{Client,Simulation}/*FullBuild*.package`,
~719 MB–1 GB each). The make-or-break for a 1 GB package is **how** you read it:

- **DON'T `Package.from(buffer)`** the whole package — it materializes every resource as a model (memory
  blowup on a 1 GB FullBuild).
- **DO `extractResourcesAsync(buffer, {resourceFilter, limit})`** — a filter+limit decodes **only the
  matched resources** (e.g. OBJDs). The only large allocation is the transient `readFile` Buffer
  (~719 MB, freed after); `readFile` ~275 ms + filtered-OBJD decode ~3 ms. Resource types come from
  `BinaryResourceType` enums — never hand-roll DBPF/TGI ids.

**`@s4tk`'s memory-bounded MMAP path (`streamResources`) needs `@s4tk/plugin-bufferfromfile`, whose
native `.node` does NOT build on this macOS setup** (custom Makefile/`step` build, not node-gyp;
`allowBuilds` + `pnpm rebuild` don't produce it). The buffer path sidesteps it; the MMAP path is a
**Phase-5 production optimization** (under concurrency, N × ~719 MB transient buffers is the cost the
MMAP path avoids).

**Donor access is READ-ONLY (safety rule 4):** use `@s4tk` *read* APIs only — never a `.save()`/write on
the game's packages; the game files are immutable inputs. Writes go only to a sidecar scratch dir
(rule 3; randomized `mkdtemp` + `0o600`). The scan only *reads* + writes scratch — the atomic-export
safety path is the clone's (S1b-clone / spikes-004).

**Rule:** read a 1 GB+ Sims donor with `@s4tk` via `extractResources(filter, limit)` (decodes only
matched resources), not `Package.from`; donors are read-only (read APIs only, never write the game
packages); the MMAP memory-bounded path is a Phase-5 native-build optimization. **Enforcement:**
`pin: workers/export/test/donor/scan.test.ts` + the forbidden-grep rules 2/3 (no DB/canonical writes;
no Mods-folder write); donor-read-only is by-construction (read APIs only).
