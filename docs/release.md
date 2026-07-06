# Release

`ixunfei-docx-reader` releases are intentionally small Python package builds.

## Local Checks

Run before tagging:

```bash
python -m compileall -q src
python -m pytest -q
python -m build
```

## Tag

```bash
git tag v0.1.1
git push origin v0.1.1
```

The GitHub Actions release workflow builds `sdist` and `wheel` artifacts, uploads them as workflow artifacts, and attaches them to the GitHub Release.

## Publishing

Do not publish to PyPI until the README, privacy notes, and Windows support status are current.
