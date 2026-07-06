# Privacy

`ixunfei-docx-reader` does not run a hosted service and does not upload document content. `ixfdoc` is the source of truth; Codex and Claude Code wrappers only call the CLI and follow its JSON error hints.

The CLI reads local cookies and remote i讯飞/LarkShell document data only to produce local Markdown/TSV artifacts. Outputs are written to the directory chosen by the user.

Cookie export uses the local desktop login session on supported macOS and Windows systems. Diagnostic and setup commands must not print cookie values.

## Local Files

The following files can contain private data:

- exported cookie JSON files
- generated Markdown files
- generated TSV blocks
- `manifest.json`
- debug or diagnostic logs

Delete these files when they are no longer needed.

Do not commit generated artifacts, paste cookie values into issues or prompts, or share exported cookie files.
