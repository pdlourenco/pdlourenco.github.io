---
layout: page
permalink: /publications/
title: publications
description: Journal and conference papers, book chapters, theses and preprints, followed by posters and talks. Generated from a Zotero library by bin/transform.py.
nav: false # on when an export is staged: Phase 4's export fills _bibliography/papers.bib (D8/D59)
nav_order: 2
---

<!-- GENERATED SECTION ORDER — see docs/DECISIONS.md D46/D47.
     One {% bibliography %} block per section, each selecting on the `section` field the
     transform assigns. jekyll-scholar's `group_by: year` groups *within* a block and
     cannot produce these headings, which is why the page is written this way.
     A section with no entries renders its heading and nothing else, so the transform
     simply never emits a section that would be empty (Books, today). -->

{% include bib_search.liquid %}

<div class="publications">

<h2 class="bibliography-section">Journal papers</h2>

{% bibliography --query @*[section=journal] %}

<h2 class="bibliography-section">Conference papers</h2>

{% bibliography --query @*[section=conference] %}

<h2 class="bibliography-section">Book chapters</h2>

{% bibliography --query @*[section=chapter] %}

<!-- Books: the owner keeps this category, but there are none yet, so no heading is
     rendered. Add the block back when the first book exists (D47). -->

<h2 class="bibliography-section">Theses</h2>

{% bibliography --query @*[section=thesis] %}

<h2 class="bibliography-section">Preprints</h2>

{% bibliography --query @*[section=preprint] %}

<h2 class="bibliography-section">Posters</h2>

{% bibliography --query @*[section=poster] %}

<h2 class="bibliography-section">Talks and invited lectures</h2>

{% bibliography --query @*[section=talk] %}

</div>
