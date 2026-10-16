---
name: confident-client
description: >
  Work with the Confident AI API from code using the `confident-ai` package for
  Python and TypeScript. TRIGGER when the user wants to manage an account —
  organizations, projects, members, invitations, roles, policies, permissions,
  governance policies, API keys — or to read and write the resources a project
  holds: prompts, datasets and goldens, traces, spans and threads, metrics and
  metric collections, test runs, evaluations, dashboards, annotation queues, red
  teaming. Also TRIGGER to provision or rotate API keys, onboard or offboard
  team members, set up RBAC (permissions → policies → roles → members), or
  automate project provisioning. Account-level calls need an Organization API
  Key (`CONFIDENT_ORG_API_KEY`); everything else needs a Project API Key
  (`CONFIDENT_PROJ_API_KEY`). DO NOT TRIGGER to instrument an application with
  tracing (use the `confident-tracing` or `confident-otel` skill) or to write a
  pytest eval suite; this skill calls the API, it does not run evals or emit
  spans from a running app.
license: Apache-2.0
metadata:
  author: Confident AI
  version: "2.0.0"
  category: api
  tags: "confident-ai, api, organizations, projects, members, invitations, rbac, roles, governance, api-keys, prompts, datasets, traces, metrics, test-runs"
  compatibility: "Python (`pip install confident-ai`) or TypeScript (`npm install confident-ai`). Account-level methods need an Organization API Key (`CONFIDENT_ORG_API_KEY`); every other resource needs a Project API Key (`CONFIDENT_PROJ_API_KEY`). Both are distinct from the `CONFIDENT_API_KEY` that confident-trace uses, so they can be configured side by side."
---

# Confident AI SDK

Use this skill to call the **Confident AI API** from code with the
`confident-ai` package, available for both Python and TypeScript. It covers
**275 operations across 35 resources**: the account (organizations, projects,
members, RBAC, governance, API keys) and the resources a project holds
(prompts, datasets, traces, spans, threads, metrics, test runs, evaluations,
dashboards, annotation queues, red teaming).

This skill does not instrument a running application or write eval suites. For
instrumentation, see the `confident-tracing` and `confident-otel` skills.

## Two Keys, Two Scopes

Which key a call needs is decided by the resource, not by the operation:

| Key | Environment variable | Reaches |
| --- | --- | --- |
| Organization | `CONFIDENT_ORG_API_KEY` | `client.organization`, `client.projects`, `client.project(id)` |
| Project | `CONFIDENT_PROJ_API_KEY` | every other resource — prompts, datasets, traces, metrics, test runs, … |

One client can hold both, and picks the right one per call:

```python
client = ConfidentAI()  # reads both environment variables
client.organization.get()      # organization key
client.datasets.list()         # project key
```

Neither is `CONFIDENT_API_KEY`, which confident-trace uses — the distinct names let
both be configured at once.

## When to Use vs the Tracing Skills

- **This skill (`confident-client`)** — call the API: administer the account,
  and create, read, update or delete the resources a project holds.
- **`confident-tracing` skill** — instrument an app with the confident-trace
  SDK and its integrations.
- **`confident-otel` skill** — export raw OpenTelemetry / OTLP traces.

Use this skill for API calls: pulling a prompt, pushing goldens to a dataset,
or reading a test run's results. Use the tracing skills for work inside a running
program, such as emitting a span from a live request.

## Prerequisites

- The SDK installed: `pip install confident-ai` (Python) or
  `npm install confident-ai` (TypeScript).
- An **Organization API Key** (`confident_us_org_...`) for account work, a
  **Project API Key** (`confident_us_proj_...`) for everything else, or both.
  Read by default from `CONFIDENT_ORG_API_KEY` and `CONFIDENT_PROJ_API_KEY`.

## Language Detection

Each reference file contains both Python and TypeScript examples. Before writing
code, determine which language the user is working in, then use the matching
code block (```` ```python ```` or ```` ```typescript ````) within the
reference.

1. **Honor an explicit request first** — if the user names a language or shows a
   snippet, use that regardless of the project files.
2. **Otherwise infer from the project — but only for a _clean single-language_
   project** (markers from one ecosystem and none from the other):
   - Python markers: `*.py`, `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`, a `.venv`/`venv`
   - TypeScript/Node markers: `*.ts`, `*.tsx`, `package.json`, `tsconfig.json`, `node_modules` (JavaScript-only counts as TypeScript — same `confident-ai` package)
