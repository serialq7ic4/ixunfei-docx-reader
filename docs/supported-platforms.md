# Supported Platforms

`ixfdoc` targets desktop i讯飞/LarkShell environments where local authenticated session data exists. The CLI is the source of truth for cookie export, diagnostics, reading, and conversion; Codex and Claude Code wrappers call the CLI rather than implementing separate readers.

| Platform | Status | Notes |
|---|---|---|
| macOS | Tier 1 | `ixfdoc cookies export --provider auto` reads LarkShell Chromium profile data and decrypts cookies with Keychain. |
| Windows | CI-tested / experimental | `ixfdoc cookies export --provider windows-larkshell` reads LarkShell Chromium profile data and decrypts cookies locally with DPAPI through `pywin32`, but it still needs live Windows LarkShell validation before Tier 1 support. |

Linux is not supported because i讯飞 does not ship a Linux desktop client.

## Windows

Windows support uses the local LarkShell Chromium cookie database and DPAPI through `pywin32`. It is covered by automated Windows CI for packaging, imports, and unit tests; live Windows LarkShell cookie export has not yet been validated.

Install with:

```bash
python -m pip install -e ".[windows]"
ixfdoc cookies export --provider windows-larkshell --output %TEMP%\\ixunfei_profile_explorer_cookies.json
ixfdoc doctor --json --cookies %TEMP%\\ixunfei_profile_explorer_cookies.json
```

Exported cookie files are sensitive local artifacts. Do not log, screenshot, commit, or keep them longer than needed.
