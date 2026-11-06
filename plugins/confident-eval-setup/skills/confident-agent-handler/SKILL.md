---
name: confident-agent-handler
description: >
  Connect an AI app that has no HTTP endpoint to Confident AI with the
  Confident Agent's handler mode: write a handler function that calls the
  app's pipeline in-process, run the agent beside it, and create and verify an
  Agent Handler AI connection. TRIGGER when the user wants Confident AI to
  evaluate or red-team an internal script, notebook, library, or pipeline
  with no API in front of it, mentions handler mode, the Confident Agent
  handler, `confident-agent --handler`, or an Agent Handler AI connection, or
  has a handler connection whose ping fails. DO NOT TRIGGER when the app
  already has an HTTP or WebSocket endpoint, public or behind a firewall (use
  the `confident-eval-setup` skill), to upload a dataset (use the
  `confident-eval-setup` skill), to instrument an app or send traces (use the
  `confident-tracing` or `confident-otel` skill), or to manage organizations,
  projects, members, or API keys (use the `confident-client` skill).
license: Apache-2.0
metadata:
  author: Confident AI
  version: "1.0.0"
  category: evaluation
  tags: "confident-ai, evals, ai-connections, confident-agent, handler-mode, mcp"
  compatibility: "Handler mode is an Enterprise feature. Uses the Confident AI MCP server (https://mcp.confident-ai.com/mcp, or eu.mcp.confident-ai.com for EU) connected with OAuth when available; otherwise the user finishes the connection in the dashboard."
---

# Confident AI Agent Handler

Use this skill to make an AI app **with no HTTP endpoint** evaluable from the
Confident AI platform. Instead of pointing an AI connection at a URL, the user
runs the **Confident Agent** in their own environment with a small `handler`
function. The agent dials out to Confident AI, receives each input over that
outbound tunnel, calls the handler, and relays the output back. Nothing is
inbound, and the app's code never leaves the user's network.

This skill writes the handler, gives the user the command to run the agent,
creates the **Agent Handler** AI connection, and proves it works with a ping.

## When This Skill Applies

- The pipeline is an internal script, notebook, or library with no API in
  front of it.
- Standing up an endpoint, even an internal one, is more work than the user
  wants for an evaluation.
- Security or compliance requires inputs to be processed in place, with
  nothing inbound.

If the app already has an HTTP endpoint, handler mode is not needed. Use the
`confident-eval-setup` skill instead; for an endpoint behind a firewall it
connects through the Confident Agent's default forwarding mode.

## Prerequisites

- An Enterprise plan. Handler mode is an Enterprise feature; say so before
  writing anything.
- A **project API key** for the agent, in `CONFIDENT_API_KEY`. The agent
  connects to the project the key belongs to, so the connection must be
  created in that same project.
- Outbound internet access on port 443 (WSS) from the machine running the
  agent. No inbound ports are needed.
- A runtime where the pipeline is importable, with its dependencies installed.
- The Confident AI MCP server, to create and ping the connection. If its tools
  (`list_projects`, `create_ai_connection`, ...) are missing, give the user
  the setup for their client from `references/mcp-setup.md`, or finish with
  the dashboard steps in [Dashboard Fallback](#dashboard-fallback).

## Workflow

1. **Pick the project.** Call `list_projects`. If there is more than one, ask
   which to use, and confirm the agent's API key belongs to it.
2. **Reuse before creating.** Call `list_ai_connections`. If an Agent Handler
   connection already exists for this app, fix and ping it (step 7) instead
   of creating a duplicate.
3. **Find the pipeline.** Locate the function that turns an input into the
   app's answer, and work out:
   - the language and the environment the pipeline runs in;
   - what it takes (a question, a conversation, a context list) and what it
     returns;
   - for a RAG pipeline, where the retrieved chunks are; for an agent, where
     the tools called are;
   - for a multi-turn app, what has to carry from one turn to the next.
   Never invent values the code does not show. Ask the user when the entry
   point is unclear.
4. **Write the handler.** Add one handler file beside the pipeline, using the
   language's SDK from `references/handler-sdks.md`. Import the pipeline and
   call it directly; the handler is only glue. Map the request fields the
   pipeline needs and return a `Response` with `output` plus every field the
   pipeline can produce. Read `references/request-response.md`. Keep
   expensive setup at module level, because the handler is imported once and
   called once per input.
5. **Install and run the agent.** Install `confident-agent` into the
   pipeline's own environment, then give the user the run command with
   `<your-api-key>` as a placeholder. Never read, print, or write the key.
   Ask the user to start it and confirm it connected.
6. **Create the connection.** Call `create_ai_connection` with a `name` and
   `type: "AGENT_HANDLER"`. Send no `endpoint`, `payload`, or key paths:
   `Response` fields are mapped automatically.
7. **Verify with a ping.** Call `ping_ai_connection`, with `multiturn: true`
   for a multi-turn app. It sends one sample input through the tunnel, runs
   the handler, and returns `active`. A failed ping is still a successful
   call: read `error` and `response`, fix the handler or how the agent runs,
   restart the agent if the handler changed, and ping again. Repeat until
   `active` is `true`, or until the problem is one only the user can fix,
   then tell them exactly what to change. See the troubleshooting table in
   `references/request-response.md`.

## Dashboard Fallback

Without the MCP server, steps 6 and 7 happen in the dashboard. Tell the user:

1. Open **AI Connections** from the project sidebar, click **New AI
   Connection**, give it a name, and click **Create**.
2. Pick **Agent Handler** from the response mode dropdown next to the
   endpoint. There is no endpoint URL to configure.
3. Click **Ping**. A green result confirms the handler is found, runs, and
   returns an output.

## Core Principles

1. The goal is a connection whose ping returns `active: true`. Do not hand off
   before that.
2. Evidence only: the handler calls the pipeline the code shows, with the
   inputs the code shows. Leave out what you cannot see.
3. The handler runs in the pipeline's runtime. Never install the agent into a
   separate environment or the stock Docker image for a pipeline that needs
   its own dependencies.
4. One handler per agent process, and only glue in it: no reimplementation of
   the pipeline.
5. The API key stays with the user: placeholders only, never in a file.
6. Do not start an evaluation yourself. The user runs it from a dataset page
   or a red teaming assessment.

## Final Report

Tell the user:

- the handler file you wrote and the command that runs the agent;
- the AI connection's name and that its ping passed;
- that the agent must stay running for evaluations and red teaming to reach
  the app;
- the next step: upload a dataset and press **Evaluate** (the
  `confident-eval-setup` skill does this), or run a red teaming assessment
  against the connection.

## References

| Topic | File |
| --- | --- |
| Connecting the Confident AI MCP server to a coding agent | `references/mcp-setup.md` |
| Installing the agent and writing the handler in Python, TypeScript, Go, Java, Rust, and other languages | `references/handler-sdks.md` |
| Request and response fields, multi-turn state, errors, and ping troubleshooting | `references/request-response.md` |
