# Instrument the application and run a batch

Add Confident AI tracing to the AI application in the current folder, then run
it on 7 to 10 inputs. Tracing means the application's LLM calls, agent steps,
tool calls, and retrieval show up as spans in Confident AI.

Read before you write, and do not invent an API. Every name below comes from
the `confident-trace` documentation, and its README is the authority when
anything here is unclear:

- Python: https://github.com/confident-ai/confident-trace/blob/main/python/README.md
- TypeScript and JavaScript:
  https://github.com/confident-ai/confident-trace/blob/main/typescript/README.md

## Boundaries

- Keep the diff small. Tracing must not change what the application returns,
  and must not break its build, tests, or startup.
- Instrument AI components only: LLM calls, agent loops, tool calls, and
  retrieval. Do not trace web servers, databases, or other infrastructure.
- Do not refactor code that tracing does not need.

## Orient

1. Read the repository from its Git root, so a monorepo's workspaces, shared
   packages, and scripts make sense. Only instrument applications in or below
   the current folder.
2. For each application, note its language and runtime version, package
   manager, entry point, and the LLM providers and frameworks it calls, such as
   OpenAI, Anthropic, LangChain, LangGraph, LlamaIndex, CrewAI, Pydantic AI,
   the OpenAI Agents SDK, the Vercel AI SDK, or Mastra. Note whether its code
   is bundled and whether it already sets up OpenTelemetry.
3. If nothing here calls an LLM, retrieves documents, or uses tools, stop and
   tell the user.
4. Python, JavaScript, and TypeScript use `confident-trace`. Any other language
   uses OpenTelemetry.

## Python, JavaScript, and TypeScript: `confident-trace`

Install `confident-trace` as a regular dependency with the project's own
package manager. It needs Python 3.10 or newer, or Node.js 22 or newer. If the
runtime is older, do not upgrade it or force the install: stop and tell the
user the version you found.

Use the automatic integrations first. Add manual spans only where they do not
reach.

### Python

Call `init()` once at startup, before the application creates model clients:

```python
import confident_trace as ct

ct.init()
```

`init()` reads `CONFIDENT_API_KEY` from the environment and instruments the
supported SDKs that are installed: OpenAI, Anthropic, Google GenAI, Bedrock,
LangChain, LangGraph, LlamaIndex, CrewAI, Pydantic AI, Agno, smolagents, Google
ADK, Strands, LiteLLM, and the others the README lists. Do not wrap calls an
integration already covers.

The OpenAI Agents SDK needs the extra: install `confident-trace[openai-agents]`.

Python flushes spans when the interpreter exits normally. A process that exits
with `os._exit` must call `ct.shutdown()` first.

### JavaScript and TypeScript

Automatic instrumentation needs both parts:

1. `init()` once in the existing entry file, before application work:

   ```ts
   import { init } from "confident-trace";

   const tracing = init();
   ```

2. The preload, in the start command the project already uses:

   ```sh
   node --import confident-trace/register dist/index.js
   node --import tsx --import confident-trace/register src/index.ts
   ```

This covers OpenAI, Anthropic, Google GenAI, the Vercel AI SDK, LangChain,
LangGraph, Mastra, and OpenAI Agents.

The preload cannot instrument SDK code a bundler packed into the application.
A bundled application calls `init({ instrumentations: [] })` and uses the
matching manual adapter. Read its README section first.

- OpenAI: `instrumentOpenAI(client)` from `confident-trace/openai`.
- Anthropic: `instrumentAnthropic(client)` from `confident-trace/anthropic`.
- Google GenAI: `instrumentGoogleGenAI(client)` from
  `confident-trace/google-genai`.
- LangChain or LangGraph: `new ConfidentLangChainCallbackHandler()` from
  `confident-trace/langchain`, or `new ConfidentLangGraphCallbackHandler()`
  from `confident-trace/langgraph`, in the root invocation's `callbacks`.
- Vercel AI SDK: `createVercelAITracer()` from `confident-trace/vercel-ai`.
- Mastra: `new ConfidentMastraExporter()` from `confident-trace/mastra`.
- OpenAI Agents: `new ConfidentOpenAIAgentsProcessor()` from
  `confident-trace/openai-agents`, registered with `addTraceProcessor`.

JavaScript and TypeScript have no exit hook. A short-lived script must
`await tracing.shutdown()` before it exits, in a `finally` block, or its spans
are lost. A server shuts tracing down in its graceful-shutdown path, never
after each request.

### An existing OpenTelemetry setup

