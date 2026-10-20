"""Check the marketplace files, plugin manifests, and skill folders."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = {"confident-onboard", "confident-trace", "confident-client", "confident-eval-setup"}
MARKETPLACES = [
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
]
MANIFESTS = [".claude-plugin/plugin.json", ".cursor-plugin/plugin.json", ".codex-plugin/plugin.json"]
BANNED_WORD = "deep" + "eval"

errors = []


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"{path.relative_to(ROOT)}: {e}")
        return None


def source_path(source):
    if isinstance(source, str):
        return source
    if isinstance(source, dict) and source.get("source") == "local":
        return source.get("path")
    return None


for rel in MARKETPLACES:
    data = load(ROOT / rel)
    if data is None:
        continue
    names = {p.get("name") for p in data.get("plugins", [])}
    if names != PLUGINS:
        errors.append(f"{rel}: lists {sorted(names)}, expected {sorted(PLUGINS)}")
    for plugin in data.get("plugins", []):
        path = source_path(plugin.get("source"))
        if path is None:
            errors.append(f"{rel}: {plugin.get('name')} has no local source")
            continue
        folder = (ROOT / path).resolve()
        if not folder.is_dir():
            errors.append(f"{rel}: {plugin.get('name')} source {path} does not exist")
        elif not list(folder.glob("skills/*/SKILL.md")):
            errors.append(f"{rel}: {plugin.get('name')} has no skills/*/SKILL.md")

for name in sorted(PLUGINS):
    for rel in MANIFESTS:
        path = ROOT / "plugins" / name / rel
        data = load(path)
        if data is not None and data.get("name") != name:
            errors.append(f"{path.relative_to(ROOT)}: name is {data.get('name')}, expected {name}")

for path in ROOT.rglob("*"):
    if ".git" in path.parts or not path.is_file():
        continue
    try:
        text = path.read_text()
    except (UnicodeDecodeError, OSError):
        continue
    if BANNED_WORD in text.lower():
        errors.append(f"{path.relative_to(ROOT)}: mentions a separate product")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("All marketplaces and plugins are valid.")
