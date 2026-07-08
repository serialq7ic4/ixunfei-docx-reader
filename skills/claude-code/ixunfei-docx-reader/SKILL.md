---
name: ixunfei-docx-reader
description: Read authorized i讯飞/LarkShell private document, OKR, or local Markdown sources into local Markdown/TSV artifacts for Claude Code analysis. Use when users ask to pull, save, summarize, analyze, or mine requirements from i讯飞 wiki/docx/OKR/mindnote/bitable sources.
---

# ixunfei-docx-reader

This skill is a thin wrapper around the shared `ixfdoc` CLI.

## Command

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<source>" --out-dir "$out" --expand-sheets --print-manifest --cleanup
```

OKR pages are supported by the same command and are rendered as Objective / Key Result Markdown.

Use the manifest output to locate generated files while the command is running. With `--cleanup`, generated Markdown/TSV files are removed before the command exits.

## Non-Zero Exit

Read the last line of `stderr` as JSON:

```json
{"ok": false, "error": {"type": "cookie", "subtype": "cookie_file_missing", "message": "...", "hint": "...", "retryable": false}}
```

Follow `hint`; do not guess around authentication or cookie failures.

For cookie-related errors, export the local desktop session first:

```bash
ixfdoc cookies export --provider auto --output /tmp/ixunfei_profile_explorer_cookies.json
```

Then retry the read command with `--cookies /tmp/ixunfei_profile_explorer_cookies.json`.
