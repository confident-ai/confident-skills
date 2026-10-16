# Roles, Policies & Permissions (RBAC)

Source: https://www.confident-ai.com/docs/settings/project/management/roles-policies-permissions

Confident AI uses role-based access control (RBAC). Access is granted by
composing three building blocks — bundle permissions into policies, bundle
policies into roles, then assign roles to members:

- **Permissions** are the atomic actions you can grant (e.g. `traces:read`).
  They are predefined by the platform, so you can only list them.
- **Policies** are named bundles of permissions.
- **Roles** are named bundles of policies that you assign to members.

```
Permissions (atomic actions)
  → bundled into Policies
      → bundled into Roles
          → assigned to Members
```

Each building block exists independently at both the **organization** and
**project** level. Organization-level roles govern access across the
organization; project-level roles govern access within a single project.

All methods here require an **Organization API Key**. See
`references/quickstart.md` to create a client. The methods are flat on each
client — `client.organization.list_roles()`, and the same verbs on the
`client.project(id)` handle. Each operation is shown for both Python and
TypeScript — use the code block matching your project.

## Permissions

Permissions are read-only. List them to discover the ids to attach to policies.
The rows are on `.permissions`.

```python
from confident_ai import ConfidentAI

client = ConfidentAI()
project = client.project("<PROJECT-ID>")

permissions = client.organization.list_permissions()
project_permissions = project.list_permissions()

for permission in permissions.permissions:
    print(permission.id, permission.name)
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();
const project = client.project("<PROJECT-ID>");

const permissions = await client.organization.listPermissions();
const projectPermissions = await project.listPermissions();

permissions.permissions.forEach((permission) =>
  console.log(permission.id, permission.name),
);
```

## Policies

A policy is a named bundle of permission ids. `name` and `permission_ids` are
positional; `description` is optional. **Update replaces the bundle** — send the
full permission list you want the policy to end up with, not just additions.

```python
# List — rows are on `.policies`
policies = client.organization.list_policies()

# Create
policy = client.organization.create_policy(
    "Billing", ["<PERMISSION-ID>"], description="Read billing data"
)

# Update — `name` and `permission_ids` are required, and replace what is stored
policy = client.organization.update_policy(
    "<POLICY-ID>", "Billing", ["<PERMISSION-ID>", "<OTHER-PERMISSION-ID>"]
)

# Delete
client.organization.delete_policy("<POLICY-ID>")
```

```typescript
// List — rows are on `.policies`
const policies = await client.organization.listPolicies();

// Create
const policy = await client.organization.createPolicy(
  "Billing",
  ["<PERMISSION-ID>"],
  "Read billing data",
);

// Update — `name` and `permissionIds` are required, and replace what is stored
const updated = await client.organization.updatePolicy("<POLICY-ID>", "Billing", [
  "<PERMISSION-ID>",
  "<OTHER-PERMISSION-ID>",
]);

// Delete
await client.organization.deletePolicy("<POLICY-ID>");
```

The same verbs exist on a project: `project.list_policies()`,
`project.create_policy(...)`, and so on.

## Roles

A role is a named bundle of policy ids, and roles are what you assign to
members. As with policies, **update replaces the bundle**.

```python
# List — rows are on `.roles`
roles = client.organization.list_roles()

# Create
role = client.organization.create_role(
    "Analyst", ["<POLICY-ID>"], description="Read-only analyst"
)

# Update — `name` and `policy_ids` are required, and replace what is stored
role = client.organization.update_role(
    "<ROLE-ID>", "Analyst", ["<POLICY-ID>", "<OTHER-POLICY-ID>"]
)

# Delete
client.organization.delete_role("<ROLE-ID>")
```

```typescript
// List — rows are on `.roles`
const roles = await client.organization.listRoles();

// Create
const role = await client.organization.createRole(
  "Analyst",
  ["<POLICY-ID>"],
  "Read-only analyst",
);

// Update — `name` and `policyIds` are required, and replace what is stored
const updated = await client.organization.updateRole("<ROLE-ID>", "Analyst", [
  "<POLICY-ID>",
  "<OTHER-POLICY-ID>",
]);

// Delete
await client.organization.deleteRole("<ROLE-ID>");
```

The same verbs exist on a project: `project.list_roles()`,
`project.create_role(...)`, and so on. A project role draws from project
permissions and is assigned with `project.update_member_role(...)`.

## Putting It Together

Compose in one direction, then assign:

```python
permissions = client.organization.list_permissions()
wanted = [p.id for p in permissions.permissions if p.name.endswith(":read")]

policy = client.organization.create_policy("Read Everything", wanted)
role = client.organization.create_role("Auditor", [policy.id])
client.organization.update_member_role("<USER-ID>", role.id)
```

```typescript
const permissions = await client.organization.listPermissions();
const wanted = permissions.permissions
  .filter((p) => p.name.endsWith(":read"))
  .map((p) => p.id);

const policy = await client.organization.createPolicy("Read Everything", wanted);
const role = await client.organization.createRole("Auditor", [policy.id]);
await client.organization.updateMemberRole("<USER-ID>", role.id);
```

## Next Steps

- Assign the roles you defined — `references/members-and-invitations.md`.
- Attach compliance controls to projects — `references/governance.md`.
