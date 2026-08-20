# Decisions

Resolved decisions, newest section last. **This file is the highest authority**: it overrides
`docs/IMPLEMENTATION-PLAN.md`, which overrides `seed.md`.

Each entry records what was decided and why, so a later session does not re-litigate it. A
decision that turns out wrong should be superseded by a new entry, not edited away.

---

## Phase 0 — Bootstrap

### D1 — al-folio is adopted by selective template import, not by forking its history

Upstream `alshedivat/al-folio` commit **`e25f178e9e56695d6a453e848fc6fc190282912e`**
(2026-08-09) is the import base. Its history was _not_ merged into this repo.

**Why:** al-folio v1.x is a thin starter whose runtime lives in versioned gems
(`al_folio_core` and friends), so upgrades are gem bumps plus the `al_folio_upgrade` CLI —
not template merges. Merging thousands of unrelated commits would make every future
`git merge upstream` a conflict over demo content we deleted. Recording the SHA keeps
upgrades diffable: `git diff e25f178..<new> -- <path>` against an upstream clone shows
exactly what changed in the files we actually took.

### D2 — `baseurl` is empty; `url` is `https://pdlourenco.github.io`

Upstream ships `baseurl: /al-folio` and its `AGENTS.md` warns that blanking it breaks the
site. That warning is about _upstream's_ repo, which is served from a project-page subpath.
This is a **user site** served at the domain root, so empty is the only correct value.

### D3 — No demo content and no demo media in git history

Upstream carries ~50 MB of example assets (27 MB of video, a 14 MB `prof_pic_color.png`).
Importing and then deleting would leave the blobs in history permanently, so the import was
selective from the start. The imported tree is ~800 KB.

Stock content was also **Albert Einstein's** — bio, CV, publications, citation cache. None of
it may appear on a personal site. The files whose _schema_ later phases need are vendored,
un-rendered, under `docs/reference/al-folio-stock/`: `cv.yml`, `socials.yml`, `resume.json`,
`papers.bib`. They are reference material, excluded from the build.

Consequently: `_data/cv.yml`, `_data/coauthors.yml` and `_data/citations.yml` do **not**
exist yet, `_bibliography/papers.bib` is a placeholder comment, and `_config.yml`'s
`jekyll_get_json` block (which loaded `assets/json/resume.json`) is commented out —
Phase 1 reinstates it only if JSONResume beats RenderCV.

### D4 — Generated output is committed; CI only ever verifies it

Restates the plan's P4 decision as binding: `bin/transform.py` runs on a developer machine,
its output is committed, and CI runs `--check`. No workflow regenerates transform output.
This is why `render-cv.yml`'s `git add -A` was narrowed to `git add assets/rendercv` — as
shipped it would commit anything else dirty in the tree straight to the default branch.

**One deliberate exception, so nobody "fixes" it later:** `render-cv.yml` _is_ CI generating
and committing a file to the default branch — the rendered CV PDF under
`assets/rendercv/rendercv_output/`. That is a build artifact of a pinned external tool, not
transform output, and it cannot be produced on a developer machine reliably (Typst fetches
font packages at render time). The rule that matters is the narrow one: **nothing that
`bin/transform.py` owns is ever written by CI.** The `git add` narrowing above is what keeps
this exception from widening.

Its commit step is also guarded — `git commit` exits 1 on "nothing to commit", so an
unchanged render would otherwise fail the run the moment Phase 3 re-enables the trigger:

```bash
git diff --cached --quiet || (git commit -m "chore: render the latest CV" && git push)
```

### D5 — Our `CLAUDE.md` is authoritative; upstream's agent docs are vendored reference

`seed.md` was written as a `CLAUDE.md` (its first line still says so) and upstream ships its
own root `CLAUDE.md` + `AGENTS.md`, so the import collided. Resolution:

- root `CLAUDE.md` is **ours** — it points at `seed.md`, the plan, and this file, and states
  the precedence order;
- upstream's long-form docs are vendored at `docs/al-folio/` (`ARCHITECTURE.md`,
  `BOUNDARIES.md`, `CUSTOMIZE.md`, `INSTALL.md`, …), read-only;
- upstream's `AGENTS.md`, `CONTRIBUTING.md`, `SHOWCASE.md`, `docs/releases/`,
  `.github/agents/`, `.github/instructions/`, `.github/ISSUE_TEMPLATE/`,
  `copilot-instructions.md` and the al-folio PR template were **not** imported: they describe
  contributing to al-folio itself, which is not what this repo is;
- `.agents/skills/` **was** imported (`al-folio-bootstrap`, `al-folio-v1-migration`) with the
  `.claude/skills` symlink, because both are useful when working on a site built from the
  template.

Two upstream rules deliberately do not bind us, and `CLAUDE.md` says so: the "stop sign"
against local `_layouts/`/`_includes/`/`_sass/`, and `npm run lint:style-contract` which
enforces it. Upstream itself carves out sites built from the template. Phase 5's
`_layouts/personal.liquid` depends on this.

### D6 — Workflow set

**Kept:** `deploy.yml` (build + publish `_site` to `gh-pages`), `prettier.yml`,
`prettier-html.yml`, `broken-links.yml`, `render-cv.yml` (trigger disabled, see D7).

**Dropped:** `unit-tests.yml` and upstream's `test/` suite — it runs the style contract we
deliberately do not want (D5) and seven `integration_*.sh` scripts that exercise demo content
this phase removed. `visual-regression.yml` (diffs against an upstream `v0.16.3` baseline),
`lighthouse-badger.yml`, `star-history.yml`, `update-screenshots.yml`, `update-tocs.yml`,
`update-citations.yml`, `axe.yml`, `broken-links-site.yml`, `codeql.yml`,
`copilot-setup-steps.yml`, `prettier-comment-on-pr.yml`, `release.yml`, `stale.yml`,
`deploy-image.yml`, `deploy-docker-tag.yml`, `docker-slim.yml`.

Two upstream `bin/` scripts went with their workflows: `capture_screenshots.js`
(`update-screenshots.yml`) and `generate_star_history.py` (`star-history.yml`). The rest of
`bin/` is imported unchanged and stays upstream-owned.

**Fixed on import:** `broken-links.yml` was guarded by
`if: github.repository == 'alshedivat/al-folio'`, so it would never have run here — the guard
is removed and its lychee excludes now name paths that exist in this repo.

Phase 7 owns the rest of CI wiring, and `docs/IMPLEMENTATION-PLAN.md` Phase 7 records what
still needs doing: `deploy.yml`'s `paths:` filter must learn about `_incoming/**` and
`bin/**`, or a transform-only change will not redeploy.

### D7 — Python dependencies are pinned, and RenderCV is pinned to 2.x with the config adapted

`requirements.txt` upstream is unpinned (`rendercv[full]`, `pyyaml`, `nbconvert`,
`scholarly`), and `render-cv.yml` installs from it — so an upstream release can turn CI red
with no change on our side. Pinned here: `rendercv[full]==2.3`, `click==8.4.2`,
`pyyaml==6.0.3`, `nbconvert==7.17.1`. `scholarly` is dropped along with
`update-citations.yml`; reinstate both together if Google Scholar counts are ever wanted.

`click` is pinned because **RenderCV 2.3 imports `click.core` without declaring the
dependency** — in a clean venv its CLI dies with `ModuleNotFoundError: No module named
'click'`.

Upstream's `assets/rendercv/settings.yaml` and `render-cv.yml` are written for **RenderCV
1.x** and fail on 2.x. Verified locally against 2.3, and fixed here:

| Upstream (1.x)                     | Required by 2.x           |
| ---------------------------------- | ------------------------- |
| top-level key `settings:`          | `rendercv_settings:`      |
| `dont_generate_typst: false`       | removed from the schema   |
| `rendercv render … --settings <f>` | `--rendercv-settings <f>` |

Passing `--settings` to 2.x is parsed as a CV field override and rejected with
"This field is unknown for this object", which is what upstream's workflow would have hit.

