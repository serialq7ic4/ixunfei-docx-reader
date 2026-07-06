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
git tag v0.1.0
git push origin v0.1.0
```

The GitHub Actions release workflow builds `sdist` and `wheel` artifacts and uploads them as workflow artifacts.

## Publishing

Do not publish to PyPI until the README, privacy notes, and Windows support status are current.
