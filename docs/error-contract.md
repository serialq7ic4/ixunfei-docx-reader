# Error Contract

Any non-zero `ixfdoc` command should end `stderr` with one JSON object on the final line.

```json
{
  "ok": false,
  "error": {
    "type": "cookie",
    "subtype": "cookie_file_missing",
    "message": "Cookie file not found: /path/to/cookies.json",
    "hint": "Run `ixfdoc cookies export --provider auto --output <path>` or pass --cookies.",
    "retryable": false
  }
}
```

Agents should parse only the final JSON line. Human-readable text may appear before it.

## Initial Subtypes

- `usage.bad_args`
- `cookie.cookie_file_missing`
- `cookie.cookie_export_failed`
- `cookie.cookie_file_invalid`
- `cookie.cookie_csrf_missing`
- `remote.remote_read_failed`

More subtypes will be added as remote reading, cookie providers, and diagnostics mature.

## Diagnostic Commands

`doctor` is an environment and cookie-file diagnostic. It does not take a source URL and does not read remote document content.

`inspect <source>` is a source-routing diagnostic. It returns safe metadata such as source kind, host, route, token prefix, and token length. For remote sources, it redacts the token from `sourceRef` and does not fetch document content.
