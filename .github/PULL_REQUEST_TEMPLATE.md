## Summary

Describe the problem and the user-facing change.

## Scope

- [ ] CLI behavior
- [ ] Reader / remote source handling
- [ ] Markdown / TSV conversion
- [ ] Cookie export
- [ ] Skill wrapper / install / update flow
- [ ] Documentation only

## Safety

- [ ] No cookie values, CSRF tokens, full private document URLs, raw private API responses, or private document content are included.
- [ ] Diagnostics and errors remain redacted by default.
- [ ] Generated artifacts are not committed.

## Verification

Commands run:

```bash
python -m compileall -q src
python -m pytest -q
python -m ruff check .
```

If packaging or release behavior changed:

```bash
python -m build
scripts/smoke.sh
ixfdoc update skills --runtimes none --json
ixfdoc update check --json
```

## Documentation

- [ ] README / docs updated, or not needed because:
- [ ] CHANGELOG updated for user-facing changes, or not needed because:
