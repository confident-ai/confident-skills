# Projects

Source: https://www.confident-ai.com/docs/settings/project/management/projects

Projects are isolated workspaces for your datasets, prompts, traces, and
evaluations. You can create, update, and delete them programmatically, which
supports project-per-agent, project-per-environment, and project-per-customer
organization models.

All methods here require an **Organization API Key**. See
`references/quickstart.md` to create a client. Each operation is shown for both
Python and TypeScript — use the code block matching your project.

Projects can be reached two ways. `client.projects` takes the project id as an
argument; `client.project(id)` is a **handle** that holds the id, so its methods
take only what is left. Use the handle when you make several calls about one
project.

## List Projects

List every project in your organization. The call returns a `ProjectList`; the
rows are on `.projects`.

```python
from confident_ai import ConfidentAI

client = ConfidentAI()

projects = client.projects.list()
for project in projects.projects:
    print(project.id, project.name)
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();

const projects = await client.projects.list();
projects.projects.forEach((project) => console.log(project.id, project.name));
```

## Create a Project

Create a new project with just a `name`. Both `description` and `email` are
optional. Pass `email` to assign that user — by their email address — as the
project's **owner** (use this whenever the request is to create a project owned
by a specific person); the email must belong to an existing organization member.
Project names must be unique within the organization. Creating a project also
generates its first project API key, so the call returns both the `project` and
that API key — and the full secret is only available here.

If the request doesn't say who should own the project, **ask whether to assign
an owner (`email`) before creating** rather than silently omitting it.

```python
created = client.projects.create(
    "Customer Support Bot",
    description="Production support assistant",
    email="owner@example.com",  # optional — assigns this user as the project owner
)
print(created.project.id)     # e.g. "<PROJECT-ID>"
print(created.api_key.value)  # e.g. "confident_us_proj_...", shown only once
```

```typescript
const created = await client.projects.create(
  "Customer Support Bot",
  "Production support assistant",
  "owner@example.com", // optional — assigns this user as the project owner
);
console.log(created.project.id); // e.g. "<PROJECT-ID>"
console.log(created.apiKey?.value); // e.g. "confident_us_proj_...", shown only once
```

## Get a Project

By id, through the stateless client:

```python
project = client.projects.get("<PROJECT-ID>")
print(project.name, project.organization_id)
```

```typescript
const project = await client.projects.get("<PROJECT-ID>");
console.log(project.name, project.organizationId);
```

Or through the handle, which **fills itself and returns itself**, so you can
carry on using it:

```python
project = client.project("<PROJECT-ID>").get()
print(project.name, project.description)
```

```typescript
const project = await client.project("<PROJECT-ID>").get();
console.log(project.name, project.description);
```

## Update a Project

Through the stateless client, pass the fields you want changed; a field you omit
is left as it is.

```python
project = client.projects.update("<PROJECT-ID>", name="Support Bot (v2)")
```

```typescript
const project = await client.projects.update("<PROJECT-ID>", "Support Bot (v2)");
```

Through the handle, set the field and save — `update()` takes no arguments
because it sends what the handle holds. Call `get()` first so the handle is
filled with the record as stored.

```python
project = client.project("<PROJECT-ID>").get()
project.name = "Support Bot (v2)"
project.update()
```

```typescript
const project = await client.project("<PROJECT-ID>").get();
project.name = "Support Bot (v2)";
await project.update();
```

## Delete a Project

Permanently delete a project from your organization. This removes all of its
datasets, prompts, traces, and evaluations — including the API keys an SDK may
be configured with — and cannot be undone.

```python
client.project("<PROJECT-ID>").delete()
```

```typescript
await client.project("<PROJECT-ID>").delete();
```

## Next Steps

- Add users to projects and assign roles — `references/members-and-invitations.md`.
- Provision project-scoped API keys — `references/api-keys.md`.
