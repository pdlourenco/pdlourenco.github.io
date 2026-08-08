# Critical analysis & implementation plan for `seed.md`

*Written by the reviewer session (branch `claude/seeding-doc-analysis-zjqcll`). The author
session should treat this as the review contract: PRs will be reviewed against the phase
scopes and acceptance criteria below.*

---

## 1. Critical analysis of the seeding doc

### What holds up

- **Separation of concerns** (plugin knows Logseq, this repo knows al-folio, neutral YAML
  in between) is the right architecture and is stated crisply.
- **`_incoming/` staging** makes graph changes diffable and the transform re-runnable
  without Logseq. Keep it.
- **Engineering requirements** for `bin/transform.py` (idempotent, fail-loud, generated-file
  headers, `--check` for CI) are exactly right.
- **Non-destructive .bib merge** is correct: `selected`/`abbr`/`preview` are BibTeX fields
  in al-folio, not sidecar data.
- The doc is honest about its own decay ("verify the ground truth") and keeps an explicit
  known-unknowns list. Upstream spot-check (2026-08-08): al-folio v1.x is indeed gem-based,
  supports RenderCV or JSONResume for the CV, and ships `news`/`projects`/`books`/`teachings`
  collections — the doc's premises are sound.

### Problems and gaps (in priority order)

**P1 — The repo does not match the doc's premise.** The doc assumes an al-folio fork
exists ("Read `docs/CUSTOMIZE.md` in this repo", "Open `_data/cv.yml`"). The actual repo
is a stub: a moonwalk `remote_theme`, an "Under maintenance" `index.html`, a test post.
None of the files the verification checklist points at exist. **A bootstrap phase is
missing entirely** and it is the true first task, including the decision of how to adopt
al-folio (template import vs. fork) and cleanly removing the moonwalk remnants.

**P2 — The "versioned API" has no schema and no version.** The intermediate YAML is
called a contract, but nothing in this repo specifies it. The transform cannot "fail
loudly on schema mismatch" against an unspecified schema, and fixtures cannot be authored
without one. `manifest.json`'s contents are never defined. The contract needs: a written
schema (JSON Schema files committed here), a `schema_version` carried in `manifest.json`,
and a transform that refuses versions it doesn't know. This must be coordinated with the
plugin repo — it is the one place the "division of labour" line is legitimately crossed.

**P3 — Two writers fight over `_bibliography/papers.bib`.** The doc has Zotero/Better
BibTeX auto-exporting *straight into* `_bibliography/papers.bib`, and `transform.py`
merging overrides *into the same file*. Every Zotero re-export silently wipes the merged
override fields; every transform run dirties the Zotero export. This breaks both
idempotency and the "never destroys" rule as written. **Fix:** Zotero exports to
`_incoming/papers.src.bib`; the transform owns `_bibliography/papers.bib` outright
(generated, header comment, overrides merged). Entry order and untouched fields preserved
from the source.

**P4 — The CI/commit model is incoherent as written.** "Run the transform in CI with
`--check` on PRs and a real run on `main`" conflates two mutually exclusive models:
(a) generated output is committed by the author and CI only verifies (`--check`), or
(b) output is never committed and is produced at build time. If `main` runs a "real"
transform but output isn't committed, the repo copy is permanently stale and `--check`
on PRs always fails. **Decision: model (a)** — output is committed, CI runs `--check`
everywhere, the deploy workflow runs transform → `rendercv render` → Jekyll build. This
matches the doc's own diffability rationale.

**P5 — Determinism is assumed but not specified.** `--check` and "running twice produces
identical output" only work with pinned serialization: fixed key order, fixed quoting/width
(e.g. `ruamel.yaml` with explicit settings), stable sorts with defined tie-breakers
(reverse-chronological with `present` sorting first; `importance` then name for projects).
Must be specified before code is written, or `--check` will flap.

**P6 — Deletion/orphan semantics are unaddressed.** If a project or teaching entry leaves
the graph, the corresponding generated `_projects/*.md` lingers forever. The transform
must track ownership (the header comment makes generated files identifiable) and prune
generated files whose source disappeared — never touching files without the header.

**P7 — Assets have no pipeline.** The plugin exports YAML and markdown only. Publication
preview images, org logos, personal-page photo galleries, and images referenced by blog
posts all need to come from somewhere. The doc covers logos (manual `_data/icon_map.yml` +
`assets/img/logos/`) but is silent on the rest. Blog post handling is also underspecified:
`_posts/` needs `YYYY-MM-DD-title.md` filenames and front-matter mapping from whatever the
plugin emits. This needs an explicit decision: either the plugin exports referenced assets
into `_incoming/assets/` (contract change), or images are managed by hand in this repo and
the intermediate format references them by repo path.

**P8 — Latent duplication between `cv.yml` sections and collections.** Projects appear
both as a CV section and (maybe) `_projects/*.md`; likewise teaching and `_teachings/`.
The doc says "may still be used" — that ambivalence will produce drift. **Decision:**
`_data/cv.yml` is the single source for the CV page; collection files are generated *only*
if per-item detail pages are wanted, and then generated from the same intermediate entries
(never hand-maintained in parallel).

