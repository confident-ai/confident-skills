# AI Connections

An AI connection tells Confident AI how to call the user's app: where to send
the request, what body to send for each golden, and where the answer sits in
the response. It is usable when `active` is `true`, which Confident AI decides
by calling the endpoint.

## Fields That Matter Most

| Field | What it is |
| --- | --- |
| `name` | Unique within the project, e.g. `"Support agent (staging)"`. |
| `endpoint` | The `https://` URL, or `wss://` when `responseMode` is `WEBSOCKET`. Keep query parameters out of it; put them in `queryParams`. |
| `responseMode` | `HTTP_RESPONSE` (default, one JSON body), `SSE_STREAMING` (server-sent events), `HTTP_STREAMING` (NDJSON, one JSON object per line), or `WEBSOCKET`. |
| `headers` | `[{ "key": "...", "value": "..." }]`, e.g. `Authorization` and `Content-Type`. |
| `queryParams` | Same shape as `headers`, appended to every request. |
| `payload` | The JSON request body template. See [Payload Tokens](#payload-tokens). |
| `actualOutputKeyPath` | Where the answer sits in the response, as keys and array indices: `["choices", 0, "message", "content"]`. Required, unless `actualOutputTransformerId` is set instead. |
| `retrievalContextKeyPath` | For RAG apps: where the retrieved documents (a list of strings) sit. |
| `toolsCalledKeyPath` | For agents: where the list of tools called sits. |
| `stateKeyPath` | For multi-turn apps that return conversation state to send back on the next turn. |
| `timeout` | Seconds to wait per request. Defaults to 60. Raise it for slow agents. |
| `authentication` | For OAuth2 client credentials, Azure AD, Auth0, HMAC, or a custom token request instead of a static header. |

Other key paths follow the same shape: `metadataKeyPath`,
`inputTokenCountKeyPath`, `outputTokenCountKeyPath`, `tokenCostKeyPath`.

Each key path has a `...TransformerId` alternative for responses a path can't
reach (call `list_transformers`). Send one or the other per field, never both.

## Payload Tokens

Confident AI fills the payload from each golden. A token is substituted when it
is the **entire string value** of a field, keeping its type:

```json
{ "message": "golden.input", "history": "conversationalGolden.turns" }
```

Inside a longer string, wrap it in double braces and it is rendered as text:

```json
{ "session_id": "eval-{{confident.testCaseId}}" }
```

Tokens are never substituted in keys. A string that is not a known token is
sent as written, so `"{{input}}"` reaches the app literally. Use only these
spellings:

| Golden kind | Tokens |
| --- | --- |
| Single-turn | `golden.input`, `golden.actual_output`, `golden.expected_output`, `golden.retrieval_context`, `golden.context`, `golden.expected_tools`, `golden.tools_called`, `golden.additional_metadata`, `golden.custom_column_key_values` |
| Multi-turn | `conversationalGolden.turns` (list of `{ role, content }`), `conversationalGolden.lastUserTurn` (latest user message as a string), `conversationalGolden.context`, `conversationalGolden.scenario`, `conversationalGolden.expected_outcome`, `conversationalGolden.user_description`, `conversationalGolden.additional_metadata`, `conversationalGolden.custom_column_key_values` |
| Platform | `confident.testCaseId`, `confident.turnId`, `confident.state`, `confident.prompts`, `confident.hyperparameters` |

Rules:

- The field carrying the end user's message is `"golden.input"`, even if the
  app's code shows a literal question or its own placeholder there.
- For a multi-turn app that takes the whole conversation, send
  `"conversationalGolden.turns"`. For one that keeps history server-side under
  a session id, send `"conversationalGolden.lastUserTurn"` and use
  `"confident.testCaseId"` as the session id; it stays the same for every turn
  of one conversation.
- Leave model names, temperatures, flags, and routing ids at the literal values
  the app uses.
- Omit `payload` only if the app accepts Confident AI's default body
  (`input`, `context`, `turns`, `prompts`, `testCaseId`, `turnId`). Most apps
  don't.

## Recipes

Plain JSON endpoint:

```json
{
  "name": "Support agent (staging)",
  "endpoint": "https://staging.example.com/api/chat",
  "headers": [
    { "key": "Authorization", "value": "Bearer <token from the user>" },
    { "key": "Content-Type", "value": "application/json" }
  ],
  "payload": { "message": "golden.input", "model": "gpt-4.1" },
  "actualOutputKeyPath": ["reply"]
}
```

OpenAI-compatible chat endpoint:

```json
{
  "payload": {
    "model": "gpt-4.1",
    "messages": [{ "role": "user", "content": "golden.input" }]
  },
  "actualOutputKeyPath": ["choices", 0, "message", "content"]
}
```

Server-sent events: set `responseMode` to `SSE_STREAMING`, `actualOutputEvent`
to the event name that carries tokens, `actualOutputKeyPath` to the path
inside each event's JSON, and `actualOutputAccumulate` to `true` to join the
chunks (or `false` when each event carries the whole answer).

RAG app: add `retrievalContextKeyPath`, for example `["sources"]`, so
retrieval metrics have context to score.

Multi-turn app that takes the conversation:

```json
{
  "payload": { "messages": "conversationalGolden.turns" },
  "actualOutputKeyPath": ["message", "content"]
}
```

## Updating a Connection

`update_ai_connection` changes only the fields sent; omit a field to keep it,
send `null` to clear it. `headers`, `queryParams`, `prompts`,
`authentication`, and `cloudProvider` replace the whole stored value, so call
`get_ai_connection` first and resend every entry that should stay. Any change
to how the endpoint is called or parsed makes Confident AI call it again.

## Ping Troubleshooting

`ping_ai_connection` returns 200 even when the ping fails. Read these fields:

| Field | Use it for |
| --- | --- |
| `active` | The verdict. `true` means done. |
| `error` | Why it failed, or `null`. |
| `statusCode` | The app's HTTP status: 408 on timeout, 500 when the call could not be made at all, `null` when nothing was attempted. |
| `request` | The body actually sent, with tokens resolved. Check the user's message landed in the right field. |
| `response` / `rawResponse` | The app's real response. Use it to correct key paths. |
| `actualOutput` | What the key path pulled out. It should be the answer text. |
| `invalidActualOutput` | `true` when the path found something that isn't a string: the path stops too early or points at the wrong field. |

| Symptom | Fix |
| --- | --- |
| `statusCode` 500, `error` "Invalid Endpoint", no response | The host is unreachable: a typo, `localhost`, a private network, or the app isn't deployed. Ask the user for a public URL, or point them to the Confident Agent. |
| `statusCode` 401 or 403 | A missing or wrong auth header. Ask the user for the right credential and update `headers` (resend all of them). |
| `statusCode` 404 or 405 | Wrong path or method. Recheck the route in the code. |
| `statusCode` 400 or 422 | The body doesn't match what the app expects. Compare `request` with the handler's schema and fix `payload`. |
| `statusCode` 408 | The app is slower than `timeout`. Raise it. |
| `statusCode` 200 but `actualOutput` is empty | The key path reads nothing. Find the answer in `response` and fix `actualOutputKeyPath`. |
| `invalidActualOutput` is `true` | The path points at an object or list. Extend it to the string. |
| `rawResponse` is set and `response` is `null` | The app doesn't answer with JSON. Use a transformer, or the right streaming `responseMode`. |
| The message arrives as `"{{input}}"` in `request` | A literal placeholder. Replace it with `"golden.input"`. |
