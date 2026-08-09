# Schema notes — what this al-folio actually expects

Ground truth for the data formats this site consumes, read out of the **installed gems**, not
from upstream prose. Written for Phase 3 onward so no session re-derives it.

Verified against the pins in `Gemfile.lock`: `al_folio_core 1.0.15`, `al_folio_cv 1.0.2`,
`jekyll-socials 0.0.7`, `jekyll 4.4.1`, RenderCV `2.3` (`requirements.txt`). **Re-verify after
any gem bump** — everything below is version-specific, and all of it fails silently.

---

## 1. The CV page

`_pages/cv.md` sets `cv_format: rendercv`, `layout: cv`. The chain is:

```
_pages/cv.md → al_folio_core _layouts/cv.liquid → {% al_folio_cv_render %}
             → al_folio_cv templates/cv/render.liquid → templates/cv/<section>.liquid
```

The site CV is rendered entirely by **`al_folio_cv`'s own Liquid**. `rendercv` (the Python
tool) is only the optional PDF path — a RenderCV schema error does not by itself break the
page, and conversely a file RenderCV validates can still render blank here. Both contracts
must be satisfied, and they are not identical.

### Data location

`render.liquid` reads **`site.data.cv.cv`** — i.e. `_data/cv.yml` must have a top-level `cv:`
key, everything nested beneath it. With `cv_format: rendercv` set explicitly, `resume.json`
is ignored entirely (no fallback).

### Header / contact block

| Key                                                       | Rendered as                                |
| --------------------------------------------------------- | ------------------------------------------ |
| `cv.name`                                                 | Name                                       |
| `cv.label`                                                | Professional Title                         |
| `cv.email`                                                | Email                                      |
| `cv.phone`                                                | Phone                                      |
| `cv.website`                                              | Website (linked)                           |
| `cv.address.street` / `.city` / `.region` / `.postalCode` | Location, joined with commas               |
| `cv.summary`                                              | "Professional Summary" card, markdownified |

> ⚠️ **`cv.location` is a trap.** The card's visibility guard tests
> `cv.name or cv.label or cv.location or cv.email or cv.phone or cv.website`, but the table
> only ever renders `cv.address.*`. So RenderCV's canonical scalar `location:` field **makes
> the card appear and then displays nothing** — a location set that way is silently dropped.
> Use the `address:` mapping for the site. (RenderCV 2.3 accepts both.)

### Section dispatch

