# Security

`ixunfei-docx-reader` is a local, read-only tool. It reuses cookies from a user-authorized i讯飞/LarkShell desktop session to extract documents that the user can already access.

## Sensitive Data

- Cookie exports are secrets. Do not commit them, paste them into issues, or include them in logs.
- Generated Markdown, TSV, manifests, and diagnostics may contain private document content.
- Diagnostic output must redact cookie values, CSRF tokens, full document tokens, and response bodies by default.

## Supported Platforms

- macOS
- Windows

Linux is intentionally not a supported desktop-session target.

## Reporting

When reporting issues, include:

- OS version
- `ixfdoc doctor --json` output after redaction review
- command line used, with private URLs/tokens redacted

Do not include cookie files, raw internal API responses, or private document content.