Pinning 1.x instead was rejected: RenderCV **1.18 fails on upstream's own stock `cv.yml`**
(`cv.social_networks.0.network: X` is not in 1.x's allowed network list) _and_ also rejects
`--settings`. So 1.x is not the working combination it appears to be.

`render-cv.yml`'s `push:` trigger is commented out until Phase 3 generates `_data/cv.yml`.
Without that file the workflow exits 1, so the very commit that imported
`assets/rendercv/*.yaml` would have gone red.

### D8 — Nav is switched on per phase, not all at once

Pages exist but stay off the navbar until they have real content, so nothing published is
empty or misleading. Current state → the phase that flips it:

| Page               | Nav      | Turned on by                                                           |
| ------------------ | -------- | ---------------------------------------------------------------------- |
| about (`/`)        | homepage | — (placeholder text; owner supplies bio + photo)                       |
| blog               | **on**   | Phase 6 fills `_posts/`                                                |
| repositories       | **on**   | already real — `_data/repositories.yml` points at `pdlourenco`         |
| cv                 | off      | Phase 3 generates `_data/cv.yml`                                       |
| publications       | off      | Phase 4 generates `_bibliography/papers.bib`                           |
| projects, teaching | off      | **deliberate, permanent** — both render inside the CV page (`seed.md`) |
| books              | off      | Phase 5 decides `_books/` for the Reading section                      |
| personal           | absent   | Phase 5 creates it                                                     |

`_pages/about.md` also has `selected_papers`, `announcements` and `latest_posts` disabled
until Phases 4 and 6 respectively.

### D9 — Local builds need a UTF-8 locale

`bundle exec jekyll build` dies with `invalid byte sequence in US-ASCII` inside
`al_folio_core`'s legacy-pattern scanner when the shell locale is `C`/POSIX, because this
site's own content is not ASCII ("Lourenço"). Build with `LANG=C.UTF-8`. GitHub runners are
already UTF-8, so this is a local-environment note, not a CI issue.

### D10 — Third-party surface in CI is removed or pinned, not inherited

From the Phase 0 review. Upstream's `deploy.yml` ran `fjogeleit/yaml-update-action@main` — a
**mutable** third-party ref inside a `contents: write` workflow that publishes the site — to
stamp `giscus.repo`. Removed rather than pinned: giscus has no `repo_id`/`category_id` and no
page enables comments, so the step did nothing. If comments are ever wanted, set
`giscus.repo` in `_config.yml` directly. Same file: `pip3 install --upgrade nbconvert` now
installs the D7 pin instead of re-floating the version on every deploy.

Standing rule: a third-party action in a workflow with write permission is either pinned to a
commit SHA or removed. Upstream inheritance is not a reason to keep one.

### D11 — Stock branding counts as demo content

Also from the review, and a genuine miss in D3's verification: `blog_name: al-folio` /
`blog_description: a simple whitespace theme for academics` render as the `/blog/` masthead
(`<h1>`/`<h2>`), and blog is one of the two pages with nav on. The import check grepped for
"Einstein" and `/al-folio` links, which does not catch upstream's own product name used as
site copy. Both are blank now (the Liquid guards on a non-empty value, so the header bar
simply doesn't render), as is `disqus_shortname: al-folio`, which pointed at upstream's forum.

Lesson for later phases: when checking that nothing upstream leaked into a page, read the
rendered `_site` output, don't just grep sources for the obvious names.

`.lycheeignore` was trimmed for the same reason — most of it named demo files that were never
imported, plus paths already excluded in `broken-links.yml`. Only the URL excludes remain
(`linkedin.com` blocks bots and would flake the check against `_data/socials.yml`).

### D12 — Imported skills carry an adaptation note

`.agents/skills/` is auto-loaded into every future session through the `.claude/skills`
symlink, and both imported skills are written for someone working _on_ al-folio: they tell the
reader to build with `--baseurl /al-folio` (wrong here per D2), to read a root `AGENTS.md`
(not imported per D5), and to route changes into plugin repos. Each now opens with a short
"Adaptations for this repo" note instead of being rewritten, which keeps the diff against
upstream small for future upgrades.

---

## Phase 1 — Ground truth and content decisions

Measured facts live in [`docs/SCHEMA-NOTES.md`](SCHEMA-NOTES.md); this section records the
choices those facts forced. `seed.md`'s six known-unknowns are closed here (or, for #3,
deliberately made not to matter).

### D13 — The CV format is RenderCV, not JSONResume _(closes unknown #1)_

`_pages/cv.md` already ships `cv_format: rendercv`, `_data/cv.yml` is the file the pipeline
targets, and RenderCV is the only one of the two with a PDF path (`render-cv.yml`). JSONResume
would additionally require re-enabling `jekyll_get_json` and maintaining
`assets/json/resume.json`. RenderCV version pinned at **2.3** (D7) — that pin _is_ the answer
to the "exact RenderCV schema version" unknown.

Note that `al_folio_cv` accepts both vocabularies in its section templates, so a RenderCV file
with the odd JSONResume key still renders. That is tolerance, not a reason to mix: the transform
emits RenderCV names only, because the PDF path validates strictly.

### D14 — Custom CV sections use `BulletEntry` or `OneLineEntry`, and reuse special-cased titles where possible

Forced by the gem: `render.liquid`'s fallback for a non-special-cased section title renders
**only** `entry.bullet`, or `entry.label` + `entry.details`. Every other key produces an empty
card — heading, no content, no warning. `seed.md`'s suggestion of `NormalEntry` for sections
like "Supervised Students" would render blank on the site while validating fine in RenderCV.

Therefore:

- **Supervised Students**, **Jury** → `BulletEntry` (`bullet:` holding markdown), which also
  matches `seed.md`'s own advice to push detail into free text rather than invent keys.
- **Research Interests** → name the section **`Academic Interests`** so it hits the richer
  `interests.liquid` template (`name` + `keywords` + `icon`) instead of the fallback.
- Experience, Education, Projects, Awards, Skills, Languages use the special-cased titles
  exactly as spelled in `SCHEMA-NOTES.md` §1.
- Location goes in `cv.address.*`, never `cv.location` — the latter is accepted and then
  silently not rendered.

Phase 3 must assert this: an entry landing in a fallback section without `bullet`/`label` is a
transform error, not a warning. The site gives no feedback, so the transform has to.

### D15 — The transform sorts every section; the gem's sorting is a coincidence, not a contract

`al_cv_sort_by_date` re-sorts only **Experience + Volunteer** and **Education**. Projects,
Awards and custom sections render in array order, and `rendercv render` uses array order for
_everything_. So the transform owns ordering outright:

- experience, education, and any dated custom section: reverse-chronological, ongoing first;
- projects: `importance` then name (per `seed.md`);
- tie-break on a stable key so `--check` cannot flap (P5).

Emit `end_date: present` for ongoing entries — the gem recognises `present`/`current`/`ongoing`/`now`,
and RenderCV accepts `present`.

### D16 — `_teachings/` is used only for courses that have their own page _(closes unknown #2)_

The collection exists and is wired: `{% include courses.liquid %}` groups by `year` then
`term`, and `layout: course` gives per-course pages with `instructor`/`term`/`location`/`time`/`schedule`.

But `seed.md` puts teaching **inside the CV page**, and `/teaching/` stays off-nav (D8). So:
the CV page's Teaching section is generated from `_incoming/cv.yml` and is the canonical
listing; `_teachings/*.md` is generated **only** for courses that warrant a detail page, from
the same intermediate entries, never hand-maintained in parallel (this is D23/P8 applied to
teaching). If no course needs a page, the collection stays empty and that is fine.

### D17 — Reading uses the native `_books/` collection, not Goodreads _(closes unknown #4)_

Confirms the plan's provisional call with the mechanics verified: `layout: book-review` for
entries, `layout: book-shelf` for the index, no third-party dependency, no API that can be
retired under us. Book entries come from the graph like everything else.

`jekyll-socials` has no built-in `goodreads` key, but that costs less than first recorded: an
**arbitrary** key whose value is a `{logo, title, url}` hash renders as a social icon (there is
no literal `custom_social:` keyword — see `SCHEMA-NOTES.md` §2), so the Goodreads profile
(`7400919-pedro`) can be a first-class icon rather than only an in-page link. Same mechanism
covers Wikiloc under D19.

### D18 — The Personal page needs no local layout override _(closes unknown #5)_

`page.liquid` renders `{{ content }}` verbatim and Jekyll processes Liquid inside page content,
so `_pages/personal.md` with `layout: page` can loop over `site.data.personal` inline. A local
`_layouts/personal.liquid` remains **permitted** (D5) but is no longer _expected_ — Phase 5
should reach for it only if the inline version becomes unreadable, and record why.

### D19 — Wikiloc is designed around, not verified _(unknown #3 stays open, deliberately)_

`www.wikiloc.com` is blocked by this environment's egress proxy, so whether their per-trail
iframe still works **could not be tested here**, and I am not going to record a guess as a
finding. It does not need to block anything: the Personal page's Cycling & Hiking section is
built link-first — a plain profile/trail link that always works, with an embed added only if
someone confirms it renders. That is the graceful-degradation rule the plan already requires
for every third-party embed, so the unknown costs nothing.

### D20 — The export path is `<graph>/.logseq/plugins/storages/…` — `seed.md` is wrong _(closes unknown #6)_

| Source                               | Path                                                                        |
| ------------------------------------ | --------------------------------------------------------------------------- |
| `seed.md`                            | `<graph>/assets/storages/logseq-alfolio-export/_logseq_export/` ❌          |
| plugin `README.md` and **`sync.sh`** | `<graph>/.logseq/plugins/storages/logseq-alfolio-export/_logseq_export/` ✅ |

`sync.sh` is the authority because it is the thing that copies the files. `seed.md` is frozen
and not corrected in place (per its precedence note); this entry is the correction.

### D21 — `sync.sh` violated the pipeline contract — **resolved upstream**

> **Resolved.** Verified directly at plugin HEAD `f9b781c`: `sync.sh` now copies into
> `<site>/_incoming/` only, and requires `--site` explicitly with no default "so a stray run
> cannot touch a real site repo by accident". The overwrite hazard below is historical. It does
> **not** yet implement D64 — the manifest is copied before the blog posts and nothing is
> pruned — but that is a staleness bug, not a destructive one. Running it is now safe.
>
> Kept rather than deleted because the owner action item it produced stood for several phases,
> and because the original finding is the reason the boundary exists.

Found while resolving D20, and the most consequential Phase 1 finding: **`sync.sh` copies the
export straight into `_data/` and `_posts/`**, with `manifest.json` renamed to
`_data/export_manifest.json`. It does not know `_incoming/` exists.

That is not a cosmetic mismatch. Run against this repo today it would:

1. **overwrite `_data/cv.yml` with intermediate-format YAML.** The site reads
   `site.data.cv.cv` with the section names in `SCHEMA-NOTES.md` §1 — an intermediate file
   would render a blank or half-empty CV page with no error;
2. **write `_posts/` directly from the graph**, skipping the `YYYY-MM-DD-title.md` naming and
   front-matter mapping Phase 6 owns;
3. **clobber generated output that CI verifies with `--check`** (D4), so the next PR would fail
   with a diff nobody authored.

Decision: **`sync.sh` must target `_incoming/` only** — `_incoming/*.yml`,
`_incoming/manifest.json`, `_incoming/blog/*.md` — and never write `_data/` or `_posts/`. The
transform is the only writer of al-folio formats. Until the plugin repo is updated, **do not
run `sync.sh` against this repository**; copy the export directory to `_incoming/` by hand.

This is the one place the plugin/site division of labour is legitimately crossed (P2), so it is
a coordinated change: Phase 2 opens an issue on `pdlourenco/logseq-alfolio-export` alongside the
committed JSON Schemas, and the schemas here stay normative regardless of when that lands.

### D22 — Assets are managed by hand in this repo; the intermediate format references them by repo path _(resolves P7)_

The plugin exports YAML and markdown only, and `manifest.json` carries no asset list. Rather
than widen the contract to ship binaries — which would put photo galleries into the versioned
API and make every graph edit a binary diff — images live in this repo:

- publication previews: `assets/img/publication_preview/`
- organisation logos: `assets/img/logos/` + `_data/icon_map.yml` (manual, per `seed.md`)
- Personal-page galleries: `assets/img/personal/<section>/`
- blog post images: `assets/img/posts/`

The intermediate YAML references them by **repo-relative path**, and the transform **fails
loudly if a referenced path does not exist** — that check is what stops a silent broken image.
`imagemagick` generates responsive widths from `assets/img/` (`SCHEMA-NOTES.md` §7), which is
another reason to keep everything under that tree.

### D23 — `_data/cv.yml` is the single source for the CV page; collection files are generated only for detail pages _(records P8)_

Restates the plan's P8 decision as binding, now with the collections verified as present
(`books`, `news`, `projects`, `teachings`). `_projects/*.md` and `_teachings/*.md` are generated
from the **same** intermediate entries that feed the CV section, only when a per-item page is
wanted, and are pruned when their source disappears (P6). Neither `/projects/` nor `/teaching/`
appears in nav (D8) — both render inside the CV page.

### D24 — Bibliography ownership _(records P3)_

Restates the plan's P3 fix as binding: Zotero / Better BibTeX exports to
**`_incoming/papers.src.bib`**; `bin/transform.py` owns **`_bibliography/papers.bib`** outright
(generated header, overrides from `_incoming/publication_overrides.yml` merged into the entries
as BibTeX fields, entry order and untouched fields preserved). Zotero must never be pointed at
`_bibliography/` again — that was the two-writers bug.

`_data/coauthors.yml` is generated too, keyed as verified in `SCHEMA-NOTES.md` §5: lowercased
accent-stripped surname → list of `{firstname: [variants], url}`. The list-of-people shape is
what resolves surname collisions, provided every initial form appearing in the `.bib` is
emitted.

> **Amended by Phase 4 (D43–D54).** "Entry order and untouched fields preserved" no longer
> describes the implementation, and the plan's matching acceptance criterion is superseded
> there too. `papers.bib` is a **derived view**, not an annotated copy: entries are reordered
> by section and date, fields are reordered and some dropped, values are rewritten, and
> entries are folded or excluded outright. That was not a drift — D43–D54 each require it, and
> a copy-with-annotations could not produce the page the owner asked for.
>
> **D24's core is untouched and is the part that mattered:** Zotero writes only
> `_incoming/papers.src.bib`, the transform owns `_bibliography/papers.bib` outright, and
> overrides survive a re-export because they live in a separate file keyed by cite-key.
>
> `_data/coauthors.yml` is **not generated yet**: the plugin exports no person data, so there
> is no source for the `url` each entry needs. Named here so it is not mistaken for done —
> the `SCHEMA-NOTES.md` §5 shape stays correct for when it is.

### D25 — CI lints with the versions the lockfile pins

`prettier.yml` as inherited ran `npm install --save-dev --save-exact prettier @shopify/prettier-plugin-liquid`,
installing whatever was newest and ignoring `package-lock.json`. It now runs `npm ci`.

This was not hypothetical: it failed PR #3. The runner picked up
`@shopify/prettier-plugin-liquid 1.11.0` where the lockfile pins `1.10.0`, and 1.11.0's Liquid
printer reformats fenced ` ```liquid ` blocks. `docs/SCHEMA-NOTES.md` quotes a **deliberately
truncated** excerpt of `bib.liquid`, so the newer plugin "fixed" it by appending
`{% endif -%}{%- endfor -%}{%- endif %}` — turning a faithful quotation into code the gem does
not contain, and the `{% if %}` into a self-closed no-op. A green local check and a red CI check
on identical bytes.

Two changes, because either alone leaves a hole:

1. **CI uses the lockfile** (`npm ci`), so local and CI check with the same versions. This is
   D10's rule applied to lint tooling: an unpinned dependency in CI is a build that changes
   under you.
2. **Quoted source excerpts are fenced as `text`**, not as their language, whenever they are
   truncated. A formatter should never be in a position to rewrite a quotation.

### D26 — Enumerate a gem's accepted keys by parsing the gem, not by grepping it

`SCHEMA-NOTES.md` §2 originally listed 47 of `jekyll-socials`' 49 built-in keys and claimed
unknown keys are silently dropped. Both errors came from method: the list was assembled with a
regex over patterns like `*_username` / `*_id` / `*_url`, which structurally cannot match
`academia_edu` or `research_gate_profile`, and the silent-drop claim was inferred from the key
maps without reading the render loop's `else` branch — which in fact implements the
custom-social mechanism and raises `NoMethodError` on a scalar value.

Rule for the rest of the pipeline work: when a document's value _is_ its accuracy, enumerate
from the source of truth mechanically (parse the constant, run the code) and state how it was
obtained. A grep proves a key exists; it never proves a list is complete. The corrected §2 was
produced by parsing the gem's constant tables and by executing the failing expression.

---

## Phase 2 — Intermediate format contract and fixtures

### D27 — The contract was derived by running the plugin, not by reading it

`docs/intermediate-schema/` describes what the plugin **actually emits**: its own vitest
fixtures were driven through `runExport()` and the files it wrote to sandbox storage captured
verbatim. That is D26's rule applied to a whole contract, and it immediately paid for itself —
reading the source alone would have reproduced `seed.md`'s wrong claim about nulls (D28) and
missed that `cv.yml` has no `cv:` wrapper.

The plugin's fixtures use fictional sample identities (`John Doe`, `University of Porto`); ours
match them deliberately, so a fixture can be traced across the two repos and no biography is
invented to fill a test.

### D28 — Optional fields accept both `null` and absent, because the plugin emits both

The plugin's YAML writer drops `null` inside a **mapping** but emits it inside a **list item**.
So `cv.yml`'s entries carry explicit `description: null`, while `profile.yml`'s `github.url`
simply disappears when unset. `seed.md` says the intermediate YAML "omits empty properties
entirely" — true of mappings only.

Every optional field in the schemas therefore accepts `null` as well as being absent, and the
transform must treat them identically. We asked the plugin **not** to make this uniform: it
would be a breaking shape change for no gain, and would force a `schema_version` bump.

### D29 — `schema_version` is required, and today's exports fail that gate on purpose

`manifest.json` must carry `schema_version` (integer, currently `1`). The transform refuses a
version it does not know **and** an export with no version at all, rather than guessing.

> **✅ Resolved upstream** at plugin `a6f769f` — `index.js:1245` emits
> `schema_version: SCHEMA_VERSION`. The plugin session reports validating a real export against
> these schemas and running `bin/transform.py` over it end to end: manifest valid, both-
> directions file check clean, hashes recomputed, exit 0.
>
> **This repeals the advice this entry produced.** "`schema_version` is the blocker — nothing
> processes until it lands" was true when written and is now simply wrong; the pipeline runs
> today. `legacy-unversioned/` stays exactly as it is, because its job changed rather than
> ended: it is no longer "the actual current export", it is the **regression fixture** proving
> the gate still fires. Keeping it means a future plugin that stops emitting the field is
> caught rather than silently accepted, so it should not be promoted.

The plugin did not emit it at first, so early real output was invalid against the contract. That
was recorded rather than papered over: `test/fixtures/incoming/legacy-unversioned/` holds such an
export and the validator asserts it fails **specifically on `schema_version`**.

Breaking shape changes increment the version; additive optional fields do not — which is why
entry objects set `additionalProperties: true` and `hashes` is optional-but-validated. A plugin
that learns a new field cannot break a transform that has not learned it yet.

The same tolerance at `cv.yml`'s **top level** means an unknown or renamed _section_ validates
cleanly, so **Phase 3 must fail or warn loudly on a top-level section it has no mapping for**.
Forward-compatibility in the schema is correct; without that guard it would just relocate a
silent-content-loss bug from the validator into the transform.

### D30 — Three fixture sets, each with an expectation the validator enforces

`test/fixtures/incoming/` holds `valid/` (must pass, schemas _and_ manifest consistency),
`legacy-unversioned/` (must fail, on `schema_version`), and `broken/` (must surface **every**
planted violation, not stop at the first — 13 of them across `cv.yml` and `manifest.json`).
`test/validate_fixtures.py` asserts all three, and Phase 3 moves this validation into
`bin/transform.py`. `jsonschema` is pinned in `requirements.txt` per D7.

The manifest checks the schema cannot express live in the validator too — files listed vs files
present in both directions, and SHA-256 comparison — because that is what makes a half-finished
copy detectable instead of transformable.

### D31 — `format` in JSON Schema validates nothing; use `pattern` when it must hold

Found while writing the negative fixture: `broken/manifest.json`'s `exported_at:
"not-a-timestamp"` **passed** validation. `format: date-time` is annotation-only in JSON Schema
and enforces nothing unless a format checker is explicitly wired up (and for `date-time`,
`jsonschema` needs an extra package even then). The malformed value was accepted silently.

`exported_at` now carries a `pattern` alongside the `format` annotation. Standing rule: if a
string constraint must actually hold, express it as `pattern` or `enum`. This is the same class
as D14 (a template that renders nothing for an entry shape it does not recognise) and D25
(a linter pinned by nobody) — a check that looks like it is checking something and isn't.

### D32 — Filed as one issue upstream, and it does not block us

`pdlourenco/logseq-alfolio-export#1` covers all five gaps: `sync.sh` retargeting to `_incoming/`
(the damaging one), `schema_version`, hashes, the incomplete `files` list, and the hard-coded
`plugin_version`. Per the amended Phase 2, the schemas here are normative regardless of when
that lands, and Phase 3 proceeds against them.

### D33 — Non-content files are excluded from the build explicitly

Found by checking the `gh-pages` branch after a merge rather than only the PR's CI: the deployed
site was serving **`requirements.txt`** at its root. `_config.yml`'s `exclude:` list is
allow-by-default, upstream's list never mentioned that file, and `docs/` was excluded while
nothing covered `test/` — so Phase 2's fixtures and validator would have been published too.

Both are excluded now. Standing rule: anything added at the repo root or as a new top-level
directory needs an `exclude:` entry unless it is genuinely site content. Dot-directories
(`.github/`, `.agents/`, `.devcontainer/`) are safe — Jekyll skips them by default.

The general lesson is about verification, not YAML: a PR's `deploy` job builds but does **not**
publish, so the published tree is only observable after a merge. Post-merge runs and the
`gh-pages` contents are part of checking a phase, not an afterthought.

---

## Phase 3 — The transform core (CV + socials)

### D34 — One entry can satisfy both contracts; the anchor key is what makes it work

The gem and RenderCV want different keys, and for Awards they genuinely conflict:
al-folio's `awards.liquid` renders `title`/`awarder`, and RenderCV **rejects**
`{title, awarder, date, summary, url}` outright.

Probing RenderCV 2.3 one entry at a time found the rule (`docs/SCHEMA-NOTES.md` §1): an entry
must carry a key that **anchors** it to a RenderCV entry type, after which RenderCV tolerates
al-folio's extra keys alongside. Upstream's own stock Awards entries validate only because
`authors` next to `title` makes them a `PublicationEntry` — remove `authors` and the identical
entry is rejected.

So the transform emits **`name` _and_ `title`** for awards: `name` anchors a `NormalEntry` for
RenderCV, `title`/`awarder` are what the gem renders. Verified both ways on generated output —
`rendercv render` validates, and all 11 cards render with content on `/cv/`. There was no need
to trade a good-looking page against a valid PDF; it just had to be deliberate.

### D35 — Section titles are chosen for the gem's dispatch table, not for prose

`Research Interests` reaches al*folio_cv's bare fallback; **`Academic Interests`** reaches the
richer `interests.liquid`. Same content, better rendering, so that is the title emitted (D14).
Conversely `Supervised Students` and `Jury` are deliberately \_not* special-cased titles, so
their entries are `BulletEntry` — structure lives in the markdown of the bullet, which is what
`seed.md` suggested for supervisor affiliations anyway.

`SECTION_ORDER` in the transform is asserted against the sections actually built: a mapping
added without an order entry raises rather than silently dropping the section.

### D36 — Grouped skills and interests; `level` orders, it does not display

`skills.liquid` renders `name` + `keywords`, which reads better as "Programming: Python,
JavaScript" than as one card per skill, so the transform emits one entry per `group`. The
graph's `level` is not rendered by that template, so it is used to order members within the
group rather than being dropped silently. Same for research interests.

### D37 — The version gate fires before content validation, deliberately

`broken/` (schema_version 99) fails on the version gate and never reaches its cv.yml
violations. That is correct — content cannot be checked against a contract version we do not
know — but it means that fixture cannot exercise the report-everything path through the
transform. `test/test_transform.py` therefore builds a **valid-v1 manifest with broken
content** for that case, and asserts both orderings separately. Found by a test failing for
the right reason; noted because "the fixture covers it" was wrong.

### D38 — An absent `_incoming/` is success, not failure

`bin/transform.py` with no staged export prints what it did not find and exits 0. That keeps
`--check` green in CI from the moment it is wired (now) until a real export exists, without
weakening any check that applies once data is present. The states that _do_ fail: no manifest,
no `schema_version`, an unknown version, files disagreeing with the manifest list or hashes, a
schema violation, an unmapped section, an entry the site would render blank, or a
hand-written file in the way. **Refined by D42**: nothing-staged is only a no-op when no
generated files are committed either.

### D39 — Deferred from this phase, named so it is not mistaken for done

`personal.yml` (Phase 5) and `publication_overrides.yml` (Phase 4) are validated and then
reported as "not consumed yet" on every run, rather than ignored. Also deferred: `cv.address`
(the graph has no location fields — the gem drops scalar `location`, per §1), `cv.label`,
`social_networks` for the PDF, and `_data/icon_map.yml` + the logo assets D22 calls for — the
graph's `icon` short keys are carried through the intermediate format but not yet mapped to
files.

### D40 — An entry with no dates is undated, never "present"

`end_date()` emits `present` only when a `start` exists, and `_sort_key_chronological` has
three ranks — ongoing (start, no end), dated, undated — rather than folding undated in with
ongoing. This mirrors `al_folio_cv`'s own `date_sorting.rb`, whose rule is that a start with
no end is ongoing and no dates at all is undated.

The reason this needed a decision rather than a quiet fix: the earlier behavior emitted
`end_date: present` for a dateless entry and sorted it first, so the CV asserted that an
undated role was the current one. Nothing downstream would have caught it — RenderCV 2.3
validates `end_date: present` with no `start_date`, and the gem's undated-sorts-last rule
never applied because the transform handed it an explicit `"present"` first. **A transform
that invents a value is worse than one that omits it**, because the invented value is
type-correct and therefore invisible to every check that isn't a human reading the page.
This is the concrete case behind the "never invents" line in `bin/transform.py`'s docstring.

Fixture note worth keeping: the dateless entry pinning the _ordering_ has to be an
**experience**, not a project. `map_projects` sorts by `importance`, so a dateless project
sorts last for an unrelated reason and passes the assertion without exercising the date rank
at all. `valid/cv.yml` carries both — a dateless experience for ordering, a dateless project
for key omission.

### D41 — Unmapped profile fields are an error, matching the unmapped-section guard

`profile.schema.json` is deliberately open (`additionalProperties: true`) so a plugin that
learns a new network still validates. That makes the transform the only place the gap can be
caught, exactly as with `cv.yml`'s unmapped sections (the schema is permissive; the transform
is loud). `build_socials` tracks a `consumed` set — `SOCIALS_BUILTIN` ∪ `SOCIALS_CUSTOM` ∪
`CONSUMED_BY_CV` (the identity scalars the CV header reads) — and raises on anything left
over, naming the keys and the three places a mapping can go.

