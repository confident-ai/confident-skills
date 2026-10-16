# Introduction to the SDK

Source: https://www.confident-ai.com/docs/settings/project/management/introduction

The `confident-ai` package is the Confident AI API in Python and TypeScript:
**275 operations across 35 resources**, covering both the account
(organizations, projects, members, RBAC, governance, API keys) and the resources
a project holds (prompts, datasets, traces, spans, threads, metrics, test runs,
evaluations, dashboards, annotation queues, red teaming).

Both SDKs are generated from the same OpenAPI spec, so they expose the same
operations under the same names — `snake_case` in Python, `camelCase` in
TypeScript.

## Reference Convention

Every topic below has one reference file (`references/<topic>.md`) containing
both Python and TypeScript examples. Within each file, use the code block for
your language (```` ```python ```` or ```` ```typescript ````). The APIs are
otherwise equivalent; only idioms differ (snake_case vs camelCase, keyword
arguments vs positional, and `await` in TypeScript).

## The Two Scopes

Which key a call needs is decided by the resource, not the operation. One client
can hold both keys and picks the right one per call.

| Scope | Key | Reaches |
| --- | --- | --- |
| Organization | `CONFIDENT_ORG_API_KEY` | `client.organization`, `client.projects`, `client.project(id)` |
| Project | `CONFIDENT_PROJ_API_KEY` | every other resource |

## How the Surface Is Shaped

**One client per resource, with flat methods.** Each resource client exposes one
method per route, named for what it does:

```python
client.organization.get()
client.organization.list_api_keys()
client.organization.create_role("Analyst", ["<POLICY-ID>"])
client.datasets.list()
client.prompts.list()
```

```typescript
await client.organization.get();
await client.organization.listApiKeys();
await client.organization.createRole("Analyst", ["<POLICY-ID>"]);
await client.datasets.list();
await client.prompts.list();
```

**A list returns an envelope.** `list_members()` returns an
`OrganizationMemberList`: the rows are on `.members`, and the pagination fields
sit beside them. Read the rows off the named field.

**Three resources return a stateful handle.** `client.project(id)`,
`client.prompt(id)` and `client.dataset(id)` hold the record's id, so their
methods take only what is left:

```python
project = client.project("<PROJECT-ID>").get()   # fills the handle, returns it
project.name = "Checkout Assistant"
project.update()                                  # sends what the handle holds
project.list_members()
```

```typescript
const project = await client.project("<PROJECT-ID>").get();
project.name = "Checkout Assistant";
await project.update();
await project.listMembers();
```

**Types come from the resource:**

```python
from confident_ai.datasets import SingleTurnGolden
```

```typescript
import { SingleTurnGolden } from "confident-ai/datasets";
```

**Python has an async twin for every method**, prefixed `a_`
(`await client.organization.a_get()`). TypeScript is already promise-based.

## Key Capabilities

Each capability links to its reference below (both Python and TypeScript
examples live in the same file).

- **Organization** — read and rename the organization tied to your API key.
  See `references/organization.md`.
- **Projects** — create, read, update, and delete projects.
  See `references/projects.md`.
- **Members & invitations** — invite members, manage memberships, and assign
  roles. See `references/members-and-invitations.md`.
- **RBAC** — define roles, policies, and permissions.
  See `references/roles-policies-permissions.md`.
- **API keys** — provision, rotate, disable and delete organization- and
  project-scoped keys. See `references/api-keys.md`.
- **Governance policies** (organization scope only) — create, read, update and
  delete compliance policies, and assign/unassign them to projects.
  See `references/governance.md`.

### Project-scoped resources

- **Prompts, datasets, traces, spans, threads, metrics, test runs and
  evaluations** — see `references/resources.md`, which also indexes the
  remaining resources.

Every one is reached off the client with a project key configured, and every
method carries the route's own summary and description as its docstring or
JSDoc.

`client.prompts`, `client.datasets`, `client.traces`, `client.spans`,
`client.threads`, `client.metrics`, `client.metric_collections`,
`client.test_runs`, `client.evaluate`, `client.dashboards`, `client.widgets`,
`client.annotations`, `client.annotation_queues`, `client.annotation_forms`,
`client.classifiers`, `client.personas`, `client.rt_frameworks`,
`client.attack_methods`, `client.vulnerabilities`, `client.reports`,
`client.report_templates`, `client.scheduled_alerts`, `client.evaluation_rules`,
`client.export_destinations`, `client.export_schedules`,
`client.forwarding_connectors`, `client.ai_connections`, `client.mcp_servers`,
`client.model_costs`, `client.transformers`, `client.metrics_data`,
`client.metrics_batch`, `client.governance`.
