# CLAUDE.md — pdlourenco.github.io

Personal academic + personal-interest website for **Pedro Lourenço**, built on
[al-folio](https://github.com/alshedivat/al-folio) v1.x (Jekyll). Content is authored in a
**Logseq graph**, exported by a **companion plugin**, and transformed into al-folio's data
formats by scripts that live _in this repo_.

## Read these first, in this order

| Document                                                     | What it is                                                                                                            |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| [`seed.md`](seed.md)                                         | The original brief: architecture, target site structure, pipeline, conventions. Kept unedited as a historical record. |
| [`docs/IMPLEMENTATION-PLAN.md`](docs/IMPLEMENTATION-PLAN.md) | Critical analysis of the brief, the phased plan, and the review contract every PR is held to.                         |
| [`docs/DECISIONS.md`](docs/DECISIONS.md)                     | Resolved decisions with rationale.                                                                                    |
| [`docs/SCHEMA-NOTES.md`](docs/SCHEMA-NOTES.md)               | What this al-folio actually expects, read out of the installed gems. Read before writing any transform mapping.       |
| [`docs/intermediate-schema/`](docs/intermediate-schema/)     | The plugin↔repo contract, v1: normative JSON Schemas plus the conventions that are easy to get wrong.                 |

**Precedence — later overrides earlier: `seed.md` → `docs/IMPLEMENTATION-PLAN.md` →
`docs/DECISIONS.md`.** `seed.md` is deliberately not rewritten as decisions supersede it, so
check the later two before treating anything in it as current. Known supersessions so far:
the bibliography ownership model (P3/D24), the CI/commit model (P4/D4), the `_projects/`
duplication question (P8/D23), Goodreads vs the native `_books/` collection (D17), the
plugin's export path (D20 — `seed.md`'s is wrong), and the entry types custom CV sections
must use (D14 — `seed.md`'s `NormalEntry` guess renders blank).

## What is upstream's and what is ours

This is a **site built from** al-folio, not a fork of the al-folio starter. Runtime —
layouts, includes, Sass, Liquid tags, feature JS — lives in versioned gems
(`al_folio_core`, `al_folio_cv`, `al_citations`, …), _not_ in this repo.

| Ours                                                                | Upstream's (leave alone unless deliberate + recorded)                    |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `seed.md`, `docs/*.md` (except `docs/al-folio/`, `docs/reference/`) | `bin/*` (except `bin/transform.py`), `.devcontainer/`, `.agents/skills/` |
| `_incoming/` (staged intermediate YAML), `bin/transform.py`         | `docs/al-folio/` — vendored upstream docs, read-only reference           |
| `_data/*`, `_pages/*`, content collections, `_config.yml`           | `docs/reference/al-folio-stock/` — stock files kept for schema study     |

Upstream's own agent guidance is vendored at
[`docs/al-folio/`](docs/al-folio/) — start with `ARCHITECTURE.md`, `BOUNDARIES.md` (which
gem owns what) and `CUSTOMIZE.md`. Two upstream rules **do not** apply here:

- the "stop sign" forbidding local `_layouts/`, `_includes/`, `_sass/` — upstream states
  that restriction binds its own starter repo, and that sites built from the template may
  legally shadow gem-owned files. Overrides are therefore permitted here, but not expected:
  `page.liquid` renders `{{ content }}` verbatim and Jekyll runs Liquid inside page content,
  so even the `_data`-driven Personal page needs no override (`docs/DECISIONS.md` D18).
- `npm run lint:style-contract`, which enforces that stop sign. It was not imported.

Three upstream rules **do** apply, and all three fail silently:

1. A feature renders only when its gem is loaded **and** its flag is on **and** the page
   opts in. Otherwise the Liquid tag emits an empty string — no warning.
2. `Gemfile` and `_config.yml` are two lists that must agree. A plugin in only one is inert.
3. `baseurl` must stay **empty** here. Upstream ships `/al-folio`; this is a user site
   served at the domain root, so a non-empty baseurl breaks every link.

## Dev loop

```bash
bundle install                   # ruby gems (versions pinned in Gemfile / Gemfile.lock)
bundle exec jekyll serve         # → http://localhost:4000/   (no baseurl here)
JEKYLL_ENV=production bundle exec jekyll build
npm ci && npx prettier . --check # prettier.yml gates this on every PR
python3 -m pip install -r requirements.txt   # pinned; rendercv 2.x
python3 test/validate_fixtures.py && python3 test/test_transform.py
python3 bin/transform.py --check  # what CI runs; never writes
```

## Pipeline (see `seed.md` for the full picture)

```
Logseq graph → plugin → _incoming/*.yml (committed) → bin/transform.py → al-folio formats
```

The intermediate YAML is specified in [`docs/intermediate-schema/`](docs/intermediate-schema/)
(contract v1) with fixtures under `test/fixtures/incoming/`; `python3 test/validate_fixtures.py`
checks them, including a fixture that must fail and one that must report every violation.

`bin/transform.py` exists as of Phase 3 (CV + socials; bibliography, personal and blog
follow in Phases 4-6). Its contract:
idempotent, fails loudly on schema mismatch, marks the files it owns with
`# GENERATED by bin/transform.py from _incoming/ — do not edit by hand`, prunes generated
files whose source disappeared, and has a `--check` mode. Generated output **is committed**;
CI verifies it with `--check` and never regenerates anything the transform owns.

The one exception, so you don't "fix" it: `render-cv.yml` does commit the rendered CV PDF
under `assets/rendercv/rendercv_output/` back to the default branch. That is a pinned
external tool's build artifact, not transform output — see `docs/DECISIONS.md` D4.

## Companion repo

`github.com/pdlourenco/logseq-alfolio-export` — the Logseq plugin. It knows Logseq and
nothing about al-folio; this repo knows al-folio and nothing about Logseq. The contract
between them is the intermediate YAML, which is a versioned API. Do not blur that line.
