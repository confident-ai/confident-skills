# Langfuse SDK v4

Applies to Python `langfuse>=4` and TypeScript `@langfuse/tracing` v4 or v5.
Check TypeScript with `npm ls @langfuse/tracing`.

Both run on OpenTelemetry. confident-trace speaks the same protocol, so the
switch replaces the Langfuse client setup with `init()`, renames the decorator,
and keeps every span the app emits today.

## Methods

| Method | Available |
| --- | --- |
| Full switch to confident-trace | Yes, Python and TypeScript |
| OpenTelemetry exporter on Langfuse | Yes, Python and TypeScript |

## Full Switch

1. Install confident-trace and call `init()` once (see `common.md`). In
   TypeScript, `init()` replaces the `NodeSDK` and `LangfuseSpanProcessor`
   setup.
2. Replace `langfuse.openai` (Python) and `observeOpenAI` from
   `@langfuse/openai` (TypeScript) with the plain OpenAI client.
3. Rename `@observe` to `@span` and `observe(fn, { name })` to
   `span({ name }, fn)`. `start_as_current_observation()` becomes
   `with span("..."):` and `startActiveObservation()` becomes `withSpan()`.
4. Move every call that sets trace fields (name, user ID, session ID, tags,
   metadata, input, output) onto `update_trace()` (`updateTrace()`). Session ID
   becomes `thread_id` (`threadId`).
5. Move span and generation updates, such as `update_current_span()` and
   `updateActiveObservation()`, onto `update_span()` (`updateSpan()`).
6. Drop generations around covered model calls. Keep an LLM span for the rest
   (see `common.md`).
7. Replace `LangfuseMedia` with `Media`. In TypeScript,
   `new LangfuseMedia({ source: "bytes", contentBytes, contentType })` from
   `@langfuse/core` becomes `Media.fromBytes(contentBytes, contentType)`.
8. Remove the Langfuse `CallbackHandler` from LangChain callbacks.
9. Replace the Langfuse flush calls with `flush()` and `tracing.shutdown()`.

### Example

```typescript
// Before (Langfuse v4/v5)
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { observeOpenAI } from "@langfuse/openai";
import { observe } from "@langfuse/tracing";
import OpenAI from "openai";

const sdk = new NodeSDK({ spanProcessors: [new LangfuseSpanProcessor()] });
sdk.start();
const openai = observeOpenAI(new OpenAI());

const answer = observe(
  async (question: string) => {
    const response = await openai.chat.completions.create({
      model: "gpt-4.1-mini",
      messages: [{ role: "user", content: question }],
    });
    return response.choices[0].message.content;
  },
  { name: "answer" },
);
```

```typescript
// After (confident-trace)
import { init, span } from "confident-trace";
import OpenAI from "openai";

const tracing = init();
const client = new OpenAI();

const answer = span({ name: "answer" }, async (question: string) => {
  const response = await client.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [{ role: "user", content: question }],
  });
  return response.choices[0].message.content;
});
```

Python follows the v3 pattern: `from langfuse import observe` and
`@observe()` become `from confident_trace import span` and `@span`. See the
example in `langfuse-v3.md`.

## OpenTelemetry Method

Add a Confident AI exporter next to the Langfuse one. `observe` decorators,
OpenAI wrappers, and trace updates stay as they are.

Tell the user these limits before using it:

- Python: the Langfuse keys must stay set, or Langfuse creates no spans.
- Python: `LANGFUSE_SAMPLE_RATE` and the `mask` function passed to
  `Langfuse()` also shape what Confident AI receives.
- TypeScript: `mask` belongs to `LangfuseSpanProcessor`, so data masked for
  Langfuse reaches Confident AI unmasked. Mask it in the app before it reaches
  the span, or use the full switch.
- TypeScript: the exporter goes on the Node SDK or tracer provider the app
  already configures for `LangfuseSpanProcessor`.
- Langfuse uploads `LangfuseMedia` and base64 media to its own storage, and in
  Python keeps uploading after the Langfuse export stops. Confident AI
  receives the audio as text.
- Scores, prompts, and datasets are not sent over OpenTelemetry.
- Every span on the provider is exported, including HTTP client and database
  spans from other instrumentations.

### Add the exporter

```python
# Python: the OTLP exporter already ships with Langfuse v4
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

If the app passes its own `tracer_provider` to `Langfuse()`, add the processor
to that provider instead.

```bash
npm install @opentelemetry/exporter-trace-otlp-proto @opentelemetry/sdk-trace-base
```

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";

const sdk = new NodeSDK({
  spanProcessors: [
    new LangfuseSpanProcessor(),
    new BatchSpanProcessor(
      new OTLPTraceExporter({
        url: "https://otel.confident-ai.com/v1/traces",
        headers: { "x-confident-api-key": process.env.CONFIDENT_API_KEY! },
      }),
    ),
  ],
});
sdk.start();
```

If the app sets an isolated provider with `setLangfuseTracerProvider()`, add
the processor to that provider instead. Use
`https://eu.otel.confident-ai.com/v1/traces` for EU projects, or the full
OTLP/HTTP traces URL for self-hosted.

### Stop sending to Langfuse at cut-over

```python
from langfuse import Langfuse

langfuse = Langfuse(should_export_span=lambda span: False)
```

In TypeScript, remove `new LangfuseSpanProcessor()` from `spanProcessors` and
keep the Confident AI `BatchSpanProcessor`.

### What carries over

| Langfuse | Confident AI |
| --- | --- |
| Span tree, names, timing, OpenTelemetry status | Kept as they are |
| Observation types (generation, embedding, agent, tool, retriever, and more) | Span types, with generations and embeddings as LLM spans |
| Observation input and output | Span input and output |
| Model, usage details, cost details | Model, token counts, cost per token |
| `level="ERROR"` and status message | Errored span with that error |
| Trace name, tags, metadata, input, output | The same trace fields |
| Session ID, user ID | Thread and user |
| Prompt name and version | Prompt alias and version |
| `LangfuseMedia` | Not sent. The span keeps text in its place |
| Scores, prompts, datasets | Not sent |

## Running Both

Point an OpenTelemetry Collector at both endpoints and compare before
cut-over. `CONFIDENT_OTEL_ENDPOINT` accepts a Collector URL.
