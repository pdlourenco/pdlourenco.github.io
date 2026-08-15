# The intermediate format — contract v1

The versioned API between [`logseq-alfolio-export`](https://github.com/pdlourenco/logseq-alfolio-export)
(the plugin, which knows Logseq) and this repository (which knows al-folio). The plugin writes
these files; `bin/transform.py` reads them and nothing else.

**The schemas in this directory are normative.** They were derived from the plugin's actual
output, not from prose: the plugin's own vitest fixtures were driven through its `runExport()`
and the emitted files captured verbatim (per `docs/DECISIONS.md` D26 — enumerate mechanically,
and say how). Where the plugin's current behaviour and this contract differ, the differences are
listed below and tracked in a plugin-repo issue; the contract wins and the transform enforces it.

## The files

| File                        | Shape                                                     | Schema                                                                   |
| --------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------ |
| `cv.yml`                    | mapping of CV sections, each a list of entries            | [`cv.schema.json`](cv.schema.json)                                       |
| `profile.yml`               | flat mapping: identity scalars + `{id, url}` link objects | [`profile.schema.json`](profile.schema.json)                             |
| `personal.yml`              | mapping of page slug → page object with `sections`        | [`personal.schema.json`](personal.schema.json)                           |
| `publication_overrides.yml` | mapping of BibTeX cite-key → display overrides            | [`publication_overrides.schema.json`](publication_overrides.schema.json) |
| `manifest.json`             | export metadata: version, file list, hashes, counts       | [`manifest.schema.json`](manifest.schema.json)                           |
| `blog/YYYY-MM-DD-slug.md`   | markdown with YAML front matter                           | Phase 6                                                                  |

All of them live under `_incoming/` in this repository, committed, exactly as exported.

## Conventions that are easy to get wrong

**`cv.yml` has no `cv:` wrapper.** Its top-level keys are the sections themselves
(`experience`, `education`, …). al-folio's `_data/cv.yml` _does_ need a `cv:` wrapper and
different section names — building it is the transform's job, not the plugin's. See
[`../SCHEMA-NOTES.md`](../SCHEMA-NOTES.md) §1.

**Absent values arrive two different ways, and both mean "absent".** The plugin's YAML writer
drops null values inside a **mapping** but emits them inside a **list item**. So
`experience[0].description` appears as an explicit `description: null`, while
`profile.github.url` simply disappears when unset. Every optional field in these schemas
therefore accepts `null` as well as being absent, and the transform must treat the two
identically. (`seed.md` says "the intermediate YAML omits empty properties entirely" — true of
mappings only.)

**Dates are strings, `YYYY-MM` or `YYYY-MM-DD`,** already converted from Logseq's `YYYY/MM/DD`.
Ongoing entries have `end: null` — the _transform_ turns that into RenderCV's
`end_date: present` (D15).

**`icon` values are short keys**, not paths (`up`, `uminho`). Mapping them to files is this
repo's manual job via `_data/icon_map.yml` and `assets/img/logos/` (D22).

**Numeric fields are integers**, already parsed: `level`, `speaking`, `understanding`,
`writing`, `importance`.

**An all-dropped document is `{}`, not zero bytes.** When every key of a document is dropped,
the plugin writes a literal `{}`. Whole documents only — a nested `key:` with a null value
stays as it is, because absent-vs-null equivalence above is load-bearing.

This is a contract guarantee rather than a consumer requirement: `bin/transform.py` reads an
empty file as `{}` anyway, and all four content schemas accept `{}`. The point is that the
format should not depend on a consumer being tolerant, and that a zero-byte file stays
available as a signal that something went wrong (`docs/DECISIONS.md` D65).

## Staging lifecycle — who may delete what in `_incoming/`

`_incoming/` is **not exclusively the plugin's**. `papers.src.bib` is staged from Zotero by
hand on a different cadence, and `README.md` belongs to this repo. Both are exempt from the
manifest's file-list check, **by exact relative path** — a nested `blog/README.md` is not
exempt, and is a hard error like any other unlisted file.

Because the export is not the only writer, **the plugin must not clear the directory**. It
prunes by the _previous_ `manifest.json`'s `files` list — exactly the paths it last wrote,
nothing else — and writes its own manifest **last**, so the manifest is the commit point and a
crashed export leaves the previous one intact for the next run to prune by. An unreadable or
unknown-version previous manifest prunes nothing. See `docs/DECISIONS.md` D64.

> ⚠️ **Agreed, not yet implemented.** Today's `sync.sh` prunes nothing and writes
> `manifest.json` **before** the blog posts, which violates the ordering rule above on its own.
> Until the plugin lands D64, a dropped page leaves a stale file behind and the next
> `bin/transform.py` run fails with "present but not listed" — that error is currently a
> **normal consequence of a deletion**, not necessarily a mistake, and the fix is to remove the
> stale file by hand. Tracked in the companion repo alongside the D29 `schema_version` gap.

Once the plugin implements it, the consequence for this repo is that `_incoming/` stops
accumulating stale files across exports, and "present but not listed" goes back to meaning
only what it should: a partial copy, or a file placed by hand that the plugin does not know
about.

## Versioning

`manifest.json` carries `schema_version` — an integer, currently **1**. The transform refuses a
version it does not know rather than guessing, and refuses an export with no version at all.

A breaking change to any file's shape increments it. Additive, optional fields do not: the
schemas set `additionalProperties: true` on entry objects precisely so a plugin that learns a
new field does not break a transform that has not learned it yet.

**That tolerance is deliberate, and it hands one duty to the transform.** `cv.yml`'s _top level_
is tolerant too, so an unknown or renamed section — a future `talks:`, or a typo'd
`experiences:` — validates cleanly. If the transform silently maps only the sections it knows,
that content disappears with no error, which is the failure class this project keeps running into
(D11, D14, D31). So, as a **named Phase 3 requirement**: `bin/transform.py` must fail, or at
minimum warn loudly, on a top-level `cv.yml` section it has no mapping for. The schema stays
permissive; the transform is where the noise belongs.

## Where the plugin does not match this contract yet

Observed in `logseq-alfolio-export` at the time of writing, and filed upstream:

1. **No `schema_version`.** The manifest has `exported_at`, `plugin_version`, `website`,
   `files` and `counts`. Until the plugin adds it, the transform's version gate fails with an
   actionable message — see the `legacy-unversioned` fixture.
2. **No content hashes.** `manifest.json` cannot currently detect a half-finished copy, which is
   what hashes are for. The schema defines `hashes` as optional-but-validated so the plugin can
   start emitting them without a version bump.
3. **`files` is incomplete.** It is computed before `manifest.json` and the blog posts are added,
   so it lists four entries while five or more files are written.
4. **`plugin_version` is a hard-coded string** in the plugin source rather than read from its
   `package.json`, so it can silently disagree with the released version.
5. **`sync.sh` writes to the wrong place** — `_data/` and `_posts/` instead of `_incoming/`.
   This is the dangerous one; see `docs/DECISIONS.md` D21.

None of these block this repository: the schemas are normative, the transform gates on them, and
the fixtures cover both the target contract and today's real output.
