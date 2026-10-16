# Langfuse SDK v3

Applies to Python `langfuse>=3,<4` (last release 3.15.0) and TypeScript
`langfuse@3` (last release 3.39.2).

Langfuse **Python** v3 runs on OpenTelemetry. Langfuse **TypeScript** v3 still
sends traces through the Langfuse ingestion API.

## Methods

| Method | Available |
| --- | --- |
| Full switch to confident-trace | Yes, Python and TypeScript |
| OpenTelemetry exporter on Langfuse | Python only. Not available in TypeScript v3 |

## Full Switch

1. Install confident-trace and call `init()` once (see `common.md`).
2. Replace `langfuse.openai` (Python) and `observeOpenAI(new OpenAI())`
   (TypeScript) with the plain OpenAI client.
3. Rename `@observe()` to `@span`. `with langfuse.start_as_current_span(name="...")`
   becomes `with span("..."):`. In TypeScript, a `trace.span()` opened and ended
   by hand becomes a `span` function.
4. Move `get_client().update_current_trace()` and `langfuse.trace()` fields
   onto `update_trace()` (`updateTrace()`). `session_id` becomes `thread_id`
   (`threadId`).
5. Move `update_current_span()`, `update_current_generation()`, and
   `span.update()` onto `update_span()` (`updateSpan()`).
6. Drop `@observe(as_type="generation")` and TypeScript generations around
   covered model calls. Keep an LLM span for the rest, passing what was in
   `usage_details` (`usageDetails`) as token counts (see `common.md`).
7. Replace `LangfuseMedia` with `Media`. In TypeScript,
   `new LangfuseMedia({ contentBytes, contentType })` becomes
   `Media.fromBytes()`.
8. Remove the Langfuse `CallbackHandler` (`langfuse.langchain` in Python,
   `langfuse-langchain` in TypeScript) from LangChain callbacks.
9. Replace `get_client().flush()` with `flush()` and
   `langfuse.shutdownAsync()` with `tracing.shutdown()`.

### Example

```python
# Before (Langfuse v3)
from langfuse import get_client, observe

langfuse = get_client()

@observe()
def support_chat(question: str) -> str:
    langfuse.update_current_trace(
        name="support-chat",
        user_id="user-7",
        session_id="session-42",
        tags=["support"],
        metadata={"plan": "enterprise"},
    )
    langfuse.update_current_span(metadata={"region": "EU"})
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

The TypeScript v3 client API matches v2. Follow the TypeScript example in
`langfuse-v2.md`.

## OpenTelemetry Method (Python Only)

Langfuse Python v3 creates spans on the global tracer provider. Add a Confident
AI exporter to that provider and every Langfuse span also reaches Confident AI.
`@observe`, `langfuse.openai`, and `get_client()` calls stay as they are.

Tell the user these limits before using it:

- The Langfuse keys must stay set. Without `LANGFUSE_PUBLIC_KEY` and
  `LANGFUSE_SECRET_KEY`, Langfuse creates no spans, so nothing reaches
  Confident AI either.
- `LANGFUSE_SAMPLE_RATE` and the `mask` function passed to `Langfuse()` also
  shape what Confident AI receives.
- Adding the exporter works on every v3 release. Stopping the Langfuse export
  needs 3.0.5 or later. Passing your own `tracer_provider` needs 3.2.0 or later.
- Langfuse uploads `LangfuseMedia` and base64 media to its own storage, even
  after the Langfuse export stops. Confident AI receives the audio as text.
- Scores, prompts, and datasets are not sent over OpenTelemetry.
- Every span on the provider is exported, including HTTP client and database
  spans from other instrumentations.

### Add the exporter

The OTLP exporter already ships with Langfuse v3.

```python
import os

from langfuse import get_client
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