Accounting by name rather than by shape is the point: a key is either listed somewhere or it
is an error, so there is no `{id, url}`-sniffing heuristic to be wrong about. `email_work` is
handled as an alias, not a mapping — jekyll-socials has exactly one `email` key, so the
transform prefers `email_personal` and falls back to `email_work` rather than emitting no
email at all.

### D42 — Header-marked files are evidence an export existed; D38 is refined accordingly

D38 stands — a repository that never staged anything is a clean no-op — but "nothing staged"
must not stay quiet when generated files are still committed. Deleting the export after
`_data/cv.yml` was committed would otherwise leave sourceless generated content served
indefinitely with `--check` green.

The nothing-staged branch therefore scans the prune roots for `_is_ours()` files. None → the
D38 no-op, unchanged. Some → error under `--check`, prune in a real run. No state file is
needed because the evidence is already on disk: the generated header _is_ the record that an
export once existed.

The two modes deliberately disagree here, which is the one place in the transform where
`--check` is not "the real run but asserting." `--check` answers _is this commit
consistent?_ — and a sourceless generated file means no. A real run answers _make it
consistent_ — and the export is gone, so the output should be too. Both are correct; the
asymmetry is called out in a comment at the branch so it does not read as a bug.

---

## Phase 4 — Bibliography, publications page, teaching page

