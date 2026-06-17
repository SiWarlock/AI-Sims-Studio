---
description: Look up a topic in the architecture lookup table and read only that section. Usage: /check-arch <topic>
allowed-tools: Read, Grep
argument-hint: "<topic>"
---

Look up a topic in the area `CLAUDE.md` lookup table and read **only that section** of the cited file (`Read` with `offset`/`limit`). Context-efficiency primitive.

Argument: `$ARGUMENTS` — the topic to look up.

**Area-resolved lookup table.** `/check-arch` reads the lookup table in the `CLAUDE.md` of your current code area; resolve it from your cwd basename:

```bash
case "$(basename "$PWD")" in
  desktop)   AREA_CLAUDE="apps/desktop/CLAUDE.md" ;;
  pipeline)  AREA_CLAUDE="services/pipeline/CLAUDE.md" ;;
  export)    AREA_CLAUDE="workers/export/CLAUDE.md" ;;
  blender)   AREA_CLAUDE="workers/blender/CLAUDE.md" ;;
  contracts) AREA_CLAUDE="packages/contracts/CLAUDE.md" ;;
  evals)     AREA_CLAUDE="evals/CLAUDE.md" ;;
  *) echo "Unknown area cwd: $PWD — run /check-arch from a code-area directory"; exit 1 ;;
esac
```

## Procedure

1. Read the lookup table in `$AREA_CLAUDE` (top section, near "Lookup table — where to find canonical info").

2. Find the row matching `$ARGUMENTS`. Match flexibly — partial keyword match, case-insensitive.

3. If a match is found:
   - Read only the cited section of the cited file (use `Read` with `offset` + `limit` to read just that section).
   - Report the section content + its file:section reference.

4. If no match is found:
   - Fall back to `grep` across `ARCHITECTURE.md` for the topic keyword.
   - Report the best matches with file:line references.
   - **Recommend adding a row to the lookup table** if the topic will recur.

## Output format

```
Topic: <argument>
Source: <file>:§<section>

<section content — abbreviated to ~50 lines max; cite further reads if needed>
```

If fallback grep was used:

```
Topic: <argument> (no lookup-table match)
Grep matches:
- <file>:<line> — <snippet>

Recommendation: add a row to the $AREA_CLAUDE lookup table:
| <topic> | <file> | §<section> |
```

## Forbidden in this command

- **Loading the entire `ARCHITECTURE.md`.** The whole point is targeted reads.
- **Inferring sections beyond what the lookup table or grep surfaces.** If a topic isn't documented, say so; don't fabricate.
