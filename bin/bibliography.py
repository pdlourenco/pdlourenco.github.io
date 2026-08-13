#!/usr/bin/env python3
"""Turn a Zotero/Better-BibTeX export into al-folio's `_bibliography/papers.bib`.

Imported by `bin/transform.py`; kept separate because the bibliography rules are the
largest single mapping and are worth reading on their own.

The shape of the problem (docs/DECISIONS.md D43-D54):

* One Zotero library holds three different things — the owner's work, work he supervised,
  and his engineering section's output that is neither. **Authorship decides destination**
  and nothing else does (D43).
* A paper and the talk that presented it are one record; a poster is **not** (D44). The
  discriminator is venue *and* date, never the title alone.
* `bib.liquid` reads a handful of fields and silently ignores the rest, and two of its
  behaviours are traps: a `type` field shadows the entry type (D45), and `address` /
  `howpublished` render nothing at all (D53). See docs/SCHEMA-NOTES.md §6.
* The export flavour is changing from Better BibTeX to Better BibLaTeX (D54), so every
  field read goes through `canonical()` rather than being spelled inline.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# ---------------------------------------------------------------------------------------
# Flavour normalisation (D54)
# ---------------------------------------------------------------------------------------

#: BibLaTeX spelling -> the spelling the rest of this module uses. Both flavours are read
#: so the Better BibTeX → Better BibLaTeX switch is a data change, not a code change.
#: `location` is deliberately the canonical name: it is what `bib.liquid` itself reads.
FIELD_ALIASES = {
    "journaltitle": "journal",
    "address": "location",  # BibTeX's spelling; renders nothing under that name (D53)
    "eventtitle": "event",  # BibLaTeX only — the meeting name BibTeX cannot carry
    "venue": "event_place",  # BibLaTeX only — Zotero's "Event Place"
    "institution": "school",
}

#: Fields never copied to the generated file.
#: `type` shadows the entry type inside bib.liquid and drops the venue line (D45).
#: `file` is a local Zotero path, never a URL (D50). The rest are Zotero bookkeeping.
#: `abstract` and `annotation` are deliberately NOT here: bib.liquid renders them as the
#: "Abs" toggle and the author-line info popover (SCHEMA-NOTES §6). Dropping them threw away
#: content the theme displays — caught by the PR #5 post-merge audit.
DROPPED_FIELDS = frozenset(
    {"type", "file", "copyright", "ids", "langid", "urldate", "keywords", "collaborator",
     "shorttitle"}
)


def canonical(entry: dict, key: str) -> Any:
    """A field's value under either flavour's spelling, or None."""
    fields = entry["fields"]
    if key in fields:
        return fields[key]
    for alias, target in FIELD_ALIASES.items():
        if target == key and alias in fields:
            return fields[alias]
    return None


# ---------------------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------------------


class BibError(Exception):
    """A bibliography problem the operator must fix. Carries every instance found."""

    def __init__(self, summary: str, problems: list[str] | None = None):
        self.summary = summary
        self.problems = problems or []
        super().__init__(summary)


_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,]*)\s*,", re.S)


def _matching_brace(text: str, start: int) -> int:
    """Index of the `}` closing the `{` at `start`. Raises on an unterminated entry."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise BibError("unterminated BibTeX entry — a brace is never closed.")


def _parse_fields(body: str) -> dict[str, str]:
    """Field assignments inside one entry. Brace-aware: titles nest `{{...}}` heavily."""
    fields: dict[str, str] = {}
    pos = 0
    while pos < len(body):
        m = re.compile(r"\s*(\w+)\s*=\s*").match(body, pos)
        if not m:
            nxt = body.find(",", pos)
            if nxt < 0:
                break
            pos = nxt + 1
            continue
        start = m.end()
        if start < len(body) and body[start] == "{":
            end = _matching_brace(body, start)
            value, pos = body[start + 1 : end], end + 1
        elif start < len(body) and body[start] == '"':
            end = body.find('"', start + 1)
            value, pos = body[start + 1 : end], end + 1
        else:  # bare value: `year = 2026`
            end = body.find(",", start)
            end = end if end >= 0 else len(body)
            value, pos = body[start:end].strip(), end
        fields[m.group(1).lower()] = value.strip()
        nxt = body.find(",", pos)
        if nxt < 0:
            break
        pos = nxt + 1
    return fields


