---
name: ixunfei-docx-reader
description: Read authorized i讯飞/LarkShell wiki, docx, mindnote, bitable, embedded sheet, or local Markdown sources into local Markdown/TSV artifacts for Codex analysis. Use when the user provides private i讯飞 document links or asks to summarize, analyze, or mine requirements from those documents.
---

# ixunfei-docx-reader

Use the `ixfdoc` CLI as the source of truth. Do not reimplement document parsing in the skill.

## Read Sources

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<source>" --out-dir "$out" --expand-sheets --print-manifest --cleanup
```

Multiple sources are allowed:

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<url-1>" "<url-2>" "/path/to/local.md" --out-dir "$out" --expand-sheets --print-manifest --cleanup
```

## Error Handling

If a command exits non-zero, parse the final line of `stderr` as JSON and follow `error.hint`. Do not parse human-readable prose.

If the error subtype is `cookie_file_missing` or `cookie_export_failed`, run:

```bash
ixfdoc cookies export --provider auto --output /tmp/ixunfei_profile_explorer_cookies.json
```

Then retry the read command with `--cookies /tmp/ixunfei_profile_explorer_cookies.json`.

## Safety

- Treat cookie files as secrets.
- Do not print cookie values.
- Generated Markdown/TSV may contain private document content.