`cv.sections` is a **mapping**, not a list: each key is the section heading shown on the page
(rendered verbatim, `slugify`'d for its anchor). Order of appearance follows the mapping order,
except Experience, which is hoisted to the top.

| Section title (exact match)          | Template used                            |
| ------------------------------------ | ---------------------------------------- |
| `Experience` + `Volunteer`           | merged, date-sorted, `experience.liquid` |
| `Education`                          | date-sorted, `education.liquid`          |
| `Awards` or `Honors and Awards`      | `awards.liquid`                          |
| `Publications`                       | `publications.liquid`                    |
| `Skills`                             | `skills.liquid`                          |
| `Languages`                          | `languages.liquid`                       |
| `Interests` or `Academic Interests`  | `interests.liquid`                       |
| `Certificates`                       | `certificates.liquid`                    |
| `Projects` or `Open Source Projects` | `projects.liquid`                        |
| `References`                         | `references.liquid`                      |
| **anything else**                    | **generic fallback — see below**         |

> ⚠️ **The generic fallback renders only two entry shapes.** For a section title that is not
> in the table above, `render.liquid` emits a list item for `entry.bullet`, or
> `<strong>{{ entry.label }}:</strong> {{ entry.details }}` for `entry.label` — and **nothing
> at all for any other keys**. An entry with `name` + `start_date` + `highlights` in a custom
> section produces an empty card: heading, no content, no warning.
>
> In RenderCV vocabulary the fallback supports **`BulletEntry`** (`bullet`) and
> **`OneLineEntry`** (`label` + `details`) only. `seed.md`'s guess that custom sections should
> use `NormalEntry` is wrong for the site rendering. This is the single most important
> constraint on the Phase 3 mapping — see `docs/DECISIONS.md` D14.
>
> Consequence for `seed.md`'s target CV: "Research Interests" is **not** a special-cased title
> (`Interests` and `Academic Interests` are), and neither is "Supervised Students" or "Jury".

### Keys each section template consumes

RenderCV and JSONResume names are both accepted; the RenderCV name is listed first where they
differ. Anything not listed is ignored silently.

| Template       | Keys                                                                                               |
| -------------- | -------------------------------------------------------------------------------------------------- |
| `experience`   | `company` / `organization` / `name`, `position`, `location`, `summary`, `highlights`, `url`, dates |
| `education`    | `institution`, `area`, `degree` / `studyType`, `location`, `courses`, `highlights`, `url`, dates   |
| `projects`     | `name`, `summary`, `highlights`, `url`, dates                                                      |
| `skills`       | `name`, `keywords`, `level`, `icon`                                                                |
| `languages`    | `language` / `name`, `fluency`, `summary`, `icon`                                                  |
| `interests`    | `name`, `keywords`, `icon`                                                                         |
| `awards`       | `title`, `awarder`, `date`, `summary`, `url`                                                       |
| `certificates` | `name`, `issuer`, `date`, `url`, `icon`                                                            |
| `publications` | `title` / `name`, `publisher`, `date` / `releaseDate`, `summary`, `url`                            |
| `references`   | `name`, `reference`, `icon`                                                                        |

Note `education` reads **both** `degree` (RenderCV) and `studyType` (JSONResume), which is why
upstream's JSONResume-flavoured stock file still renders.

### Dates and sorting

`al_cv_sort_by_date` (`al_folio_cv/date_sorting.rb`) is applied by the gem to **Experience +
Volunteer** and **Education** only. Everything else — Projects, Awards, custom sections —
renders in **array order**.

- Date keys read: `start_date`/`startDate`, `end_date`/`endDate`, and `date`/`releaseDate` for
  point-in-time entries.
- Accepted formats: `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, plus `/` and `.` separators, plus a
  last-resort bare-year match inside free text ("Fall 2019" → 2019).
- **Ongoing values** (case-insensitive): `present`, `current`, `ongoing`, `now` → sorted first.
- A `start_date` with **no** `end_date` is also treated as ongoing (and rendered "2020 -
  Present"); a bare `date` is a point in time and never ongoing.
- Undated entries sort last. Ties break on original array position, so the sort is stable.
- Partial dates are padded to the period edge: a year-only `end_date` sorts _after_ a
  mid-year one.

Because the PDF path (`rendercv render`) renders in array order and the gem re-sorts only two
sections, **the transform must emit every section already sorted** — see D15.

---

## 2. `_data/socials.yml` (`jekyll-socials 0.0.7`)

Order in the file is display order. Every key the gem knows:

`acm_id`, `arxiv_id`, `blogger_url`, `bluesky_url`, `cv_pdf`, `dblp_url`, `discord_id`,
`email`, `facebook_id`, `flickr_id`, `github_username`, `gitlab_username`, `hal_id`,
`ieee_id`, `inspirehep_id`, `instagram_id`, `kaggle_id`, `keybase_username`, `lastfm_id`,
`lattes_id`, `leetcode_id`, `letterboxd_id`, `linkedin_username`, `mastodon_username`,
`medium_username`, `orcid_id`, `osf_id`, `pinterest_id`, `publons_id`, `quora_username`,
`rss_icon`, `scholar_userid`, `scopus_id`, `semanticscholar_id`, `spotify_id`,
`stackoverflow_id`, `strava_userid`, `telegram_username`, `unsplash_id`, `wechat_username`,
`whatsapp_number`, `wikidata_id`, `wikipedia_id`, `work_url`, `x_username`, `youtube_id`,
`zotero_username`.

Unknown keys are dropped with no warning — the first of upstream's three silent failure modes.

Relevant to this site: `strava_userid`, `spotify_id` and `lastfm_id` exist and are useful for
the Personal page. **There is no `goodreads` and no `wikiloc` key** — both need
`custom_social` (`logo` + `title` + `url`) or plain links in page content.

---

## 3. Collections

`_config.yml` defines exactly four, all with `output: true`: **`books`**, **`news`**
(defaults to `layout: post`), **`projects`**, **`teachings`**. There is no `talks` or
`students` collection — anything like that is either a CV section or a new collection we add.

`_teachings/` entries drive `{% include courses.liquid %}`: grouped by `year` descending, then
sorted by `term`, showing `title`, `term`, `instructor`, `description`. Per-course pages use
`layout: course`, which additionally renders `instructor`, `term`, `location`, `time`,
`schedule` (a table) plus the page body.

`_books/` has `layout: book-review` for entries and `layout: book-shelf` for the index page.

---

## 4. Layouts and includes are gem-owned

`al_folio_core 1.0.15` ships `_layouts/`: `about`, `archive`, `bib`, `book-review`,
`book-shelf`, `course`, `cv`, `default`, `distill`, `none`, `page`, `post`, `profiles`.

`_includes/`: `audio`, `bib_search`, `calendar`, `citation`, `course_schedule`, `courses`,
`disqus`, `figure`, `footer`, `giscus`, `head`, `header`, `latest_posts`, `metadata`, `news`,
`newsletter`, `pagination`, `related_posts`, `projects`, `projects_horizontal`,
`selected_papers`, `scripts`, `video`, plus `plugins/` and `repository/` subdirectories.

**`page.liquid` renders `{{ content }}` verbatim**, and Jekyll processes Liquid inside page
content. A `_data`-driven page therefore needs **no local layout override**: `_pages/*.md`
with `layout: page` can loop over `site.data.*` inline. This closes `seed.md` known-unknown
\#5 — see D18.

---

## 5. `_data/coauthors.yml`

Consumed by `al_folio_core _layouts/bib.liquid`. Matching is:

Excerpt from `bib.liquid`, fenced as `text` on purpose — it is truncated mid-block, and a
Liquid formatter would "complete" it with closing tags the real source does not have here:

```text
{%- assign clean_last_name = author_last_name | downcase | remove_accents -%}
{% if site.data.coauthors[clean_last_name] %}
  {%- for coauthor in site.data.coauthors[clean_last_name] -%}
    {% if coauthor.firstname contains author.first %}
```

So the key is the **lowercased, accent-stripped last name**, and the value is a **list**, each
item `{firstname: [...variants...], url: ...}`:

```yaml
"bach":
  - firstname: ["Johann Sebastian", "J. S."]
    url: https://en.wikipedia.org/wiki/Johann_Sebastian_Bach
  - firstname: ["Carl Philipp Emanuel", "C. P. E."]
    url: https://en.wikipedia.org/wiki/Carl_Philipp_Emanuel_Bach
```

The list-plus-`firstname`-variants shape is exactly how surname collisions are resolved, which
answers the concern raised in the PR #1 review: the schema handles it, provided the generator
emits **every initial form** that appears in the `.bib` (`"Pedro"`, `"P."`, `"P. T. V."`, …).
`contains` is a substring test on a string and membership on a list, so listing variants
explicitly is the safe form.

Own-name entries are italicised rather than linked, driven by `_config.yml`'s
`scholar.last_name` / `scholar.first_name` lists — currently `[Lourenço, Lourenco]` and
`[Pedro, P.]`.

---

## 6. Responsive images

`imagemagick.enabled: true` scans `input_directories: [assets/img/]` for
`.jpg/.jpeg/.png/.tiff/.gif` and generates widths `480`, `800`, `1400`. It needs the
ImageMagick `convert` binary on `PATH` (the deploy workflow installs it; local builds without
it just skip generation with a warning). Anything referenced through al-folio's figure/lightbox
helpers should therefore live under `assets/img/`.