def parse(text: str) -> list[dict]:
    """Parse a .bib into `{type, key, fields}` dicts, in file order.

    Deliberately not a general BibTeX implementation: no @string, @preamble or crossref,
    because Better BibTeX emits none of them. Anything unexpected is a loud failure
    upstream rather than a silent partial parse here.
    """
    entries, pos = [], 0
    while True:
        m = _ENTRY_RE.search(text, pos)
        if not m:
            break
        open_brace = text.index("{", m.start())
        close = _matching_brace(text, open_brace)
        entries.append(
            {
                "type": m.group(1).lower(),
                "key": m.group(2).strip(),
                "fields": _parse_fields(text[m.end() : close]),
            }
        )
        pos = close + 1
    return entries


# ---------------------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------------------

_LATEX_ACCENTS = {
    r"{\c c}": "c", r"\c{c}": "c", r"{\'e}": "e", r"\'{e}": "e", r"{\'a}": "a",
    r"{\~a}": "a", r"{\^e}": "e", r"{\'o}": "o", r"{\'i}": "i", r"{\`a}": "a",
}


def plain(value: str | None) -> str:
    """A field with LaTeX accents and braces removed, for comparison only.

    The export writes `Louren{\\c c}o`, so a plain "Lourenço" test matches 1 of 74 real
    entries. Every name comparison in this module goes through here — see D43.
    """
    if not value:
        return ""
    out = value
    for tex, ascii_ in _LATEX_ACCENTS.items():
        out = out.replace(tex, ascii_)
    out = re.sub(r"[{}\\]", "", out)
    out = unicodedata.normalize("NFKD", out)
    return "".join(c for c in out if not unicodedata.combining(c))


def _names(value: str | None) -> list[str]:
    return [n.strip() for n in re.split(r"\s+and\s+", plain(value)) if n.strip()]


def _display_name(name: str) -> str:
    """`Ventura, Rodrigo` -> `Rodrigo Ventura`. A bare surname list reads as one person."""
    if "," in name:
        last, _, first = name.partition(",")
        return f"{first.strip()} {last.strip()}".strip()
    return name.strip()


def is_self(value: str | None, surname: str, forenames: list[str]) -> bool:
    """Whether a name list contains the site owner.

    Better BibTeX writes `Last, First`, but a Zotero single-field name has no comma at all,
    and that form silently failed to match before. Both are handled: with a comma the
    surname is the part before it, without one it is the last whitespace-separated word.
    """
    want = plain(surname).lower()
    for name in _names(value):
        last = name.split(",")[0].strip() if "," in name else name.split()[-1:] and name.split()[-1]
        if str(last).strip().lower() != want:
            continue
        if not forenames or any(f.lower() in name.lower() for f in forenames):
            return True
    return False


# ---------------------------------------------------------------------------------------
# Classification (D43)
# ---------------------------------------------------------------------------------------

PUBLICATION, SUPERVISION, EXCLUDED = "publication", "supervision", "excluded"

_THESIS_TYPES = ("thesis", "dissertation")


def _looks_like_thesis(entry: dict) -> bool:
    if entry["type"] in ("phdthesis", "mastersthesis", "thesis"):
        return True
    raw = (entry["fields"].get("type") or "").lower()
    return any(t in raw for t in _THESIS_TYPES) and canonical(entry, "school") is not None


def classify(entry: dict, surname: str, forenames: list[str]) -> str:
    """Where an entry belongs: his own work, his supervisions, or nowhere.

    The `collaborator` rule is narrowed to theses on purpose. One real record — the
    Earth-Fixed Trajectory poster — lists him as a collaborator on his *own* poster, so an
    unqualified rule would file his work under other people's supervisions (D43).
    """
    if is_self(entry["fields"].get("author"), surname, forenames):
        return PUBLICATION
    if is_self(entry["fields"].get("collaborator"), surname, forenames):
        return SUPERVISION if _looks_like_thesis(entry) else PUBLICATION
    return EXCLUDED


# ---------------------------------------------------------------------------------------
# Sections (D46, D47)
# ---------------------------------------------------------------------------------------

#: Page order. A section with no entries is not emitted at all, so `book` staying empty
#: costs nothing and needs no code change when it fills (D47).
SECTION_ORDER = [
    "journal", "conference", "chapter", "book", "thesis", "preprint",
    "poster", "talk", "supervision",
]

