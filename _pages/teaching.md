---
layout: page
permalink: /teaching/
title: teaching
description: Theses supervised or co-supervised, newest first. Generated from a Zotero library by bin/transform.py.
nav: true
nav_order: 3
---

<!-- Supervisions render through the same bibliography machinery as publications, so they
     get the same links and formatting for free — they are simply the entries the transform
     tagged `section: supervision` (docs/DECISIONS.md D43/D48). The CV page's own supervision
     list comes from the Logseq graph instead; see D48 on why the two sources are kept apart. -->

<div class="publications">

{% bibliography --query @*[section=supervision] %}

</div>
