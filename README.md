<img src="assets/confident-skills-banner-radial-4s.svg" alt="Confident Skills: a moonlit observatory atrium where glowing trails from distant towers meet at one lit doorway, with roses in the foreground" width="100%" />

# `confident-skills`: Agent Skills for Confident AI

Confident Skills helps coding agents instrument AI applications, export
OpenTelemetry traces, and work with the Confident AI API. Install the plugins
in Claude Code, Cursor, or Codex to give your agent the setup instructions,
reference material, and templates for each task.

## What it does

- **AI tracing:** add the
  [`confident-trace`](https://github.com/confident-ai/confident-trace) SDK to
  your application, using supported integrations and custom spans.
- **OpenTelemetry setup:** configure your application's OpenTelemetry SDK to
  send traces to Confident AI over OTLP/HTTP.
- **Platform management:** use the `confident-ai` SDK to manage organizations,
  projects, members, roles, governance policies, and API keys.

## Plugins

Both plugins support Claude Code, Cursor, and Codex. Install the ones your
project needs.

| Plugin | Included skills | Purpose |
| --- | --- | --- |
| [`confident-trace`](plugins/confident-trace) | `confident-tracing`, `confident-otel` | Instrument AI applications and configure trace export. |
| [`confident-client`](plugins/confident-client) | `confident-client` | Work with the Confident AI platform through its SDK. |

## Install

### Claude Code

```
/plugin marketplace add confident-ai/confident-skills
/plugin install confident-trace@confident-skills
/plugin install confident-client@confident-skills
```

### Codex

```bash
codex plugin marketplace add confident-ai/confident-skills
```

Then run `/plugins` in Codex and install `confident-trace` or
`confident-client`.

### Cursor

Cursor has no command to add a marketplace from GitHub. Use one of these:

- **Teams and Enterprise:** an admin opens Dashboard, then Plugins & MCPs,
  then Team Marketplaces. Choose Add Marketplace, then Import from Repo, and
  paste `https://github.com/confident-ai/confident-skills`. Team members
  install the plugins from Customize in the sidebar.
- **Local:** copy a plugin folder into `~/.cursor/plugins/local/`, then run
  Developer: Reload Window.

```bash
git clone https://github.com/confident-ai/confident-skills
cp -r confident-skills/plugins/confident-trace ~/.cursor/plugins/local/
```

## Repository

| Directory | Contents |
| --- | --- |
| `plugins/` | Installable plugins, agent manifests, skills, references, and templates. |
| `skills/` | Shared skills that span the platform. |
| `.claude-plugin/` | Claude Code marketplace manifest. |
| `.cursor-plugin/` | Cursor marketplace manifest. |
| `.agents/plugins/` | Codex marketplace manifest. |
| `scripts/` | Marketplace and plugin validation. |

Validate the marketplace manifests and plugin structure:

```sh
python3 scripts/validate.py
```

## License

[Apache License 2.0](LICENSE).
