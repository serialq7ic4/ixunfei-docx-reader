# Release

`ixunfei-docx-reader` releases are intentionally small Python package builds.

## Changelog

Every release must have a human-readable changelog entry.

Before tagging:

1. Update [`CHANGELOG.md`](../CHANGELOG.md).
2. Move relevant `Unreleased` entries under the new version heading.
3. Include the release date.
4. Keep entries user-facing: what changed, why it matters, and any migration notes.

## Local Checks

Run before tagging:

```bash
python -m compileall -q src
python -m pytest -q
python -m ruff check .
rm -rf dist build
python -m build
scripts/smoke.sh
```

The smoke scripts require exactly one wheel under `dist/`. They install that
wheel into a temporary virtual environment, compare the CLI version with the
installed package metadata, and install the bundled Codex skill under a
temporary home directory. They do not use a globally installed `ixfdoc`.

For releases that change packaged skills, also verify the explicit update path
after installing the published wheel:

```bash
ixfdoc --version
python -m pip show ixunfei-docx-reader
ixfdoc update skills --runtimes codex --json
ixfdoc update check --json
```

## Tag

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The GitHub Actions release workflow builds `sdist` and `wheel` artifacts, uploads them as workflow artifacts, and attaches them to the GitHub Release.
It extracts the matching tag section from `CHANGELOG.md` and uses that content
as the Release body. If the tag has no changelog section, the workflow fails
instead of creating a Release with empty notes.

After the workflow completes, confirm the GitHub Release contains:

- The changelog text for the release.
- The wheel artifact.
- The source distribution artifact.

## Publishing

Do not publish to PyPI until the README, privacy notes, and Windows support status are current.
