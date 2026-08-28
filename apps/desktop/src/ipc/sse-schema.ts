/**
 * The SSE event boundary (§4): a Zod runtime validator for the frozen 8-event discriminated union.
 *
 * The *types* come from the generated contract (root CLAUDE.md "import the generated type, don't
 * duplicate"); Zod is purely the *runtime* validator. A static parity manifest (below) pins the
 * Zod-inferred output to the generated members + their domain enums, so the validator cannot drift
 * from the frozen type — `pnpm typecheck` fails if it does. The `error` branch routes `code`
 * through `parseErrorCode` (carry-forward 0.2/D10b: unknown code → SYSTEM).
 */
import { z } from "zod";

import { parseErrorCode } from "../../../../packages/contracts/generated/helpers";
import type {
  CostEvent,
  DoneEvent,
  ErrorCategory,
  ErrorEvent,
  GateKind,
  GateNeededEvent,
  LogEvent,
  LogLevel,
  ProgressEvent,
  Severity,
  StepState,
  StepStateEvent,
  ValidationEvent,
  ValidationScope,
} from "../../../../packages/contracts/generated/contracts";

// --- domain/protocol enums (mirror the generated string-literal unions; pinned by the manifest) ---
const stepStateEnum = z.enum([
  "pending",
  "running",
  "succeeded",
  "failed",
  "waiting-for-user",
  "cancelled",
  "retrying",
  "skipped",
]);
const doneStatusEnum = z.enum(["succeeded", "failed", "cancelled"]);
const severityEnum = z.enum(["error", "warn", "info", "pass"]);
const validationScopeEnum = z.enum(["project", "item", "mesh", "overlay", "export"]);
const gateKindEnum = z.enum(["plan", "concept", "mesh", "overlay", "export"]);
const logLevelEnum = z.enum(["debug", "info", "warning", "error"]);
const errorCategoryEnum = z.enum([
  "provider",
  "network",
  "validation",
  "geometry",
  "packaging",
  "budget",
  "system",
]);

const errorEnvelopeSchema = z
  .object({
    category: errorCategoryEnum,
    // Strict producer / tolerant consumer: accept any string, degrade unknown → SYSTEM (D10b).
    code: z.string().transform(parseErrorCode),
    creatorMessage: z.string(),
    maintainerDetail: z.string(),
    retryable: z.boolean(),
    suggestedAction: z.string().nullish(),
    traceRef: z.string().nullish(),
  })
  .strict();

const progressSchema = z
  .object({
    event: z.literal("progress"),
    id: z.string(),
    runId: z.string(),
    fraction: z.number(),
    message: z.string().nullish(),
  })
  .strict();

const stepStateSchema = z
  .object({
    event: z.literal("step-state"),
    id: z.string(),
    runId: z.string(),
    stepId: z.string(),
    status: stepStateEnum,
  })
  .strict();

const logSchema = z
  .object({
    event: z.literal("log"),
    id: z.string(),
    level: logLevelEnum,
    message: z.string(),
    stepId: z.string().nullish(),
  })
  .strict();

const validationSchema = z
  .object({
    event: z.literal("validation"),
    id: z.string(),
    scope: validationScopeEnum,
    severity: severityEnum,
    message: z.string(),
    itemId: z.string().nullish(),
  })
  .strict();

const costSchema = z
  .object({
    event: z.literal("cost"),
    id: z.string(),
    runId: z.string(),
    amountCents: z.number(),
    currency: z.string().optional(),
  })
  .strict();

const gateNeededSchema = z
  .object({
    event: z.literal("gate-needed"),
    id: z.string(),
    runId: z.string(),
    gate: gateKindEnum,
    itemId: z.string().nullish(),
  })
  .strict();

const doneSchema = z
  .object({
    event: z.literal("done"),
    id: z.string(),
    runId: z.string(),
    status: doneStatusEnum,
  })
  .strict();

const errorSchema = z
  .object({
    event: z.literal("error"),
    id: z.string(),
    error: errorEnvelopeSchema,
    runId: z.string().nullish(),
    stepId: z.string().nullish(),
  })
  .strict();