#: Singular label used inside an entry's own `note` line. Derived from SECTION_TITLES by
#: stripping an "s" this is not: "Talks and invited lectures" must not become
#: "Talks and invited lecture", which is what the first render showed.
SECTION_LABEL = {
    "poster": "Poster",
    "talk": "Invited talk",
    "preprint": "Preprint",
}

SECTION_TITLES = {
    "journal": "Journal papers",
    "conference": "Conference papers",
    "chapter": "Book chapters",
    "book": "Books",
    "thesis": "Theses",
    "preprint": "Preprints",
    "poster": "Posters",
    "talk": "Talks and invited lectures",
    "supervision": "Supervised theses",
}

_BY_ENTRY_TYPE = {
    "article": "journal",
    "inproceedings": "conference",
    "conference": "conference",
    "incollection": "chapter",
    "inbook": "chapter",
    "book": "book",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
    "thesis": "thesis",
}

#: Zotero `type` values, lowercased, for entries whose entry type does not say enough.
#: Read before `type` is dropped (D45).
_BY_TYPE_FIELD = {
    "poster": "poster",
    "paper presentation": "presentation",
    "presentation": "talk",
    "invited lecture": "talk",
    "invited talk": "talk",
    "lecture": "talk",
    "workshop": "talk",
}


def section_of(entry: dict) -> str | None:
    """The page section an entry belongs to, or None if it cannot be determined."""
    raw_type = re.sub(r"\s+", " ", plain(entry["fields"].get("type") or "")).strip().lower()
    if raw_type in _BY_TYPE_FIELD:
        return _BY_TYPE_FIELD[raw_type]
    if entry["type"] in _BY_ENTRY_TYPE:
        return _BY_ENTRY_TYPE[entry["type"]]
    if entry["type"] in ("misc", "unpublished"):
        # A preprint is a @misc that names an archive; anything else here is unclassifiable
        # and must be reported rather than guessed at (D52).
        if entry["fields"].get("archiveprefix") or entry["fields"].get("eprint"):
            return "preprint"
        return None
    return None


# ---------------------------------------------------------------------------------------
# Merging a presentation into its paper (D44)
# ---------------------------------------------------------------------------------------

_MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), start=1)}


def _title_key(entry: dict) -> str:
    return re.sub(r"[^a-z0-9]", "", plain(entry["fields"].get("title")).lower())


def _when(entry: dict) -> tuple[str, int]:
    """(year, month) for an entry, under either flavour. BibLaTeX uses `date`."""
    date = entry["fields"].get("date")
    if date:
        parts = str(date).split("-")
        return (parts[0], int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0)
    month = str(entry["fields"].get("month") or "").strip().lower()[:3]
    return (str(entry["fields"].get("year") or ""), _MONTHS.get(month, 0))


def _where(entry: dict) -> str:
    place = canonical(entry, "event_place") or canonical(entry, "location") or ""
    return re.sub(r"[^a-z0-9]", "", plain(place).lower())


def same_event(a: dict, b: dict) -> bool:
    """Whether two records describe the same event — title AND place AND date.

    Title alone is not enough, and posters are the counter-example that proves it: every
    poster shares a paper's title but was presented in Lisbon on another date, and one
    paper has *two* posters two months apart (D44).
    """
    return _title_key(a) == _title_key(b) and _where(a) == _where(b) and _when(a) == _when(b)


def fold_presentations(entries: list[dict]) -> tuple[list[dict], list[str]]:
    """Fold each `presentation` into the paper it presented. Returns (kept, notes).

    A presentation with no matching paper is kept as a talk rather than dropped — losing a
    record because a title was edited on one side is exactly the silent failure this repo
    keeps guarding against.
    """
    papers = [e for e in entries if e["section"] in ("journal", "conference", "chapter", "book")]
    kept, notes = [], []
    for entry in entries:
        if entry["section"] != "presentation":
            kept.append(entry)
            continue
        host = next((p for p in papers if same_event(p, entry)), None)
        if host is None:
            entry["section"] = "talk"
            notes.append(f"{entry['key']}: presentation with no matching paper — kept as a talk")
            kept.append(entry)
            continue
        host.setdefault("merged", []).append(entry["key"])
    return kept, notes


# ---------------------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------------------