If the application already owns a tracer provider, keep it. In Python, pass it
to `init(tracer_provider=provider)`. In TypeScript, add `createSpanProcessor()`
from `confident-trace/otel` where the provider is built. Never register a
second global provider.

### Manual spans

Only around an entry point or component no integration sees. Span types are
`agent`, `llm`, `retriever`, `tool`, and `custom`.

```python
@ct.span(type="tool")
def lookup_order(order_id: str) -> dict: ...

with ct.span("answer", type="agent", input=question):
    ...
```

```ts
import { span, withSpan } from "confident-trace";

const lookupOrder = span({ name: "lookup_order", type: "tool" }, fetchOrder);
const answer = await withSpan({ name: "answer", type: "agent" }, async () => {
  /* ... */
});
```

### Threads and users

Only when the code already has a conversation, session, or user id. Never
invent one.

- Python: `ct.update_trace(thread_id=..., user_id=...)`, or
  `with ct.turn(thread_id=..., turn_id=...):` around each turn.
- TypeScript: `updateTrace({ threadId, userId })`, or
  `await turn({ threadId, turnId }, async () => { ... })`.

## Any other language: OpenTelemetry

Use the language's own OpenTelemetry SDK. Before writing code, open
https://www.confident-ai.com/docs/integrations/opentelemetry and confirm these
three values. If the page does not confirm all three, stop and tell the user.

- Protocol: OTLP over HTTP with protobuf. Not gRPC.
- Endpoint: the `otelEndpoint` from the helper script. Through
  `OTEL_EXPORTER_OTLP_ENDPOINT`, give the base URL without `/v1/traces`.
- Header: `x-confident-api-key`, read from `CONFIDENT_API_KEY` at runtime.

Attach the exporter through a batch span processor, wrap the AI components in
spans with `confident.span.type` (`llm`, `tool`, `agent`, `retriever`, or
`base`) and `confident.span.input` / `confident.span.output` as strings, and
flush before a short-lived process exits.

## Load the key without reading it

`confident-trace` reads `CONFIDENT_API_KEY` from the process environment. It
does not load `.env` or `.env.local`. The `.env.local` value must win over an
older key in the shell or another dotenv file.

- If the application already loads a dotenv file, load `.env.local` the same
  way, before `init()`, with override on and after any other dotenv file:
  `load_dotenv(".env.local", override=True)` in Python,
  `dotenv.config({ path: ".env.local", override: true })` in JavaScript.
- Otherwise load it in the run command without displaying it:
  `set -a; . ./.env.local; set +a; <command>`. Do not rely on
  `node --env-file` or `uv run --env-file` alone, since they keep a value the
  shell already set.
- When the helper reported the key is only in the shell environment, load no
  file.

For an EU key, set `CONFIDENT_OTEL_ENDPOINT` to the EU `otelEndpoint` in the run
command or the application's non-secret config, or pass it to `init()` as
`endpoint`. The endpoint is not a secret.

## Run the batch

One trace shows that tracing works. A batch shows what the application does, so
run it on 7 to 10 inputs, each producing its own trace.

Find the smallest real entry point that reaches an LLM call: a script, a CLI
command, an existing test, or a local server plus requests. Then write inputs
that fit what the application is for:

- About half typical: the requests it was built for, varied in topic and
  length.
- About half hard cases chosen from what you read in its code and prompts:
  ambiguous requests, multi-step requests needing several tool calls,
  questions it cannot answer, out-of-scope requests, false premises, very long
  or misspelled input, or a benign instruction override such as "reply in
  pirate speak".
- If it holds conversations, make one or two multi-turn under one thread id.

The point is a realistic picture, not a failing score. Do not make inputs
harmful or abusive, and do not tune them until the application fails.

Run the batch with one small driver script in the working directory, named
`confident_examples` with the language's extension, that reuses the entry
point, loops over the inputs, and flushes or shuts down tracing at the end.
Prefer an existing batch, eval, or test runner if there is one.

- Run inputs one after another, not in parallel.
- One input failing is a result: catch the error, let the trace record it, and
  continue.
- No side effects. Do not send messages or emails, charge cards, or write to
  production data. If the only entry point would, stop and tell the user.
- If the run needs secrets or services you do not have, such as a model
  provider key, do not fake them, mock the model, or stub the call. Stop and
  tell the user exactly what is needed and the exact command to run.
- Run one input first. If it fails because of your tracing change, fix it and
  try once more. Then run the whole batch, once.
- The run command you give the user must work pasted into a fresh shell in this
  folder, load the key as above, and never contain the key itself.
