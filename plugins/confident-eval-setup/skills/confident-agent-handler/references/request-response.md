# Request and Response

Every native SDK carries the same contract. Field names follow each
language's conventions: snake_case in Python and Rust (`retrieval_context`),
camelCase in TypeScript and Java (`retrievalContext`), PascalCase in Go
(`RetrievalContext`). Exactly one handler per agent process; the function
name is the user's choice.

The handler module is imported **once** when the agent starts, so expensive
setup (loading a model, creating clients) belongs at module level. The
function is then called **once per input**.

## Request

Read only the fields the pipeline needs. Unused fields are safe to ignore.

| Field (Python) | Description |
| --- | --- |
| `request.input` | The input for a single-turn golden |
| `request.context` | Context from the golden |
| `request.retrieval_context` | Retrieval context from the golden |
| `request.expected_output` | Expected output, when present |
| `request.turns` | Turn history for multi-turn evaluations |
| `request.scenario` | Scenario for conversational goldens |
| `request.state` | State returned from the previous turn |
| `request.prompts` | Prompt versions attached to the connection |
| `request.hyperparameters` | Hyperparameters attached to the connection |
| `request.test_case_id` | Identifier for linking the test case to a trace |
| `request.turn_id` | Identifier for linking an individual turn to a trace |

## Response

Return a `Response`. A plain string is also accepted as output-only
shorthand.

| Field (Python) | Description |
| --- | --- |
| `output` | The app's actual output (required) |
| `retrieval_context` | Retrieved chunks, for RAG metrics |
| `tools_called` | Tools the app invoked, for tool metrics |
| `state` | Updated state to carry into the next turn |

`Response` fields are mapped automatically, so an Agent Handler connection
needs **no output key paths**.

Return every field the pipeline can produce:

- A RAG pipeline returns `retrieval_context`, so retrieval metrics have
  something to score.
- An agent returns `tools_called`, so tool-use metrics have something to
  score.

```python
from confident_agent import handler, Request, Response

@handler
def rag_handler(request: Request) -> Response:
    result = pipeline(request.input)
    return Response(
        output=result.answer,
        retrieval_context=result.chunks,
        tools_called=result.tools,
    )
```

## Multi-Turn

`request.turns` carries the conversation so far and `request.state` carries
whatever the handler returned as `state` on the previous turn. Return an
updated `state` to thread information forward, for example a session id the
pipeline needs on every turn.

```python
@handler
def chat_handler(request: Request) -> Response:
    session_id = request.state or new_session_id()
    reply = chat(session_id, request.input)
    return Response(output=reply, state=session_id)
```

Ping a multi-turn connection with `multiturn: true`.

## Errors

If the handler raises or returns an error, the agent reports the failure for
that one input and the run continues; the message shows on the test case.
Raise on inputs the pipeline cannot handle rather than returning an empty
output.

```python
@handler
def summarize_handler(request: Request) -> Response:
    if not request.input:
        raise ValueError("empty input")
    return Response(output=summarize(request.input, request.context))
```

## Ping Troubleshooting

| What the ping shows | Cause | Fix |
| --- | --- | --- |
| Agent not connected | The agent is not running, or it runs with a key from another project | Start the agent with a key for the project the connection is in |
| Handler not found | The agent started without `--handler` / `CONFIDENT_HANDLER`, or the file registers no handler | Point `--handler` at the file and make sure exactly one function is registered |
| `ModuleNotFoundError` on the user's packages | The agent runs outside the pipeline's environment, or in the stock Docker image | Install and run the agent in the pipeline's environment, or build on the image |
| `Cannot use import statement outside a module` | A `.ts` or `.js` handler in a CommonJS project | Rename the handler to `.mts` (or set `"type": "module"`) |
| An error raised by the handler | The pipeline failed on the sample input | Fix the handler or the pipeline call and ping again |
| Empty output | The handler returned nothing, or `output` is empty | Return the pipeline's answer as `output` |
