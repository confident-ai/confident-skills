# SDK Quickstart

Source: https://www.confident-ai.com/docs/settings/project/management/quickstart

Install the SDK, configure it with the keys you need, create a client, and make
a first call. Each operation is shown for both Python and TypeScript — use the
code block matching your project.

## Install

```bash
# Python
pip install confident-ai
```

```bash
# TypeScript
npm install confident-ai
```

## Configure the Keys

Which key a call needs is decided by the resource:

| Key | Environment variable | Reaches |
| --- | --- | --- |
| Organization | `CONFIDENT_ORG_API_KEY` | `client.organization`, `client.projects`, `client.project(id)` |
| Project | `CONFIDENT_PROJ_API_KEY` | every other resource — prompts, datasets, traces, metrics, … |

The client reads both environment variables and picks the right one per call, so
set whichever the work needs — or both. Neither is `CONFIDENT_API_KEY`, which
confident-trace uses for tracing, so all three can be configured at once.

```bash
export CONFIDENT_ORG_API_KEY="confident_us_org_..."
export CONFIDENT_PROJ_API_KEY="confident_us_proj_..."
```

```python
from confident_ai import ConfidentAI

client = ConfidentAI()
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();
```

Either key can be passed explicitly instead, which is useful when managing
several organizations or projects from one process.

```python
client = ConfidentAI(
    api_key="confident_us_org_...",
    project_api_key="confident_us_proj_...",
)
```

```typescript
const client = new ConfidentAI({
  apiKey: "confident_us_org_...",
  projectApiKey: "confident_us_proj_...",
});
```

The base URL resolves from `CONFIDENT_BASE_URL`, else `CONFIDENT_REGION`
(`US` / `EU`), defaulting to `https://api.confident-ai.com`.

## Verify the Client

`client.whoami()` returns the organization tied to your organization key — it is
a shortcut for `client.organization.get()`.

A list returns an **envelope**: the rows sit on a named field, alongside the
pagination fields.

```python
# Confirm which organization the key belongs to
organization = client.whoami()
print(organization.id, organization.name)

# List the projects in your organization
projects = client.projects.list()
for project in projects.projects:
    print(project.id, project.name)
```

```typescript
// Confirm which organization the key belongs to
const organization = await client.whoami();
console.log(organization.id, organization.name);

// List the projects in your organization
const projects = await client.projects.list();
projects.projects.forEach((project) => console.log(project.id, project.name));
```

To check the project key instead, list something project-scoped:

```python
print(len(client.datasets.list().datasets))
```

```typescript
console.log((await client.datasets.list()).datasets.length);
```

## Importing Types

Each resource re-exports its own types, so import from the resource rather than
reaching inside it:

```python
from confident_ai.datasets import SingleTurnGolden
from confident_ai.prompts import PromptInterpolationType
```

```typescript
import { SingleTurnGolden } from "confident-ai/datasets";
import { PromptInterpolationType } from "confident-ai/prompts";
```

## Async (Python)

In Python, every method has an async twin prefixed with `a_` — `a_list`,
`a_create`, `a_get`, `a_update`, `a_delete`, and `client.a_whoami()`. The
signatures match their sync counterparts; call them with `await` from async
code. (TypeScript is asynchronous by default — every method already returns a
promise.)

```python
import asyncio
from confident_ai import ConfidentAI

client = ConfidentAI()

async def main():
    projects = await client.projects.a_list()
    organization = await client.a_whoami()
    print(organization.id, len(projects.projects))

asyncio.run(main())
```

## Next Steps

- The whole surface and the two scopes — `references/introduction.md`.
- Create, update, and delete projects — `references/projects.md`.
- Manage organization and project membership — `references/members-and-invitations.md`.
- Manage roles, policies, and permissions — `references/roles-policies-permissions.md`.
- Automate key provisioning and rotation — `references/api-keys.md`.
