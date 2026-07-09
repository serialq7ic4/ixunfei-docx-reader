# Block Support

`ixfdoc read` converts authorized i讯飞/LarkShell sources into local Markdown and TSV artifacts. This page documents the current rendering behavior so formatter changes stay intentional.

## Command Boundaries

- `ixfdoc doctor` checks the local runtime and cookie metadata. It does not inspect a specific document.
- `ixfdoc inspect <source>` prints a safe routing summary for one source. It does not read document content and redacts full remote tokens.
- `ixfdoc read <source>...` performs the actual read and writes Markdown/TSV artifacts when `--out-dir` is supplied.

## Source Coverage

| Source | Current behavior |
|---|---|
| Local Markdown | Copies the source content into the output artifact |
| Docx URL | Fetches docx client variables and renders Markdown |
| Wiki URL | Resolves the wiki target, then reads the supported document payload |
| OKR URL | Renders objectives and key results as Markdown |
| Mindnote URL | Renders mindnote nodes as nested Markdown bullets |
| Bitable wiki | Renders the selected table view as TSV in Markdown |
| Embedded sheet | Expands supported sheets as TSV when `--expand-sheets` is set |

## Docx Block Rendering

| Block type | Current behavior |
|---|---|
| `page` | Uses the page text as the top-level title when present |
| `heading1` through `heading6` | Renders Markdown headings |
| `text` | Renders paragraph text, preserving inline URL links when metadata is available |
| `bullet` | Renders unordered list items, including nested bullets |
| `ordered` | Renders numbered list items among siblings |
| `todo` | Renders Markdown task-list items |
| `code` | Renders fenced code blocks, including language metadata when available |
| `divider` | Renders a Markdown horizontal rule |
| `quote_container` | Renders child lines as Markdown blockquotes |
| `callout` | Renders a `[callout]` marker plus supported child content |
| `sheet` | Renders a sheet marker, and TSV content when sheet expansion succeeds |
| `table`, `table_cell` | Renders simple structured tables as Markdown tables; falls back to placeholders when structure is incomplete |
| `image`, `whiteboard`, `mindnote`, `isv` | Renders placeholders |
| Unknown containers | Preserves supported child content and emits a warning |

## Safety

- Cookie values are never printed by diagnostics.
- Remote source summaries redact full tokens.
- Generated Markdown and TSV files may contain private document content and should be treated as sensitive local artifacts.
