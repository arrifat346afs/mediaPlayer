#!/usr/bin/env python3
"""Static checks for the manifest, the QML sources and the translations.

Runs anywhere with Python 3.10+ and no third-party packages.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "mediaPlayer"
PERMISSIONS = {"settings_read", "settings_write", "process", "network"}
TYPES = {"widget", "daemon", "launcher", "desktop", "dash", "dashCard", "composite"}
REQUIRED = ("id", "name", "description", "version", "author", "type", "capabilities")

# Patterns the registry review flagged in the 1.x code, kept out for good.
FORBIDDEN = {
    r"\bDank[A-Z]\w*\s*\{": "deprecated Dank* component (use the D* widgets)",
    r"\bProcess\s*\{": "spawning processes (the widget needs none)",
    r"\bcurl\b": "network download (TrackArtService resolves album art)",
    r"\bI18n\.tr\(": "I18n.tr() never reads the plugin's translations/ (use I18n.trFor)",
    r"/tmp/": "writing to /tmp",
}

errors = []


def error(message):
    errors.append(message)


def check_manifest():
    path = ROOT / "plugin.json"
    try:
        manifest = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        error(f"plugin.json: {exc}")
        return {}
    for key in REQUIRED:
        if not manifest.get(key):
            error(f"plugin.json: missing {key}")
    if manifest.get("id") != PLUGIN_ID:
        error(f"plugin.json: id must stay {PLUGIN_ID!r} so existing installs keep their settings")
    if not re.fullmatch(r"[a-z][a-zA-Z0-9]*", manifest.get("id", "")):
        error("plugin.json: id must be camelCase")
    if manifest.get("type") not in TYPES:
        error(f"plugin.json: unknown type {manifest.get('type')!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        error("plugin.json: version must be X.Y.Z")
    unknown = set(manifest.get("permissions", [])) - PERMISSIONS
    if unknown:
        error(f"plugin.json: permissions not in the DMS schema: {sorted(unknown)}")
    requires = manifest.get("requires_dms", "")
    match = re.fullmatch(r">=(\d+)\.\d+\.\d+", requires)
    if not match or int(match.group(1)) < 2:
        error("plugin.json: requires_dms must be >=2.0.0 or newer (the D* widgets and I18n.trFor)")
    for key in ("component", "settings"):
        target = manifest.get(key)
        if target and not (ROOT / target).is_file():
            error(f"plugin.json: {key} {target} does not exist")
    return manifest


def check_changelog(manifest):
    changelog = (ROOT / "CHANGELOG.md").read_text()
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    if not released or released[0] != manifest.get("version"):
        error(f"CHANGELOG.md: latest release {released[:1]} does not match plugin.json version {manifest.get('version')}")


def qml_files():
    return sorted(ROOT.glob("*.qml"))


def check_sources():
    strings = set()
    for path in qml_files():
        text = path.read_text()
        for pattern, reason in FORBIDDEN.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                error(f"{path.name}:{line}: {reason}")
        for match in re.finditer(r"I18n\.trFor\(\s*([^,]+?)\s*,\s*\"((?:[^\"\\]|\\.)*)\"", text):
            line = text.count("\n", 0, match.start()) + 1
            if match.group(1) != f'"{PLUGIN_ID}"':
                error(f"{path.name}:{line}: trFor must use the literal plugin id \"{PLUGIN_ID}\"")
            strings.add(match.group(2))
        # A repeating timer that never stops wakes the shell forever.
        for match in re.finditer(r"Timer\s*\{(?P<body>[^{}]*)\}", text):
            body = match.group("body")
            if re.search(r"running:\s*true\b", body) and re.search(r"repeat:\s*true\b", body):
                line = text.count("\n", 0, match.start()) + 1
                error(f"{path.name}:{line}: repeating Timer with running: true")
    return strings


def placeholders(text):
    return sorted(re.findall(r"%\d", text))


def check_translations(strings):
    files = sorted((ROOT / "translations").glob("*.json"))
    if not files:
        error("translations/: no catalogs")
    for path in files:
        try:
            catalog = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            error(f"{path.name}: invalid JSON: {exc}")
            continue
        keys = set(catalog)
        for missing in sorted(strings - keys):
            error(f"{path.name}: missing {missing!r}")
        for stale in sorted(keys - strings):
            error(f"{path.name}: stale key {stale!r}")
        for term, bucket in catalog.items():
            value = bucket.get(term) if isinstance(bucket, dict) else None
            if not value:
                error(f"{path.name}: empty translation for {term!r}")
            elif placeholders(value) != placeholders(term):
                error(f"{path.name}: placeholders differ for {term!r}")


def main():
    manifest = check_manifest()
    check_changelog(manifest)
    check_translations(check_sources())
    if errors:
        print("\n".join(errors))
        print(f"verify: {len(errors)} problem(s)")
        return 1
    print(f"verify: plugin.json, {len(qml_files())} QML files and translations OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
