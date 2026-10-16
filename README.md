<img src="assets/confident-skills-banner.png" alt="Confident Skills: a moonlit observatory atrium where glowing trails from distant towers meet at one lit doorway, with roses in the foreground" width="100%" />

# Confident Skills

Agent skills for Confident AI, packaged as plugins for Claude Code, Cursor, and
Codex.

Confident AI is AI monitoring. You trace your AI app, and it catches what's
going wrong.

## Plugins

| Plugin | Path | Skills | Agents |
| --- | --- | --- | --- |
| `confident-trace` | [plugins/confident-trace](plugins/confident-trace) | `confident-tracing`, `confident-otel` | Claude Code, Cursor, Codex |
| `confident-client` | [plugins/confident-client](plugins/confident-client) | `confident-client` | Claude Code, Cursor, Codex |

- `confident-tracing` instruments an AI app with the confident-trace SDK.
- `confident-otel` exports raw OpenTelemetry traces to Confident AI.
- `confident-client` calls the Confident AI API with the confident-ai SDK.

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

## Layout

- `plugins/` holds one folder per plugin, with its skills and its manifests
  for each agent.
- `skills/` is for skills that span the platform rather than one SDK.
- `.claude-plugin/`, `.cursor-plugin/`, and `.agents/plugins/` hold the
  marketplace for each agent.

Run `python scripts/validate.py` to check the marketplaces and plugins.

## License

Apache-2.0
