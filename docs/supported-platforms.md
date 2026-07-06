# Supported Platforms

`ixfdoc` targets desktop i讯飞/LarkShell environments where local authenticated session data exists.

| Platform | Status | Notes |
|---|---|---|
| macOS | Tier 1 | `ixfdoc cookies export --provider auto` reads LarkShell Chromium profile data and decrypts cookies with Keychain. |
| Windows | Tier 1 | `ixfdoc cookies export --provider windows-larkshell` reads LarkShell Chromium profile data and decrypts cookies locally with DPAPI through `pywin32`. |

## Windows

Windows support uses the local LarkShell Chromium cookie database and DPAPI through `pywin32`.

Install with:

```bash
python -m pip install -e ".[windows]"
ixfdoc cookies export --provider windows-larkshell --output %TEMP%\\ixunfei_profile_explorer_cookies.json
ixfdoc doctor --json --cookies %TEMP%\\ixunfei_profile_explorer_cookies.json
```

Exported cookie files are sensitive local artifacts. Do not log, screenshot, commit, or keep them longer than needed.

Do not use this on Linux; i讯飞 does not ship a Linux desktop client.
