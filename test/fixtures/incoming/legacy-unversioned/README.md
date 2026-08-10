# `legacy-unversioned` — what the plugin actually emits today

Captured verbatim from `logseq-alfolio-export` by driving its own vitest fixtures through
`runExport()` and writing the sandbox-storage calls to disk. Only `exported_at` differs run
to run.

This fixture is **expected to fail** validation, and that is its job: `manifest.json` has no
`schema_version`, so it is exactly the input the transform's version gate must reject with an
actionable message rather than transform on a guess. It also shows the incomplete `files` list
(four entries for five written files) described in `docs/intermediate-schema/README.md`.

Replace it with a passing copy once the plugin emits `schema_version` — at which point the
negative case it covers has genuinely gone away.
