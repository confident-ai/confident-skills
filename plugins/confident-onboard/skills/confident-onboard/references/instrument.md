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
   the OpenAI Agents SDK, the Vercel AI SDK, Mastra, Google ADK, Spring AI,
   LiveKit Agents, or Pipecat. Note whether its code is bundled and whether it already sets up
   OpenTelemetry.
   Note whether it is a voice agent: it takes calls or speech, through LiveKit,
   Pipecat, a telephony provider, a realtime speech model, or its own
   speech-to-text and text-to-speech. A voice agent also follows
   [Voice agents](#voice-agents).
3. If nothing here calls an LLM, retrieves documents, or uses tools, stop and
   tell the user.
4. Python, JavaScript, and TypeScript use `confident-trace`. Any other language
   uses OpenTelemetry: export the spans an OpenTelemetry-native framework
   already emits, or add spans manually.

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

### Voice agents

A voice agent's traces need the call audio: Confident AI plays back each call
and each turn, and its classifiers and voice metrics listen to it. Capture the
audio the application already has. Never generate, synthesize, or fake audio.

**LiveKit Agents** (Python and TypeScript). `init()` instruments it, and each
call becomes one trace. Read
https://www.confident-ai.com/docs/integrations/third-party/livekit first.

- Call `init()` at module scope in the file LiveKit loads for each job. LiveKit
  runs jobs in separate worker processes, so `init()` inside the entrypoint or
  only under `if __name__ == "__main__":` misses them.
- TypeScript also needs the preload in the worker's start command:
  `node --import confident-trace/register dist/agent.js dev`.
- Record the call: pass `record=True` to `session.start()` (`record: true` in
  TypeScript). The SDK uploads the recording to the call's trace when the job
  ends.

**Pipecat** (Python). `init()` instruments it, and each call becomes one trace.
Read https://www.confident-ai.com/docs/integrations/third-party/pipecat first.

- Call `init()` at module scope, before the pipeline is built. Pipecat's own
  `setup_tracing()` and `enable_tracing=True` are not needed.
- Record the call: add
  `AudioBufferProcessor(num_channels=2, auto_start_recording=True)` from
  `pipecat.processors.audio.audio_buffer_processor` to the pipeline right after
  `transport.output()`. If the pipeline already has one, keep it and add no
  second one. The SDK uploads the recording when the pipeline ends.

For both, recordings upload only over the default OTLP HTTP export with
content capture on: do not pass `capture_content=False`, set
`LIVEKIT_TELEMETRY_ALLOW_PII=0`, or swap in a gRPC exporter. Recordings over
18 MB are skipped. If the code deliberately leaves recording off, such as
`record=False` or recording only after consent, keep it that way and tell the
user.

**Any other voice agent** (a telephony webhook, a realtime speech model, or its
own speech-to-text and text-to-speech). `init()` traces its model calls. Wrap
each turn in a span and attach that turn's audio to its messages with `Media`:

```python
from confident_trace import Media

ct.update_span(
    input={
        "role": "user",
        "content": transcript,
        "audio": Media.from_bytes(user_clip, "audio/wav"),
    },
    output={
        "role": "assistant",
        "content": reply,
        "audio": Media.from_bytes(agent_clip, "audio/mpeg"),
    },
)
```

```ts
import { Media, updateSpan } from "confident-trace";

updateSpan({
  input: {
    role: "user",
    content: transcript,
    audio: Media.fromBytes(userClip, "audio/wav"),
  },
  output: {
    role: "assistant",
    content: reply,
    audio: Media.fromBytes(agentClip, "audio/mpeg"),
  },
});
```

- The user clip is the audio sent to speech-to-text; the agent clip is what
  text-to-speech returned. Use bytes the code already holds.
- Always pass the media type. Wrap raw PCM in a WAV container first, such as
  with Python's `wave` module, or it cannot be played.
- Confident AI uploads the bytes itself. Do not add a bucket or upload step.
- Group a call's turns into a thread with the call's own id, such as the call
  SID, room name, or session id, as in Threads and users.

## Any other language: OpenTelemetry

Use the language's own OpenTelemetry SDK. Before writing code, open
https://www.confident-ai.com/docs/integrations/opentelemetry and confirm these
three values. If the page does not confirm all three, stop and tell the user.

- Protocol: OTLP over HTTP with protobuf. Not gRPC.
- Endpoint: the `otelEndpoint` from the helper script. Through
  `OTEL_EXPORTER_OTLP_ENDPOINT`, give the base URL without `/v1/traces`.
- Header: `x-confident-api-key`, read from `CONFIDENT_API_KEY` at runtime.

Attach the exporter through a batch span processor and flush before a
short-lived process exits. Then pick one of the two cases below.

### An OpenTelemetry-native framework

Some frameworks emit their own OpenTelemetry spans, and Confident AI maps them
into agent, LLM, and tool spans on arrival. For these, export the spans the
framework already emits and add no spans of your own:

| Framework | Languages | How Confident AI recognises its spans |
| --- | --- | --- |
| Google ADK | Go, Java | `gcp.vertex.agent.*` attributes |
| Spring AI | Java | `spring.ai.kind`, or `gen_ai.*` spans from the Spring Boot instrumentation scope |

Turn on the framework's own tracing as its docs describe, register the
exporter above on the tracer provider it uses (usually the global one, set
before the framework starts), and run the batch. In the traces, check that
the spans show as agent, LLM, and tool spans with their inputs and outputs. If
they arrive as plain spans without them, the framework is not emitting what
Confident AI maps: add spans manually around the gaps, as below.

### Any other framework: manual spans

A framework not in the table is instrumented by hand, even if it emits
OpenTelemetry of its own. Wrap the AI components in spans with
`confident.span.type` (`llm`, `tool`, `agent`, `retriever`, or `base`) and
`confident.span.input` / `confident.span.output` as strings.

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
  ask the user how to continue, with the choices in step 7 of `SKILL.md`.
- Run one input first. If it fails because of your tracing change, fix it and
  try once more. Then run the whole batch, once.
- The run command you give the user must work pasted into a fresh shell in this
  folder, load the key as above, and never contain the key itself.

### A voice agent

A voice agent answers calls, so it usually cannot be driven from a script.
Never synthesize speech, play audio files into it, or fake a caller to make a
batch. Instead:

1. Start the agent in the background the way the project runs it in
   development, such as `python agent.py dev`, loading the key as above.
2. Ask the user to make one or two test calls of a few turns each, through
   what they already use to talk to it: LiveKit's Agents Playground, the link
   Pipecat's development runner prints, or the app's phone number.
3. Once they hang up, stop the agent gracefully, never with a forced kill, so
   the last spans and the recording upload.

LiveKit and Pipecat send one trace per call; other voice agents usually send
one per turn. If the agent cannot start because its LiveKit, telephony, or
model credentials are missing, that is the missing-secret case in step 7 of
`SKILL.md`.
