---
name: dutch-native
description: Write Dutch that was composed in Dutch, not translated from English. Use for any Dutch output or review of Dutch text. Handles Belgian (BE) and Netherlands (NL) localisation. Triggers on Nederlands, Vlaams, LinkedIn-post, mail, blog, landingspagina, offerte, rapport, nieuwsbrief.
license: CC BY 4.0
---

# Dutch that reads as Dutch

Language models compose in English and render into Dutch. The output is grammatical and still obviously foreign. This skill targets the rendering step.

## 0. Pick a variant first

Ask or infer once: **BE** or **NL**. Write it down. Never mix inside one text. If unknown, ask. Do not default silently.

Register default: BE leans one notch more formal than NL. In BE, `u` is safe with a stranger. In NL, `je` is normal in business writing and `u` can read as cold.

## 1. The generation rule

**Compose, do not convert.**

If an English draft exists, read it, close it, and write the Dutch from the point it makes. Sentence-by-sentence conversion preserves English clause order, English idiom, English abstraction level and English rhythm. Each of those is detectable on its own.

Diagnostic: if the Dutch sentences map one to one onto English sentences of similar length, it was translated.

## 2. The seven structural tells

These are generation defects, not vocabulary defects. Fixing these does more than any word list.

**T1. No modal particles.** English has no `wel, toch, eens, even, maar, nu, al, gewoon, hoor, zeker`. So the render drops them and the Dutch reads like a manual.
`Dat werkt.` → `Dat werkt wel.`
`Kun je dit controleren?` → `Kun je dit eens nakijken?`
`Ik zal het bekijken.` → `Ik bekijk het even.`
Dose: one or two per paragraph. Sprinkling is its own tell.

**T2. Missing `er`.** Dutch needs a presentational or pronominal `er` where English needs nothing.
`Drie opties zijn mogelijk.` → `Er zijn drie opties.`
`Niets is veranderd.` → `Er is niets veranderd.`
`Ik denk over na.` → `Ik denk erover na.`
Rule: a preposition with a non-human pronoun object contracts. `met het` → `ermee`, `over dat` → `daarover`, `van het` → `ervan`.

**T3. `zullen` and `aan het` overuse.** English marks future with *will* and progress with *-ing*. Dutch marks neither.
`We zullen volgende week lanceren.` → `We lanceren volgende week.`
`We zijn aan een oplossing aan het werken.` → `We werken aan een oplossing.`

**T4. Verbs hidden in nouns.** English tolerates nominalisation, Dutch turns it into ambtenarentaal.
`Het uitvoeren van de analyse gebeurt door het team.` → `Het team analyseert.`
`na de implementatie van het systeem` → `zodra het systeem draait`
Search for `-ing van`, `het -en van`, `de uitvoering`, `de realisatie`, `de optimalisatie`.

**T5. Adverbial order.** English is Manner, Place, Time. Dutch is **Time, Manner, Place**.
`We hebben elkaar op kantoor gisteren gezien.` → `We hebben elkaar gisteren op kantoor gezien.`
Also: `Echter, dit werkt niet.` is an English comma-adverb. Write `Dit werkt echter niet.` or `Maar dit werkt niet.`

**T6. Calqued prepositions.** Dutch verbs carry fixed prepositions that English does not predict.
`wachten op` (niet *voor*) · `zoeken naar` · `vragen naar, vragen om` · `bestaan uit` · `deelnemen aan` · `twijfelen aan` · `discussiëren over` · `afhangen van` · `verantwoordelijk voor` · `geïnteresseerd in` · `voorzien van` (uitrusten) vs `voorzien in` (invullen)

**T7. Flat rhythm.** Every sentence 12 to 18 words, every one opening with the subject. Vary from 6 to 25 and never open three sentences in a row the same way.

## 3. Two mechanical errors worth a grep

- **Adjective after `een` with a het-word takes no `-e`.** `een groot probleem`, `een goed idee`, `een nieuw systeem`. But `het grote probleem`, `een grote fout` (de-woord). Models get this wrong constantly.
- **Comma between a fronted subordinate clause and the main clause.** `Als je dat doet, werkt het.` English drops it, Dutch does not.

## 4. Calques to kill

