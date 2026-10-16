# API Keys

Source: https://www.confident-ai.com/docs/settings/project/management/api-keys

API keys authenticate requests to Confident AI, and come in two scopes:

- **Organization API keys** authenticate at the organization level — the
  account-wide resources: the organization itself, projects, members, RBAC,
  governance.
- **Project API keys** are scoped to a single project. They authenticate
  everything inside it — prompts, datasets, traces, metrics, test runs — for
  this SDK and for your application alike.

```
Organization API Key → client.organization, client.projects, client.project(id)
Project API Key      → every other resource
```

The full secret `value` of an API key is **only returned when it is created**.
Subsequent reads return a masked value, so store the secret securely at creation
time.

Managing keys at either scope requires an **Organization API Key**. See
`references/quickstart.md` to create a client. Each operation is shown for both
Python and TypeScript — use the code block matching your project.

Key ids are strings. Methods are flat on the client:
`client.organization.list_api_keys()`, and the same verbs on the project handle.

## List API Keys

List every API key at the organization or project level, with secret values
masked. The call returns an `ApiKeyList`; the rows are on `.api_keys`.

```python
from confident_ai import ConfidentAI

client = ConfidentAI()
project = client.project("<PROJECT-ID>")

organization_keys = client.organization.list_api_keys()
project_keys = project.list_api_keys()

for api_key in organization_keys.api_keys:
    print(api_key.id, api_key.name, api_key.valid)
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();
const project = client.project("<PROJECT-ID>");

const organizationKeys = await client.organization.listApiKeys();
const projectKeys = await project.listApiKeys();

organizationKeys.apiKeys.forEach((apiKey) =>
  console.log(apiKey.id, apiKey.name, apiKey.valid),
);
```

## Get an API Key

Retrieve a single API key by its id, with its secret value masked.

```python
api_key = client.organization.get_api_key("<API-KEY-ID>")
project_api_key = project.get_api_key("<API-KEY-ID>")
```

```typescript
const apiKey = await client.organization.getApiKey("<API-KEY-ID>");
const projectApiKey = await project.getApiKey("<API-KEY-ID>");
```

## Create an API Key

Create a new key at either scope. The returned object's `value` is the full
secret, so store it securely when the key is created. `expires_in_days` is
optional; omit it for a key that does not expire.

```python
api_key = client.organization.create_api_key("ci-pipeline")
print(api_key.value)  # e.g. "confident_us_org_...", shown only once

project_api_key = project.create_api_key("ci-pipeline", expires_in_days=90)
print(project_api_key.value)  # e.g. "confident_us_proj_..."
```

```typescript
const apiKey = await client.organization.createApiKey("ci-pipeline");
console.log(apiKey.value); // e.g. "confident_us_org_...", shown only once

const projectApiKey = await project.createApiKey("ci-pipeline", 90);
console.log(projectApiKey.value); // e.g. "confident_us_proj_..."
```

## Rotate an API Key

Rotating issues a replacement without the gap that delete-and-recreate leaves.
Prefer it for a key that is in use.

**Which field holds the new secret depends on the grace period**, so read the
right one:

| Call | Shape returned | The new secret is on |
| --- | --- | --- |
| no grace period | `ImmediatelyRotatedApiKey` | `value` — the old key stopped working as this response was produced |
| `grace_period_in_hours` set | `PendingRotationApiKey` | `shadow_value` — `value` is the *outgoing* key, masked, still valid until `rotates_at` |

Either way the secret is returned **only here**.

```python
# No grace period: the old key stops working immediately.
rotated = client.organization.rotate_api_key("<API-KEY-ID>")
print(rotated.value)  # the new secret

# With a grace period: both keys authenticate until `rotates_at`.
pending = client.organization.rotate_api_key(
    "<API-KEY-ID>",
    grace_period_in_hours=24,
    expires_in_days=90,
)
print(pending.shadow_value)  # the new secret — NOT `value`
print(pending.rotates_at)    # when the outgoing key stops working
```

```typescript
// No grace period: the old key stops working immediately.
const rotated = await client.organization.rotateApiKey("<API-KEY-ID>");
console.log(rotated.value); // the new secret

// With a grace period: both keys authenticate until `rotatesAt`.
const pending = await client.organization.rotateApiKey("<API-KEY-ID>", 24, 90);
console.log(pending.shadowValue); // the new secret — NOT `value`
console.log(pending.rotatesAt); // when the outgoing key stops working
```

## Enable or Disable an API Key

Set `valid` to false to revoke a key without deleting it, or back to true to
re-enable it. Prefer this over deleting when the revocation may be temporary.

```python
api_key = client.organization.update_api_key("<API-KEY-ID>", False)
project_api_key = project.update_api_key("<API-KEY-ID>", False)
```

```typescript
const apiKey = await client.organization.updateApiKey("<API-KEY-ID>", false);
const projectApiKey = await project.updateApiKey("<API-KEY-ID>", false);
```

## Delete an API Key

Permanently delete an API key by its id, which immediately revokes it.

```python
client.organization.delete_api_key("<API-KEY-ID>")
project.delete_api_key("<API-KEY-ID>")
```

```typescript
await client.organization.deleteApiKey("<API-KEY-ID>");
await project.deleteApiKey("<API-KEY-ID>");
```

## Next Steps

- Learn how organization- and project-level auth works (Confident AI
  authentication docs).
- Manage the projects your keys are scoped to — `references/projects.md`.