Design settled against the **real** Zotero export (106 entries) rather than a fixture, and
against the owner's stated spec for what the page should contain. Counts below are measured.

### D43 — Authorship decides destination: `author` → publications, `collaborator` → teaching, neither → nowhere

The owner heads an engineering section and keeps the whole section's output in one Zotero
library, including work he neither authored nor supervised. That work must not appear on the
site at all. The library already encodes the distinction, so no manual exclusion list is
needed:

| "Lourenço" appears in | meaning          | destination   | count |
| --------------------- | ---------------- | ------------- | ----- |
| `author`              | his own work     | publications  | 74    |
| `collaborator` only   | he supervised it | teaching page | 19    |
| neither               | section output   | **excluded**  | 13    |

Verified that the excluded 13 are genuinely other people's supervisions — their
`collaborator` lists Nuno Paulino, Pedro Batista, Aurélio Araújo — and not misfiled work of
his. Name matching must normalise the LaTeX cedilla: the export writes `Louren{\c c}o`, so a
plain `"Lourenço"` substring test finds **1 of 74**. That near-miss is why this rule is
implemented over a normalised name and asserted by a test.

### D44 — A paper presentation merges into its paper; a poster never does

Per the owner's WordPress precedent, a paper and the talk that presented it are one entry, not
two. `bib.liquid` supports this directly (SCHEMA-NOTES §6): `note` renders a second line under
the venue, and `slides` renders a button. So a "Paper Presentation" folds into its paper as
`note` + `slides` and is never listed separately.

