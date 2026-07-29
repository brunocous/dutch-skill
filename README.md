# dutch-native

A portable skill that makes LLMs write Dutch instead of translating English into Dutch. Covers Belgian and Netherlands localisation.

## The problem it targets

Language models compose in English and render into Dutch. The result is grammatical and still obviously foreign: no modal particles, missing `er`, `zullen` everywhere, nominalised verbs, English adverb order, calqued prepositions. Spelling checkers do not catch any of this, because none of it is a spelling error.

## Layout

The repo follows the [openai/plugins](https://github.com/openai/plugins) convention: the skill lives at `skills/<name>/SKILL.md` and the manifests sit beside it.

```
dutch-skill/
├── skills/
│   └── dutch-native/
│       ├── SKILL.md                  # the rules, loads when the skill triggers
│       ├── references/
│       │   └── be-nl.md              # BE/NL word lists, loads only when needed
│       └── evals/                    # test cases, see Evals below
├── .codex-plugin/plugin.json         # Codex plugin manifest
├── .claude-plugin/
│   ├── plugin.json                   # Claude plugin manifest
│   └── marketplace.json              # Claude marketplace
└── .agents/plugins/marketplace.json  # Codex marketplace
```

That one path is doing the load-bearing work. `skills/<name>/SKILL.md` is the *default* skill location for the Claude plugin spec and the Codex plugin spec alike, so both hosts find the skill without a custom path and without a second copy of the file. Everything else here is metadata.

## Install

### As a plugin

The repo is its own single-plugin marketplace on both sides, so there is nothing to clone.

Claude Code:

```text
/plugin marketplace add brunocous/dutch-skill
/plugin install dutch-native@dutch-native
/reload-plugins
```

Codex CLI:

```bash
codex plugin marketplace add brunocous/dutch-skill
codex plugin add dutch-native@dutch-native
```

In both, `owner/repo` is the GitHub path, and `dutch-native@dutch-native` reads as `plugin@marketplace`. The two names match here only because this repo ships one plugin.

Invoke it as `/dutch-native` in Claude Code and `$dutch-native` in Codex, or let it trigger on any Dutch writing task. Restart Codex or the ChatGPT desktop app if the plugin does not show up. This route also picks up updates, which the clone route below does not.

### As a bare skill, without the plugin machinery

If you would rather not install a plugin, copy the skill folder into the directory your agent scans. Note that the skill is a *subdirectory* of the repo, so this is a clone followed by a copy:

```bash
git clone --depth 1 https://github.com/brunocous/dutch-skill.git /tmp/dutch-skill

# Claude Code, personal
cp -R /tmp/dutch-skill/skills/dutch-native ~/.claude/skills/

# Codex, personal. Note .agents/skills, not .codex/skills
mkdir -p ~/.agents/skills && cp -R /tmp/dutch-skill/skills/dutch-native ~/.agents/skills/
```

For project scope, use `.claude/skills/` or `.agents/skills/` inside the repo that needs it, and commit the folder. Run `/skills` in either tool to confirm it loaded.

### Claude apps (claude.ai, desktop)

Settings → Capabilities → Skills takes a zip. The folder itself must be at the zip root, not the loose files:

```bash
git clone https://github.com/brunocous/dutch-skill.git dutch-native
zip -r dutch-native.zip dutch-native -x '*.git*'
```

### ChatGPT Custom GPT

The instruction box caps at 8000 characters. Paste everything in `skills/dutch-native/SKILL.md` **below** the YAML frontmatter: that is 7749 characters and fits unmodified. The frontmatter is only there for agents that read it, and pasting it costs you 340 characters you need.

Upload `skills/dutch-native/references/be-nl.md` under Knowledge.

### Project instructions (Claude Projects, ChatGPT Projects)

Paste `skills/dutch-native/SKILL.md` into the project instructions and upload `references/be-nl.md` as project knowledge or a project file. Section 6 of the skill points at that filename, so keep the name.

### Any model, one-off

Paste `SKILL.md` at the top of the conversation. Append `references/be-nl.md` too if the text is BE/NL sensitive.

## Evals

Seeing the skill trigger only tells you Claude found it. Whether the output is actually better than the same model with no skill is a separate question, and the only way to answer it is a baseline comparison: run each prompt twice, once with the skill and once without, and compare.

`skills/dutch-native/evals/evals.json` holds four test cases in the [skill-creator format](https://agentskills.io/skill-creation/evaluating-skills): a BE email, an NL LinkedIn post, an unspecified-variant prompt that the skill should answer by *asking*, and a repair pass over `evals/files/translationese.md`, a fixture that deliberately contains every one of the seven structural tells.

The assertions are deliberately mechanical, because that is what this skill claims to fix. `"Drie opties zijn beschikbaar is rewritten to an er construction"` can be graded; `"the Dutch sounds natural"` cannot.

To run the loop:

```text
/plugin install skill-creator@claude-plugins-official
/reload-plugins
```

Then ask Claude to `evaluate my dutch-native skill with skill-creator`. It runs each case in a fresh subagent, grades the assertions into `grading.json`, and aggregates with-skill against without-skill into `benchmark.json` so you can see the pass-rate gain against the token cost.

Two things to watch when reading results, both from the guidance in that doc:

- An assertion that passes **without** the skill is not evidence the skill works. The base model already handles it. Replace it.
- An assertion that fails in both arms is usually a broken assertion, not a hard test case.

The cases here are a starting point and have not been run against a benchmark yet, so no pass rates are claimed.

## Design constraints

- The body of `SKILL.md` is under 8000 characters so it fits a Custom GPT instruction box unmodified.
- Every rule is checkable. No rule says "write naturally".
- The review loop in section 8 is greppable, so it survives being run by a weaker model.
- Rules only. No copied text from any advice site.

## Sources

Rules follow the consensus of Taaladvies.net (Nederlandse Taalunie, Genootschap Onze Taal, Instituut voor de Nederlandse Taal, Team Taaladvies van de Vlaamse overheid) and the VRT Taalcharter. Language rules are facts and are restated here in this project's own words. No advice text is reproduced. Those sources are authoritative; this file is not.

Note that vrttaal.net stopped being updated and VRT now refers to Team Taaladvies and het Groene Boekje.

## Licence

[CC BY 4.0](LICENSE). Use it, adapt it, ship it commercially. Just credit "dutch-native by Bruno Coussement" with a link to this repo, and say if you changed anything.

## Contributing

Useful contributions are counterexamples: a Dutch sentence this skill judges wrong that a native speaker would write, or a translationese pattern the seven tells do not catch. Open an issue with the pair.
