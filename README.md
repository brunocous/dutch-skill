# dutch-native

A portable skill that makes LLMs write Dutch instead of translating English into Dutch. Covers Belgian and Netherlands localisation.

## The problem it targets

Language models compose in English and render into Dutch. The result is grammatical and still obviously foreign: no modal particles, missing `er`, `zullen` everywhere, nominalised verbs, English adverb order, calqued prepositions. Spelling checkers do not catch any of this, because none of it is a spelling error.

## Install

**Claude (skills):** drop the folder in your skills directory. `SKILL.md` loads on trigger, `references/be-nl.md` loads on demand.

**Claude (Projects):** paste `SKILL.md` into project instructions. Upload `references/be-nl.md` as project knowledge.

**ChatGPT (Custom GPT):** paste `SKILL.md` into the instruction box. It is under 8000 characters by design. Upload `references/be-nl.md` as knowledge.

**ChatGPT (Projects):** paste `SKILL.md` into project instructions.

**Any model, one-off:** paste `SKILL.md` at the top of the conversation.

## Design constraints

- `SKILL.md` is under 8000 characters so it fits a Custom GPT instruction box unmodified.
- Every rule is checkable. No rule says "write naturally".
- The review loop in section 8 is greppable, so it survives being run by a weaker model.
- Rules only. No copied text from any advice site.

## Sources

Rules follow the consensus of Taaladvies.net (Nederlandse Taalunie, Genootschap Onze Taal, Instituut voor de Nederlandse Taal, Team Taaladvies van de Vlaamse overheid) and the VRT Taalcharter. Language rules are facts and are restated here in this project's own words. No advice text is reproduced. Those sources are authoritative; this file is not.

Note that vrttaal.net stopped being updated and VRT now refers to Team Taaladvies and het Groene Boekje.

## Licence

CC BY 4.0.

## Contributing

Useful contributions are counterexamples: a Dutch sentence this skill judges wrong that a native speaker would write, or a translationese pattern the seven tells do not catch. Open an issue with the pair.