#: Written in this order so the generated file diffs cleanly.
FIELD_ORDER = [
    "title", "author", "journal", "booktitle", "school", "publisher", "series",
    "volume", "number", "pages", "year", "month", "location", "event", "note",
    "additional_info", "doi", "arxiv", "eprint", "archiveprefix", "primaryclass",
    "url", "pdf", "slides", "poster", "code", "website", "abstract", "section",
    "abbr", "preview", "selected", "bibtex_show",
]


#: LaTeX the `latex` bibtex_filter does not resolve. `\textbar` reached the rendered
#: teaching page verbatim on the first build, so these are rewritten at emission.
_LATEX_MACROS = {
    r"\textbar": "|", r"\textbackslash": "\\", r"\&": "&",
    r"\textemdash": "—", r"\textendash": "–", r"\%": "%", r"\_": "_",
}


def _escape(value: str) -> str:
    out = str(value).replace("\n", " ")
    for tex, plain_text in _LATEX_MACROS.items():
        out = out.replace(tex, plain_text)
    # A BibTeX tie is a non-breaking space, but a tilde inside an accent macro (`{\~a}`) is
    # part of the letter, and a tilde in a URL is data. Only ties between word characters
    # are rewritten — "for~Attitude" yes, "example.org/~user" and "Guimar{\~a}es" no.
    out = re.sub(r"(?<=[A-Za-z0-9])~(?=[A-Za-z])", " ", out) if "://" not in out else out
    return re.sub(r"\s+", " ", out).strip()


def emit(entries: list[dict]) -> str:
    """Serialise entries to BibTeX deterministically."""
    out = []
    for entry in entries:
        lines = [f"@{entry['type']}{{{entry['key']},"]
        fields = entry["fields"]
        ordered = [k for k in FIELD_ORDER if k in fields]
        ordered += sorted(k for k in fields if k not in FIELD_ORDER)
        for key in ordered:
            value = fields[key]
            if value in (None, ""):
                continue
            lines.append(f"  {key} = {{{_escape(value)}}},")
        lines.append("}")
        out.append("\n".join(lines))
    return "\n\n".join(out) + "\n"


# ---------------------------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------------------------

#: Cite-keys must be usable as identifiers: they key publication_overrides.yml and become
#: page anchors. Two real entries are `::` and `::a` (D-owner-action-7).
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_:.\-]{2,}$")


def build(
    bib_text: str,
    overrides: dict | None,
    surname: str,
    forenames: list[str],
    asset_names: frozenset[str] = frozenset(),
) -> tuple[str, list[str]]:
    """Source .bib + overrides -> generated .bib text. Returns (text, notes).

    Raises BibError listing every problem, never just the first.
    """
    entries = parse(bib_text)
    if not entries:
        raise BibError("papers.src.bib parsed to zero entries — is it really a .bib export?")

    problems, notes = [], []

    bad_keys = [e for e in entries if not _KEY_RE.match(e["key"])]
    if bad_keys:
        problems += [
            f"unusable cite-key {e['key']!r} on {plain(e['fields'].get('title'))[:60]!r}"
            for e in bad_keys
        ] + [
            "Cite-keys key publication_overrides.yml and become page anchors, so a generated",
            "substitute would change on the next export and break any override pointing at it.",
            "Fix these in Zotero (Better BibTeX → pin a citation key).",
        ]

    seen: dict[str, str] = {}
    for e in entries:
        if e["key"] in seen:
            problems.append(f"duplicate cite-key {e['key']!r}")
        seen[e["key"]] = e["key"]

    # Titles of things that are unambiguously papers, used to recognise a bare @misc that
    # merely restates one (a preprint record, or Zotero cruft) — see D52.
    paper_titles = {
        _title_key(e)
        for e in entries
        if e["type"] in ("article", "inproceedings", "incollection", "inbook", "book")
    }

    kept = []
    for entry in entries:
        where = classify(entry, surname, forenames)
        if where == EXCLUDED:
            continue
        if where == SUPERVISION:
            entry["section"] = "supervision"
            kept.append(entry)
            continue

        section = (overrides or {}).get(entry["key"], {}).get("section") or section_of(entry)

        # An untyped @misc that restates a paper is a preprint/duplicate record; the paper
        # is the better record of the same work, so it wins and this one is dropped (D52).
        if section is None and entry["type"] in ("misc", "unpublished"):
            if _title_key(entry) in paper_titles:
                notes.append(
                    f"{entry['key']}: untyped @{entry['type']} restating a paper — suppressed "
                    "in favour of the paper record (D52)"
                )
                continue

        if section is None:
            problems.append(
                f"{entry['key']}: cannot tell what this is — @{entry['type']} with no usable "
                f"`type` field ({plain(entry['fields'].get('title'))[:50]!r}), and it does not "
                "restate a paper. Give it a Zotero item type or a `type` value, or set "
                "`section:` for it in publication_overrides.yml. Refusing to guess (D52)."
            )
            continue
        if section not in SECTION_ORDER and section != "presentation":
            problems.append(
                f"{entry['key']}: section {section!r} is not one the page renders — "
                f"expected one of {', '.join(SECTION_ORDER)}."
            )
            continue
        entry["section"] = section
        kept.append(entry)

    if problems:
        raise BibError(
            "the staged bibliography cannot be transformed as it stands.", problems
        )

    kept, fold_notes = fold_presentations(kept)
    notes += fold_notes

    for entry in kept:
        _rewrite(entry, asset_names, surname, forenames)

    if overrides:
        notes += _apply_overrides(kept, overrides)

    order = {s: i for i, s in enumerate(SECTION_ORDER)}
    kept.sort(key=lambda e: (order.get(e["fields"]["section"], 99),
                             *_neg_when(e), _title_key(e)))
    return emit(kept), notes


