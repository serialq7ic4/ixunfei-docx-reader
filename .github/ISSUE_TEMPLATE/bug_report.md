---
name: Bug report
about: Report a reproducible ixunfei-docx-reader problem without private data
title: "[Bug] "
labels: bug
assignees: ""
---

## Summary

Describe the problem and the expected behavior.

## Environment

- OS:
- Python version:
- `ixfdoc --version`:
- Install method: release wheel / editable source / other

## Command

Paste the command with private URLs, document tokens, cookie paths, and usernames redacted.

```bash
ixfdoc ...
```

## Safe Diagnostics

Review and redact before pasting.

```bash
ixfdoc doctor --json
ixfdoc inspect "<redacted-source>" --json
```

## Reproduction

Steps to reproduce:

1.
2.
3.

## Actual Output

Paste only redacted output. Do not include cookies, CSRF tokens, full private document URLs, raw internal API responses, or private document content.

## Additional Context

For rendering bugs, prefer a synthetic or anonymized `client_vars` fixture instead of private source data.