langfuse = get_client()

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint="https://otel.confident-ai.com/v1/traces",
            headers={"x-confident-api-key": os.environ["CONFIDENT_API_KEY"]},
        )
    )
)
```

Use `https://eu.otel.confident-ai.com/v1/traces` for EU projects, or the full
OTLP/HTTP traces URL for self-hosted. If the app passes its own
`tracer_provider` to `Langfuse()`, add the processor to that provider instead.

### Stop sending to Langfuse at cut-over

```python
from langfuse import Langfuse

langfuse = Langfuse(blocked_instrumentation_scopes=["langfuse-sdk"])
```

Spans are still created and still reach Confident AI.

### What carries over

| Langfuse | Confident AI |
| --- | --- |
| Span tree, names, timing, OpenTelemetry status | Kept as they are |
| Observation types | Span types, with generations as LLM spans |
| Observation input and output | Span input and output |
| Model, usage details, cost details | Model, token counts, cost per token |
| `level="ERROR"` and status message | Errored span with that error |
| Trace name, tags, metadata, input, output | The same trace fields |
| `session_id`, `user_id` | Thread and user |
| Prompt name and version | Prompt alias and version |
| `LangfuseMedia` | Not sent. The span keeps text in its place |
| Scores, prompts, datasets | Not sent |

## Field Mapping

### Python

| Langfuse v3 | confident-trace |
| --- | --- |
| `get_client()` | `init()` |
| `@observe()` | `@span` |
| `@observe(as_type="generation")` | Automatic instrumentation, or `@span(type="llm")` |
| `start_as_current_span(name=...)` | `with span("..."):` |
| `update_current_trace(name=..., user_id=...)` | `update_trace(name=..., user_id=...)` |
| `update_current_trace(session_id=...)` | `update_trace(thread_id=...)` |
| `update_current_trace(tags=..., metadata=...)` | `update_trace(tags=..., metadata=...)` |
| `update_current_span(input=..., output=..., metadata=...)` | `update_span(input=..., output=..., metadata=...)` |
| `update_current_generation(model=...)` | `update_span(model=...)` |
| `update_current_generation(usage_details={"input": ..., "output": ...})` | `update_span(input_token_count=..., output_token_count=...)` |
| `LangfuseMedia(content_bytes=..., content_type=...)` | `Media.from_bytes(..., ...)` |
| `LangfuseMedia(file_path=...)` | `Media.from_file(...)` |
| `LangfuseMedia(base64_data_uri=...)` | `Media.from_data_uri(...)` |
| `get_client().flush()` | `flush()` |

### TypeScript

| Langfuse v3 | confident-trace |
| --- | --- |
| `new Langfuse()` | `init()` |
| `observeOpenAI(new OpenAI())` | `new OpenAI()` with automatic instrumentation |
| `langfuse.trace({ name, userId })` | `span({ name }, fn)` and `updateTrace({ userId })` |
| `langfuse.trace({ sessionId })` | `updateTrace({ threadId })` |
| `langfuse.trace({ tags, metadata })` | `updateTrace({ tags, metadata })` |
| `trace.update({ input, output })` | `updateTrace({ input, output })` |
| `trace.span({ name })` | `span({ name }, fn)` or `withSpan({ name }, fn)` |
| `span.update({ input, output, metadata })` | `updateSpan({ input, output, metadata })` |
| `trace.generation({ model, input })` | Automatic instrumentation, or `withSpan({ type: "llm" }, fn)` with `updateSpan({ model, input })` |
| `usageDetails: { input, output }` | `updateSpan({ inputTokenCount, outputTokenCount })` |
| `new LangfuseMedia({ contentBytes, contentType })` | `Media.fromBytes(contentBytes, contentType)` |
| `new LangfuseMedia({ base64DataUri })` | `Media.fromDataUri(base64DataUri)` |
| `await langfuse.shutdownAsync()` | `await tracing.shutdown()` |

## Running Both

In Python, point an OpenTelemetry Collector at both endpoints and compare
before cut-over. In TypeScript, Langfuse v3 and confident-trace do not share a
client, so both can trace the same app.
