# pdlourenco.github.io

Personal website of Pedro Lourenço, built on [al-folio](https://github.com/alshedivat/al-folio)
v1.x (Jekyll). Content is authored in a Logseq graph, exported as neutral intermediate YAML by
a [companion plugin](https://github.com/pdlourenco/logseq-alfolio-export), and transformed into
al-folio's data formats by scripts in this repository.

## Where things are documented

| File                                                         | What it is                                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------------------ |
| [`CLAUDE.md`](CLAUDE.md)                                     | Working notes: what is ours vs upstream's, the dev loop, the pipeline.   |
| [`seed.md`](seed.md)                                         | The original brief. Frozen as a historical record.                       |
| [`docs/IMPLEMENTATION-PLAN.md`](docs/IMPLEMENTATION-PLAN.md) | Critical analysis of the brief, the phased plan, the review contract.    |
| [`docs/DECISIONS.md`](docs/DECISIONS.md)                     | Resolved decisions, and the repository settings only a human can change. |
| [`docs/al-folio/`](docs/al-folio/)                           | Vendored upstream al-folio documentation, for reference.                 |

Precedence when they disagree: `seed.md` → `docs/IMPLEMENTATION-PLAN.md` → `docs/DECISIONS.md`.

## Build

```bash
bundle install
LANG=C.UTF-8 bundle exec jekyll serve   # → http://localhost:4000/
```

The site is built and deployed by `.github/workflows/deploy.yml`; GitHub Pages cannot build it
directly, because al-folio v1.x runs on gems that Pages does not allow. See
[`docs/DECISIONS.md`](docs/DECISIONS.md#owner-action-items-nothing-in-a-commit-can-do-these)
for the one-time repository settings this requires.
