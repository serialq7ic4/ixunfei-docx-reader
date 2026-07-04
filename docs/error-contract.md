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

More subtypes will be added as remote reading, cookie providers, and diagnostics mature.

