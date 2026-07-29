#!/usr/bin/env python3
"""Structural checks for the dutch-native skill repo.

Run locally with `python3 scripts/validate.py`. CI runs the same script, so a
green local run means a green CI run.

These checks exist because the repo makes promises that are easy to break
silently: three manifests each declare a version, the README quotes a character
budget, and the skill bans a character that is invisible in review.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "dutch-native"
SKILL_MD = SKILL_DIR / "SKILL.md"

# A Custom GPT instruction box holds 8000 characters. The README tells readers
# to paste the body below the frontmatter, so that body is what must fit.
CUSTOM_GPT_LIMIT = 8000

EM_DASH = "—"

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def note(msg: str) -> None:
    notes.append(msg)


def load_json(rel: str) -> dict | None:
    path = ROOT / rel
    if not path.exists():
        fail(f"{rel}: missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{rel}: invalid JSON ({exc})")
        return None


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter, body). Empty frontmatter if the file has none."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2].lstrip("\n")


def check_manifests() -> None:
    claude_plugin = load_json(".claude-plugin/plugin.json")
    claude_market = load_json(".claude-plugin/marketplace.json")
    codex_plugin = load_json(".codex-plugin/plugin.json")
    codex_market = load_json(".agents/plugins/marketplace.json")

    if not all([claude_plugin, claude_market, codex_plugin, codex_market]):
        return

    # Every manifest must agree on the plugin name, or one host installs
    # something the other cannot find.
    names = {
        ".claude-plugin/plugin.json": claude_plugin.get("name"),
        ".codex-plugin/plugin.json": codex_plugin.get("name"),
        ".claude-plugin/marketplace.json[0]": claude_market["plugins"][0].get("name"),
        ".agents/plugins/marketplace.json[0]": codex_market["plugins"][0].get("name"),
    }
    if len(set(names.values())) != 1:
        fail(f"plugin name disagrees across manifests: {names}")
    elif SKILL_DIR.name != claude_plugin.get("name"):
        note(
            f"skill dir 'skills/{SKILL_DIR.name}' differs from plugin name "
            f"'{claude_plugin.get('name')}' (allowed, but the invoke name changes)"
        )

    versions = {
        ".claude-plugin/plugin.json": claude_plugin.get("version"),
        ".codex-plugin/plugin.json": codex_plugin.get("version"),
        ".claude-plugin/marketplace.json[0]": claude_market["plugins"][0].get("version"),
    }
    if len(set(versions.values())) != 1:
        fail(f"version disagrees across manifests: {versions}")

    # Codex requires these on every marketplace entry.
    entry = codex_market["plugins"][0]
    policy = entry.get("policy", {})
    for key in ("installation", "authentication"):
        if key not in policy:
            fail(f".agents/plugins/marketplace.json: plugins[0].policy.{key} is required")
    if "category" not in entry:
        fail(".agents/plugins/marketplace.json: plugins[0].category is required")

    # The Codex manifest points at the skills dir; make sure it resolves.
    skills_path = codex_plugin.get("skills", "./skills/")
    if not (ROOT / skills_path.lstrip("./")).is_dir():
        fail(f".codex-plugin/plugin.json: skills path '{skills_path}' does not resolve")

    return versions[".claude-plugin/plugin.json"]


def check_skill() -> None:
    if not SKILL_MD.exists():
        fail("skills/dutch-native/SKILL.md: missing")
        return

    text = SKILL_MD.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)

    if not frontmatter:
        fail("SKILL.md: no YAML frontmatter, so no host will index the skill")
        return

    for field in ("name", "description"):
        if not re.search(rf"^{field}:\s*\S", frontmatter, re.MULTILINE):
            fail(f"SKILL.md: frontmatter is missing required field '{field}'")

    name_match = re.search(r"^name:\s*(\S+)", frontmatter, re.MULTILINE)
    if name_match and name_match.group(1) != SKILL_DIR.name:
        fail(
            f"SKILL.md: frontmatter name '{name_match.group(1)}' does not match "
            f"directory '{SKILL_DIR.name}'"
        )

    size = len(body)
    if size > CUSTOM_GPT_LIMIT:
        fail(
            f"SKILL.md: body is {size} chars, over the {CUSTOM_GPT_LIMIT}-char "
            f"Custom GPT budget the README promises. Trim {size - CUSTOM_GPT_LIMIT} chars."
        )
    else:
        headroom = CUSTOM_GPT_LIMIT - size
        note(f"Custom GPT budget: {size}/{CUSTOM_GPT_LIMIT} chars, {headroom} to spare")
        if headroom < 300:
            note("  headroom is thin; the next addition may break the Custom GPT path")

    # Section 6 sends the reader to this file on demand.
    if "references/be-nl.md" in text and not (SKILL_DIR / "references" / "be-nl.md").exists():
        fail("SKILL.md references references/be-nl.md, which does not exist")


def check_no_em_dash() -> None:
    """The skill bans em-dashes in Dutch output, so the repo should not ship them.

    The eval fixture is exempt: it contains an em-dash on purpose, as something
    the skill is supposed to remove.
    """
    exempt = {SKILL_DIR / "evals" / "files" / "translationese.md"}
    for path in [SKILL_MD, ROOT / "README.md", ROOT / "CHANGELOG.md"]:
        if not path.exists() or path in exempt:
            continue
        text = path.read_text(encoding="utf-8")
        if EM_DASH in text:
            lines = [i for i, line in enumerate(text.splitlines(), 1) if EM_DASH in line]
            fail(f"{path.relative_to(ROOT)}: em-dash (U+2014) on line(s) {lines}")


def check_evals() -> None:
    evals_path = SKILL_DIR / "evals" / "evals.json"
    if not evals_path.exists():
        note("no evals/evals.json, skipping eval checks")
        return
    try:
        data = json.loads(evals_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"evals/evals.json: invalid JSON ({exc})")
        return

    cases = data.get("evals", [])
    if not cases:
        fail("evals/evals.json: no cases defined")
        return

    ids = [c.get("id") for c in cases]
    if len(set(ids)) != len(ids):
        fail(f"evals/evals.json: duplicate case ids {ids}")

    for case in cases:
        cid = case.get("id")
        for field in ("prompt", "expected_output", "assertions"):
            if not case.get(field):
                fail(f"evals/evals.json: case {cid} is missing '{field}'")
        for ref in case.get("files", []):
            # Paths are written relative to the skill dir.
            if not (SKILL_DIR / ref).exists():
                fail(f"evals/evals.json: case {cid} references missing file '{ref}'")

    note(f"evals: {len(cases)} cases, {sum(len(c.get('assertions', [])) for c in cases)} assertions")


def check_changelog(version: str | None) -> None:
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        fail("CHANGELOG.md: missing")
        return
    text = path.read_text(encoding="utf-8")
    released = re.findall(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    if not released:
        fail("CHANGELOG.md: no released version heading like '## [1.0.0]'")
        return
    if version and released[0] != version:
        fail(
            f"CHANGELOG.md: newest release is {released[0]} but the manifests "
            f"declare {version}"
        )


def main() -> int:
    version = check_manifests()
    check_skill()
    check_no_em_dash()
    check_evals()
    check_changelog(version)

    for msg in notes:
        print(f"  note: {msg}")
    if failures:
        print()
        for msg in failures:
            print(f"  FAIL: {msg}")
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nAll checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
