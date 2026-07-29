# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versioning applies to the packaged skill, not to Dutch. A rule change that makes
the skill judge previously accepted text as wrong is a minor bump. Restructuring
the repo so an existing install path stops working is a major bump.

## [Unreleased]

## [1.0.0] - 2026-07-29

First packaged release. The skill content existed before this, but nothing could
install it.

### Added

- `.claude-plugin/` and `.codex-plugin/` manifests, plus a marketplace on each
  side, so the repo installs as a plugin in Claude Code and in Codex without a
  clone.
- `skills/dutch-native/evals/` with four graded test cases and a translationese
  fixture that carries all seven structural tells. Not yet run against a
  benchmark, so no pass rates are claimed.
- `scripts/validate.py` and a CI workflow that check manifest and version
  agreement, the Custom GPT character budget, frontmatter, eval integrity, and
  stray em-dashes.
- A release workflow that publishes the `claude.ai` upload zip on a version tag.

### Changed

- Moved the skill to `skills/dutch-native/SKILL.md`, following the
  [openai/plugins](https://github.com/openai/plugins) convention. This is the
  default skill path for the Claude and Codex plugin specs alike, so both hosts
  resolve it with no custom path and no duplicated file.
- Rewrote the install section to cover plugin installs, bare skill installs,
  the claude.ai zip upload, Custom GPT, and project instructions.

### Fixed

- The repo shipped `skill.md` and `be-nl.md` at the root while the README and
  the skill itself both referenced `SKILL.md` and `references/be-nl.md`. No
  agent could load it, because Claude Code and Codex both require the file to
  be named `SKILL.md`.
- The README claimed `SKILL.md` fits a Custom GPT instruction box. The file is
  8005 characters against an 8000 limit. The body below the frontmatter is 7664
  and does fit, so the README now says which part to paste. CI enforces it.
- Counted the budget in characters rather than bytes. The skill contains `ë`,
  `ï`, `€` and `→`, so the byte length overstates it by 84.

[Unreleased]: https://github.com/brunocous/dutch-skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/brunocous/dutch-skill/releases/tag/v1.0.0
