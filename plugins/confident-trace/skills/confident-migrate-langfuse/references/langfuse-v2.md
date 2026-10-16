# Langfuse SDK v2

Applies to Python `langfuse>=2,<3` (last release 2.60.10) and TypeScript
`langfuse@2` (last release 2.8.0).

Langfuse v2 sends traces through its own ingestion API, not OpenTelemetry. In
Python the decorator API maps one to one: `@observe()` becomes `@span` and
`langfuse_context` becomes `update_trace()` and `update_span()`. In TypeScript
the client's traces, spans, and generations become `span`, `updateTrace()`, and
automatic instrumentation.

## Methods

| Method | Available |
| --- | --- |
| Full switch to confident-trace | Yes, Python and TypeScript |
| OpenTelemetry exporter on Langfuse | No. v2 is not OpenTelemetry |

## Steps

1. Install confident-trace and call `init()` once (see `common.md`).
2. Replace traced OpenAI calls with the plain client.
   - Python: drop `from langfuse.openai import openai`.
   - TypeScript: v2 has no OpenAI integration. Remove the generation you
     wrapped around each call.
3. Rename `@observe()` to `@span` and `@observe(name="...")` to
   `@span(name="...")`. In TypeScript, a `trace.span()` opened and ended by
   hand becomes a `span` function.
4. Move `langfuse_context.update_current_trace()` and `langfuse.trace()` fields
   onto `update_trace()` (`updateTrace()`). `session_id` becomes `thread_id`
   (`threadId`).
5. Move `langfuse_context.update_current_observation()` and `span.update()`
   onto `update_span()` (`updateSpan()`).
6. Drop `@observe(as_type="generation")` and TypeScript generations around
   covered model calls. Keep an LLM span for the rest (see `common.md`).
7. Replace `LangfuseMedia` with `Media` (Python only; TypeScript v2 has no
   `LangfuseMedia`).
8. Remove the Langfuse `CallbackHandler`, or
   `langfuse_context.get_current_langchain_handler()`, from LangChain
   callbacks.
9. Replace `langfuse_context.flush()` with `flush()` and
   `langfuse.shutdownAsync()` with `tracing.shutdown()`.

## Example

```python
# Before (Langfuse v2)
from langfuse.decorators import langfuse_context, observe

@observe()
def support_chat(question: str) -> str:
    langfuse_context.update_current_trace(
        name="support-chat",
        user_id="user-7",
        session_id="session-42",
        tags=["support"],
        metadata={"plan": "enterprise"},
    )
    langfuse_context.update_current_observation(metadata={"region": "EU"})
    return answer(question)
```

```python
# After (confident-trace)
from confident_trace import span, update_span, update_trace

@span
def support_chat(question: str) -> str:
    update_trace(
        name="support-chat",
        user_id="user-7",
        thread_id="session-42",
        tags=["support"],
        metadata={"plan": "enterprise"},
    )
    update_span(metadata={"region": "EU"})
    return answer(question)
```

```typescript
// Before (Langfuse v2)
async function supportChat(question: string) {
  const trace = langfuse.trace({
    name: "support-chat",
    userId: "user-7",
    sessionId: "session-42",
    tags: ["support"],
    metadata: { plan: "enterprise" },
  });
  const span = trace.span({ name: "handle", metadata: { region: "EU" } });
  const output = await answer(trace, question);
  span.end({ output });
  trace.update({ output });
  return output;
}
```

```typescript
// After (confident-trace)
import { span, updateSpan, updateTrace } from "confident-trace";

const supportChat = span({ name: "support-chat" }, async (question: string) => {
  updateTrace({
    userId: "user-7",
    threadId: "session-42",
    tags: ["support"],
    metadata: { plan: "enterprise" },
  });
  updateSpan({ metadata: { region: "EU" } });
  return answer(question);
});
```

## Field Mapping

### Python

| Langfuse v2 | confident-trace |
| --- | --- |
| `@observe()` | `@span` |
| `@observe(as_type="generation")` | Automatic instrumentation, or `@span(type="llm")` |
| `update_current_trace(name=...)` | `update_trace(name=...)` |
| `update_current_trace(user_id=...)` | `update_trace(user_id=...)` |
| `update_current_trace(session_id=...)` | `update_trace(thread_id=...)` |
| `update_current_trace(tags=..., metadata=...)` | `update_trace(tags=..., metadata=...)` |
| `update_current_trace(input=..., output=...)` | `update_trace(input=..., output=...)` |
| `update_current_observation(input=..., output=..., metadata=...)` | `update_span(input=..., output=..., metadata=...)` |
| `update_current_observation(model=...)` | `update_span(model=...)` |
| `update_current_observation(usage_details={"input": ..., "output": ...})` | `update_span(input_token_count=..., output_token_count=...)` |
| `LangfuseMedia(content_bytes=..., content_type=...)` | `Media.from_bytes(..., ...)` |
| `LangfuseMedia(file_path=...)` | `Media.from_file(...)` |
| `LangfuseMedia(base64_data_uri=...)` | `Media.from_data_uri(...)` |
| `langfuse_context.flush()` | `flush()` |

### TypeScript

| Langfuse v2 | confident-trace |
| --- | --- |
| `new Langfuse()` | `init()` |
| `langfuse.trace({ name })` | `span({ name }, fn)` or `updateTrace({ name })` |
| `langfuse.trace({ userId })` | `updateTrace({ userId })` |
| `langfuse.trace({ sessionId })` | `updateTrace({ threadId })` |
| `langfuse.trace({ tags, metadata })` | `updateTrace({ tags, metadata })` |
| `trace.update({ input, output })` | `updateTrace({ input, output })` |
| `trace.span({ name })` | `span({ name }, fn)` or `withSpan({ name }, fn)` |
| `span.update({ input, output, metadata })` | `updateSpan({ input, output, metadata })` |
| `trace.generation({ model, input })` | Automatic instrumentation, or `withSpan({ type: "llm" }, fn)` with `updateSpan({ model, input })` |
| `usage: { input, output }` | `updateSpan({ inputTokenCount, outputTokenCount })` |
| `await langfuse.shutdownAsync()` | `await tracing.shutdown()` |

## Running Both

Langfuse v2 and confident-trace do not share a client, so both can trace the
same app while the user compares. Remove the Langfuse calls at cut-over.
