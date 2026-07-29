# dutch-native

[![CI](https://github.com/brunocous/dutch-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/brunocous/dutch-skill/actions/workflows/ci.yml)

A portable skill that makes LLMs write Dutch instead of translating English into Dutch. Covers Belgian and Netherlands localisation.

## The problem it targets

Language models compose in English and render into Dutch. The result is grammatical and still obviously foreign: no modal particles, missing `er`, `zullen` everywhere, nominalised verbs, English adverb order, calqued prepositions. Spelling checkers do not catch any of this, because none of it is a spelling error.

## What it looks like

Every sentence on the left is correct Dutch. A spelling checker passes all of it. It is still not something anyone would write.

**Before** ([`evals/files/letterlijk.md`](skills/dutch-native/evals/files/letterlijk.md)):

> Ik hoop dat deze mail je goed vindt.
>
> Ik wilde even de basis aanraken over het project waar we vorige week over spraken. Ik denk dat we op dezelfde pagina moeten zitten voordat we voortbewegen, want aan het einde van de dag is het de klant die de rekening betaalt.
>
> In termen van de planning: we hebben momenteel geen bandbreedte om dit voor het einde van de maand op te pakken. Ik ben ok met dat, maar ik wil er zeker van zijn dat jij ook comfortabel bent met de timing.
>
> Wij zijn erg opgewonden over waar dit naartoe gaat. Als we de laaghangende vruchten eerst plukken, denk ik dat we een echte game changer in handen hebben.
>
> Ik waardeer je tijd en kijk ernaar uit om van jou te horen.

**After:**

> Even over het project van vorige week. Voor we verder gaan wil ik zeker weten dat we hetzelfde voor ogen hebben, want uiteindelijk is het de klant die betaalt.
>
> Qua planning: we krijgen dit deze maand niet meer rond. Dat is wat mij betreft geen probleem, maar ik wil wel weten of jij daarmee uit de voeten kunt.
>
> Als we beginnen met wat er voor het rapen ligt, scheelt dat later een hoop werk. De cijfers neem ik graag een keer rustig met je door.
>
> Zullen we volgende week even bellen? Laat maar weten wat jou schikt.

Three things to notice. `Ik hoop dat deze mail je goed vindt` is not translated, it is deleted: the sentence exists only because English business mail needs a runway. `opgewonden` is not what `excited` means in this register. And the rewrite is a third shorter, because the politeness scaffolding carried no information.

`python3 scripts/lint.py` counts 16 errors in the first and none in the second.

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

The instruction box caps at 8000 characters. Paste everything in `skills/dutch-native/SKILL.md` **below** the YAML frontmatter: that is 7664 characters and fits unmodified. The whole file is 8005 characters and does not fit, and the frontmatter it would spend those 341 characters on is only there for agents that read it.

Count characters, not bytes. The skill contains `ë`, `ï`, `€` and `→`, so the byte length overstates it by 84 and can talk you out of a paste that would have fitted. `scripts/validate.py` enforces the character budget on every push.

Upload `skills/dutch-native/references/be-nl.md` under Knowledge.

### Project instructions (Claude Projects, ChatGPT Projects)

Paste `skills/dutch-native/SKILL.md` into the project instructions and upload `references/be-nl.md` as project knowledge or a project file. Section 6 of the skill points at that filename, so keep the name.

### Any model, one-off

Paste `SKILL.md` at the top of the conversation. Append `references/be-nl.md` too if the text is BE/NL sensitive.

## Evals

Seeing the skill trigger only tells you Claude found it. Whether the output is actually better than the same model with no skill is a separate question, and the only way to answer it is a baseline comparison: run each prompt twice, once with the skill and once without, and compare.

`skills/dutch-native/evals/evals.json` holds six test cases in the [skill-creator format](https://agentskills.io/skill-creation/evaluating-skills):

| # | What it tests |
| --- | --- |
| 1 | A BE email: `u` throughout, Flemish closing, a modal particle that earns its place |
| 2 | An NL LinkedIn post: `je`, sentence-case heading, audible rhythm |
| 3 | An unspecified variant: resolve it and say so, without blocking on a question |
| 4 | Repairing `translationese.md`, which carries all seven structural tells |
| 5 | Reviewing `native-be.md`, which is already good. The right answer is to leave it alone |
| 6 | Rewriting `letterlijk.md`, grammatical Dutch that is pure English idiom |

Case 5 is the one most eval suites lack. Every other case rewards finding defects, which is exactly the pressure that makes a skill invent them. Case 5 fails if the model "corrects" idiomatic Flemish into Netherlands Dutch, or pads a clean text with particles to hit a quota.

**Mechanical assertions are not graded by a model.** Roughly half of what this skill promises is a string operation, and paying a language model to decide whether a text contains an em-dash is slower, costs money and is less accurate than a one-line string comparison. Those checks live in `scripts/lint.py` and run offline and free. Each eval case carries a `lint` block naming the variant to lint its output against. What is left in `assertions` is only what needs a reader: consistency, register, rhythm, and whether the text reads as composed in Dutch.

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

## The linter

```bash
python3 scripts/lint.py draft.md               # variant inferred from marker words
python3 scripts/lint.py --variant be draft.md
python3 scripts/lint.py --json draft.md
python3 scripts/lint.py --self-test
```

Section 8 of the skill is a review loop written as grep steps. This is that loop as code. It grades *output*, so it works on text from any model, and on text a person wrote.

```text
skills/dutch-native/evals/files/letterlijk.md, variant: NL
  ! L3    letterlijk vertaald idioom: 'hoop dat deze mail je goed vindt'  -> schrap het, begin bij je punt
  ! L5    calque: 'aan het einde van de dag'  -> uiteindelijk
  ! L5    letterlijk vertaald idioom: 'op dezelfde pagina'  -> het eens zijn
  ! L7    letterlijk vertaald idioom: 'bandbreedte'  -> tijd, ruimte
  ? L9    naamwoordstijl: 'het uitvoeren van'  -> T4: use the verb
16 fout(en), 1 waarschuwing(en).
```

`!` is an error: deterministic, high confidence, a hit is a defect. `?` is a warning: a heuristic worth a look, never a build failure. Rules that cannot tell native Dutch from translationese are warnings or they are deleted.

**How the rules are tested.** `--self-test` runs every rule against four committed fixtures and requires them to separate: `translationese.md` and `letterlijk.md` must trigger, `native-be.md` and `native-nl.md` must stay silent. The second half is the part that matters. Without a known-good fixture, a regex that silently stopped matching looks exactly like text that has no defects. `scripts/validate.py` runs the self-test, so CI covers it.

## Design constraints

- The body of `SKILL.md` is under 8000 characters so it fits a Custom GPT instruction box unmodified.
- Every rule is checkable. No rule says "write naturally".
- The review loop in section 8 is greppable, so it survives being run by a weaker model.
- Rules only. No copied text from any advice site.

## Checks and releases

```bash
python3 scripts/validate.py
```

No dependencies, and CI runs the same script, so a green local run means a green CI run. It checks what is easy to break without noticing:

- the four manifests agree on the plugin name and version
- the `SKILL.md` body stays inside the 8000-character Custom GPT budget, counted in characters
- the frontmatter carries `name` and `description`, and `name` matches the directory
- every file the skill and the evals point at actually exists
- no stray em-dash in the prose this repo ships, including `references/` and the fixtures, since the skill bans them. `translationese.md` is exempt: it carries one on purpose
- every eval case names the variant to lint its output against, so a case cannot silently go unlinted
- `scripts/lint.py` passes its self-test, which is what stops a rule from rotting into silence

CI also builds the claude.ai upload zip on every run and checks that `SKILL.md` lands at `dutch-native/SKILL.md` inside it, so the upload instructions cannot rot.

To release, bump the version in all three manifests, move the `Unreleased` entries into a new section in [CHANGELOG.md](CHANGELOG.md), and push a `v<version>` tag. The release workflow refuses a tag that disagrees with the manifests, then publishes the zip with that section as the release notes.

## Sources

Rules follow the consensus of Taaladvies.net (Nederlandse Taalunie, Genootschap Onze Taal, Instituut voor de Nederlandse Taal, Team Taaladvies van de Vlaamse overheid) and the VRT Taalcharter. Language rules are facts and are restated here in this project's own words. No advice text is reproduced. Those sources are authoritative; this file is not.

Note that vrttaal.net stopped being updated and VRT now refers to Team Taaladvies and het Groene Boekje.

## Licence

[CC BY 4.0](LICENSE). Use it, adapt it, ship it commercially. Just credit "dutch-native by Bruno Coussement" with a link to this repo, and say if you changed anything.

## Contributing

**The bar first, so nobody wastes an evening.** A rule earns space in `SKILL.md` only if it changes what a model writes. `SKILL.md` has about 86 characters of headroom against the Custom GPT budget, so every addition is really a swap, and "this is also true" is not an argument for including something.

The most useful contribution is a counterexample, and it now has a shape:

- **The skill flagged something a native would write.** That is a false positive, and it is the more valuable kind. Run `python3 scripts/lint.py --variant be yourtext.md`, paste the output, and say what you would have written. If a lint rule caused it, that rule is wrong until proven otherwise.
- **The skill missed a pattern.** Add the sentence to `evals/files/letterlijk.md` or `translationese.md`, or open an issue with the prompt, what the model wrote, and what a Fleming or Nederlander would have written instead.

Where a fix belongs, since there are four surfaces and it is not obvious:

| It is... | It goes in |
| --- | --- |
| a fixed English phrase rendered word for word | `IDIOMS` or `CALQUES` in `scripts/lint.py` |
| a word that is BE or NL but not both | `references/be-nl.md` |
| a loanword the keep/translate rule gets wrong | section 5 of `SKILL.md` |
| a whole-text behaviour, not a word | a new case in `evals/evals.json` |

Anything added to `lint.py` must pass `--self-test`: it has to fire on the translationese fixtures and stay silent on the native ones. That is the whole quality bar for a rule, and it is deliberately hard to pass.

## Corpus

`scripts/scrape.py` pulls the two sources this skill can use, and deliberately skips the roughly 5,900 remaining advice pages on vlaanderen.be, which are a lookup table rather than skill content.

```bash
python3 scripts/scrape.py            # all three
python3 scripts/scrape.py --only labels
```

| Source | What | Licence |
| --- | --- | --- |
| vlaanderen.be spellingregels | 57 rule pages | free reuse, art. II.55 Bestuursdecreet |
| vlaanderen.be tips | 33 clarity pages | free reuse |
| taaladvies.net | BE/NL usage labels for 399 lemmas | all rights reserved: facts only |

Output lands in `data/`, which is gitignored, and **nothing is written into `references/` automatically.** Two reasons. Advice pages are built out of imperative sentences, so scraped prose distilled into a reference file becomes a standing instruction the skill carries forever. And taaladvies.net is all rights reserved, so only the fact (lemma, regional status, source URL) may be kept, never the Vraag/Antwoord body. Promotion into `references/` is a human step, tables only.

One finding worth recording, because it contradicts the reason the scrape was written: the 399 regionally labelled lemmas are mostly *contested* words, which is a different distribution from *common* ones. `captatiewagen`, `ei zo na` and `bedampte ruiten` will never appear in a LinkedIn post, while the words that actually mark a text as Flemish, `gsm`, `verlof`, `onthaal`, `opvolgen`, were already in the hand-written `references/be-nl.md`. The corpus is kept for reference, but it did not earn a place in the skill.