**Minor:**
- `_data/coauthors.yml` keyed by "lowercase, unaccented last names" collides on common
  surnames; verify al-folio's actual matching rules before generating.
- `manifest.json` should carry a file list + content hashes so a half-finished `sync.sh`
  copy is detected instead of transformed.
- Third-party embeds (Spotify/SoundCloud iframes) are fine for a personal site, but each
  external dependency on the Personal page should degrade to a plain link when unavailable
  — Wikiloc especially, as the doc notes.
- Goodreads: the doc already makes the case against RSS. Decide now: **use the native
  `_books/` collection**, close the unknown.

---

## 2. Implementation plan

One PR per phase. Each phase has acceptance criteria the reviewer will hold it to.
Phases 4–6 are independent of each other and may be reordered.

### Phase 0 — Bootstrap al-folio *(missing from seed.md; blocks everything)*
Import al-folio v1.x via its template, remove moonwalk remnants (`_config.yml`
`remote_theme`, `index.html`, `test.md`), set identity/config basics, get CI building
and GitHub Pages deploying a stock site.
**Accept when:** stock al-folio deploys green from this repo; no moonwalk traces remain;
pinned gem versions recorded.

### Phase 1 — Ground truth + decisions
Run seed.md's verification checklist against the now-real fork. Write
`docs/SCHEMA-NOTES.md` (actual `cv.yml` schema, `cv_format` selection, `socials.yml`
keys, collections present, gem-owned layouts) and `docs/DECISIONS.md` resolving: CV
format (RenderCV vs JSONResume), bib ownership (per P3), commit-vs-build-time (per P4:
committed), `_books/` for Reading, `_teachings/` usage, projects duplication (per P8),
asset pipeline (per P7).
**Accept when:** all six known-unknowns from seed.md plus P3/P4/P7/P8 have a recorded
decision with a one-line rationale.

### Phase 2 — Intermediate format contract + fixtures
Write JSON Schemas for `cv.yml`, `profile.yml`, `personal.yml`,
`publication_overrides.yml`, `manifest.json` under `docs/intermediate-schema/`.
`manifest.json` spec includes `schema_version`, file list, hashes. Author a realistic
fixture set under `test/fixtures/incoming/`. Coordinate the schema with the plugin repo.
**Accept when:** fixtures validate against the schemas; schemas are versioned; a
deliberately broken fixture exists for negative tests.

### Phase 3 — `bin/transform.py` core: CV + socials
Scaffold with schema validation, version gate, deterministic serialization (P5),
generated-file headers, `--check`, orphan pruning (P6). Implement
`_incoming/cv.yml → _data/cv.yml` (RenderCV mapping, entry-type selection per section,
date handling incl. `present`, sorting) and `profile.yml → _data/socials.yml`. Unit
tests on fixtures; `rendercv render` passes on the output.
**Accept when:** transform is idempotent (run-twice test in CI), fails loudly on the
broken fixture, `--check` wired into CI, RenderCV validates the generated CV.

### Phase 4 — Bibliography pipeline
`_incoming/papers.src.bib` + `publication_overrides.yml` → generated
`_bibliography/papers.bib` (P3 ownership model). Non-destructive field merge, order
preserved, unknown cite-keys in overrides are a loud error. `_data/coauthors.yml`
generation if the plugin exports person data (verify matching rules first).
**Accept when:** round-trip test proves untouched entries are byte-identical; overrides
survive a simulated Zotero re-export.

### Phase 5 — Personal page
`personal.yml → _data/personal.yml`, `_pages/personal.md`, layout override only if
gem layouts can't render it (known-unknown #5). Music/Cycling/DIY/Reading sections per
seed.md; Reading via `_books/`; every embed degrades to a link.
**Accept when:** page renders with fixtures; no broken layout when an embed source is
unreachable; nav shows Personal.

### Phase 6 — Blog + collections
`_incoming/blog/*.md → _posts/` (filename convention, front-matter mapping, asset
references per the P7 decision); `_projects/` / `_teachings/` generation per the P8
decision, including pruning.
**Accept when:** posts build; removing a fixture entry removes its generated file.

### Phase 7 — CI/deploy wiring
Deploy workflow ordering: `--check` → `rendercv render` → Jekyll build → deploy;
`--check` + tests + run-twice idempotency check on PRs. Keep al-folio's own `test/`
checks passing.
**Accept when:** a PR with stale generated output fails CI; `main` deploys green.

---

## 3. Review contract (what every PR will be checked against)

1. Generated files carry the header; no generated content edited by hand; no hand-written
   file overwritten.
2. Idempotency demonstrated (run-twice produces empty diff), not asserted.
3. Schema violations fail loudly with actionable messages; nothing half-written on error.
4. Fixtures updated alongside behavior; negative-path tests exist.
5. Decisions that deviate from `seed.md` or `docs/DECISIONS.md` are recorded there in the
   same PR, not improvised silently.
6. Phase scope respected — cross-phase work split out.
