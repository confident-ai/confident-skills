# Rules for Every Langfuse Version

## Install

One package. Provider SDKs stay optional peers. `CONFIDENT_API_KEY` replaces
the Langfuse public key, secret key, and host.

```bash
# Python
pip install confident-trace
export CONFIDENT_API_KEY=...
```

```bash
# TypeScript (alpha)
npm install confident-trace
export CONFIDENT_API_KEY=...
node --import confident-trace/register dist/index.js
```

TypeScript automatic instrumentation needs both the Node preload
(`--import confident-trace/register`) and `init()`.

Uninstall `langfuse` (or `@langfuse/*`) only when no prompt, dataset, or score
calls still use it.

| Langfuse variable | Replaced by |
| --- | --- |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | `CONFIDENT_API_KEY` |
| `LANGFUSE_HOST`, `LANGFUSE_BASEURL`, `LANGFUSE_BASE_URL` | Nothing for US projects. `CONFIDENT_OTEL_ENDPOINT` for EU or self-hosted |

## Endpoints

- US projects use `https://otel.confident-ai.com/v1/traces` by default.
- EU projects set
  `CONFIDENT_OTEL_ENDPOINT="https://eu.otel.confident-ai.com/v1/traces"`.
- Self-hosted deployments set `CONFIDENT_OTEL_ENDPOINT` to their full
  OTLP/HTTP traces URL.
- `CONFIDENT_OTEL_ENDPOINT` also accepts an OpenTelemetry Collector URL. To
  compare both platforms during the switch, point a Collector at both.

## Initialize Once

Call `init()` once at startup, before provider or framework clients are
created. It replaces the Langfuse client, `langfuse.openai`, and
`observeOpenAI`.

```python
from confident_trace import init
from openai import OpenAI

init()
client = OpenAI()
```

```typescript
import { init } from "confident-trace";
import OpenAI from "openai";

const tracing = init();
const client = new OpenAI();
```

## Model Calls

- A generation around an OpenAI call (or another covered provider) is
  redundant. Remove it. Automatic instrumentation records the model, messages,
  and token usage.
- For a model call it does not cover, such as a self-hosted model behind your
  own HTTP client, use an LLM span:

```python
from confident_trace import span, update_span

with span("answer", type="llm"):
    completion, prompt_tokens, completion_tokens = call_my_model(messages)
    update_span(
        model="my-model",
        input=messages,
        output=completion,
        input_token_count=prompt_tokens,
        output_token_count=completion_tokens,
    )
```

```typescript
import { updateSpan, withSpan } from "confident-trace";

await withSpan({ name: "answer", type: "llm" }, async () => {
  const { completion, promptTokens, completionTokens } = await callMyModel(messages);
  updateSpan({
    model: "my-model",
    input: messages,
    output: completion,
    inputTokenCount: promptTokens,
    outputTokenCount: completionTokens,
  });
});
```

`update_span()` applies model and token fields only on an LLM span. On any
other span it logs a warning and skips them.

## Trace Fields

| Langfuse | confident-trace (Python) | confident-trace (TypeScript) |
| --- | --- | --- |
| Trace name | `@span(name=...)` or `update_trace(name=...)` | `span({ name }, fn)` or `updateTrace({ name })` |
| User ID | `update_trace(user_id=...)` | `updateTrace({ userId })` |
| Session ID | `update_trace(thread_id=...)` | `updateTrace({ threadId })` |
| Tags, metadata | `update_trace(tags=..., metadata=...)` | `updateTrace({ tags, metadata })` |
| Trace input, output | `update_trace(input=..., output=...)` | `updateTrace({ input, output })` |

A function's return value becomes the span output, so a trailing
`trace.update({ output })` is usually unnecessary.

## LangChain

Remove the Langfuse `CallbackHandler` from LangChain callbacks. That includes
`langfuse_context.get_current_langchain_handler()` in v2, `langfuse.langchain`
in Python v3 and later, and `langfuse-langchain` in TypeScript. `init()`
instruments LangChain directly.

## Media

`LangfuseMedia` becomes `Media` from confident-trace. Put it on a message,
next to its `role` and `content`, and the span shows a player on that message.

| Langfuse | Python | TypeScript |
| --- | --- | --- |
| Bytes and content type | `Media.from_bytes(data, "audio/wav")` | `Media.fromBytes(data, "audio/wav")` |
| File path | `Media.from_file(path)` | `Media.fromFile(path)` |
| Base64 data URI | `Media.from_data_uri(uri)` | `Media.fromDataUri(uri)` |

```python
from confident_trace import Media, span, update_span

@span
def voice_turn(audio: bytes) -> str:
    update_span(
        input={
            "role": "user",
            "content": "What's my balance?",
            "audio": Media.from_bytes(audio, "audio/wav"),
        }
    )
    return answer(audio)
```

Automatic instrumentation does not keep audio sent to a model, such as an
OpenAI `input_audio` part. Add it to a message with `Media` as well.

## Flush and Shutdown

| Langfuse | confident-trace |
| --- | --- |
| `langfuse.flush()`, `langfuse_context.flush()`, `get_client().flush()` | `flush()` |
| `await langfuse.shutdownAsync()` | `await tracing.shutdown()` |

Finish active work and streams before flushing or shutting down.
