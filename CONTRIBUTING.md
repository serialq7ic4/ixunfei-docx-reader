# Contributing

Thanks for helping improve `ixunfei-docx-reader`. This project handles private document workflows, so contribution quality includes both code correctness and data-safety discipline.

## Scope

Good contributions usually fit one of these areas:

- Reader support for authorized i讯飞/LarkShell source types.
- Safer local diagnostics and clearer error contracts.
- Markdown/TSV conversion fidelity for supported payloads.
- macOS/Windows local cookie export reliability.
- Documentation, install, update, and release workflow improvements.

Out of scope unless discussed first:

- Hosted services, telemetry, background daemons, or browser extensions.
- Linux desktop-session support, because i讯飞 does not ship a Linux desktop client.
- Open Platform / OpenAPI authentication modes without a concrete permission model and maintainer agreement.

## Privacy Rules

Do not include private data in issues, pull requests, commits, tests, logs, or screenshots.

Never share:

- Cookie files or cookie values.
- CSRF tokens.
- Full private document URLs or document tokens.
- Raw internal API responses from private documents.
- Generated Markdown/TSV/manifests containing private content.

When reporting diagnostics, review and redact output first. `ixfdoc doctor --json` and `ixfdoc inspect <source> --json` are intended to provide safer summaries, but contributors are still responsible for checking what they paste.

## Before Opening an Issue

1. Search existing issues and recent releases.
2. Upgrade to the latest GitHub Release wheel if possible.
3. Run:

```bash
ixfdoc --version
ixfdoc doctor --json
ixfdoc inspect "<redacted-source>" --json
```

4. Include only redacted output and a minimal reproduction.

For rendering bugs, prefer a synthetic `client_vars` fixture or a reduced anonymized block payload instead of private source data.

## Pull Request Checklist

Before opening a PR:

```bash
python -m compileall -q src
python -m pytest -q
python -m ruff check .
```

If the change affects packaging or release behavior, also run:

```bash
python -m build
scripts/smoke.sh
ixfdoc update skills --runtimes none --json
ixfdoc update check --json
```

PRs should include:

- A clear problem statement and the user-facing behavior change.
- Tests for behavior changes, especially parser, converter, CLI, cookie, or diagnostic changes.
- Documentation updates when commands, safety behavior, supported sources, or install/update flows change.
- `CHANGELOG.md` updates for user-facing changes.

## Code Guidelines

- Keep `ixfdoc` as the source of truth; skills should remain thin wrappers around the CLI.
- Preserve local-only behavior: no telemetry, hosted services, or silent uploads.
- Prefer small, reviewable changes with focused tests.
- Keep JSON error contracts stable unless the PR explicitly changes and documents the contract.
- Do not print secrets in errors, diagnostics, tests, or logs.
- For derived outputs, prefer deterministic filenames, stable manifests, and reproducible conversion behavior.

## Testing Fixtures

Use synthetic fixtures whenever possible. If a real document exposes a bug, reduce it to the smallest anonymized payload that reproduces the issue.

Recommended fixture style:

- Use fake tokens such as `doxfixturetoken`, `wiki_fixture`, or `okr_fixture`.
- Use generic hosts such as `tenant.xfchat.iflytek.com`.
- Keep document text short and non-sensitive.
- Assert that private tokens or cookie values do not appear in command output.

## Release Notes

Maintainers should follow `docs/release.md` for releases. Each release must include non-empty GitHub Release notes derived from `CHANGELOG.md`, plus wheel and source distribution assets.
