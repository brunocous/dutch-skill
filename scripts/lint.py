#!/usr/bin/env python3
"""Deterministic checks for Dutch text.

The skill's section 8 is a review loop written as grep steps. This is that loop
as code. It grades *output*, not prompts, so it works on text from any model and
on text a human wrote.

    python3 scripts/lint.py draft.md
    python3 scripts/lint.py --variant nl draft.md
    python3 scripts/lint.py --json draft.md
    python3 scripts/lint.py --self-test

Why this exists as a separate tool rather than as eval assertions: roughly half
of what the skill promises is a string operation. Paying a language model to
decide whether a text contains an em-dash is slower, costs money, and is less
accurate than `"—" in text`. Those checks live here, run offline and free,
and the eval suite keeps only the judgements a model is actually needed for.

Severity:
  error  deterministic and high confidence. A hit is a defect.
  warn   heuristic. A hit is worth a human look, not a build failure.

Exit codes: 0 clean or warnings only, 1 errors found, 2 bad usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "dutch-native"
FIXTURES = SKILL_DIR / "evals" / "files"

EM_DASH = "—"

# Section 4. The replacement is what the skill tells you to write instead, so it
# doubles as the fix hint in the output.
CALQUES = [
    (r"voel je vrij om", "laat gerust iets weten"),
    (r"voelt u zich vrij om", "laat gerust iets weten"),
    (r"wij zijn verheugd", "vanaf vandaag kan je..."),
    (r"we zijn verheugd", "vanaf vandaag kan je..."),
    (r"maak zeker dat", "zorg dat, let erop dat"),
    (r"\badresseren\b", "aanpakken"),
    (r"\bimpacteren\b", "gevolgen hebben voor"),
    (r"aan het einde van de dag", "uiteindelijk"),
    (r"wij geloven dat", "schrap het, zeg wat je doet"),
    (r"we geloven dat", "schrap het, zeg wat je doet"),
    (r"\bnaadloos\b", "zonder gedoe, je merkt er niets van"),
    (r"\buitdagingen\b", "problemen, knelpunten"),
]

# English idioms carried across word for word. Each one is grammatical Dutch and
# means nothing to a Dutch reader, which is why a spelling checker never flags
# them and why they are the loudest sign of a literal translation.
IDIOMS = [
    (r"hoop dat deze (mail|e-mail) (je|u) goed vindt", "schrap het, begin bij je punt"),
    (r"\bin termen van\b", "wat ... betreft, qua"),
    (r"de basis aanraken", "even bijpraten"),
    (r"op dezelfde pagina", "het eens zijn"),
    (r"laaghangend[e]? vrucht", "wat voor het rapen ligt"),
    (r"de bal ligt (nu )?in (jouw|uw|je) kamp", "nu is het aan jou"),
    (r"\bvoortbeweg(en|end)\b", "verder gaan, hierna"),
    (r"\bbandbreedte\b", "tijd, ruimte"),
    (r"diep(er)? duiken", "uitspitten, grondig bekijken"),
    (r"offline nemen", "apart bespreken"),
    (r"kijk ernaar uit om", "ik hoor graag van je"),
    (r"waardeer (je|uw) tijd", "bedankt voor je tijd"),
    (r"\bopgewonden\b", "blij, benieuwd"),
    (r"comfortabel (bent|zijn) met", "akkoord gaan met"),
    (r"\bgame.?changer\b", "zeg wat het verandert"),
    (r"werkt (dat|dit) voor (jou|u)", "schikt dat?"),
]

# Section 7 and section 8 step 3. Stiff formal register that reads as translated
# officialese rather than as Dutch.
STIFF = [
    (r"\bteneinde\b", "om te"),
    (r"\bmiddels\b", "met, via"),
    (r"\bdient te\b", "moet"),
    (r"\bdienen te\b", "moeten"),
]

# Section 6. Words that place a text in the wrong variant. Only the
# high-frequency, uncontested ones: these are what actually fingerprints a text.
NL_ONLY = ["hartstikke", "ontzettend", "prima", "best wel", "zo meteen",
           "mobieltje", "pinnen", "gezellig", "leuk"]
BE_ONLY = ["goesting", "kuisen", "plezant", "seffens", "camion", "chauffage",
           "gsm", "onthaal", "solden", "confituur", "living", "kot"]

# Section 2, T1. Only the particles whose non-particle homograph is rare enough
# that a bare word count means something. `maar`, `al`, `nu` and `even` are
# excluded on purpose: they are far more often conjunction, adverb or adjective,
# so counting them measures the wrong thing.
PARTICLES = ["wel", "toch", "eens", "gewoon", "hoor", "zeker", "nou", "maar eens"]

MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
          "augustus", "september", "oktober", "november", "december"]
DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag",
        "zondag"]

# Words that legitimately start a heading with a capital even in sentence case.
HEADING_PROPER = {"nederlands", "vlaams", "belgisch", "europa", "linkedin",
                  "claude", "chatgpt", "dutch"}


class Finding:
    def __init__(self, line, severity, rule, message, fix=None):
        self.line = line
        self.severity = severity
        self.rule = rule
        self.message = message
        self.fix = fix

    def as_dict(self):
        return {"line": self.line, "severity": self.severity, "rule": self.rule,
                "message": self.message, "fix": self.fix}


def strip_code_and_inline(text):
    """Blank out fenced code blocks so rules do not fire on samples.

    Replaces content with spaces rather than deleting it, so line and column
    numbers stay true.
    """
    out = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def split_sentences(text):
    """Return (sentence, line_number) pairs.

    Deliberately crude. Dutch abbreviations that end in a full stop will split
    wrongly; that costs a little precision on the rhythm warnings and nothing on
    the error-severity rules, none of which depend on sentence boundaries being
    exact.
    """
    pairs = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ">", "|", "-", "*")):
            continue
        for part in re.split(r"(?<=[.!?])\s+", stripped):
            part = part.strip()
            if part:
                pairs.append((part, lineno))
    return pairs


def word_count(sentence):
    return len(re.findall(r"[\w'’-]+", sentence, re.UNICODE))


def check_em_dash(text, findings):
    for lineno, line in enumerate(text.splitlines(), 1):
        if EM_DASH in line:
            findings.append(Finding(lineno, "error", "em-dash",
                                    "em-dash (U+2014)",
                                    "komma, punt of dubbelepunt"))


def check_phrases(text, findings):
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for pattern, fix in CALQUES:
            for m in re.finditer(pattern, low):
                findings.append(Finding(lineno, "error", "calque",
                                        "calque: '%s'" % line[m.start():m.end()],
                                        fix))
        for pattern, fix in IDIOMS:
            for m in re.finditer(pattern, low):
                findings.append(Finding(lineno, "error", "idioom",
                                        "letterlijk vertaald idioom: '%s'" % line[m.start():m.end()],
                                        fix))
        for pattern, fix in STIFF:
            for m in re.finditer(pattern, low):
                findings.append(Finding(lineno, "error", "stiff",
                                        "ambtenarentaal: '%s'" % line[m.start():m.end()],
                                        fix))


def check_welke(text, findings):
    """`welke` as a relative pronoun. Interrogative `welke` is correct Dutch.

    Heuristic: a question mark anywhere in the sentence, or `welke` as the first
    word, reads as interrogative and is left alone.
    """
    for sentence, lineno in split_sentences(text):
        if "welke" not in sentence.lower():
            continue
        if sentence.rstrip().endswith("?"):
            continue
        if sentence.lower().lstrip().startswith("welke"):
            continue
        findings.append(Finding(lineno, "error", "welke",
                                "'welke' as a relative pronoun",
                                "die of dat"))


def check_echter(text, findings):
    for sentence, lineno in split_sentences(text):
        if re.match(r"^echter\s*,", sentence.strip(), re.IGNORECASE):
            findings.append(Finding(lineno, "error", "echter",
                                    "sentence-initial 'Echter,' is an English comma-adverb",
                                    "'... echter ...' mid-sentence, or 'Maar ...'"))


def check_comparatives(text, findings):
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for m in re.finditer(r"\b(groter|kleiner|beter|slechter|meer|minder|hoger|lager)\s+als\b", low):
            findings.append(Finding(lineno, "error", "als-dan",
                                    "'%s' should be 'dan'" % line[m.start():m.end()],
                                    "... dan"))
        for m in re.finditer(r"\baan hun\b", low):
            findings.append(Finding(lineno, "error", "hun-hen",
                                    "'aan hun' as an indirect object", "aan hen"))


def check_dates(text, findings):
    for lineno, line in enumerate(text.splitlines(), 1):
        for month in MONTHS + DAYS:
            for m in re.finditer(r"\b%s\b" % month.capitalize(), line):
                # Sentence-initial is legitimate.
                before = line[:m.start()].rstrip()
                if before and not before.endswith((".", "!", "?", ":")):
                    findings.append(Finding(lineno, "error", "month-case",
                                            "'%s' capitalised mid-sentence" % month.capitalize(),
                                            month))
        for month in MONTHS:
            if re.search(r"\b%s\s+\d{1,2}\b" % month, line, re.IGNORECASE):
                findings.append(Finding(lineno, "error", "date-order",
                                        "English date order",
                                        "21 %s 2025" % month))


def check_headings(text, findings):
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip()
        if not heading:
            continue
        if heading.endswith("."):
            findings.append(Finding(lineno, "error", "heading-stop",
                                    "heading ends with a full stop", "drop it"))
        words = re.findall(r"[\w'’À-ɏ-]+", heading, re.UNICODE)
        capped = [w for w in words[1:]
                  if w[:1].isupper() and w.lower() not in HEADING_PROPER
                  and not w.isupper()]
        if len(words) >= 3 and len(capped) >= 2:
            findings.append(Finding(lineno, "error", "title-case",
                                    "Title Case heading: '%s'" % heading,
                                    "sentence case"))


def check_variant(text, variant, findings):
    if variant not in ("be", "nl"):
        return
    banned = NL_ONLY if variant == "be" else BE_ONLY
    other = "NL" if variant == "be" else "BE"
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for word in banned:
            for m in re.finditer(r"\b%s\b" % re.escape(word), low):
                findings.append(Finding(
                    lineno, "error", "variant",
                    "%s word '%s' in a %s text" % (other, word, variant.upper()),
                    "see references/be-nl.md"))


def check_particles(text, findings):
    sentences = split_sentences(text)
    if len(sentences) < 4:
        return
    joined = " ".join(s for s, _ in sentences).lower()
    hits = sum(len(re.findall(r"\b%s\b" % re.escape(p), joined)) for p in PARTICLES)
    ratio = hits / max(len(sentences), 1)
    if ratio < 0.15:
        findings.append(Finding(
            0, "warn", "particles",
            "modal particles: %d in %d sentences (%.2f per sentence)" % (hits, len(sentences), ratio),
            "T1: aim for roughly one or two per paragraph"))


def check_rhythm(text, findings):
    sentences = split_sentences(text)
    if len(sentences) < 5:
        return
    lengths = [word_count(s) for s, _ in sentences]
    lo, hi = min(lengths), max(lengths)
    mean = sum(lengths) / len(lengths)
    var = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    sd = var ** 0.5
    if sd < 4.0:
        findings.append(Finding(
            0, "warn", "rhythm",
            "sentence lengths %d-%d, sd %.1f" % (lo, hi, sd),
            "T7: vary from about 6 to 25 words"))
    # Three consecutive sentences opening the same way. Compares the first two
    # words, so `Wij doen X. Wij zijn Y.` and `Het team doet X. Het team is Y.`
    # both count, which the bare first-word test misses.
    openings = []
    for sentence, lineno in sentences:
        words = re.findall(r"[\w'’À-ɏ-]+", sentence.lower(), re.UNICODE)
        openings.append((" ".join(words[:2]), lineno))
    run = 1
    for i in range(1, len(openings)):
        if openings[i][0] and openings[i][0] == openings[i - 1][0]:
            run += 1
            if run >= 3:
                findings.append(Finding(
                    openings[i][1], "warn", "openings",
                    "three sentences in a row open with '%s'" % openings[i][0],
                    "T7: vary the opening"))
                run = 1
        else:
            run = 1


def check_nominalisation(text, findings):
    """T4. Verbs hidden in nouns."""
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for m in re.finditer(r"\bhet\s+\w+en\s+van\b", low):
            findings.append(Finding(lineno, "warn", "nominalisation",
                                    "naamwoordstijl: '%s'" % line[m.start():m.end()],
                                    "T4: use the verb"))
        for m in re.finditer(r"\bde\s+(uitvoering|realisatie|optimalisatie|implementatie)\s+van\b", low):
            findings.append(Finding(lineno, "warn", "nominalisation",
                                    "naamwoordstijl: '%s'" % line[m.start():m.end()],
                                    "T4: use the verb"))


def check_future(text, findings):
    """T3. `zullen` where the present tense is the Dutch default.

    Two uses are correct Dutch and are skipped: the proposal (`Zullen we even
    bellen?`) and any other question. Only the declarative future is a tell.
    """
    for sentence, lineno in split_sentences(text):
        if sentence.rstrip().endswith("?"):
            continue
        for m in re.finditer(r"\b(zullen|zal)\b\s+\w+", sentence, re.IGNORECASE):
            if m.start() == 0:
                continue
            findings.append(Finding(lineno, "warn", "zullen",
                                    "'%s' marks the future; Dutch usually does not" % m.group(1),
                                    "T3: present tense"))


def check_progressive(text, findings):
    """T3. `aan het ... zijn` calqued from the English -ing form."""
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"\baan het\s+\w+en\b", line, re.IGNORECASE):
            findings.append(Finding(lineno, "warn", "progressive",
                                    "progressive '%s'" % line[m.start():m.end()],
                                    "T3: plain present tense"))


ALL_CHECKS = [
    check_em_dash, check_phrases, check_welke, check_echter,
    check_comparatives, check_dates, check_headings, check_particles,
    check_rhythm, check_nominalisation, check_future, check_progressive,
]


def lint(text, variant=None):
    body = strip_code_and_inline(text)
    findings = []
    for check in ALL_CHECKS:
        check(body, findings)
    if variant:
        check_variant(body, variant, findings)
    findings.sort(key=lambda f: (f.line, f.rule))
    return findings


def guess_variant(text):
    """Infer BE or NL from uncontested marker words. None when there is no signal."""
    low = text.lower()
    be = sum(1 for w in BE_ONLY if re.search(r"\b%s\b" % re.escape(w), low))
    be += len(re.findall(r"met vriendelijke groeten", low))
    nl = sum(1 for w in NL_ONLY if re.search(r"\b%s\b" % re.escape(w), low))
    nl += len(re.findall(r"met vriendelijke groet\b", low))
    if be > nl:
        return "be", be
    if nl > be:
        return "nl", nl
    return None, 0


def render(path, findings, variant, inferred, stream=sys.stdout):
    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    label = variant.upper() if variant else "onbekend"
    how = " (afgeleid)" if inferred else ""
    print("%s, variant: %s%s" % (path, label, how), file=stream)
    for f in findings:
        where = "L%-4d" % f.line if f.line else "  -  "
        mark = "!" if f.severity == "error" else "?"
        line = "  %s %s %s" % (mark, where, f.message)
        if f.fix:
            line += "  -> %s" % f.fix
        print(line, file=stream)
    if not findings:
        print("  geen opmerkingen", file=stream)
    print("%d fout(en), %d waarschuwing(en). Niet gecontroleerd: register, opbouw, "
          "en of de tekst in het Nederlands bedacht is." % (len(errors), len(warns)),
          file=stream)


def self_test():
    """The graders are code, so they get tested like code.

    Every error-severity rule must fire on the translationese fixture and stay
    silent on the native fixtures. Without the second half, a regex that never
    matches is indistinguishable from clean text.
    """
    ok = True
    bad = FIXTURES / "translationese.md"
    if not bad.exists():
        print("FAIL: missing fixture %s" % bad)
        return False

    findings = lint(bad.read_text(encoding="utf-8"), variant="nl")
    fired = {f.rule for f in findings if f.severity == "error"}
    expected = {"em-dash", "calque", "stiff", "welke", "echter", "title-case"}
    missing = expected - fired
    if missing:
        print("FAIL: translationese.md did not trigger: %s" % ", ".join(sorted(missing)))
        ok = False
    else:
        print("  ok: translationese.md triggers %d error rules" % len(fired))

    # The literal-translation fixture is grammatical Dutch throughout. Only the
    # idiom rules can see it, which is exactly what it is there to prove.
    literal = FIXTURES / "letterlijk.md"
    if not literal.exists():
        print("FAIL: missing fixture %s" % literal)
        ok = False
    else:
        findings = lint(literal.read_text(encoding="utf-8"), variant="nl")
        idioms = [f for f in findings if f.rule == "idioom"]
        if len(idioms) < 8:
            print("FAIL: letterlijk.md raised only %d idiom findings, expected 8 or more"
                  % len(idioms))
            ok = False
        else:
            print("  ok: letterlijk.md triggers %d idiom findings" % len(idioms))

    for name, variant in (("native-be.md", "be"), ("native-nl.md", "nl")):
        path = FIXTURES / name
        if not path.exists():
            print("FAIL: missing fixture %s" % path)
            ok = False
            continue
        findings = lint(path.read_text(encoding="utf-8"), variant=variant)
        errors = [f for f in findings if f.severity == "error"]
        if errors:
            print("FAIL: %s is native Dutch but raised %d error(s):" % (name, len(errors)))
            for f in errors:
                print("    L%s %s (%s)" % (f.line, f.message, f.rule))
            ok = False
        else:
            print("  ok: %s is clean" % name)

    print("\nself-test %s" % ("passed" if ok else "FAILED"))
    return ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic checks for Dutch text.")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--variant", choices=["be", "nl"],
                        help="target variant. Inferred from marker words when omitted.")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--self-test", action="store_true",
                        help="run the graders against the committed fixtures")
    args = parser.parse_args(argv)

    if args.self_test:
        return 0 if self_test() else 1
    if not args.files:
        parser.print_usage(sys.stderr)
        print("lint.py: give it a file, or --self-test", file=sys.stderr)
        return 2

    total_errors = 0
    payload = []
    for path in args.files:
        if not path.exists():
            print("lint.py: no such file: %s" % path, file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
        variant, inferred = args.variant, False
        if not variant:
            variant, score = guess_variant(text)
            inferred = variant is not None
        findings = lint(text, variant=variant)
        total_errors += sum(1 for f in findings if f.severity == "error")
        if args.json:
            payload.append({"file": str(path), "variant": variant,
                            "inferred": inferred,
                            "findings": [f.as_dict() for f in findings]})
        else:
            render(path, findings, variant, inferred)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
