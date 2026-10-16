# Members and Invitations

Source: https://www.confident-ai.com/docs/settings/project/management/members-and-invitations

Members are the people with access to your account, and they exist at two
levels:

- **Organization members** belong to your entire organization. Invited users
  become organization members and can receive an organization-level role.
- **Project members** belong to a single project. Add organization members to
  projects to grant project access with a project-level role.

A user must be an organization member before they can be added to a project. New
members join by accepting an invitation, and project membership grants access to
specific projects.

```
Invitation (email + optional role)
  → Organization Member (organization-level role)
      → Project A Member (project-level role)
      → Project B Member (project-level role)
```

All methods here require an **Organization API Key**. See
`references/quickstart.md` to create a client. Each operation is shown for both
Python and TypeScript — use the code block matching your project.

The same verbs exist at both scopes: on `client.organization` for the
organization, and on the `client.project(id)` handle for one project.

## Members

### List Members

Both calls take `page` and `page_size`, and return an envelope whose rows are on
`.members`.

```python
from confident_ai import ConfidentAI

client = ConfidentAI()
project = client.project("<PROJECT-ID>")

# Organization members
members = client.organization.list_members(page=1, page_size=25)
for member in members.members:
    print(member.id, member.email, member.organization_role)

# Project members
project_members = project.list_members(page=1)
for member in project_members.members:
    print(member.id, member.email, member.project_role)
```

```typescript
import { ConfidentAI } from "confident-ai";

const client = new ConfidentAI();
const project = client.project("<PROJECT-ID>");

// Organization members
const members = await client.organization.listMembers(1, 25);
members.members.forEach((member) =>
  console.log(member.id, member.email, member.organizationRole),
);

// Project members
const projectMembers = await project.listMembers(1);
projectMembers.members.forEach((member) =>
  console.log(member.id, member.email, member.projectRole),
);
```

### Update a Member's Role

Assign a role to a member by their user id. Both arguments are positional: the
user id, then the role id. Roles are managed in
`references/roles-policies-permissions.md`.

```python
# Organization-level role
member = client.organization.update_member_role("<USER-ID>", "<ROLE-ID>")

# Project-level role
project_member = project.update_member_role("<USER-ID>", "<PROJECT-ROLE-ID>")
```

```typescript
// Organization-level role
const member = await client.organization.updateMemberRole(
  "<USER-ID>",
  "<ROLE-ID>",
);

// Project-level role
const projectMember = await project.updateMemberRole(
  "<USER-ID>",
  "<PROJECT-ROLE-ID>",
);
```

The Owner is protected: you can't change the Owner's role or remove the Owner
directly. Assigning the Owner role to another member instead **transfers
ownership**, demoting the previous Owner (to Admin at the organization level,
Manager at the project level).

### Remove a Member

Remove a member from your organization or from a single project by their user
id.

```python
client.organization.remove_member("<USER-ID>")
project.remove_member("<USER-ID>")
```

```typescript
await client.organization.removeMember("<USER-ID>");
await project.removeMember("<USER-ID>");
```

Removing someone from the organization removes them from its projects too;
removing them from a project leaves their organization membership intact.

## Invitations

An invitation carries an email address and, optionally, the role the invitee
receives when they accept. **Ask which role to grant** rather than silently
omitting it.

### List Invitations

List the pending invitations at either scope. The rows are on `.invitations`.

```python
invitations = client.organization.list_invitations()
project_invitations = project.list_invitations()

for invitation in invitations.invitations:
    print(invitation.id, invitation.email, invitation.status)
```

```typescript
const invitations = await client.organization.listInvitations();
const projectInvitations = await project.listInvitations();

invitations.invitations.forEach((invitation) =>
  console.log(invitation.id, invitation.email, invitation.status),
);
```

### Create Invitations

Invite one or more people by email. The role keyword differs by scope —
`organization_role_id` for the organization, `project_role_id` for a project —
because the two draw from different role sets.

```python
# Organization invitations
invitations = client.organization.create_invitations(
    ["new.hire@example.com"],
    organization_role_id="<ROLE-ID>",
)

# Project invitations
project_invitations = project.create_invitations(
    ["new.hire@example.com"],
    project_role_id="<PROJECT-ROLE-ID>",
)
```

```typescript
// Organization invitations
const invitations = await client.organization.createInvitations(
  ["new.hire@example.com"],
  "<ROLE-ID>",
);

// Project invitations
const projectInvitations = await project.createInvitations(
  ["new.hire@example.com"],
  "<PROJECT-ROLE-ID>",
);
```

### Resend and Revoke Invitations

Resend re-sends the email for a pending invitation; deleting it revokes it.

```python
# Resend
client.organization.resend_invitation("<INVITATION-ID>")
project.resend_invitation("<INVITATION-ID>")

# Revoke
client.organization.delete_invitation("<INVITATION-ID>")
project.delete_invitation("<INVITATION-ID>")
```

```typescript
// Resend
await client.organization.resendInvitation("<INVITATION-ID>");
await project.resendInvitation("<INVITATION-ID>");

// Revoke
await client.organization.deleteInvitation("<INVITATION-ID>");
await project.deleteInvitation("<INVITATION-ID>");
```

## Next Steps

- Define the roles you assign — `references/roles-policies-permissions.md`.
- Provision keys for the projects members work in — `references/api-keys.md`.