**A shared title is not evidence of a shared event, and posters are the counter-example.** The
merge rule is therefore _same title **and** same venue **and** same date_ — not title alone.
Checked entry by entry:

| record type           | matches its paper on address + date?               | disposition     |
| --------------------- | -------------------------------------------------- | --------------- |
| Paper Presentation ×7 | **yes, all 7** (Linz Jul 2015, Crete Jun 2013, …)  | merge           |
| Poster ×6             | **no, none** — all `Lisboa, Portugal`, other dates | list separately |

Every poster is a Lisbon event distinct from where the paper appeared: the _Globally
Exponentially Stable Filter_ poster is Lisboa Jul 2015 while its paper is **Linz, Austria**
Jul 2015; the _Earth-Fixed Trajectory_ poster is 2017 against a 2020 journal article. Decisive
case: _New Design Techniques_ has **two** posters, May 2016 and Jul 2016, so they are separate
events even from each other — a title-keyed merge would have silently dropped one of them.

All **6** posters are consequently their own section (D47). This corrects an earlier reading
that merged 5 of them on title alone; the owner caught it, and the venue/date comparison is
now the rule the transform implements and a test asserts.

Two further records legitimately survive as duplicates-by-title: an invited lecture given
twice (IST, 2022-03 and 2025-10) is two events, and a 2024 conference paper later extended
into a 2025 journal submission is two outputs.

### D45 — The generated `.bib` must not carry a `type` field

A BibTeX `type` field shadows the entry type inside `bib.liquid` and silently drops the venue
line — proved in SCHEMA-NOTES §6, and it would hit **20 of 106** entries here, i.e. most of
the teaching page. The transform strips `type` and carries the degree in the fields that
actually render.

This is the same failure class as D14 and D34: the input validates, the build succeeds, and
the page is quietly wrong. It is caught here by an assertion on generated output rather than
by looking at the page.

### D46 — Sections come from a `section` field queried per block, not from `group_by`

`scholar.group_by: year` groups _within_ one `{% bibliography %}` call and cannot produce a
type-ordered page. `{% bibliography --query @*[section=journal] %}` selects on an arbitrary
field and does work (verified by build). The transform assigns each entry exactly one
`section` value; the page is one query block per section. `section` is added to
`filtered_bibtex_keywords` so it does not leak into the "Bib" popup.

### D47 — Page order is the owner's, and an empty section renders nothing

Journal papers · Conference papers · Book chapters · Books · Theses · Preprints — then
Posters · Talks. Measured: 15 · 23 · 2 · **0** · 2 · 4 — then 6 · 12.

Books is specified by the owner and currently empty, and its block is **commented out** in
`_pages/publications.md` so no empty heading renders. To be precise about the mechanism, since
an earlier wording of this entry overstated it: the headings are **hard-coded in the page**,
one `{% bibliography %}` block each. A section whose query matches nothing still renders its
heading. Books is the only one handled, because it is the only one expected to stay empty;
if another section can empty out, its block needs the same treatment.

### D48 — Supervised theses get their own page, sourced from the bib, not the graph

**Supersedes part of D16 and D8.** `seed.md` put teaching inside the CV page and kept
`/teaching/` off-nav; the owner has since asked for a separate teaching page for supervised
theses, so `/teaching/` is now `nav: true` and carries the supervision list. What D16 decided
about `_teachings/` is unchanged: that collection is still only for courses warranting their
own page, and `{% include courses.liquid %}` (which reads `site.teachings`) can return to this
page above the supervision list as soon as any course does. Removing the include now costs
nothing — the collection is empty — but it is the one thing on this page that was not
replaced by something equivalent, so it is named here rather than left to a silent diff.

19 distinct supervisions, 2021–2026. They render from `collaborator` per D43, which raises a
duplication risk worth stating: the Logseq graph _also_ carries
`cv.teaching.supervised_students`, which Phase 3 already renders on the CV. These are two
sources for one fact. The CV keeps the graph as its source (it is a CV section), the teaching
page uses the bib (it needs per-thesis links), and the transform must not invent a third.

Note Zotero stores every supervision as `@phdthesis` regardless of degree — 16 of 19 are
M.Sc. theses — so the degree comes from the `type` field's _value_ before D45 strips the
field, never from the entry type.

### D49 — `papers.src.bib` is owner-staged, so the manifest check must tolerate it

The export integrity check (both directions, D-Phase-2) flags any file in `_incoming/` that
the manifest does not list. `papers.src.bib` comes from Zotero by hand, not from the plugin,
so it would fail that check the moment it is staged.

**Implemented.** `MANIFEST_EXEMPT = {README.md, papers.src.bib}` is what
`_check_export_integrity` skips, and two tests assert it: one stages a plugin export and a
bibliography together, one stages a bibliography alone. The exemption stays narrow, so a
plugin that later _does_ emit the bibliography still round-trips through the integrity check.

This entry was wrong twice, in opposite directions — first describing the exemption as done
before it was, then (corrected in the same PR that implemented it) as pending after it was.
The lesson is the one D39 already encodes: a decision that describes code has to be re-read
when that code lands, not only when it is planned.

### D49b — A bibliography can be staged without re-exporting the graph

`papers.src.bib` comes from Zotero on the owner's cadence; the manifest comes from the plugin
on the graph's cadence. Requiring a manifest to process the bibliography therefore made
"update the publication list" imply "re-export the whole graph", which is not a workflow
anyone would want and blocked filling the two pages that need it.

So: when every staged file is one the plugin never emits (`MANIFEST_EXEMPT`), the manifest is
not required and the transform processes what is there, saying so on stdout. A single
plugin-exported file present alongside brings the full integrity check back. This is narrow on
purpose — the manifest is the only defence against a partial copy of a plugin export, and that
defence is untouched.

### D50 — A link is emitted only when its asset exists

Zotero's `file` field holds local Windows paths
(`..\Papers\My Research\Conference\Branco et al_2021_….pdf`), not URLs, and covers only 47 of
the 74 authored entries. A path like that cannot become a working link, so the transform never
copies one into `pdf`/`slides`/`poster`. Instead it maps a staged asset under `assets/pdf/`
and emits the field only if that file is present — an absent PDF means no button, never a
dead one. Getting the PDFs into the repo is an owner action (see below).

### D51 — Peer-review venues are deferred, pending a source

Not in the Zotero export at all, and the owner's previous site listed them. The intended home
is a new `peer_review` section in the intermediate contract, which needs a companion-plugin
change — so the page waits on the plugin rather than being hand-authored into `_data/` and
becoming a second content source outside Logseq. Recorded here so it is not mistaken for an
oversight. The owner was offered a hand-authored interim file and did not choose it.

### D52 — Judgment calls on ambiguous records, stated rather than silently applied

Adopted as defaults because they change presentation only, and each is reversible from Zotero:

