# Langfuse SDK v1

Applies to Python `langfuse<2` (last release 1.14.0) and TypeScript
`langfuse@1` (last release 1.3.0).

Langfuse v1 sends traces through its own ingestion API, not OpenTelemetry. Each
trace is built by hand: a client, a trace, then a span or generation for every
step. confident-trace replaces those objects with OpenTelemetry spans.

## Methods

| Method | Available |
| --- | --- |
| Full switch to confident-trace | Yes, Python and TypeScript |
| OpenTelemetry exporter on Langfuse | No. v1 is not OpenTelemetry |

## Steps

1. Install confident-trace and call `init()` once (see `common.md`).
2. Replace traced OpenAI calls with the plain client.
   - Python: drop `from langfuse.openai import openai`.
   - TypeScript: v1 has no OpenAI integration. Remove the generation you
     wrapped around each call.
3. Replace `langfuse.trace()` with `span` on the traced function and
   `update_trace()` for its fields. `sessionId` becomes `thread_id`
   (`threadId`).
4. Replace `trace.span()` with `span`, a `with span("name"):` block, or
   `withSpan()` in TypeScript.
5. Drop generations around covered model calls. Keep an LLM span for the rest
   (see `common.md`).
6. Remove the Langfuse `CallbackHandler` from LangChain callbacks.
7. Replace `langfuse.flush()` with `flush()` and `langfuse.shutdownAsync()`
   with `tracing.shutdown()`.

## Example

```python
# Before (Langfuse v1)
from langfuse import Langfuse
from langfuse.model import CreateTrace

langfuse = Langfuse()

def support_chat(question: str) -> str:
    trace = langfuse.trace(
        CreateTrace(
            name="support-chat",
            userId="user-7",
            sessionId="session-42",
            input=question,
            metadata={"plan": "enterprise"},
        )
    )
    return openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": question}],
    ).choices[0].message.content
```

```python
# After (confident-trace)
from confident_trace import span, update_trace

@span(name="support-chat")
def support_chat(question: str) -> str:
    update_trace(
        user_id="user-7",
        thread_id="session-42",
        metadata={"plan": "enterprise"},
    )
    return client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": question}],
    ).choices[0].message.content
```

```typescript
// Before (Langfuse v1)
async function supportChat(question: string) {
  const trace = langfuse.trace({
    name: "support-chat",
    userId: "user-7",
    sessionId: "session-42",
    input: question,
    metadata: { plan: "enterprise" },
  });
  const answer = await answerQuestion(question);
  trace.update({ output: answer });
  return answer;
}
```

```typescript
// After (confident-trace)
import { span, updateTrace } from "confident-trace";

const supportChat = span({ name: "support-chat" }, async (question: string) => {
  updateTrace({
    userId: "user-7",
    threadId: "session-42",
    metadata: { plan: "enterprise" },
  });
  return answerQuestion(question);
});
```

## Field Mapping

### Python

| Langfuse v1 | confident-trace |
| --- | --- |
| `Langfuse()` | `init()` |
| `CreateTrace(name=...)` | `@span(name=...)` or `update_trace(name=...)` |
| `CreateTrace(userId=...)` | `update_trace(user_id=...)` |
| `CreateTrace(sessionId=...)` | `update_trace(thread_id=...)` |
| `CreateTrace(input=..., output=...)` | `update_trace(input=..., output=...)` |
| `CreateTrace(metadata=...)` | `update_trace(metadata=...)` |
| `CreateSpan(name=...)` | `@span` or `with span("name"):` |
| `CreateGeneration(model=..., prompt=...)` | `span(type="llm")` with `update_span(model=..., input=...)` |
| `UpdateGeneration(completion=...)` | `update_span(output=...)` |
| `Usage(promptTokens=..., completionTokens=...)` | `update_span(input_token_count=..., output_token_count=...)` |
| `langfuse.flush()` | `flush()` |

### TypeScript

| Langfuse v1 | confident-trace |
| --- | --- |
| `new Langfuse({ ... })` | `init()` |
| `langfuse.trace({ name })` | `span({ name }, fn)` or `updateTrace({ name })` |
| `langfuse.trace({ userId })` | `updateTrace({ userId })` |
| `langfuse.trace({ sessionId })` | `updateTrace({ threadId })` |
| `trace.update({ input, output })` | `updateTrace({ input, output })` |
| `langfuse.trace({ metadata })` | `updateTrace({ metadata })` |
| `trace.span({ name })` | `span({ name }, fn)` or `withSpan({ name }, fn)` |
| `trace.generation({ model, prompt })` | `withSpan({ type: "llm" }, fn)` with `updateSpan({ model, input })` |
| `generation.end({ completion })` | `updateSpan({ output })` |
| `usage: { promptTokens, completionTokens }` | `updateSpan({ inputTokenCount, outputTokenCount })` |
| `await langfuse.shutdownAsync()` | `await tracing.shutdown()` |

## Running Both

Langfuse v1 and confident-trace do not share a client, so both can trace the
same app while the user compares. Remove the Langfuse calls at cut-over.
