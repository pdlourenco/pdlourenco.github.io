---
layout: page
permalink: /personal/
title: personal
description: Music, cycling and hiking, and things built by hand.
nav: true
nav_order: 4
---

<!-- Rendered inline from `_data/personal.yml`, which bin/transform.py generates from the
     graph's Personal/* pages. No local layout override: `page.liquid` renders {{ content }}
     verbatim and Jekyll runs Liquid inside page content, so a loop here is enough
     (docs/DECISIONS.md D18). Reading is not here — it has the whole /books/ shelf (D17).

     Every third-party reference is rendered as a plain link, never an embed. That is the
     graceful-degradation rule the plan requires for all of them, and the reason Wikiloc's
     untested iframe costs nothing (D19). -->

{% assign personal = site.data.personal %}

{% if personal and personal.pages %}
{% for page in personal.pages %}

## {{ page.title }}

{% if page.description %}{{ page.description }}{% endif %}

{% if page.links %}

<p class="personal-links">
{% for link in page.links %}<a href="{{ link.url }}" title="{{ link.name }}">{{ link.name }}</a>{% unless forloop.last %} · {% endunless %}{% endfor %}
</p>
{% endif %}

{% if page.sections %}
{% for section in page.sections %}
{% unless section.slug == '_root' %}### {{ section.title }}{% endunless %}

{% for entry in section.entries %}
{% if entry._name %}**{{ entry._name }}**{% endif %}
{% assign shown = false %}
{% for pair in entry %}{% unless pair[0] == '_name' or pair[1] == nil %}{% assign shown = true %}{% endunless %}{% endfor %}
{% if shown %}

<ul class="personal-entry">
{% for pair in entry %}{% unless pair[0] == '_name' or pair[1] == nil %}
  <li><em>{{ pair[0] | replace: '_', ' ' | capitalize }}:</em>
  {%- if pair[1].id -%}
    {%- if pair[1].url %} <a href="{{ pair[1].url }}">{{ pair[1].id }}</a>{% else %} {{ pair[1].id }}{% endif -%}
  {%- else -%}
    {{ ' ' }}{{ pair[1] }}
  {%- endif -%}
  </li>
{% endunless %}{% endfor %}
</ul>
{% endif %}
{% endfor %}
{% endfor %}
{% endif %}

{% endfor %}
{% else %}

<!-- No Personal export staged yet. The page stays deliberately empty rather than showing
     placeholder content, per the no-invented-content rule (docs/DECISIONS.md D3). -->

{% endif %}

{% assign books = site.books | where_exp: 'b', 'b.title' %}
{% if books and books.size > 0 %}

## Reading

I keep a [bookshelf]({{ '/books/' | relative_url }}) with {{ books.size }} book{% if books.size != 1 %}s{% endif %}.

{% endif %}
