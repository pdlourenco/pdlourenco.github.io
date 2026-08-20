# Critical analysis & implementation plan for `seed.md`

_Written by the reviewer session (branch `claude/seeding-doc-analysis-zjqcll`). The author
session should treat this as the review contract: PRs will be reviewed against the phase
scopes and acceptance criteria below._

_Amended 2026-08-09 by the author session, folding in the six findings from the PR #1
review. Every amendment is marked **[amended]** and carries its reasoning inline. All
upstream facts below were re-verified against al-folio commit `e25f178` (2026-08-09)._

**Document precedence — later overrides earlier: `seed.md` → this plan → `docs/DECISIONS.md`.**
`seed.md` is the original brief and is deliberately left un-rewritten as a historical
record; where it conflicts with this plan (the bibliography model per P3, the CI model per
P4, the `_projects/` ambivalence per P8, Goodreads vs `_books/`), **this plan wins**, and
where `docs/DECISIONS.md` records a resolved decision, **that wins over both**.

> **[amended] The scope this whole plan assumes is under review.** `seed.md` makes the graph
> the "source of truth for CV, students, projects, personal pages", and Phases 5 and 6 built
> exactly that. [Issue #10](https://github.com/pdlourenco/pdlourenco.github.io/issues/10)
> proposes narrowing the pipeline to **entity data only** — CV, profile, publication overrides
> — and authoring narrative content (blog, project write-ups, the Personal page, books)
> directly as markdown here.
>
> **Undecided as of this writing.** `docs/DECISIONS.md` **D66** records the assessment, which
> is favourable, along with the one gap the proposal does not cover: under D23 a project would
> end up with two sources, and the rule that resolves it is _the graph owns the record, the
> repo owns the write-up_. Nothing has been removed, and Phases 5–6 remain as built and
> merged. If the narrowing is adopted, the phases it retires are 5 and 6 plus the collection
> half of P8 — and D55–D58, D62, D63 and half of D65 need marking superseded rather than
> silently outliving their subject.

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
BibTeX auto-exporting _straight into_ `_bibliography/papers.bib`, and `transform.py`
merging overrides _into the same file_. Every Zotero re-export silently wipes the merged
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
everywhere, the deploy workflow runs `--check` → `rendercv render` → Jekyll build. This
matches the doc's own diffability rationale.

> **[amended]** This sentence originally read "the deploy workflow runs transform", which
> contradicted the model-(a) decision made in the same breath: a deploy that regenerates
> output would publish files nobody reviewed, and `master` could disagree with `_site`.
> The transform is never run by CI — only verified.

**P5 — Determinism is assumed but not specified.** `--check` and "running twice produces
identical output" only work with pinned serialization: fixed key order, fixed quoting/width
(e.g. `ruamel.yaml` with explicit settings), stable sorts with defined tie-breakers
(reverse-chronological with `present` sorting first; `importance` then name for projects).
Must be specified before code is written, or `--check` will flap.

> **[amended]** `ruamel.yaml` is not in upstream's `requirements.txt` (`nbconvert`, `pyyaml`,
> `rendercv[full]`, `scholarly` — all unpinned). Adding it is fine, but note that
> `render-cv.yml` does `pip install -r requirements.txt` and `bin/setup-python-deps`
> deliberately ignores that file, so Phase 0 must decide where transform dependencies live
> and pin them.

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
`_data/cv.yml` is the single source for the CV page; collection files are generated _only_
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

### Phase 0 — Bootstrap al-folio _(missing from seed.md; blocks everything)_

Import al-folio v1.x via its template, remove moonwalk remnants (`_config.yml`
`remote_theme`, `index.html`, `test.md`), set identity/config basics, get CI building
and GitHub Pages deploying a stock site.
**Accept when:** stock al-folio deploys green from this repo; no moonwalk traces remain;
pinned gem versions recorded.

