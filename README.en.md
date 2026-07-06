# ixunfei-docx-reader

**English** | [简体中文](README.md)

Let Codex, Claude Code, and other local coding agents read authorized i讯飞/LarkShell private documents as local Markdown/TSV artifacts.

> Built for Codex / Claude Code usage, with `ixfdoc` as the local execution engine. Local-session based, no server, no telemetry, no Open Platform app required.

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB">
  <img alt="platform" src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20experimental-lightgrey">
  <img alt="license" src="https://img.shields.io/badge/license-Apache%202.0-green">
</p>

`ixunfei-docx-reader` is primarily used through Codex / Claude Code skills. `ixfdoc` is the local execution engine those skills call, and it can also be used directly for debugging and automation.

- Paste private i讯飞/LarkShell `docx` and `wiki` links in Codex / Claude Code and read them as Markdown.
- Expand supported embedded sheets into TSV sidecar files.
- Reuse your local desktop login session for authentication.
- Install Codex / Claude Code skills backed by the same `ixfdoc` engine.
- Keep document content, cookies, and generated artifacts on your machine.

This project is intentionally small. It is not a browser extension, daemon, sync service, or general Feishu backup product.

## Why This Exists

Private i讯飞/LarkShell documents are often inaccessible to coding agents through ordinary HTTP fetches. This project bridges that gap by letting Codex / Claude Code call `ixfdoc` through a local skill, reuse the desktop session you already have, and convert authorized documents into agent-friendly local files.

Compared with browser-extension projects such as LarkSnap, this project focuses on a narrower workflow:

| Project shape | Best for |
|---|---|
| Codex / Claude Code skill + `ixfdoc` | Let agents read authorized private docs during local development |
| Browser extension | One-click browser export, visual UI, PDF/HTML export, attachment workflows |

The design rule is simple: Codex / Claude Code skills are the user-facing entry points; parsing, cookie export, diagnostics, and conversion are centralized in the local `ixfdoc` execution engine so each agent integration does not reimplement the reader.

## Install

### Recommended: Ask Your Agent To Install It

If you are using Codex, ask Codex:

> Please install ixunfei-docx-reader from https://github.com/serialq7ic4/ixunfei-docx-reader. Install the GitHub Release wheel first (`[crypto]` on macOS, `[windows]` on Windows), then run `ixfdoc setup skills --runtimes codex --json` to install the Codex skill, and verify with `ixfdoc --version`.

If you are using Claude Code, ask Claude Code:

> Please install ixunfei-docx-reader from https://github.com/serialq7ic4/ixunfei-docx-reader. Install the GitHub Release wheel first (`[crypto]` on macOS, `[windows]` on Windows), then run `ixfdoc setup skills --runtimes claude-code --json` to install the Claude Code skill, and verify with `ixfdoc --version`.

Manual installation is documented below.

### Manual Install

From GitHub Release:

```bash
python -m pip install "ixunfei-docx-reader[crypto] @ https://github.com/serialq7ic4/ixunfei-docx-reader/releases/download/v0.1.1/ixunfei_docx_reader-0.1.1-py3-none-any.whl"
ixfdoc --version
```

For local development:

```bash
git clone https://github.com/serialq7ic4/ixunfei-docx-reader.git
cd ixunfei-docx-reader
python -m pip install -e ".[crypto,dev]"
ixfdoc --version
```

For experimental Windows cookie export:

```bash
python -m pip install "ixunfei-docx-reader[windows] @ https://github.com/serialq7ic4/ixunfei-docx-reader/releases/download/v0.1.1/ixunfei_docx_reader-0.1.1-py3-none-any.whl"
```

`crypto` is needed for macOS cookie decryption. `dev` is for tests and release builds. Windows support is covered by CI and unit tests, but still needs validation on a real Windows i讯飞/LarkShell desktop client before it is treated as Tier 1.

## Quick Start

1. Open i讯飞/LarkShell desktop and confirm you are logged in.
2. Export local session cookies.
3. Run `doctor` to verify the cookie file shape without printing secrets.
4. Read one or more private document links.

```bash
ixfdoc cookies export \
  --provider auto \
  --output /tmp/ixunfei_profile_explorer_cookies.json

ixfdoc doctor \
  --json \
  --cookies /tmp/ixunfei_profile_explorer_cookies.json

ixfdoc read \
  "https://your-domain.xfchat.iflytek.com/wiki/xxxx" \
  --cookies /tmp/ixunfei_profile_explorer_cookies.json \
  --out-dir ./out \
  --expand-sheets \
  --print-manifest
```

