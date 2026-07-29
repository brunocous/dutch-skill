# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versioning applies to the packaged skill, not to Dutch. A rule change that makes
the skill judge previously accepted text as wrong is a minor bump. Restructuring
the repo so an existing install path stops working is a major bump.

## [Unreleased]

## [1.1.0] - 2026-07-29

Makes the mechanical half of the skill testable without a model, and stops the
skill blocking in contexts where nobody can answer a question.

### Added

- `scripts/lint.py`, the section 8 review loop as code. Checks em-dashes,
  calques, literally translated English idioms, ambtenarentaal, `welke` as a
  relative pronoun, sentence-initial `Echter,`, date and month form, Title Case
  headings, and BE/NL variant leakage. Errors are deterministic; heuristics are
  warnings and never fail a build. Runs offline, no API key.
- Known-good fixtures `native-be.md` and `native-nl.md`, plus `--self-test`,
  which requires every rule to fire on the translationese fixtures and stay
  silent on the native ones. Without a known-good fixture, a rule that stopped
  matching is indistinguishable from clean text.
- `evals/files/letterlijk.md`: grammatical Dutch that is pure English idiom
  carried across word for word. Nothing in it is a grammar or spelling error, so
  it isolates the failure the seven tells do not describe.
- Eval case 5, reviewing already-idiomatic Flemish. It fails if the model
  "corrects" good Dutch into Netherlands Dutch or pads it with particles. Every
  other case rewards finding defects, which is the pressure that makes a skill
  invent them.
- Eval case 6, rewriting `letterlijk.md`.
- `scripts/scrape.py` for the 57 spelling rules, 33 clarity tips and 399
  BE/NL-labelled lemmas. Output stays in gitignored `data/`; promotion into
  `references/` is a human step.
- A worked before and after example in the README, and a contribution routing
  table.

### Changed

- Section 0 no longer blocks on "BE or NL?". The variant now resolves through an
  explicit instruction, a `## Projectvoorkeuren` block, inference from the text,
  then a BE default, and the output states which was used. The old rule was
  unenforceable in subagents, scheduled runs and one-shot API calls, where the
  model would ask and then answer itself: silent defaulting while claiming not
  to. The closing variant line doubles as the only signal that the skill loaded.
- A `## Projectvoorkeuren` block now outranks sections 0, 5 and 6, so variant,
  aanspreking and loanword policy are configurable. Section 5's keep and
  translate lists are right for tech and business and wrong for a bank.
- Eval case 3 now asserts the variant is *stated*, not that a question is asked.
- Mechanical assertions moved out of `evals.json` into the linter. Grading
  "contains no em-dash" with a language model is slower, costs money and is less
  accurate than a string comparison. Cases carry a `lint` block instead.
- Trimmed sections 4, 5, 6 and the sources note to pay for section 0. Every
  dropped row is still in `references/be-nl.md`.
- `validate.py` scans `references/` and the fixtures for em-dashes, requires a
  `lint` variant on every eval case, and runs the linter self-test.

### Fixed

- `validate.py` silently skipped the changelog version check when a manifest was
  missing, so one missing file disabled an unrelated check.
- `validate.py` built an em-dash exemption set that could never match, leaving
  `references/be-nl.md` unscanned.
- The linter no longer flags `Zullen we even bellen?`. The proposal and the
  question are correct Dutch; only the declarative future is a tell.

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
