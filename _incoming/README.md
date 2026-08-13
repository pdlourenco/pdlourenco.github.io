# `_incoming/` — the staged Logseq export

Raw intermediate YAML exactly as the plugin wrote it, committed so `git diff` here shows
what changed in the graph. `bin/transform.py` reads this directory and nothing else.

Expected contents ([contract v1](../docs/intermediate-schema/README.md)):

```
_incoming/
├── cv.yml
├── profile.yml
├── personal.yml
├── publication_overrides.yml
├── manifest.json          # schema_version, file list, hashes
├── papers.src.bib         # Zotero / Better BibTeX export (Phase 4, per D24)
└── blog/YYYY-MM-DD-slug.md
```

## How to put an export here

⚠️ **Do not run the plugin's `sync.sh` against this repository yet.** As written it copies
into `_data/` and `_posts/`, which would overwrite generated files and leave the CV page
rendering intermediate YAML it cannot read — see [`../docs/DECISIONS.md`](../docs/DECISIONS.md)
D21 and [`logseq-alfolio-export#1`](https://github.com/pdlourenco/logseq-alfolio-export/issues/1).

Until that lands, copy by hand from the plugin's sandbox storage:

```bash
cp -r "<graph>/.logseq/plugins/storages/logseq-alfolio-export/_logseq_export/." _incoming/
python3 bin/transform.py          # writes _data/… ; commit both together
```

The transform will refuse an export that has no `manifest.json`, declares no
`schema_version`, or whose files disagree with the manifest's list or hashes. Those refusals
are the point: a half-copied export should fail loudly rather than produce a half-empty site.
Today's plugin does not emit `schema_version` yet, so expect that refusal until the upstream
issue is resolved.

This file is excluded from the Jekyll build, and the transform ignores it.