> **[amended]** Six additions, all discovered while verifying the import against upstream:
>
> 1. **`baseurl` must be emptied.** Upstream's effective baseurl is `/al-folio` and its own
>    `AGENTS.md` calls blanking it out a failure mode — but that is advice for _upstream's_
>    repo. This is a GitHub **user site** at `pdlourenco.github.io`, so `baseurl: ""` and
>    `url: https://pdlourenco.github.io` are correct here, and leaving `/al-folio` in place
>    would break every link.
> 2. **Human action items must be listed explicitly, because no commit can perform them.**
>    `deploy.yml` publishes `_site` to `gh-pages` via `JamesIves/github-pages-deploy-action`,
>    and GitHub's built-in Pages Jekyll build _cannot_ build a gem-based theme
>    (`theme: al_folio_core` plus ~20 `al_*` gems, none on the Pages allowlist). Upstream
>    `docs/INSTALL.md` §"Deployment" confirms the sequence: enable Actions → grant
>    `Read and write permissions` → let Deploy run → set Pages source to `gh-pages`.
>    Phase 0 closes when the repo side is done and these are documented, not when a human
>    has clicked them.
> 3. **No demo content or demo media may enter git history.** Upstream carries ~50 MB of
>    example assets (27 MB video, a 14 MB `prof_pic_color.png`). Importing then deleting
>    leaves the blobs in history forever, so the import is selective from the start.
> 4. **Do not publish someone else's identity.** The stock content is Albert Einstein's —
>    bio, CV, publications. It must not be what lands on a personal site. Files whose
>    _schema_ Phase 1 needs are kept as vendored reference under
>    `docs/reference/al-folio-stock/` instead of live under `_data/`.
> 5. **Curate upstream's 23 workflows, and drop the style contract.**
>    `npm run lint:style-contract` fails CI if `_layouts/`, `_includes/`, `_sass/` or
>    `assets/tailwind/` exist — which is exactly what Phase 5's `_layouts/personal.liquid`
>    override needs. Upstream's `AGENTS.md` states the restriction applies to _its_ repo
>    only and that a site built from the template may legally shadow gem-owned files, so
>    the gate is dropped here deliberately, not by accident. Upstream's seven
>    `test/integration_*.sh` scripts also exercise demo content this phase removes.
> 6. **Record an ours-vs-upstream path inventory** in `docs/DECISIONS.md`. `bin/` is
>    upstream-owned (`al-folio`, `cibuild`, `deploy`, `entry_point.sh`, `setup-python-deps`,
>    two `*.py` helpers); P6's pruning must never consider those files, and upstream ships
>    `al_folio_upgrade` + `upgrade-check.yml`, so knowing which paths are ours is what makes
>    a future upgrade tractable. Record the imported upstream commit SHA for the same reason.

### Phase 1 — Ground truth + decisions

Run seed.md's verification checklist against the now-real fork. Write
`docs/SCHEMA-NOTES.md` (actual `cv.yml` schema, `cv_format` selection, `socials.yml`
keys, collections present, gem-owned layouts) and `docs/DECISIONS.md` resolving: CV
format (RenderCV vs JSONResume), bib ownership (per P3), commit-vs-build-time (per P4:
committed), `_books/` for Reading, `_teachings/` usage, projects duplication (per P8),
asset pipeline (per P7).
**Accept when:** all six known-unknowns from seed.md plus P3/P4/P7/P8 have a recorded
decision with a one-line rationale.

> **[amended]** Add one empirical check that Phase 3 depends on: **does stock `_data/cv.yml`
> pass `rendercv render` unmodified?** Upstream's stock file mixes RenderCV and JSONResume
> vocabulary — `label`, `image`, an `address:` mapping (RenderCV has `location: str`), and
> `studyType` / `score` / `courses` in education entries (RenderCV uses `degree`) — while
> RenderCV rejects unknown keys. `render-cv.yml` feeds the file to
> `rendercv render --settings assets/rendercv/settings.yaml` with no preprocessing, so the
> answer is observable, and it decides Phase 3's acceptance gate. Record the answer plus the
> pinned RenderCV version in `docs/SCHEMA-NOTES.md`; that version _is_ the answer to
> seed.md known-unknown #1. Note also that the site CV is rendered by the `al_folio_cv` gem's
> own Liquid — `rendercv` is only the optional PDF path.

### Phase 2 — Intermediate format contract + fixtures

Write JSON Schemas for `cv.yml`, `profile.yml`, `personal.yml`,
`publication_overrides.yml`, `manifest.json` under `docs/intermediate-schema/`.
`manifest.json` spec includes `schema_version`, file list, hashes. Author a realistic
fixture set under `test/fixtures/incoming/`. Coordinate the schema with the plugin repo.
**Accept when:** fixtures validate against the schemas; schemas are versioned; a
deliberately broken fixture exists for negative tests.

