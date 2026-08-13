#!/usr/bin/env python3
"""Checks for bin/bibliography.py. Dependency-free, same style as test_transform.py.

    python3 test/test_bibliography.py

Every assertion here corresponds to a decision in docs/DECISIONS.md, and the ones that
matter most are the negative cases: work that must NOT appear, and records that must NOT
be merged. Those are the failures that would otherwise be invisible on the rendered page.
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "bin"))

import bibliography as bib  # noqa: E402

FIXTURE = (REPO / "test" / "fixtures" / "bibliography" / "papers.src.bib").read_text(
    encoding="utf-8"
)
SURNAME, FORENAMES = "Lourenço", ["Pedro", "P."]

_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS  {label}")
    else:
        print(f"FAIL  {label}" + (f"\n        {detail}" if detail else ""))
        _failures.append(label)


def build(overrides=None, assets=frozenset()):
    return bib.build(FIXTURE, overrides, SURNAME, FORENAMES, assets)


def entries_by_key(text: str) -> dict[str, dict]:
    return {e["key"]: e for e in bib.parse(text)}


# ---------------------------------------------------------------------------------------

out, notes = build()
by_key = entries_by_key(out)
sections = {k: e["fields"].get("section") for k, e in by_key.items()}


# --- D43: authorship decides destination ------------------------------------------------

check(
    "the owner's own paper is published",
    sections.get("lourencoJournal2020") == "journal",
)
check(
    "a thesis he supervised goes to the teaching page",
    sections.get("studentThesis2024") == "supervision",
)
check(
    "work he neither authored nor supervised appears NOWHERE",
    "notMineThesis2024" not in by_key,
    "his section's output must not reach the site at all (D43)",
)
check(
    "the LaTeX cedilla is matched — a plain 'Lourenço' test would find almost nothing",
    bib.is_self(r"Louren{\c c}o, Pedro", SURNAME, FORENAMES),
)
check(
    "a different Lourenço is not assumed to be him",
    not bib.is_self("Lourenco, Sofia", SURNAME, FORENAMES),
)


# --- D44: presentations merge, posters never do -----------------------------------------

check(
    "a paper presentation at the same venue and date is folded into its paper",
    "lourencoConfPresentation2021" not in by_key,
)
check(
    "the paper it folded into says so",
    "Presented" in (by_key["lourencoConference2021"]["fields"].get("note") or ""),
)
check(
    "a poster sharing the paper's title is NOT merged — different venue and date",
    sections.get("lourencoPoster2021") == "poster",
    "the real library has six such posters, two of them two months apart (D44)",
)
check(
    "same_event() needs venue and date, not just a matching title",
    not bib.same_event(
        {"fields": {"title": "T", "year": "2021", "month": "jun", "address": "Linz"}},
        {"fields": {"title": "T", "year": "2021", "month": "sep", "address": "Lisboa"}},
    ),
)
check(
    "a presentation with no matching paper is kept as a talk, never dropped",
    sections.get("lourencoOrphanPresentation2019") == "talk"
    and any("no matching paper" in n for n in notes),
)


# --- D45: the `type` field must not survive ---------------------------------------------

check(
    "no generated entry carries a `type` field",
    all("type" not in e["fields"] for e in by_key.values()),
    "a `type` field shadows entry.type in bib.liquid and drops the venue line (D45)",
)
check(
    "the degree survives the strip, in the note",
    "M.Sc. Thesis" in (by_key["studentThesis2024"]["fields"].get("note") or ""),
)
check(
    "a co-supervisor is named, and the owner is not listed as his own collaborator",
    (by_key["studentThesis2024"]["fields"].get("note") or "").endswith("Bob Other"),
)


# --- D53: address -> location; @misc carries its venue in note --------------------------

check(
    "`address` is renamed to `location`, which is the field bib.liquid reads",
    by_key["lourencoJournal2020"]["fields"].get("location") == "Porto, Portugal"
    and "address" not in by_key["lourencoJournal2020"]["fields"],
)
check(
    "a poster carries its place in `note`, not `location` (which would render a stray comma)",
    "Lisboa" in (by_key["lourencoPoster2021"]["fields"].get("note") or "")
    and "location" not in by_key["lourencoPoster2021"]["fields"],
)
check(
    "a tilde inside an accent macro is preserved, not turned into a space",
    "Guimar" in (by_key["lourencoTalk2023"]["fields"].get("note") or "")
    and "Guimar aes" not in (by_key["lourencoTalk2023"]["fields"].get("note") or ""),
)


# --- D46/D47: sections ------------------------------------------------------------------

check("an arXiv @misc is a preprint", sections.get("lourencoPreprint2025") == "preprint")
check("a typed lecture is a talk", sections.get("lourencoTalk2023") == "talk")
check(
    "every generated entry carries exactly one known section",
    all(s in bib.SECTION_ORDER for s in sections.values()),
    f"got {sorted(set(sections.values()))}",
)
check(
    "entries are emitted in page-section order",
    [bib.SECTION_ORDER.index(s) for s in sections.values()]
    == sorted(bib.SECTION_ORDER.index(s) for s in sections.values()),
)


# --- D50: a link only when the asset exists ---------------------------------------------

check(
    "no pdf link is emitted when assets/pdf is empty",
    all("pdf" not in e["fields"] for e in by_key.values()),
    "Zotero's `file` is a local Windows path and can never be a working link (D50)",
)
with_asset = entries_by_key(build(assets=frozenset({"lourencoJournal2020.pdf"}))[0])
check(
    "a pdf link IS emitted once the asset is staged",
    with_asset["lourencoJournal2020"]["fields"].get("pdf") == "lourencoJournal2020.pdf",
)


# --- Overrides (P3) ---------------------------------------------------------------------

check(
    "an override field is applied",
    entries_by_key(build({"lourencoJournal2020": {"abbr": "JoP"}})[0])[
        "lourencoJournal2020"
    ]["fields"].get("abbr")
    == "JoP",
)
try:
    build({"noSuchKey2020": {"abbr": "X"}})
    check("an unknown cite-key in overrides is a loud error", False, "no error raised")
except bib.BibError as exc:
    check(
        "an unknown cite-key in overrides is a loud error",
        any("noSuchKey2020" in p for p in exc.problems),
    )


# --- Loud failures ----------------------------------------------------------------------

try:
    bib.build(
        "@phdthesis{::,\n title = {Bad Key},\n author = {X, Y},\n"
        r" collaborator = {Louren{\c c}o, Pedro},"
        "\n school = {IST},\n type = {M.Sc. Thesis},\n year = {2026},\n}\n",
        None,
        SURNAME,
        FORENAMES,
    )
    check("an unusable cite-key is rejected", False, "no error raised")
except bib.BibError as exc:
    check(
        "an unusable cite-key is rejected, naming the entry",
        any("::" in p and "Bad Key" in p for p in exc.problems),
    )

try:
    bib.build(
        "@misc{mysteryEntry2023,\n title = {No Type At All},\n"
        r" author = {Louren{\c c}o, Pedro},"
        "\n year = {2023},\n}\n",
        None,
        SURNAME,
        FORENAMES,
    )
    check("an unclassifiable entry is an error, not a silent omission", False)
except bib.BibError as exc:
    check(
        "an unclassifiable entry is an error, not a silent omission",
        any("mysteryEntry2023" in p for p in exc.problems),
    )


# --- Determinism ------------------------------------------------------------------------

check("the same input produces byte-identical output", build()[0] == build()[0])


print()
if _failures:
    print(f"{len(_failures)} check(s) failed:")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
print("all bibliography checks passed")