def _neg_when(entry: dict) -> tuple[int, int]:
    year, month = _when(entry)
    return (-(int(year) if str(year).isdigit() else 0), -month)


def _rewrite(entry: dict, asset_names: frozenset[str], surname: str,
             forenames: list[str]) -> None:
    """Normalise one entry into what bib.liquid actually reads (D45, D50, D53)."""
    fields = entry["fields"]
    section = entry["section"]
    supervisors = fields.get("collaborator")

    for alias, target in FIELD_ALIASES.items():
        if alias in fields and target not in fields:
            fields[target] = fields.pop(alias)

    degree = re.sub(r"\s+", " ", plain(fields.get("type") or "")).strip()
    for key in list(fields):
        if key in DROPPED_FIELDS:
            fields.pop(key)

    # An @misc/@unpublished has no venue branch, so `location` there renders a stray leading
    # comma. Posters, talks and preprints carry event + place in `note` instead (D53).
    if section in ("poster", "talk", "preprint"):
        bits = [SECTION_LABEL[section]]
        for key in ("event", "event_place", "location"):
            if fields.get(key):
                bits.append(fields[key])
                fields.pop(key, None)
        note = " · ".join(dict.fromkeys(b for b in bits if b))
        if note and not fields.get("note"):
            fields["note"] = note

    # A supervision is a @phdthesis, so `school` already renders as its venue line — repeating
    # it in the note is the duplication that showed up on the first render. The note carries
    # what the venue line cannot: the degree, and who else supervised.
    elif section == "supervision":
        bits = [degree or "Thesis"]
        others = [n for n in _names(supervisors) if not is_self(n, surname, forenames)]
        if others:
            shown = ", ".join(_display_name(n) for n in others)
            bits.append(f"co-supervised with {shown}")
        fields["note"] = " · ".join(bits)

    if entry.get("merged"):
        fields.setdefault("note", "Presented by the author.")

    fields.pop("event_place", None)
    fields["section"] = section

    # A link is emitted only when the asset is actually present (D50).
    for field, suffix in (("pdf", ""), ("slides", "-slides"), ("poster", "-poster")):
        name = f"{entry['key']}{suffix}.pdf"
        if name in asset_names:
            fields[field] = name
        else:
            fields.pop(field, None)


def _apply_overrides(entries: list[dict], overrides: dict) -> list[str]:
    """Merge publication_overrides.yml. An unknown cite-key is a loud error (P3)."""
    by_key = {e["key"]: e for e in entries}
    unknown = sorted(set(overrides) - set(by_key))
    if unknown:
        raise BibError(
            "publication_overrides.yml names cite-key(s) that are not in the bibliography.",
            [f"unknown cite-key: {u!r}" for u in unknown]
            + ["A typo here silently does nothing, so it is an error. Check Zotero's key."],
        )
    notes = []
    for key, override in overrides.items():
        if not isinstance(override, dict):
            continue
        for field, value in override.items():
            if value is None:
                continue
            by_key[key]["fields"][field] = value
        notes.append(f"{key}: applied {len(override)} override field(s)")
    return notes
