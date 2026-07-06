# ixunfei-docx-reader

Read authorized i讯飞/LarkShell private documents into local Markdown/TSV files for agent analysis.

`ixunfei-docx-reader` is a small CLI-first project:

- `ixfdoc` is the source of truth.
- Codex and Claude Code skills are thin wrappers around `ixfdoc`.
- Document content stays local unless you choose to send generated files elsewhere.
- Cookie export uses your local desktop login session and never prints cookie values.

Supported desktop-session platforms are macOS and Windows. Linux is not supported because i讯飞 does not ship a Linux desktop client.

## Commands

```bash
ixfdoc read <url-or-file>... --out-dir ./out --expand-sheets
ixfdoc cookies export --provider auto --output /tmp/ixunfei_profile_explorer_cookies.json
ixfdoc doctor --json --cookies /tmp/ixunfei_profile_explorer_cookies.json
```

## Install

For development:

```bash
python -m pip install -e ".[crypto,dev]"
ixfdoc --version
```

For Windows cookie export:

```bash
python -m pip install -e ".[windows]"
```

`crypto` is needed for macOS cookie decryption. `dev` is for tests and local release builds.

Release build notes live in [`docs/release.md`](docs/release.md).

## Current Status

The initial package skeleton is in place with:

- CLI contract and JSON error handling foundation.
- `doctor` diagnostics for runtime and cookie metadata without printing cookie values.
- macOS LarkShell cookie export via local Chromium profile data and Keychain.
- Local Markdown input support.
- Ported remote reader functions from the original skill.
- A pure docx client-vars to Markdown converter with page titles, lists, sheet markers, resource markers, callouts, and quote structure.
- Codex and Claude Code skill wrappers.

Remote reader parity with the original skill is being migrated incrementally.

## Authentication

On macOS or Windows, export the local i讯飞/LarkShell desktop session cookies before reading private links:

```bash
ixfdoc cookies export --provider auto --output /tmp/ixunfei_profile_explorer_cookies.json
ixfdoc doctor --json --cookies /tmp/ixunfei_profile_explorer_cookies.json
ixfdoc read "<private-i讯飞-link>" --cookies /tmp/ixunfei_profile_explorer_cookies.json --out-dir ./out --expand-sheets
```

Treat exported cookie files as secrets. Do not commit or print them.

## Agent Wrappers

Install local wrappers for Codex and Claude Code:

```bash
ixfdoc setup skills --runtimes auto --json
```

The wrappers do not parse documents. They call `ixfdoc read`, parse the CLI JSON error contract, and follow the returned hint.

The wrapper sources live under:

- `skills/codex/ixunfei-docx-reader/SKILL.md`
- `skills/claude-code/ixunfei-docx-reader/SKILL.md`

Keep parsing, cookie export, diagnostics, and conversion logic in the shared Python package.

## Privacy

Treat exported cookies and generated Markdown/TSV as sensitive. Do not commit them. Do not paste cookie values into issues, logs, or prompts.
