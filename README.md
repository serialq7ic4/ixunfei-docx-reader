# ixunfei-docx-reader

Read authorized i讯飞/LarkShell private documents into agent-friendly Markdown/TSV.

This project is intentionally small:

- `ixfdoc` is the CLI.
- Codex and Claude Code skills are thin wrappers around the CLI.
- The core reader is read-only and does not upload document content.
- Supported desktop platforms are macOS and Windows.

## Commands

```bash
ixfdoc read <url-or-file>... --out-dir ./out --expand-sheets
ixfdoc cookies export --provider auto --output /tmp/ixunfei_profile_explorer_cookies.json
ixfdoc doctor --json
```

## Current Status

The initial package skeleton is in place with:

- CLI contract and JSON error handling foundation.
- macOS LarkShell cookie export via local Chromium profile data and Keychain.
- Local Markdown input support.
- Ported remote reader functions from the original skill.
- A first pure docx client-vars to Markdown converter.
- Codex and Claude Code skill wrappers.

Remote reader parity with the original skill is being migrated incrementally.

## Authentication

On macOS, export the local i讯飞/LarkShell desktop session cookies before reading private links:

```bash
ixfdoc cookies export --provider auto --output /tmp/ixunfei_profile_explorer_cookies.json
ixfdoc read "<private-i讯飞-link>" --cookies /tmp/ixunfei_profile_explorer_cookies.json --out-dir ./out --expand-sheets
```

Treat exported cookie files as secrets. Do not commit or print them.