| AI writes | Write instead |
| --- | --- |
| Voel je vrij om contact op te nemen | Laat gerust iets weten |
| Wij zijn verheugd aan te kondigen | Vanaf vandaag kan je... |
| Maak zeker dat | Zorg dat, let erop dat |
| het probleem adresseren | het probleem aanpakken |
| impacteren | gevolgen hebben voor |
| Aan het einde van de dag | Uiteindelijk |
| Wij geloven dat | (schrap, zeg wat je doet) |
| naadloos | zonder gedoe, je merkt er niets van |
| uitdagingen | problemen, knelpunten |
| teneinde | om te |

Back-translation test: render a smooth Dutch sentence word for word into English. If you land on a fluent English idiom, it is a calque.

## 5. The opposite error

Style guides tell you to replace English loanwords. In tech and business writing that produces text that is artificial in the other direction. No developer says `terugkoppeling` or `gegevensbank`.

**Keep:** feedback · deadline · meeting · call · budget · issue · release · deployment · backlog · sprint · dashboard · software · database · website · tool · template · workshop · demo · scope · roadmap · stakeholder · compliance · audit

**Translate, because the English is affectation:** `cancellen` → annuleren · `checken` → nakijken · `fixen` → oplossen · `updaten` → bijwerken · `alignen` → afstemmen · `challengen` → in vraag stellen · `sharen` → delen

Test: do the reader's own colleagues say it at work? Keep it. Is it an English verb with a Dutch ending glued on? Translate it.

## 6. BE and NL

Full lists in `references/be-nl.md`. The load-bearing differences:

| | BE | NL |
| --- | --- | --- |
| aanspreking | `u` is neutraal en veilig | `je` is normaal, `u` is afstandelijk |
| afsluiter | Met vriendelijke groeten | Met vriendelijke groet |
| volgorde bijzin | `omdat ik dat gezien heb` | `omdat ik dat heb gezien` |
| ontkende noodzaak | `Je moet dat niet doen` | `Je hoeft dat niet te doen` |
| telefoon | gsm | mobiel, mobieltje |
| vrije dagen | verlof | vakantie, vrij |
| dossier volgen | opvolgen | volgen, monitoren |
| balie | onthaal | receptie |
| intensiteit | heel, echt | hartstikke, ontzettend, prima |

Models default to NL, because NL dominates the training data. Flemish text that slips into `leuk`, `hartstikke`, `prima`, `best wel`, `zo meteen`, `mobieltje` was not written by a Fleming.

Belgicisms to avoid in either variant of written standard Dutch: `goesting`, `kuisen`, `iets aan 5 euro kopen`, `Ik heb dat gedaan geweest`, `wij zijn ons daaraan verwachten`.

## 7. Mechanics

- Headings in sentence case. No full stop, no Title Case, no colon subtitle. Title Case in a Dutch heading is the loudest translation artefact there is.
- No em-dashes (U+2014). Comma, full stop or colon.
- Days and months lowercase (`maandag`, `januari`). Languages and nationalities capitalised (`Nederlands`, `Vlaamse`).
- Numbers to twelve in letters. Thousands with a dot: `15.000`.
- Date `21 oktober 2025`, never `oktober 21, 2025`. Time `om 14.30 uur`. Amount `€ 1.200,50`.
- `die`/`dat` as relative pronoun, not `welke`.
- `groter dan`, never `groter als`. `aan hen`, not `aan hun`.
- Job titles lowercase: `de directeur`.

## 8. Review loop

Run in order. Stop at the first failure, fix, restart.

1. Variant declared and consistent? `u`/`je` consistent throughout?
2. Grep for the em-dash character. Zero hits.
3. Grep `welke`, `teneinde`, `middels`, `dient te`, `er wordt`, `Echter,`.
4. Count modal particles. Fewer than one per paragraph means T1.
5. Read every heading. Any Title Case, any full stop?
6. Back-translate the three smoothest sentences.
7. Read paragraph openings aloud. Do three in a row start the same way?
8. Check one `een + het-woord + adjective` per page.

## Sources and status

Rules follow the consensus of Taaladvies.net (Taalunie, Onze Taal, INT, Team Taaladvies) and the VRT Taalcharter, restated in this skill's own words. No text is copied from those sources. Where they disagree with this file, they win.

The BE/NL sections describe usage tendencies, not correctness. Both are standard Dutch.
