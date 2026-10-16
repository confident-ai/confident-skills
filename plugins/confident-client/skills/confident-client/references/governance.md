# Governance Policies

Governance policies are **organization-level** bundles of compliance _controls_
(for example, `PRE_DEPLOYMENT_EVALS`) that you attach to projects to enforce
standards across the account. The SDK supports the full lifecycle: create, read,
update and delete a policy, and assign or unassign it to projects.

Governance exists **only at the organization scope** (`client.organization`);
there is no project-scoped governance client. A project's currently attached
policy is visible on the project itself (`project.governance_policy` in Python,
`project.governancePolicy` in TypeScript).

All methods here require an **Organization API Key**. See
`references/quickstart.md` to create a client. Each operation is shown for both
Python and TypeScript — use the code block matching your project.

## List Governance Policies

List every governance policy in the organization. The call returns a
`GovernancePolicyList`; the rows are on `.governance_policies`. Each summary
includes its `controls` and a count of the projects it covers.

```python
from confident_ai import ConfidentAI

client = ConfidentAI()

policies = client.organization.list_governance_policies()
for policy in policies.governance_policies:
    print(policy.id, policy.name, policy.projects_count)
    for control in policy.controls:
        print("  control:", control.name, control.type)
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();

const policies = await client.organization.listGovernancePolicies();
policies.governancePolicies.forEach((policy) => {
  console.log(policy.id, policy.name, policy.projectsCount);
  policy.controls.forEach((control) =>
    console.log("  control:", control.name, control.type),
  );
});
```

## Get a Governance Policy

Retrieve one policy in full — its controls, the projects it covers, its owner,
and the policies it derives from.

```python
policy = client.organization.get_governance_policy("<GOVERNANCE-POLICY-ID>")
print(policy.name, policy.controls_count, policy.projects_count)
```

```typescript
const policy = await client.organization.getGovernancePolicy(
  "<GOVERNANCE-POLICY-ID>",
);
console.log(policy.name, policy.controlsCount, policy.projectsCount);
```

## Create a Governance Policy

`name` is required. `base_policy_ids` derives the new policy from existing ones.

```python
created = client.organization.create_governance_policy(
    "Production Gate",
    description="Controls every production project must satisfy",
)
print(created.id)
```

```typescript
const created = await client.organization.createGovernancePolicy(
  "Production Gate",
  "Controls every production project must satisfy",
);
console.log(created.id);
```

## Update a Governance Policy

Every field is optional; a field you omit is left as it is.

```python
policy = client.organization.update_governance_policy(
    "<GOVERNANCE-POLICY-ID>",
    name="Production Gate (v2)",
    owner_email="owner@example.com",
)
```

```typescript
const policy = await client.organization.updateGovernancePolicy(
  "<GOVERNANCE-POLICY-ID>",
  { name: "Production Gate (v2)", ownerEmail: "owner@example.com" },
);
```

## Delete a Governance Policy

```python
client.organization.delete_governance_policy("<GOVERNANCE-POLICY-ID>")
```

```typescript
await client.organization.deleteGovernancePolicy("<GOVERNANCE-POLICY-ID>");
```

## List Projects Covered by a Policy

List the projects a governance policy is assigned to. Supports `page` and
`page_size`; the rows are on `.projects`.

```python
projects = client.organization.list_governance_policy_projects(
    "<GOVERNANCE-POLICY-ID>", page=1, page_size=25
)
for project in projects.projects:
    print(project.id, project.name)
```

```typescript
const projects = await client.organization.listGovernancePolicyProjects(
  "<GOVERNANCE-POLICY-ID>",
  1,
  25,
);
projects.projects.forEach((project) => console.log(project.id, project.name));
```

## Assign a Policy to Projects

Attach a governance policy to one or more projects by their ids. The result
reports which project ids were assigned and which were not found. A project can
have at most one governance policy, so assigning **moves** each project off any
policy it was already on (re-assigning the same policy is a no-op).

```python
result = client.organization.assign_projects_to_governance_policy(
    "<GOVERNANCE-POLICY-ID>", ["<PROJECT-ID>", "<OTHER-PROJECT-ID>"]
)
print(result.assigned_project_ids)
print(result.not_found_project_ids)
print(result.count)
```

```typescript
const result = await client.organization.assignProjectsToGovernancePolicy(
  "<GOVERNANCE-POLICY-ID>",
  ["<PROJECT-ID>", "<OTHER-PROJECT-ID>"],
);
console.log(result.assignedProjectIds);
console.log(result.notFoundProjectIds);
console.log(result.count);
```

## Unassign a Policy from Projects

Detach a governance policy from projects by their ids. The result reports which
projects were unassigned and any that were skipped (projects the policy was not
assigned to).

```python
result = client.organization.unassign_projects_from_governance_policy(
    "<GOVERNANCE-POLICY-ID>", ["<PROJECT-ID>"]
)
print(result.unassigned_project_ids)
print(result.skipped_project_ids)
print(result.count)
```

```typescript
const result = await client.organization.unassignProjectsFromGovernancePolicy(
  "<GOVERNANCE-POLICY-ID>",
  ["<PROJECT-ID>"],
);
console.log(result.unassignedProjectIds);
console.log(result.skippedProjectIds);
console.log(result.count);
```

## Next Steps

- Manage the projects governance policies apply to — `references/projects.md`.
- Define who can administer the account — `references/roles-policies-permissions.md`.