- the 2025 entry whose venue reads "CEAS Space Journal, submitted" is listed with an explicit
  submitted marker rather than hidden — the record is real, its status is stated;
- two untyped `@misc` records duplicating a conference paper (Briz _In-Orbit Assembly_, and
  _Nonlinear MPC for Attitude Guidance_) are treated as preprints and suppressed in favour of
  the paper, matching D44;
- `guerreiroAODCSDevelopmentANTAEUS` is untyped and duplicates nothing, so it cannot be
  classified — the transform **errors** on it rather than guessing a section. This is the
  D43/D46 rule working: an entry with no derivable section is a loud failure, not a silent
  omission.

Data problems only the owner can fix are listed under owner action items.

### D53 — `address` is renamed to `location`; posters and talks carry their venue in `note`

`bib.liquid` never reads `address` or `howpublished` (SCHEMA-NOTES §6), and Zotero writes the
place as `address` on **83 of 106** entries. Renaming it to `location` is therefore not
cosmetic — without it the place disappears site-wide.

For `@misc` (posters, talks, lectures) the transform puts the event and place in **`note`**
instead, because an `@misc` with `location` renders a stray leading comma: the template emits
`{{ entrytype }}, {{ location }}` and `entrytype` is empty for entry types with no venue
branch. `note` renders as its own line and reads correctly. Papers keep `location`, where the
comma is right.

### D54 — The source export switches to **Better BibLaTeX**; the mapping is derived from the real file

The first export was Better BibTeX (legacy). Diagnosed from the field census, not guessed:
`address` 83 / `location` 0, `journal` 15 / `journaltitle` 0, `year` 105 + `month` 87 /
`date` 0, and `eventtitle` 0 / `venue` 0.

