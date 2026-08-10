#!/usr/bin/env python3
"""Validate the intermediate-format fixtures against docs/intermediate-schema/.

Phase 2's acceptance check, and the negative-path harness the review contract asks for.
Three fixture sets, each with an expectation:

  valid/               must validate cleanly
  legacy-unversioned/  must fail — it is today's real plugin output, which has no
                       schema_version (docs/intermediate-schema/README.md)
  broken/              must fail, and must report *every* violation, not just the first

Phase 3 moves this validation into bin/transform.py; until then this script is what
demonstrates the contract holds. Run: python3 test/validate_fixtures.py
"""

from __future__ import annotations

import json
import pathlib
import sys

import yaml
from jsonschema import Draft202012Validator

REPO = pathlib.Path(__file__).resolve().parent.parent
SCHEMAS = REPO / "docs" / "intermediate-schema"
FIXTURES = REPO / "test" / "fixtures" / "incoming"

# fixture file -> schema file. The manifest is JSON; everything else is YAML.
FILE_SCHEMAS = {
    "cv.yml": "cv.schema.json",
    "profile.yml": "profile.schema.json",
    "personal.yml": "personal.schema.json",
    "publication_overrides.yml": "publication_overrides.schema.json",
    "manifest.json": "manifest.schema.json",
}


def load(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    # An empty mapping is legitimate: the plugin writes `{}` for an empty section.
    return yaml.safe_load(text) or {}


def validator_for(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def errors_for(fixture_dir: pathlib.Path) -> list[str]:
    """Every validation error in a fixture set, as human-readable strings."""
    found: list[str] = []
    for name, schema_name in FILE_SCHEMAS.items():
        path = fixture_dir / name
        if not path.exists():
            continue
        try:
            data = load(path)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            found.append(f"{name}: unparseable — {exc}")
            continue
        for err in sorted(validator_for(schema_name).iter_errors(data), key=str):
            location = "/".join(str(p) for p in err.absolute_path) or "(root)"
            found.append(f"{name}: {location}: {err.message}")
    return found


def check_manifest_consistency(fixture_dir: pathlib.Path) -> list[str]:
    """The checks a schema cannot express: files present, and hashes matching.

    This is the half-finished-copy detection the manifest exists for, and it is the
    behaviour bin/transform.py inherits in Phase 3.
    """
    problems: list[str] = []
    manifest_path = fixture_dir / "manifest.json"
    if not manifest_path.exists():
        return problems
    manifest = load(manifest_path)

    listed = set(manifest.get("files") or [])
    on_disk = {
        str(p.relative_to(fixture_dir))
        for p in fixture_dir.rglob("*")
        if p.is_file() and p.name != "README.md"
    }
    for missing in sorted(listed - on_disk):
        problems.append(f"manifest lists {missing!r} but it is not present")
    for extra in sorted(on_disk - listed):
        problems.append(f"{extra!r} is present but not listed in the manifest")

    import hashlib

    for name, expected in sorted((manifest.get("hashes") or {}).items()):
        target = fixture_dir / name
        if not target.exists():
            problems.append(f"hash given for {name!r} but the file is missing")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            problems.append(f"{name}: sha256 mismatch (manifest {expected[:12]}…, file {actual[:12]}…)")
    return problems


def main() -> int:
    failures: list[str] = []

    # --- valid/ must be clean, schema and consistency alike -----------------------
    valid_errors = errors_for(FIXTURES / "valid") + check_manifest_consistency(FIXTURES / "valid")
    if valid_errors:
        failures.append("valid/ should validate cleanly but reported:")
        failures += [f"    {e}" for e in valid_errors]
    else:
        print("PASS  valid/ validates against every schema, files and hashes agree")

    # --- legacy-unversioned/ must be rejected for the *right* reason --------------
    legacy = errors_for(FIXTURES / "legacy-unversioned")
    if not legacy:
        failures.append(
            "legacy-unversioned/ validated, but it must not: it is the plugin's current "
            "output and has no schema_version. If the plugin now emits one, promote this "
            "fixture instead of loosening the schema."
        )
    elif not any("schema_version" in e for e in legacy):
        failures.append("legacy-unversioned/ failed, but not on schema_version:")
        failures += [f"    {e}" for e in legacy]
    else:
        print(f"PASS  legacy-unversioned/ rejected on schema_version ({len(legacy)} error(s))")

    # --- broken/ must report every planted violation ------------------------------
    broken = errors_for(FIXTURES / "broken")
    planted = 8 + 5  # 8 in cv.yml, 5 in manifest.json
    if len(broken) < planted:
        failures.append(
            f"broken/ reported {len(broken)} error(s); expected at least {planted}. "
            "Validation must collect every violation, not stop at the first:"
        )
        failures += [f"    {e}" for e in broken]
    else:
        print(f"PASS  broken/ reported {len(broken)} error(s), all violations surfaced")

    if failures:
        print("\nFAIL", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 1
    print("\nAll fixture expectations met.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