3. **If markers from BOTH ecosystems are present — even if one side has more
   code — or the project is empty/unclear, it is AMBIGUOUS: STOP and ask which
   language before writing any code.** Do not rationalize a "dominant" or
   "obvious" language from which files happen to have more content (e.g. a
   populated `ts/` next to a bare `.venv` is still ambiguous). Fall back to
   **Python** (never TypeScript) only after asking and getting no answer, and say
   you're defaulting.

Within each reference, the code block for the target language is authoritative
for exact method names, argument shapes (keyword arguments vs positional), and
casing (snake_case vs camelCase). Do not guess a binding from the other
language's examples.

## Workflow

1. Determine the target language — **Python** or **TypeScript** — using the
   **Language Detection** section above.
2. Work out which key the resource needs (see **Two Keys, Two Scopes**) and
   configure the client. Read `references/quickstart.md`.
3. Read the exact reference for the resource being managed before writing code,
   and follow its examples. `references/introduction.md` maps the whole surface.
4. For RBAC, compose in order: list `permissions`, bundle them into `policies`,
   bundle policies into `roles`, then assign roles to members. Read
   `references/roles-policies-permissions.md`.
5. When creating an API key (or a project, which mints its first key), capture
   the full secret `value` immediately — it is shown only once. Read
   `references/api-keys.md`.

## Core Principles

1. **Method names are flat.** A resource's client exposes one method per route:
   `client.organization.list_api_keys()`.
2. **A resource client is a property.** `client.organization.get()`,
   `client.datasets.list()`.
3. **A list returns an envelope.** `list_members()` returns an
   `OrganizationMemberList`: `.members` holds the rows, `.page` and
   `.page_size` describe the window. Read the rows off the named field.
4. **`client.project(id)`, `client.prompt(id)` and `client.dataset(id)` return
   a stateful handle** that holds the record's id, so its methods take only
   what is left. `get()` fills the handle and returns it; `update()` sends what
   the handle holds.
5. **Types are imported from the resource**: `from confident_ai.datasets import
   SingleTurnGolden` (Python), `import { SingleTurnGolden } from
   "confident-ai/datasets"` (TypeScript).
6. An API key's full secret `value` is returned **only at creation** (creating a
   project also mints its first project key). Store it securely then; later
   reads are masked. Prefer `rotate_api_key` over delete-and-recreate when a key
   is in use — it can issue the replacement with a grace period.
7. RBAC composes in one direction: permissions → policies → roles → members.
   Permissions are predefined and read-only; you can only list them.
8. A user must be an **organization member** before being added to a project.
   Invitations create membership when accepted.
9. Destructive operations are irreversible — deleting a project permanently
   removes its datasets, prompts, traces, and evaluations; deleting a key
   immediately revokes it. Prefer disabling a key (set `valid` to false) over
   deleting when you only need to revoke temporarily.
10. Never hardcode secrets or raw sensitive data; prefer environment variables
    for keys.
11. Governance policies are **organization-scoped** and support full CRUD —
    create, read, update, delete, and assign or unassign to projects.
12. **Python has an async twin for every method**, prefixed `a_`:
    `await client.organization.a_get()`. TypeScript is already promise-based.
13. **Clarify before mutating.** For create/update calls, confirm the required
    inputs and ask about consequential optional ones the user hasn't specified
    rather than silently omitting them or guessing. In particular: whether a new
    project should have an **owner** (`email`), and which **role** (`role_id`) to
    grant when inviting members or adding them to a project. Ask first, then act.

## References

Each topic has one reference file containing both Python and TypeScript
examples; use the code block matching the target language.

| Topic | File |
| --- | --- |
| Install, configure both keys, first call | `references/quickstart.md` |
| The whole surface, the two scopes, stateful handles | `references/introduction.md` |
| Read and rename the organization | `references/organization.md` |
| Create, read, update, delete projects | `references/projects.md` |
| Members, invitations, and role assignment | `references/members-and-invitations.md` |
| RBAC: permissions, policies, and roles | `references/roles-policies-permissions.md` |
| Provision, rotate, enable/disable, and delete API keys | `references/api-keys.md` |
| Governance policies: CRUD and assign/unassign to projects | `references/governance.md` |
| Prompts, datasets, traces, metrics, test runs and evaluations | `references/resources.md` |
| Background: why observability matters for AI products | `references/ai-pm-observability.md` |

Every method carries the route's own summary and description as its docstring
(Python) or JSDoc (TypeScript), so a resource with no worked example here is
still readable from the method itself.