> **[amended]** Two clarifications.
>
> **This phase does not block on the plugin repo.** `pdlourenco/logseq-alfolio-export`
> exists and is live (public, `tests/` with vitest — its test data may be reusable as
> fixtures, which beats hand-authoring), but it documents the five output files without
> defining any schema, and `manifest.json`'s structure is described nowhere. The schemas
> committed _here_ are therefore normative; open an issue on the plugin repo to adopt them
> and let the transform's version gate be the enforcement point. Waiting for cross-repo
> agreement would stall a phase that Phase 3 does not actually need finished.
>
> **The export path is already contradictory, not merely unknown** (seed.md known-unknown
> #6): `seed.md` says `<graph>/assets/storages/logseq-alfolio-export/_logseq_export/`, the
> plugin's own README says `<graph>/.logseq/plugins/storages/logseq-alfolio-export/_logseq_export/`.
> Pin it from the plugin's `sync.sh` — the thing that actually copies the files — and fix
> whichever document is wrong.

### Phase 3 — `bin/transform.py` core: CV + socials

Scaffold with schema validation, version gate, deterministic serialization (P5),
generated-file headers, `--check`, orphan pruning (P6). Implement
`_incoming/cv.yml → _data/cv.yml` (RenderCV mapping, entry-type selection per section,
date handling incl. `present`, sorting) and `profile.yml → _data/socials.yml`. Unit
tests on fixtures; `rendercv render` passes on the output.
**Accept when:** transform is idempotent (run-twice test in CI), fails loudly on the
broken fixture, `--check` wired into CI, and the CV gate below is met.

> **[amended]** The RenderCV gate is now **conditional on Phase 1's empirical finding**,
> because as originally written it may have been unmeetable — and chasing it would have meant
> contorting the generated file to satisfy a validator the theme never requires:
>
> - stock `_data/cv.yml` **does** pass `rendercv render` → gate stays "the generated CV
>   passes `rendercv render`" with the RenderCV version pinned;
> - stock **does not** pass → the gate becomes "the CV page renders correctly under
>   `al_folio_cv`", PDF generation is declared out of scope, and `render-cv.yml` is disabled
>   rather than left permanently red.

### Phase 4 — Bibliography pipeline

`_incoming/papers.src.bib` + `publication_overrides.yml` → generated
`_bibliography/papers.bib` (P3 ownership model). Non-destructive field merge, order
preserved, unknown cite-keys in overrides are a loud error. `_data/coauthors.yml`
generation if the plugin exports person data (verify matching rules first).
**Accept when:** round-trip test proves untouched entries are byte-identical; overrides
survive a simulated Zotero re-export.

> **[amended]** The shipped pipeline **does not** preserve entries byte-identically, and the
> acceptance criterion above is superseded. `docs/DECISIONS.md` D43–D54 require the transform
> to reorder entries (by section, then date), reorder and drop fields, rewrite values
> (`address`→`location`, `type`→a note), fold presentations into their papers, and exclude
> work the owner neither authored nor supervised. "Non-destructive field merge, order
> preserved" was written when `papers.bib` was imagined as a lightly-annotated copy of the
> Zotero export; it is instead a **derived view** of it.
>
> What the original criterion was protecting still holds, and is what to test instead:
> **the source file is never edited**, and **overrides survive a Zotero re-export** because
> they live in a separate file keyed by cite-key (D24). The round-trip property is therefore
> asserted on the _generated_ file — same input, byte-identical output — plus the
> unknown-cite-key error that catches an override whose entry disappeared.
>
> `_data/coauthors.yml` is **not applicable** yet: the plugin exports no person data, so
> there is nothing to generate it from. Recorded rather than quietly dropped.

### Phase 5 — Personal page

`personal.yml → _data/personal.yml`, `_pages/personal.md`, layout override only if
gem layouts can't render it (known-unknown #5). Music/Cycling/DIY/Reading sections per
seed.md; Reading via `_books/`; every embed degrades to a link.
**Accept when:** page renders with fixtures; no broken layout when an embed source is
unreachable; nav shows Personal.

> **[amended]** A local `_layouts/personal.liquid` is legitimate here — upstream's
> `AGENTS.md` "stop sign" forbidding `_layouts/`, `_includes/`, `_sass/` binds _upstream's_
> starter repo, not sites built from it, and it says so explicitly. The gate that would have
> blocked it (`npm run lint:style-contract`) is dropped in Phase 0 for this reason. Prefer
> config and `_data` first regardless, per upstream's own bootstrap skill.

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

> **[amended]** This is two upstream workflows, not one, and both need edits:
>
> 1. **`deploy.yml` is path-filtered.** It triggers on assets/markdown/YAML/HTML/JS/Liquid/
>    Gemfile changes, so a transform-only change (`_incoming/**`, `bin/transform.py`) can
>    silently fail to redeploy. Add those paths.
>
>    _(Phase 7: **mostly wrong** — see `docs/DECISIONS.md` D61. `**.yml`/`**.bib`/`**/*.md`
>    already matched `_incoming/` and every generated file. Only `manifest.json` and `bin/*.py`
>    were unmatched; both added. The real hole was `transform-check.yml` watching
>    `bin/transform.py` by name, which excluded `bin/bibliography.py`.)_
>
> 2. **`render-cv.yml` pushes to the default branch** — its last step is
>    `git add -A && git commit -m "chore: render the latest CV" && git push`. Under model (a)
>    that `-A` is a route for un-reviewed generated output to reach `master` and then drift
>    from `_incoming/`. Narrow it to `assets/rendercv/`.
> 3. **Pick an ordering mechanism now:** `render-cv.yml` already exposes `workflow_call:`, so
>    either `deploy.yml` calls it (giving the stated `--check` → rendercv → build → deploy
>    order) or the two stay independent and the ordering claim is dropped.
>
> "Keep al-folio's own `test/` checks passing" is narrowed to **the checks we kept** —
> Phase 0 drops the style contract (it forbids Phase 5's layout override) and the
> `test/integration_*.sh` scripts that exercise removed demo content. `docs/DECISIONS.md`
> lists what survives; that list is the Phase 7 target.

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
7. **[amended]** Upstream-owned files are left alone unless the change is deliberate and
   recorded: no edits under `bin/` (except our own `bin/transform.py`), no vendored upstream
   doc rewritten in place, and any newly shadowed gem-owned file justified in
   `docs/DECISIONS.md`. The imported upstream SHA in `docs/DECISIONS.md` is what makes a
   later upgrade diffable — keep it current when upstream is re-pulled.
