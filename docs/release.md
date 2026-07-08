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
python -m build
scripts/smoke.sh
```

For releases that change packaged skills, also verify the explicit update path:

```bash
ixfdoc update skills --runtimes none --json
ixfdoc update check --json
```

## Tag

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The GitHub Actions release workflow builds `sdist` and `wheel` artifacts, uploads them as workflow artifacts, and attaches them to the GitHub Release.

After the workflow completes, confirm the GitHub Release contains:

- The changelog text for the release.
- The wheel artifact.
- The source distribution artifact.

## Publishing

Do not publish to PyPI until the README, privacy notes, and Windows support status are current.
