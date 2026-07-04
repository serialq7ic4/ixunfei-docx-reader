# Privacy

`ixunfei-docx-reader` does not run a hosted service and does not upload document content.

The CLI reads local cookies and remote i讯飞/LarkShell document data only to produce local Markdown/TSV artifacts. Outputs are written to the directory chosen by the user.

## Local Files

The following files can contain private data:

- exported cookie JSON files
- generated Markdown files
- generated TSV blocks
- `manifest.json`
- debug or diagnostic logs

Delete these files when they are no longer needed.