The owner reports that the event names **are** recorded in Zotero for posters, presentations
and conference papers. They are absent from the export because **plain BibTeX has no field to
hold them** — there is no `eventtitle` in BibTeX, so BBT discards the meeting/conference name.
BibLaTeX has `eventtitle` and `venue`, and BBT maps the meeting name into `eventtitle`
(upstream BBT issues #643, #644, #1195). So this is a translator limitation, not missing data
and not a transform bug.

BibLaTeX is a net simplification here, which is why it wins over patching:

| datum      | BibTeX (was)                | BibLaTeX       | net effect                    |
| ---------- | --------------------------- | -------------- | ----------------------------- |
| event name | **dropped**                 | `eventtitle`   | the fix                       |
| place      | `address` (renders nothing) | `location`     | **D53's rename becomes moot** |
| journal    | `journal`                   | `journaltitle` | one rename to add             |
| date       | `year` + `month`            | `date`         | must be split back out        |

Rejected alternative: keep BibTeX and add `tex.eventtitle:` lines to each item's Zotero
`Extra` field. BBT does support that (`:` plain-text, `=` raw LaTeX, optionally scoped with a
`bibtex.`/`biblatex.` prefix), and it is the right tool for a one-off field — but not for ~40
items, and it would leave the export permanently lossy for anything else BibTeX cannot carry.

**The mapping is not written until the BibLaTeX file exists.** Entry types change
(presentations become `@unpublished`), and BBT's exact routing of Place vs Event Place is not
something to infer from documentation. This repo has already been bitten three times by
plausible-but-wrong assumptions about a format (D14, D34, D45), and D26/D27 exist precisely to
say: enumerate from the artifact, do not derive from prose.

Two things that de-risk the switch, both worth knowing before it happens:

- **Cite-keys are stable across translators** — BBT pins them per item — so
  `publication_overrides.yml` keys survive. The malformed `::` / `::a` keys still need fixing
  in Zotero regardless.
- **D45 still applies.** BibLaTeX uses `type` for thesis degree (`mathesis`, `phdthesis`), so
  the `type`-shadowing strip remains necessary.

---

## Phase 5 — Personal page and the bookshelf

### D59 — A page joins the nav when it has content, not when its code lands

Publications, teaching and personal all shipped `nav: true` while their generated data was
still absent, so the site served three nav entries leading to empty headings. D8 already said
nav flips per phase; what was missing is that the trigger is **content**, not code.

All three are `nav: false` with a one-line reason in their front matter, and they flip on when
an export is staged. This is the same rule as D3's no-invented-content: an empty page reached
from the nav is a promise the site cannot keep. D48's supersession of D8 for `/teaching/`
stands — the owner asked for the page; it just does not go in the nav while it is empty.

### D55 — The Personal page renders from data inline; no layout override was needed

> **Corrected after checking the plugin.** A later change removed two `sorted()` calls from
> `build_personal` on the stated grounds that "the graph's order is the author's editorial
> order". That is **half true**, and the half that is false was asserted about a counterparty
> without reading it — the same error D64 names.
>
> The plugin has _two_ orderings, not one (`sortExport`, plugin `index.js:598-618`):
>
> | what               | plugin                                     | consequence here                                     |
> | ------------------ | ------------------------------------------ | ---------------------------------------------------- |
> | page keys          | `sortKeys()` — **alphabetised**            | authored order never arrives; not sorting is a no-op |
> | sections in a page | **authored order preserved**, deliberately | not sorting is load-bearing                          |
>
> So removing the _section_ sort was a real fix; removing the _page_ sort was a no-op wearing a
> rationale. Both are kept — the page one because it is the correct no-op, staying right if the
> plugin ever stops sorting — but the comment now says which is which.
>
> The fixture was also unrepresentative: its pages were in an order `sortKeys` cannot produce.
> Page keys are now alphabetical, sections keep authored order (`diy` is tools-then-projects),
> and a test pins the half that matters.

D18 predicted this and it held: `_pages/personal.md` loops over `site.data.personal` with
`layout: page`, because `page.liquid` renders `{{ content }}` verbatim and Jekyll runs Liquid
inside page content. A local `_layouts/personal.liquid` stays permitted (D5) and unused.

The transform deliberately does **not** enumerate the properties of a Personal entry. The
contract is open on purpose — this page is the site's distinguishing feature and its content
is not a fixed schema — so properties are carried through and the page renders whatever is
there. The only transformation is structural: `sections` becomes an ordered list, with the
`_root` pseudo-section first, so rendering does not depend on mapping order surviving a YAML
round-trip.

### D56 — Reading is not rendered twice

`personal.yml`'s `reading` page becomes `_books/*.md` and nothing else; the Personal page
links to `/books/` rather than repeating the list. Same rule as D48: one fact, one source.

### D57 — Front matter must open on line 1, so the ownership marker moves inside it

Generated files carry `GENERATED_HEADER` on their first line, and `_is_ours()` reads that line
to decide what the transform owns. That breaks for a Markdown file: Jekyll only parses front
matter when `---` is the very first thing in the file, so a marker above it silently costs the
page its layout — the `_books/` pages rendered unstyled until this was caught by building the
site.

Resolution: for front-matter files the marker is a **YAML comment on line 2**, inside the
block, and `_is_ours()` scans the first three lines instead of only the first. Ownership,
pruning and `--check` behave identically; only the marker's position moved.

### D58 — Book dates are padded to a full date, and status is a closed set

`book-shelf.liquid` groups on `item.started | date: '%Y'`. Liquid's `date` filter cannot parse
a partial date and returns its input unchanged, so a `2026-07` start rendered the year
_heading_ as "2026-07". Date-like book fields are padded (`2026` → `2026-01-01`,
`2026-07` → `2026-07-01`).

The shelf also colours the caption from a closed set — `abandoned, finished, interested,
paused, queued, reading, reread` — and renders anything else as `UNCATEGORIZED` with no
warning. So an unrecognised `status` is a transform error, and a missing one is inferred from
the section header (`currently_reading` → `reading`).

Both were found by rendering the page, not by reading the template. That is now the third
Phase where a build caught something a read did not (D14, D45, and this).

---

## Phase 7 — CI and deploy wiring

### D60 — Deploy is gated on the transform check, because independent workflows race

`transform-check.yml` and `deploy.yml` both triggered on push and ran concurrently. A push
carrying stale generated output would therefore turn the check red **while deploy published
the stale site beside it** — the check was reporting a problem it had no power to prevent.

`transform-check.yml` now exposes `workflow_call:` and `deploy.yml` runs it as a `verify` job
that `deploy` `needs:`. The called workflow keeps its own `permissions: contents: read`, so the
gate stays read-only even though the caller holds `contents: write`.

`deploy.yml` also carries a `concurrency` group, for the same reason at a different layer.
Two pushes in quick succession ran two deploys, and the publish step is last-writer-wins by
_finish_ time — so a slower earlier run could overwrite a faster later one and leave the site
on the older commit. Grouping by ref serialises them; `cancel-in-progress: false` lets an
in-flight publish complete rather than being torn down half-written, and GitHub keeps only the
newest run queued behind it, so the newest commit still wins.

Both halves of D60 are the same failure: CI that observes a problem it cannot prevent.

The plan's stated ordering was `--check` → `rendercv render` → build → deploy. Only the
`--check` half is implemented, deliberately: `render-cv.yml` **commits** the rendered PDF to
the default branch, so calling it from deploy would make publishing a writing operation and
widen exactly the carve-out D4 keeps narrow. The two stay independent and the rendercv half of
the ordering claim is dropped rather than left as an unmet aspiration.

### D61 — The plan's Phase 7 path-filter finding was overstated; the real gap was elsewhere

The `[amended]` note on Phase 7 says a transform-only change "can silently fail to redeploy"
because `_incoming/**` and `bin/transform.py` are missing from `deploy.yml`'s `paths:`. Checked
pattern by pattern, that is mostly wrong: `**.yml`, `**.bib` and `**/*.md` already match
`_incoming/cv.yml`, `_incoming/papers.src.bib`, `_incoming/blog/*.md`, and every generated
file (`_data/*.yml`, `_bibliography/papers.bib`, `_books/*.md`, `_pages/*.md`). Under D4 the
site is built from committed output, and that output was always matched.

Genuinely unmatched were `_incoming/manifest.json` (`.json`) and `bin/*.py`. Both are now
listed — cheap, and it means a transform change rebuilds even before its output is
regenerated.

**The real gap was in the other workflow.** `transform-check.yml` watched `bin/transform.py`
by name, so Phase 4's new `bin/bibliography.py` was outside its `paths:` — a change to the
entire bibliography pipeline would not have run the checks that cover it. Widened to `bin/**`,
which is also immune to the next module being added.

Recorded because the correction matters more than the fix: the plan named a plausible failure
that was already handled, and the actual hole was one this repo's own later work created.

---

## Phase 6 — Blog and per-item collection pages

### D62 — A per-item page is generated only when the graph asks for one, via `page: true`

D23 and D16 both say `_projects/*.md` and `_teachings/*.md` are generated "only when a
per-item page is wanted" — and neither says how _wanted_ is signalled. The intermediate
contract has no such field, so the choice was between inventing a heuristic (has a
description? has a url? importance above some threshold?) and requiring an explicit marker.

An explicit marker wins, for the same reason D40 gives: a heuristic would generate pages
nobody asked for and they would look deliberate. `page: true` on a project or course entry is
the signal; `cv.schema.json` leaves these objects open, so it validates under contract v1
without a schema bump. No entry carries it today, so nothing is generated — the mechanism is
in place and inert, which is the correct state until the graph opts something in.

### D62b — Every generator that derives a filename from a title shares one collision check

The same bug was written twice: a slug collision silently overwriting a page, found in
`build_books` during the Phase 5 review, fixed there, and then reintroduced weeks later in
`build_collection_pages` — new code, same mistake. The fix was correct and local, which is
exactly why it did not transfer.

`add_page()` is now the only way a generated page enters an output dict, and it holds the
check. The point is not the check itself but its placement: a fix that lives at the one call
site it was written for is a fix the next call site will not get.

### D62c — `teaching`'s subkeys get the same loud guard as every other mapping level

`cv.yml`'s top-level sections raise on an unmapped key (D-Phase-3) and so do `profile.yml`'s
fields (D41), but `teaching`'s subkeys did not. A `teaching.courses` list therefore validated
against the open schema, rendered in no CV section, generated no page without a marker, and
reported nothing at all — the exact silent-loss shape those other two guards exist to prevent.

Both halves are fixed: unknown subkeys are now an error naming what is known, and `courses`
is mapped to a **Courses** CV section rather than left to vanish. That closes the gap D16 left
open — the CV is the canonical teaching listing, so courses had to reach it, with
`_teachings/*.md` still only for entries wanting their own page (D62).

### D63 — Post bodies are passed through; only front matter is normalised

The body of a blog post is the author's markdown and is copied verbatim. The transform sets
`layout: post` (D-note below), defaults `date` from the filename, and otherwise leaves front
matter alone, passing through keys `post.liquid` does not know rather than dropping them — the
layout ignores what it does not recognise, and dropping would lose what the author wrote.

**`layout: post` is a default, not an override** — set with `setdefault`, since a post that
declares `layout: distill` means it. It has to be set at all because `_config.yml` sets no `defaults:` mapping for `_posts`
(only the `news` collection has a layout default), so a post without an explicit layout
renders its raw body with no page furniture at all. Verified by building: the generated post
appears on `/blog/`, and its page renders with the full layout.

Two things are hard errors rather than best-effort:

- **A filename Jekyll would not recognise as a post.** `YYYY-MM-DD-slug.md` is what makes
  Jekyll date and publish the file; anything else is not a post and would silently never
  appear. That is the same invisible-failure class as D14 and D45.
- **An image reference with no file in this repo** (D22). Blog images are added by hand to
  `assets/img/posts/`, so a reference the repo cannot satisfy fails the transform instead of
  rendering a broken image. External URLs and `data:` URIs are left alone.

---

## Contract lifecycle — decided with the plugin

### D64 — The plugin prunes `_incoming/` by the _previous_ manifest, and writes its own last

> **Status: ✅ implemented upstream** at plugin `a6f769f` (landed in PR 2.5, `d0a928b`).
> Verified directly rather than taken on report: `sync.sh` has a `PRUNE` branch that removes
> files only, tolerates an already-absent entry and leaves empty directories alone, and
> `cp manifest.json` runs **after** the copy/prune loop — the ordering rule as agreed.
>
> This entry previously carried a not-yet-implemented warning, and that warning outlived its
> subject by two merges because the status was verified once and never re-checked. Which is
> D21's failure, not D49's: the convention catches _not yet true_, and nothing catches _no
> longer true_. Both directions need a re-read when the counterparty ships.

An export that drops a blog post leaves the old file in `_incoming/`, unlisted by the new
manifest, which `_check_export_integrity` treats as a hard error. Something has to remove it,
and the obvious answer is wrong: **`_incoming/` is not exclusively the plugin's.**
`papers.src.bib` is staged from Zotero by hand on a different cadence (D49/D49b) and
`README.md` is ours, so "clear the directory before writing" would delete hand-maintained
input on every sync.

The plugin therefore reads the existing `_incoming/manifest.json` before overwriting anything,
deletes exactly the paths in its `files` list, then writes the new export. It never touches a
file it did not previously write. Widening `MANIFEST_EXEMPT` was rejected for the reason its
own comment gives — it is the check standing between a partial copy and a half-built site.

Three properties make it safe, and the ordering one is load-bearing:

1. **The manifest is written last.** It is the commit point. Written first, a crashed export
   leaves a manifest naming files that do not exist _and_ destroys the only record of what the
   previous export owned, stranding the stale files permanently. Files first, prune, manifest
   last means a crash leaves the previous manifest intact and a re-run is still correct.
2. **An unreadable previous manifest prunes nothing**, and says so — unparseable, missing
   `files`, or an unknown `schema_version` are all treated as "no previous export". Pruning by
   a list you do not understand is worse than not pruning.
3. **Only listed file paths are removed**, never directories, and an already-absent entry is
   not an error. Leftover empty directories are harmless: the integrity check filters on
   `is_file()`.

The one case this gets wrong is a hand-placed file that a past export also listed. Checked
against history before adopting: `_incoming/README.md` is the only file ever committed there
and `papers.src.bib` has never been staged, so the case is currently vacuous.

**Known better shape, deliberately not taken yet.** Exporting into a plugin-owned subdirectory
(`_incoming/graph/`) would make ownership positional rather than an allowlist, and would make
that failure case structurally impossible instead of merely unlikely — the D62b lesson again.
It costs a contract v2 and a transform change, and D64 is correct without it. The trigger to
revisit is hand-staging in `_incoming/` growing beyond those two files.

**Fixed here while deciding this:** `MANIFEST_EXEMPT` was matched against `p.name`, so a
`README.md` _anywhere_ in the tree — `blog/README.md` — was silently exempt from the integrity
check. It is now matched on the exact relative path, with a test. D64's safety argument leans
on that set being exactly what it claims to be.

### D65 — An all-dropped document serialises to `{}`, not to zero bytes

When every key of a mapping is dropped, the plugin writes `{}` rather than an empty file.
Scoped to a **whole document only** — a nested `key:` with a null value is untouched, because
D28 makes explicit-null and absent equivalent here and changing that would be a semantic
change rather than a spelling one.

The rationale is narrower than it first looked, and worth recording accurately because the
obvious argument is wrong. `bin/transform.py` does `yaml.safe_load(text) or {}`, so an empty
file _already_ becomes `{}`, and none of the four content schemas set `required` or
`minProperties`, so `{}` validates cleanly. **The two spellings are indistinguishable to this
consumer.** The "an empty file fails loudly" reasoning that first motivated this was simply
untrue.

Nor is the truncation argument as strong as it sounds: a zero-byte file has a well-defined
sha256, so if the manifest lists that file's hash, truncation is caught already. That gap only
opens when `hashes` is absent — which the schema permits, since only `schema_version`,
`exported_at` and `files` are required.

What remains, and what actually decides it: **`or {}` is this consumer's defence, not the
format's guarantee.** The intermediate YAML is a versioned API, and `bin/transform.py`
happening to be tolerant is not a property the format should lean on. `{}` is self-describing
under any consumer, and costs nothing.

No transform change: both spellings were already handled, which is why this is recorded as a
contract fact rather than a code change.

**✅ Implemented upstream** at plugin `a6f769f` — `index.js:53` and `:82` emit `{}`, correctly
scoped to the root document (`indent === 0`), leaving nested nulls untouched as agreed.

---

## Open proposal — pipeline scope

### D66 — Narrowing the pipeline to entity data: assessed, **not yet decided**

> **Status: this is an assessment of an open proposal, not a decision.** Nothing here binds
> anything, and no code has been removed. Recorded so the reasoning is not re-derived, and
> marked because writing a proposal up as settled is the failure mode D64 names. Tracked as
> [#10](https://github.com/pdlourenco/pdlourenco.github.io/issues/10) with companion
> `pdlourenco/logseq-alfolio-export#8`.

The proposal: narrow the Logseq pipeline to **entity data** (CV, profile, publication
overrides) and author **narrative content** — blog, project write-ups, the Personal page,
books — directly as markdown in this repo. "The site is a projection of the graph" becomes
"the CV is a projection of the graph".

**The assessment is favourable, and the strongest evidence is in the code it would delete:**

- **D55 is the schema admitting defeat.** `build_personal` deliberately does not enumerate
  properties, because "the contract is open on purpose — this page's content is not a fixed
  schema". A schema whose defining property is that it declines to constrain anything is what
  modelling non-entity data looks like.
- **The blog pipeline was already split.** D22 puts images in this repo while prose came from
  the graph, and `_check_asset_refs` exists only to catch the mismatch that split creates.
- **`build_posts` barely earns its keep.** Of its four jobs — copy the body, inject `layout`,
  default `date` from the filename, validate filename and image refs — three are needed _only
  because_ the file took a trip through the graph.

**The problem the proposal does not address, and the rule that fixes it.** D23 generates
project detail pages from the same intermediate entries that feed the CV's Projects section.
Hand-authoring the detail page while the CV entry stays generated gives one project two
sources — the duplication D23 and D48 exist to prevent. Proposed rule, should the narrowing be
adopted:

> **The graph owns the record; the repo owns the write-up.** A project's CV entry stays
> generated (name, dates, institution, importance) and carries a `url` pointing at its
> hand-authored page. Different content, one source each.

Rejecting the alternative — projects leaving the graph entirely — because it costs the CV a
Projects section, which is real CV content.

**On `personal.yml`:** it would be _absorbed_, not deleted. Its link properties (`lastfm`,
`wikiloc`, `strava`, `goodreads`) are identity data that already has a home in `profile.yml` →
`_data/socials.yml`, and `build_socials` already handles that `{id, url}` shape. The prose
becomes `_pages/personal.md`.

**One of the proposal's open questions is already closed:** D17 settled native `_books/` over
Goodreads, with the mechanics verified against the gem. Narrowing changes where entries come
from, not the mechanism.

**Cost if adopted:** four functions from `bin/transform.py` (~300 lines) and ~25 checks, and
D55–D58, D62, D63 and half of D65 become historical. Sunk cost should not weigh — the code was
cheap and the gem findings are banked in `SCHEMA-NOTES.md` either way. The documentation cost
is the real one: those entries need marking as superseded, or this becomes a third instance of
the staleness problem (D21, D64).

**Not contingent on the outcome, and already landed:** `_config.yml` had no `defaults:` for
`_posts`, so a hand-authored post with no explicit `layout:` rendered its raw body with no page
furniture, silently — the D14/D45 failure class. A `defaults:` entry now supplies
`layout: post`, verified by building a post that declares none. Front matter still wins, so a
`layout: distill` post is unaffected, and generated posts (D63) are unchanged.

---

## Owner action items (nothing in a commit can do these)

GitHub Pages **cannot** build this site itself: it is gem-based (`theme: al_folio_core` plus
~20 `al_*` gems, none on the Pages allowlist). `deploy.yml` builds the site in Actions and
publishes `_site` to a `gh-pages` branch. That means the repository settings must change by
hand — see `docs/al-folio/INSTALL.md` §Deployment:

1. **Actions → enable** workflows for this repository.
2. **Settings → Actions → General → Workflow permissions → Read and write permissions**
   (`deploy.yml` and `render-cv.yml` both declare `contents: write`).
3. Let **Deploy site** run once on `master`; it creates the `gh-pages` branch. Do not commit
   to that branch by hand.
4. **Settings → Pages → Source: deploy from branch → `gh-pages`** (not `master`).
5. Content the site cannot invent: a profile photo (drop it in `assets/img/` and name it in
   `_pages/about.md`), the About bio, and `email:` in `_data/socials.yml`. All three are
   deliberately left blank rather than guessed.
6. ✅ ~~**Do not run the plugin's `sync.sh` against this repository yet.**~~ **Resolved** — see
   D21. `sync.sh` at plugin HEAD `f9b781c` copies into `_incoming/` only and refuses to run
   without an explicit `--site`, so it is safe to use. It does not yet prune stale files or
   write its manifest last (D64), so a deletion in the graph still needs the leftover file
   removed by hand until that lands. Original text follows for the record: as written it copied
   the Logseq export straight into `_data/` and `_posts/`, which overwrites generated files and
   would leave the CV page rendering intermediate-format YAML it cannot read — see **D21**. Copy
   the export directory to `_incoming/` by hand until the plugin repo is updated.

Until step 4 happens, `pdlourenco.github.io` keeps serving whatever it serves today; merging
Phase 0 does not publish anything.

### Added by Phase 4 — things in the Zotero library only the owner can fix

7. ⚠️ **Two cite-keys are `::` and `::a`.** Both are 2026 M.Sc. theses he supervises (Maria
   Fernandes, _System Architecture and Guidance & Control Design…_; Catarina Gomes, _Modelling
   and Control of Modular and Flexible Large Space Structures_), so both land on the teaching
   page. Cite-keys are the primary key `publication_overrides.yml` references and appear in
   page anchors, so they must be fixed **in Zotero** — a generated substitute would change on
   the next export and silently break any override pointing at it. The transform rejects them
   with a message naming both entries.
8. **One supervision is dated 2028** (Cachim, _Verification & Validation of Guidance and
   Control…_) and **one authored entry has no year** (_Earth-Fixed Trajectory and Map Online
   Estimation_). Probably a typo and an omission; both are reported, neither is guessed at.
9. **`guerreiroAODCSDevelopmentANTAEUS` cannot be classified** — an untyped `@misc` that
   duplicates nothing (D52). Give it a Zotero item type or a `type` value and it files itself.
10. **PDFs are not in the export.** Zotero's `file` field holds local Windows paths, so the
    paper/slides/poster buttons the previous site had need the actual files copied to
    `assets/pdf/` (D50). Naming is matched on the Zotero filename, so copying them across
    unchanged is enough. Until then those entries simply show no button.
    11b. **The first real staging will refuse to write `_bibliography/papers.bib`, and that is
    correct.** That file is still the Phase 0 placeholder, which has no generated header, so
    the transform refuses to overwrite it rather than clobbering what might be hand-written
    content. Delete the placeholder (or move it aside) once and the transform owns the file
    from then on. Noted so it does not read as a bug on first run.

11. **Peer-review venues have no source yet** (D51) — they need either the companion plugin to
    emit a `peer_review` section, or a decision to hand-author the list in this repo.
12. ⚠️ **Re-export the library as Better BibLaTeX**, not Better BibTeX — see **D54**. The event
    names for posters, presentations and conference papers are already recorded in Zotero;
    legacy BibTeX simply has no field that can carry them, so BBT drops them on export.
    This is the one **blocking** item for the publications page. Without event names the 6
    posters render as "Poster · Lisboa, Portugal · Jul 2015", and the two _New Design
    Techniques_ posters (May 2016, Jul 2016) are indistinguishable from each other.
    Two things worth confirming while re-exporting, because BBT routes them to different
    BibLaTeX fields: whether the conference papers' event name is distinct from the proceedings
    title already in `booktitle` (26 entries have one), and whether the posters' place is
    recorded as Zotero's **Event Place** rather than plain Place.

---

## Inputs recorded for Phase 1 — consumed

Measurements taken while bootstrapping. Phase 1 has now used them: the first bullet fed D13 and
the Phase 3 gate, the third fed D13/D14. Kept for provenance; the fuller picture is in
[`docs/SCHEMA-NOTES.md`](SCHEMA-NOTES.md).

- **Stock `_data/cv.yml` validates under RenderCV 2.3.** `rendercv render` reports
  "Validating the input file has finished" with no schema errors, despite the file mixing
  RenderCV and JSONResume vocabulary (`label`, `image`, an `address:` mapping, `studyType`,
  `score`, `courses`). Per the plan's amended Phase 3 gate, this resolves to branch (a): the
  generated CV **is** expected to pass `rendercv render`.
- **PDF rendering is not verifiable in this container.** Typst fetches font packages from
  `packages.typst.org`, which the agent proxy blocks. Validation is testable locally; the PDF
  step is first exercised in CI.
- The site's CV page is rendered by the `al_folio_cv` gem's own Liquid from `_data/cv.yml`.
  `rendercv` is only the optional PDF path — a RenderCV schema failure does not by itself
  break the site.
