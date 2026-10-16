# Organization

Source: https://www.confident-ai.com/docs/settings/project/management/organization

Your organization is the top-level account that owns every project, member,
role, and API key. You can read and rename the organization tied to your API
key.

All methods here require an **Organization API Key**. See
`references/quickstart.md` to create a client. Each operation is shown for both
Python and TypeScript — use the code block matching your project.

`client.organization` is a property; call methods on it directly.

## Get Your Organization

Retrieve the organization tied to your API key, including its `id`, `name`,
`plan` and creation time.

```python
from confident_ai import ConfidentAI

client = ConfidentAI()

organization = client.organization.get()
print(organization.id, organization.name, organization.plan)
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();

const organization = await client.organization.get();
console.log(organization.id, organization.name, organization.plan);
```

`client.whoami()` is a shortcut for the same call.

## Rename Your Organization

Update your organization's `name`. It is a positional argument.

```python
organization = client.organization.update("Example Org")
```

```typescript
const organization = await client.organization.update("Example Org");
```

## Async (Python)

Every method has an `a_` twin:

```python
organization = await client.organization.a_get()
```

## Next Steps

- Create, update, and delete projects — `references/projects.md`.
- Invite members and assign roles — `references/members-and-invitations.md`.
