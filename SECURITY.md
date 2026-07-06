# Security

`ixunfei-docx-reader` is a local, read-only CLI-first tool. It reuses cookies from a user-authorized i讯飞/LarkShell desktop session to extract documents that the user can already access.

`ixfdoc` owns reading, cookie export, diagnostics, and conversion. Codex and Claude Code wrappers are thin local instructions that call `ixfdoc` and follow its JSON error contract.

## Sensitive Data

- Cookie exports are secrets. Do not commit them, paste them into issues, or include them in logs.
- Generated Markdown, TSV, manifests, and diagnostics may contain private document content.
- Diagnostic output must redact cookie values, CSRF tokens, full document tokens, and response bodies by default.
- Do not paste cookie values into prompts, issue trackers, terminal transcripts, or support requests.

## Supported Platforms

- macOS
- Windows

Linux is intentionally not a supported desktop-session target because i讯飞 does not ship a Linux desktop client.

## Reporting

When reporting issues, include:

- OS version
- `ixfdoc doctor --json` output after redaction review
- command line used, with private URLs/tokens redacted

Do not include cookie files, raw internal API responses, or private document content.
