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

## Versioning

`manifest.json` carries `schema_version` — an integer, currently **1**. The transform refuses a
version it does not know rather than guessing, and refuses an export with no version at all.

A breaking change to any file's shape increments it. Additive, optional fields do not: the
schemas set `additionalProperties: true` on entry objects precisely so a plugin that learns a
new field does not break a transform that has not learned it yet.

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
