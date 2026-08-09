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

Until step 4 happens, `pdlourenco.github.io` keeps serving whatever it serves today; merging
Phase 0 does not publish anything.

---

## Inputs recorded for Phase 1

Not decisions — measurements taken while bootstrapping, so Phase 1 does not repeat them:

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