export const sseEventSchema = z.discriminatedUnion("event", [
  progressSchema,
  stepStateSchema,
  logSchema,
  validationSchema,
  costSchema,
  gateNeededSchema,
  doneSchema,
  errorSchema,
]);

export type SseEvent = z.infer<typeof sseEventSchema>;

/** The 8 frozen SSE event tags — runtime side of the parity guard (RED #9). */
export const SSE_EVENT_TAGS = [
  "progress",
  "step-state",
  "log",
  "validation",
  "cost",
  "gate-needed",
  "done",
  "error",
] as const;
export type SseEventTag = (typeof SSE_EVENT_TAGS)[number];

/** Validate a decoded SSE payload into its typed branch; throws on unknown tag / malformed frame. */
export function parseSseEvent(data: unknown): SseEvent {
  return sseEventSchema.parse(data);
}

// ============================================================================================
// Compile-time parity manifest (RED #9). Type-only — erased at emit; `pnpm typecheck` enforces it.
// `Equals` pins each domain enum exactly to the generated union; reverse-assignability pins each
// branch's payload (sans the `event` discriminator) so a generated field add/remove/retype fails to
// compile. Full forward parity isn't asserted on purpose: `exactOptionalPropertyTypes` makes the
// `?: T | null` vs `T | null | undefined` shapes diverge harmlessly. Behavioral field-shape is also
// covered by the runtime parse tests + the contracts CI drift gate on the generated types.
// ============================================================================================
type Equals<A, B> =
  (<T>() => T extends A ? 1 : 2) extends <T>() => T extends B ? 1 : 2 ? true : false;
type AssignableTo<Sub, Sup> = [Sub] extends [Sup] ? true : false;
type Assert<T extends true> = T;

type GeneratedSseMember =
  | ProgressEvent
  | StepStateEvent
  | LogEvent
  | ValidationEvent
  | CostEvent
  | GateNeededEvent
  | DoneEvent
  | ErrorEvent;
type GeneratedTag = NonNullable<GeneratedSseMember["event"]>;

export type _SseSchemaParity = [
  // Domain/protocol enum parity (the D15-tightened drift-prone surface).
  Assert<Equals<z.infer<typeof stepStateEnum>, StepState>>,
  Assert<Equals<z.infer<typeof doneStatusEnum>, DoneEvent["status"]>>,
  Assert<Equals<z.infer<typeof severityEnum>, Severity>>,
  Assert<Equals<z.infer<typeof validationScopeEnum>, ValidationScope>>,
  Assert<Equals<z.infer<typeof gateKindEnum>, GateKind>>,
  Assert<Equals<z.infer<typeof logLevelEnum>, LogLevel>>,
  Assert<Equals<z.infer<typeof errorCategoryEnum>, ErrorCategory>>,
  // Tag-set parity: the runtime tag list ≡ the schema tags ≡ the generated member tags.
  Assert<Equals<SseEventTag, GeneratedTag>>,
  Assert<Equals<SseEvent["event"], GeneratedTag>>,
  // Per-branch payload parity (generated payload ⊆ parsed payload, discriminator removed).
  Assert<AssignableTo<Omit<ProgressEvent, "event">, Omit<z.infer<typeof progressSchema>, "event">>>,
  Assert<
    AssignableTo<Omit<StepStateEvent, "event">, Omit<z.infer<typeof stepStateSchema>, "event">>
  >,
  Assert<AssignableTo<Omit<LogEvent, "event">, Omit<z.infer<typeof logSchema>, "event">>>,
  Assert<
    AssignableTo<Omit<ValidationEvent, "event">, Omit<z.infer<typeof validationSchema>, "event">>
  >,
  Assert<AssignableTo<Omit<CostEvent, "event">, Omit<z.infer<typeof costSchema>, "event">>>,
  Assert<
    AssignableTo<Omit<GateNeededEvent, "event">, Omit<z.infer<typeof gateNeededSchema>, "event">>
  >,
  Assert<AssignableTo<Omit<DoneEvent, "event">, Omit<z.infer<typeof doneSchema>, "event">>>,
  Assert<AssignableTo<Omit<ErrorEvent, "event">, Omit<z.infer<typeof errorSchema>, "event">>>,
];
