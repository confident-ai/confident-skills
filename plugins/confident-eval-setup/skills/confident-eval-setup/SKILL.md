---
name: confident-eval-setup
description: >
  Get an LLM application ready to evaluate on the Confident AI platform through
  the Confident AI MCP server. TRIGGER when the user wants to set up evals on
  Confident AI, connect or register their app's endpoint as a Confident AI AI
  connection, fix or debug an AI connection that is inactive or failing its
  ping, or upload test cases (a CSV, JSON file, or list of examples) as a
  Confident AI dataset of goldens so the platform can evaluate the app. DO NOT
  TRIGGER to instrument an app or send traces (use the `confident-tracing` or
  `confident-otel` skill), to manage organizations, projects, members, or API
  keys (use the `confident-client` skill), or to write a local eval script that
  calls the app directly, which needs no AI connection.
license: Apache-2.0
metadata:
  author: Confident AI
  version: "1.0.0"
  category: evaluation
  tags: "confident-ai, evals, ai-connections, datasets, goldens, mcp"
  compatibility: "Requires the Confident AI MCP server (https://mcp.confident-ai.com/mcp, or eu.mcp.confident-ai.com for EU) connected with OAuth."
---

# Confident AI Eval Setup

Use this skill to make an LLM application evaluable **from the Confident AI
platform**. The hard part is the **AI connection**: a saved description of how
to call the app's endpoint, so Confident AI can send it each golden's input and
read the answer back. This skill builds that connection from the app's own
code, proves it works with a ping, uploads a dataset, and hands the user the
dataset page where they press **Evaluate**.

Everything happens through the Confident AI MCP server. Nothing is added to the
user's codebase.

## When This Skill Applies

- The user wants teammates to evaluate, compare, or red-team the app from the
  Confident AI dashboard, which needs Confident AI to call the app.
- The user has an AI connection that comes back inactive.
- The user wants test cases uploaded as a Confident AI dataset.

If the user only wants to run evals from their own machine, an AI connection is
not needed: their code can call the app directly. Say so, and only continue if
they still want the platform set up.

## Prerequisites

- The Confident AI MCP server connected to the coding agent. If its tools
  (`list_projects`, `create_ai_connection`, ...) are missing, stop and give the
  user the setup for their client from `references/mcp-setup.md`. It signs in
  with OAuth; no API key is needed.
- An endpoint Confident AI can reach: `https://`, or `wss://` for a WebSocket
  app. `localhost` and private hosts are not reachable. For an app behind a
  firewall, point the user to the Confident Agent
  (https://www.confident-ai.com/docs/llm-evaluation/ai-connections/confident-agent).

## Workflow

1. **Pick the project.** Call `list_projects`. If there is more than one, ask
   which to use. Every later call takes its `project_id`.
2. **Reuse before creating.** Call `list_ai_connections` and `list_datasets`.
   If a connection already points at the same endpoint, ping it (step 5)
   instead of creating a duplicate. If a dataset already holds the user's test
   cases, reuse it.
3. **Read how the app is called.** Find the request handler, route, or client
   code for the endpoint. Work out:
   - the URL, and whether it is a deployed `https://` address;
   - the HTTP body the app expects, and which field carries the user's
     message, or the conversation for a multi-turn app;
   - the headers it needs, such as auth and `Content-Type`;
   - how it replies (plain JSON, server-sent events, NDJSON, or a WebSocket)
     and where the answer sits in the response;
   - for a RAG app, where the retrieved documents are; for an agent, where the
     tools called are.
   Never invent values the code does not show. Ask the user for the deployed
   URL and for any secret, and never print a secret back.
4. **Create the connection** with `create_ai_connection`. Read
   `references/ai-connections.md` for the payload tokens, response modes, and
   key paths. The payload binds the request body to test data with tokens such
   as `"golden.input"`; `{{input}}` is not a token and is sent literally.
5. **Verify with a ping.** Call `ping_ai_connection`. It sends one sample test
   case and returns `active`. A failed ping is still a successful call: read
   `active`, `error`, `statusCode`, `response`, `rawResponse`, and
   `actualOutput`, fix the configuration with `update_ai_connection`, and ping
   again. Repeat until `active` is `true`, or until the problem is one only
   the user can fix (an unreachable host, an expired credential), then tell
   them exactly what to change. See the troubleshooting table in
   `references/ai-connections.md`.
6. **Upload the dataset** with `push_dataset`. Turn the user's test cases into
   goldens: single-turn goldens need `input` (and usually `expectedOutput`);
   multi-turn goldens need `scenario` (and usually `expectedOutcome`). Show the
   user the goldens and push them with `finalized: true` once they confirm,
   because only finalized goldens are evaluated. Read
   `references/datasets.md`.
7. **Hand off.** Give the user the dataset link that `push_dataset` returns
   (`https://app.confident-ai.com/project/<projectId>/datasets/<datasetId>`, or
   the EU or self-hosted equivalent). Tell them to open it, press
   **Evaluate**, choose the AI connection you created and a metric
   collection, and start the run.

## Core Principles

1. The goal is a connection whose ping returns `active: true`. Do not hand off
   before that.
2. Evidence only: every endpoint, header, body field, and key path comes from
   the user's code or the user. Leave out what you cannot see.
3. Bind the field that carries the user's message to `"golden.input"`; leave
   model names, flags, and routing values at the literal values the app uses.
4. `headers`, `queryParams`, `prompts`, `authentication`, and `cloudProvider`
   are full replacements on update. Read the connection with
   `get_ai_connection` and resend every entry that should stay.
5. Creating, updating, and pinging a connection all call the user's endpoint.
   Prefer a staging deployment.
6. Do not start the evaluation yourself. The user runs it from the dataset
   page, where they choose the metrics.

## Final Report

Tell the user:

- the AI connection's name and that its ping passed;
- the dataset's alias, how many goldens it holds, and its link;
- the next step: open the link, press **Evaluate**, choose the connection and
  a metric collection;
- anything left for them, such as a credential to rotate or an endpoint to
  deploy.

## References

| Topic | File |
| --- | --- |
| Connecting the Confident AI MCP server to a coding agent | `references/mcp-setup.md` |
| Payload tokens, response modes, key paths, recipes, and ping troubleshooting | `references/ai-connections.md` |
| Golden fields, CSV and JSON mapping, and `push_dataset` | `references/datasets.md` |
