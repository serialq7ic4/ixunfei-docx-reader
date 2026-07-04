# Supported Platforms

`ixfdoc` targets desktop i讯飞/LarkShell environments where local authenticated session data exists.

| Platform | Status | Notes |
|---|---|---|
| macOS | Tier 1 | `ixfdoc cookies export --provider auto` reads LarkShell Chromium profile data and decrypts cookies with Keychain. |
| Windows | Planned Tier 1 | DPAPI-based cookie provider is planned. |
