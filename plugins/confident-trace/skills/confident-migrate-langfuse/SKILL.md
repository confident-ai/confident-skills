---
name: confident-migrate-langfuse
description: >
  Migrate an AI application's tracing from Langfuse to Confident AI with the
  confident-trace SDK. TRIGGER when the user wants to switch, move, or migrate
  from Langfuse to Confident AI; replace @observe, langfuse_context,
  get_client(), langfuse.trace(), trace.generation(), langfuse.openai,
  observeOpenAI, LangfuseMedia, LangfuseSpanProcessor, or the Langfuse
  LangChain CallbackHandler with confident-trace; or export the spans Langfuse
  already emits to Confident AI over OpenTelemetry. Covers Langfuse SDK v1, v2,
  v3, and v4 (TypeScript v4 and v5) in Python and TypeScript. DO NOT TRIGGER
  for new instrumentation in an app with no Langfuse code (use the
  `confident-tracing` skill) or for raw OpenTelemetry export without a
  Langfuse SDK (use the `confident-otel` skill).
license: Apache-2.0
metadata:
  author: Confident AI
  version: "1.0.0"
  category: observability
  tags: "langfuse, migration, confident-trace, tracing, opentelemetry"
  compatibility: "Python 3.10+ or Node.js 22+. Requires CONFIDENT_API_KEY. confident-trace for TypeScript is an alpha release."
---

# Migrate from Langfuse

Use this skill to move an AI application's tracing from **Langfuse** to
**Confident AI**. The target is the **confident-trace** SDK: `init()` for
automatic instrumentation, `span` for your own steps, and `update_trace()` /
`update_span()` for trace and span fields.

What changes depends on the **Langfuse SDK version in the app**, not the
Langfuse server version. Each version has its own reference file.

## Workflow

1. **Find every Langfuse integration.** Search for imports of `langfuse` and
   `@langfuse/*`, `Langfuse()` and `new Langfuse()`, `@observe` and
   `observe()`, `langfuse_context`, `get_client()`, `langfuse.trace()`,
   `trace.span()`, `trace.generation()`, `start_as_current_span()`,
   `start_as_current_observation()`, `startActiveObservation()`,
   `langfuse.openai`, `observeOpenAI`, `LangfuseMedia`,
   `LangfuseSpanProcessor`, the Langfuse `CallbackHandler`, and `LANGFUSE_*`
   environment variables or keys passed in code.
2. **Confirm the installed SDK version.** Run `pip show langfuse`,
   `npm ls langfuse`, or `npm ls @langfuse/tracing`. Python and TypeScript
   services in one repo can be on different versions, so check each one.
3. **Read the reference for that version.**

   | Installed SDK | Reference |
   | --- | --- |
   | Python `langfuse<2`, TypeScript `langfuse@1` | `references/langfuse-v1.md` |
   | Python `langfuse>=2,<3`, TypeScript `langfuse@2` | `references/langfuse-v2.md` |
   | Python `langfuse>=3,<4`, TypeScript `langfuse@3` | `references/langfuse-v3.md` |
   | Python `langfuse>=4`, TypeScript `@langfuse/tracing` v4 or v5 | `references/langfuse-v4.md` |

   There is no need to upgrade Langfuse first. Every version moves straight to
   confident-trace.
4. **Pick the method.** Default to the full switch: replace the Langfuse SDK
   with confident-trace. Use the OpenTelemetry method only when the user asks
   to keep Langfuse instrumentation in place, and only where the reference
   says it is available. Tell the user its limits before you start.
5. **Make the changes** in the order the reference gives. Read
   `references/common.md` for the install, endpoint, LangChain, media, and
   flush rules that apply to every version.
6. **Preserve behavior.** Keep the same span names, nesting, inputs, outputs,
   users, sessions, tags, and metadata. A Langfuse session ID becomes a
   confident-trace thread ID.
7. **Leave prompt, dataset, and score calls alone.** Calls such as
   `get_prompt()`, `create_dataset()`, `create_dataset_item()`, and `score()`
   use the Langfuse API, not tracing. Do not delete or rewrite them. List them
   for the user. If any remain, keep the `langfuse` package installed and
   remove only the tracing code.
8. **Verify.** Run the app once and confirm the trace appears in the
   project's Observatory. If it does not, check that `CONFIDENT_API_KEY` is set
   in the same process and that the app flushes before it exits.
9. **Report.** Summarize every change. List what still needs the user:
   setting `CONFIDENT_API_KEY`, the EU or self-hosted endpoint, model calls you
   could not map, and the prompt, dataset, and score calls you left in place.
   Confident AI can import Langfuse datasets, prompts, and historical scores
   on a migration call.

## Core Principles

1. Match the reference to the installed SDK version. Stop and ask if the
   version is unclear or outside v1 to v4.
2. Let `init()` replace provider wrappers and generations around covered model
   calls. Do not wrap a call that automatic instrumentation already records.
3. Keep an LLM span (`span(type="llm")` with `update_span()`) only for model
   calls that automatic instrumentation does not cover.
4. Never trace secrets or credentials. Carry over any masking the app did
   through Langfuse.
5. For instrumentation beyond a one-to-one migration, such as a framework
   integration the app did not use before, use the `confident-tracing` skill.

## References

| Topic | File |
| --- | --- |
| Install, endpoints, LangChain, media, and flush rules for every version | `references/common.md` |
| Langfuse SDK v1 | `references/langfuse-v1.md` |
| Langfuse SDK v2 | `references/langfuse-v2.md` |
| Langfuse SDK v3, including the Python OpenTelemetry method | `references/langfuse-v3.md` |
| Langfuse SDK v4 (TypeScript v4 and v5), including the OpenTelemetry method | `references/langfuse-v4.md` |
