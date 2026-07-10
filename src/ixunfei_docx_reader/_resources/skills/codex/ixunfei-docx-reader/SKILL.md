---
name: ixunfei-docx-reader
description: Read authorized i讯飞/LarkShell wiki, docx, OKR, mindnote, bitable, embedded sheet, or local Markdown sources into local Markdown/TSV artifacts for Codex analysis. Use when the user provides private i讯飞 document or OKR links, or asks to summarize, analyze, or mine requirements from those sources.
---

# ixunfei-docx-reader

Use the `ixfdoc` CLI as the source of truth. Do not reimplement document parsing in the skill.

## Read Sources

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<source>" --out-dir "$out" --expand-sheets --download-images --print-manifest
```

Multiple sources are allowed:

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<url-1>" "<url-2>" "/path/to/local.md" --out-dir "$out" --expand-sheets --download-images --print-manifest
```

OKR pages are supported by the same command and are rendered as Objective / Key Result Markdown.

For every generated Markdown file, run `ixfdoc outline "<file>" --json`, then
read every index with `ixfdoc chunk "<file>" --index <n>`. Inspect every local
path listed in each chunk's `imagePaths` with the runtime's image-viewing
capability. Answers must incorporate text, tables, code blocks, and image
content. Do not use `read --cleanup`, because it removes artifacts before they
can be inspected.

Always run `ixfdoc cleanup "$out"` in a final step, including when reading,
chunking, image inspection, or analysis fails.

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
