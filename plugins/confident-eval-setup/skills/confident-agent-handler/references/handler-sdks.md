# Handler SDKs

A handler runs **in the same runtime as the app it calls**. Pick the section
for the language the pipeline is written in. Python and TypeScript load the
handler from a file; Go, Java, and Rust register it in code as a library; any
other language goes through a small local endpoint and the agent's forwarding
mode.

Every run command uses a **project API key** in `CONFIDENT_API_KEY`. Write it
as the placeholder `<your-api-key>` and let the user fill it in. Never read,
print, or commit the key.

## Python

Install the agent into the **same environment as the pipeline** (the same
virtualenv, conda env, or container). It ships both the runner and the
`@handler` decorator.

```bash
pip install confident-agent
```

Write the handler file, for example `confident_handler.py`:

```python
from confident_agent import handler, Request, Response
from my_company.pipeline import summarize  # the app's existing code

@handler
def summarize_handler(request: Request) -> Response:
    return Response(
        output=summarize(request.input, request.context),
    )
```

Run it from that same environment:

```bash
CONFIDENT_API_KEY=<your-api-key> confident-agent --handler confident_handler.py
```

There is no URL or port to configure.

### Docker

Only for teams that deploy everything containerized. The stock
`confidentai/confident-agent` image holds just the agent, **not the pipeline's
dependencies**, so mounting the handler into it fails on import
(`ModuleNotFoundError` on the user's own packages). Build on top of it instead:

```dockerfile
FROM confidentai/confident-agent
USER root
COPY . /app
RUN pip install -r /app/requirements.txt
USER confident
```

```bash
docker build -t my-company/confident-handler .

docker run -d \
  -e CONFIDENT_API_KEY=<your-api-key> \
  -e CONFIDENT_HANDLER=/app/confident_handler.py \
  my-company/confident-handler
```

## TypeScript

Install the agent into the same project as the pipeline:

```bash
npm install confident-agent
```

Write the handler file, for example `handler.ts`:

```ts
import { handler, type Request, type Response } from "confident-agent";
import { summarize } from "./pipeline"; // the app's existing code

handler(
  (request: Request): Response => ({
    output: summarize(request.input, request.context),
  }),
);
```

Run it from that project:

```bash
CONFIDENT_API_KEY=<your-api-key> npx confident-agent --handler ./handler.ts
```

Check these before handing the command over:

- Loading a `.ts` handler directly needs Node.js 22.18 or later. On older
  Node versions, compile the handler to `.js` and point `--handler` at that.
- `confident-agent` is ESM-only. If the project's `package.json` does not set
  `"type": "module"`, the import fails with `Cannot use import statement
  outside a module`. Name the handler `handler.mts` rather than changing the
  project's module type, unless the user prefers otherwise.
- Import `Request` and `Response` with the `type` keyword, as above. Node's
  type stripping does not erase plain named imports of types.

## Go

Go has no `--handler` flag. Register the handler in code with
`confidentagent.Handler` and start the agent from the program's own `main`.

```bash
go get github.com/confident-ai/confident-agent/go
```

```go
package main

import (
    "log"

    confidentagent "github.com/confident-ai/confident-agent/go"
)

func main() {
    confidentagent.Handler(func(request confidentagent.Request) (any, error) {
        return confidentagent.Response{
            Output: summarize(request.Input, request.Context),
        }, nil
    })

    if err := confidentagent.Run(); err != nil {
        log.Fatal(err)
    }
}
```

```bash
CONFIDENT_API_KEY=<your-api-key> go run .
```

## Java

Java has no `--handler` flag. Depend on `com.confident-ai:confident-agent`,
register the handler with `Decorator.handler(...)`, and start the agent from
the program's own entry point.

```xml
<dependency>
  <groupId>com.confident-ai</groupId>
  <artifactId>confident-agent</artifactId>
  <version>1.0.1</version>
</dependency>
```

```java
import static ai.confident.agent.handler.Decorator.handler;

import ai.confident.agent.RelayAgent;
import ai.confident.agent.schemas.Request;
import ai.confident.agent.schemas.Response;

public class MyAgent {
    public static void main(String[] args) throws InterruptedException {
        handler((Request request) -> {
            return new Response(
                summarize(request.input, request.context)
            );
        });

        RelayAgent.createAgent().start();
    }
}
```

```bash
CONFIDENT_API_KEY=<your-api-key> java -jar my-agent.jar
```

## Rust

Rust has no `--handler` flag. Add the crate to the program's own binary,
register a handler closure with `confident_agent::handler`, and run the agent.

```bash
cargo add confident-agent tokio
```

```rust
use confident_agent::{handler, Request, Response};

#[tokio::main]
async fn main() {
    handler(|request: Request| async move {
        Ok(Response {
            output: summarize(&request.input, &request.context),
            ..Response::default()
        })
    });

    if let Err(e) = confident_agent::run().await {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
```

```bash
CONFIDENT_API_KEY=<your-api-key> cargo run
```

## Other Languages

For languages without a native handler SDK (Clojure and other JVM languages,
Elixir, and so on), handler mode does not apply. Use the universal fallback
instead:

1. Wrap the pipeline in a small HTTP handler that listens only on `localhost`
   and returns `{ "output": ... }`.
2. Run the Confident Agent in forwarding mode in the same network:

   ```bash
   docker run -d \
     -e CONFIDENT_API_KEY=<your-api-key> \
     -e CONFIDENT_WS_BASE_URL=wss://offline-evals.confident-ai.com/ws/relay \
     confidentai/confident-agent
   ```

3. Create an `ENDPOINT` AI connection marked **Internal** with the local URL
   (for example `http://localhost:8000`), map the payload, and set
   `actualOutputKeyPath` to `["output"]`. Building that connection is the
   `confident-eval-setup` skill's job.

## Configuration

| Variable | Description | Required |
| --- | --- | --- |
| `CONFIDENT_API_KEY` | The project API key | Yes |
| `CONFIDENT_HANDLER` | Path to the handler file (Python and TypeScript only) | Yes, for handler mode |
| `CONFIDENT_WS_BASE_URL` | WebSocket relay URL | No, defaults to `wss://offline-evals.confident-ai.com/ws/relay` |

In Python and TypeScript, `--handler` and `CONFIDENT_HANDLER` are equivalent.
In Go, Java, and Rust the handler is registered in code, so neither applies.

Full instructions: https://www.confident-ai.com/docs/llm-evaluation/ai-connections/confident-agent-handler-mode