The generated Markdown and TSV files are local artifacts. Treat them as sensitive if the source document is sensitive.

## Commands

| Command | Purpose |
|---|---|
| `ixfdoc read <source>...` | Read private links or local Markdown files into Markdown/TSV outputs |
| `ixfdoc cookies export` | Export cookies from the local i讯飞/LarkShell desktop session |
| `ixfdoc doctor` | Inspect runtime and cookie metadata without printing cookie values |
| `ixfdoc setup skills` | Install Codex / Claude Code skills |
| `ixfdoc --version` | Print the installed CLI version |

Common read options:

| Option | Purpose |
|---|---|
| `--out-dir <dir>` | Directory for generated artifacts |
| `--cookies <file>` | Cookie JSON file exported by `ixfdoc cookies export` |
| `--expand-sheets` | Export supported embedded sheets into TSV sidecar files |
| `--print-manifest` | Print JSON manifest with output paths and metadata |
| `--cleanup` | Remove files generated by the current command before exit |

Use `--cleanup` when generated files are only needed during the current agent run:

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<private-link>" \
  --cookies /tmp/ixunfei_profile_explorer_cookies.json \
  --out-dir "$out" \
  --expand-sheets \
  --print-manifest \
  --cleanup
```

`--cleanup` removes only files generated by the current command. It does not recursively delete unrelated files in the output directory.

## Codex / Claude Code Usage

Install local skills for Codex and Claude Code:

```bash
ixfdoc setup skills --runtimes auto --json
```

Install only one runtime:

```bash
ixfdoc setup skills --runtimes codex --json
ixfdoc setup skills --runtimes claude-code --json
```

After installation, paste i讯飞/LarkShell private document links in Codex / Claude Code and ask the agent to use the `ixunfei-docx-reader` skill.

These skills do not implement their own document parser. They call `ixfdoc read`, consume the CLI manifest/error contract, and follow the returned hints.

Packaged skill sources live under:

- `skills/codex/ixunfei-docx-reader/SKILL.md`
- `skills/claude-code/ixunfei-docx-reader/SKILL.md`

## Supported Sources

Current reader coverage includes:

- i讯飞/LarkShell `docx` documents.
- i讯飞/LarkShell `wiki` links that resolve to supported document types.
- Mindnote / embedded sheet markers when exposed through the supported document payload.
- Local Markdown files for skill and workflow testing.

Some Feishu/i讯飞 block formats do not map perfectly to Markdown. The converter keeps the representation practical for agent analysis rather than trying to recreate the original visual document one-to-one.

## Supported Platforms

| Platform | Status | Notes |
|---|---|---|
| macOS | Tier 1 | Reads LarkShell Chromium profile data and decrypts cookies with Keychain. |
| Windows | CI-tested / experimental | Reads LarkShell Chromium profile data and decrypts cookies through DPAPI with `pywin32`; still needs live desktop-client validation. |

Linux is not supported because i讯飞 does not ship a Linux desktop client.

More detail: [`docs/supported-platforms.md`](docs/supported-platforms.md).

## Privacy And Security

- Cookie export uses your local desktop login session.
- Cookie values are never printed by `doctor`.
- Generated Markdown/TSV files may contain private document content.
- Do not commit cookies, generated artifacts, logs containing private links, or diagnostic output with sensitive metadata.
- This tool is for authorized document access only. Follow your organization's data handling rules.

See [`PRIVACY.md`](PRIVACY.md) and [`SECURITY.md`](SECURITY.md).

## Development

```bash
python -m pip install -e ".[crypto,dev]"
python -m compileall -q src
python -m pytest -q
python -m ruff check .
python -m build
scripts/smoke.sh
```

On Windows:

```powershell
python -m pip install -e ".[windows,dev]"
scripts\smoke.ps1
```

Release notes live in [`docs/release.md`](docs/release.md). The JSON error contract is documented in [`docs/error-contract.md`](docs/error-contract.md).

## Project Status

Implemented:

- CLI package with JSON error handling.
- macOS local cookie export.
- Windows cookie provider implementation with CI/unit-test coverage.
- Remote private document reader ported from the original skill.
- Feishu/i讯飞 docx client-vars to Markdown conversion.
- Embedded sheet expansion into TSV sidecar files.
- Codex and Claude Code skill installation.
- GitHub Actions CI and tagged Release workflow.

Known limitation:

- Windows is not promoted to Tier 1 until cookie export is validated on a real Windows i讯飞/LarkShell desktop login.

## License

[Apache License 2.0](LICENSE)
