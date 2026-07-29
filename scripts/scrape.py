#!/usr/bin/env python3
"""Pull the two Dutch language-advice corpora this skill can actually use.

Deliberately narrow. There are about 5,900 advice pages on vlaanderen.be, and
they are a lookup table, not skill content: a rule only earns space in SKILL.md
if it changes what a model writes. So this fetches three things and stops.

  1. spellingregels  59 rule pages from vlaanderen.be
  2. tips            33 clarity pages from vlaanderen.be
  3. labels          BE/NL usage labels from taaladvies.net

Licence, and why the three are treated differently:

  vlaanderen.be grants unconditional reuse under article II.55 of the
  Bestuursdecreet, stated in its own disclaimer. Text from sources 1 and 2 is
  redistributable. We attribute anyway.

  taaladvies.net is all rights reserved (Nederlandse Taalunie), and its terms
  forbid reproducing the site elsewhere. So source 3 extracts *facts only*:
  lemma, regional status label, source URL. A row saying `farde is standaardtaal
  in Belgie` is a fact about Dutch, not a copy of anyone's prose. No Vraag,
  Antwoord or Toelichting body is written to disk in a shippable file.

Output goes to data/, which is gitignored. Nothing lands in references/
automatically: scraped prose read by a model becomes an instruction the skill
carries forever, and advice pages are made of imperative sentences. Promotion
into references/ is a human step, by hand, tables only.

    python3 scripts/scrape.py            # all three
    python3 scripts/scrape.py --only labels
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

UA = "dutch-skill-scraper/1.0 (+https://github.com/brunocous/dutch-skill)"
DELAY = 0.7

VL = "https://www.vlaanderen.be"
SPELLING_INDEX = VL + "/team-taaladvies/spellingregels"
TIPS_INDEX = VL + "/team-taaladvies/tips-voor-duidelijke-taal"
TAALADVIES_API = "https://taaladvies.net/wp-json/wp/v2/posts"

# The controlled vocabulary taaladvies.net marks up inline. These ids are the
# whole reason this source is worth touching: they are the only machine-readable
# BE/NL judgement anywhere, and the skill's section 6 problem is that models
# default to NL.
LABELS = {
    "113": "standaardtaal",
    "114": "standaardtaal in Belgie",
    "115": "standaardtaal in Nederland",
    "129": "status onduidelijk",
}
REGIONAL = {"114", "115"}


def fetch(url: str, cache_key: str | None = None) -> str:
    """GET with an on-disk cache, so re-parsing never re-fetches."""
    RAW.mkdir(parents=True, exist_ok=True)
    key = cache_key or hashlib.sha1(url.encode()).hexdigest()
    path = RAW / (key + ".txt")
    if path.exists():
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError("HTTP %s for %s" % (exc.code, url)) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("network error for %s: %s" % (url, exc.reason)) from exc
    path.write_text(body, encoding="utf-8")
    time.sleep(DELAY)
    return body


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|li|h[1-6]|tr)>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def expect(count: int, low: int, what: str) -> None:
    """Fail loudly on a silently empty or truncated extraction.

    An empty result and a broken parser look identical downstream, and that is
    the failure mode that produces plausible wrong data.
    """
    if count < low:
        raise SystemExit(
            "scrape: expected at least %d %s, got %d. The page shape probably "
            "changed; fix the parser rather than shipping a short corpus." % (low, what, count)
        )


def index_links(index_url: str, pattern: str, cache_key: str) -> list:
    html = fetch(index_url, cache_key)
    seen, out = set(), []
    for m in re.finditer(r'href="(%s)"' % pattern, html):
        href = m.group(1)
        if href not in seen:
            seen.add(href)
            out.append(VL + href if href.startswith("/") else href)
    return out


def scrape_spelling() -> list:
    links = index_links(
        SPELLING_INDEX,
        r"/team-taaladvies/spellingregels/[^\"#]+/[^\"#]+",
        "index-spellingregels",
    )
    expect(len(links), 40, "spelling rule links")
    print("  spellingregels: %d pages" % len(links))
    rows = []
    for i, url in enumerate(links, 1):
        html = fetch(url)
        text = strip_tags(html)
        title = ""
        m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
        if m:
            title = strip_tags(m.group(1))
        rows.append({"source": "vlaanderen.be/spellingregels", "url": url,
                     "title": title, "text": text})
        if i % 15 == 0:
            print("    %d/%d" % (i, len(links)))
    return rows


def scrape_tips() -> list:
    links = index_links(
        TIPS_INDEX,
        r"/team-taaladvies/taaladviezen/teksten-schrijven/[^\"#]+",
        "index-tips",
    )
    expect(len(links), 20, "tips links")
    print("  tips: %d pages" % len(links))
    rows = []
    for url in links:
        html = fetch(url)
        title = ""
        m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
        if m:
            title = strip_tags(m.group(1))
        rows.append({"source": "vlaanderen.be/tips", "url": url,
                     "title": title, "text": strip_tags(html)})
    return rows


def scrape_labels() -> list:
    """Facts only: lemma, label, url. No advice prose is retained."""
    rows, page = [], 1
    while True:
        url = ("%s?per_page=100&page=%d&_fields=slug,link,title,content"
               % (TAALADVIES_API, page))
        try:
            body = fetch(url, "taaladvies-page-%d" % page)
        except RuntimeError as exc:
            if "HTTP 400" in str(exc):  # past the last page
                break
            raise
        batch = json.loads(body)
        if not batch:
            break
        for post in batch:
            html = post.get("content", {}).get("rendered", "")
            found = {}
            for m in re.finditer(r'type="tao_term/(\d+)"[^>]*>([^<]*)</a>', html):
                tid = m.group(1)
                if tid in LABELS:
                    found[tid] = LABELS[tid]
            regional = sorted(set(found) & REGIONAL)
            if not regional:
                continue
            rows.append({
                "lemma": unescape(strip_tags(post.get("title", {}).get("rendered", ""))),
                "labels": [LABELS[t] for t in regional],
                "all_labels": sorted(found.values()),
                "url": post.get("link", ""),
            })
        print("    page %d, %d labelled so far" % (page, len(rows)))
        if len(batch) < 100:
            break
        page += 1
    expect(len(rows), 200, "regionally labelled lemmas")
    return rows


def write_jsonl(name: str, rows: list) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("  wrote %s (%d rows)" % (path.relative_to(ROOT), len(rows)))
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=["spelling", "tips", "labels"],
                        help="run a single source")
    args = parser.parse_args(argv)

    jobs = [("spelling", scrape_spelling, "spellingregels.jsonl"),
            ("tips", scrape_tips, "tips.jsonl"),
            ("labels", scrape_labels, "be-nl-labels.jsonl")]
    if args.only:
        jobs = [j for j in jobs if j[0] == args.only]

    for name, fn, out in jobs:
        print("%s:" % name)
        write_jsonl(out, fn())

    print("\nRaw responses cached in data/raw/. Nothing was written to "
          "references/: promotion is a human step, tables only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
