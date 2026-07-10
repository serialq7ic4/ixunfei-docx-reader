# OKR Reader Hardening Design

## Goal

Fix two privacy risks in OKR diagnostics and remote error handling while preserving the current contract: `ixfdoc` reads exactly the OKR period identified by the `okrId` or `okr_id` in the user-provided URL.

## Scope

- Continue using `/okrx/api/okr/owner/aggr_detail/` as the only OKR content endpoint.
- Ignore unrelated URL parameters such as `lang`, `open_in_browser`, `tea_from`, and `type`.
- Redact both the owner ID in `/okr/user/<owner-id>/` and the OKR ID in query parameters from `inspect` output.
- Replace raw OKR API payloads in errors with a safe summary containing only the operation and response code.
- Add focused regression tests and update user-facing documentation.

## Non-Goals

- Listing available OKR periods.
- Selecting a period by name.
- Reading all periods from one owner URL.
- Fetching comments, progress history, references, permissions, or operation logs.
- Adding OKR write support to `ixfdoc`.
- Changing rich-text, progress, or empty Objective/KR rendering.

## Architecture

### URL and Routing

The existing `/okr/user/` route detection remains unchanged. `okr_id_from_url` continues to require an explicit `okrId` or `okr_id`; extra query parameters are ignored.

`inspect_remote_source` will identify both the owner ID path segment and the OKR ID query value, then redact both before returning `sourceRef`. Prefix and length diagnostics remain based on the OKR ID.

### API Errors

`read_okr` will not interpolate the complete response payload into exceptions. Non-zero responses will report the operation and response code. Unexpected response shapes will report the top-level field names rather than their values.

## CLI Contract

No new commands or flags are added. Existing commands retain their behavior:

```bash
ixfdoc inspect "<okr-url>" --json
ixfdoc read "<okr-url>"
```

The provided URL determines the exact period through its `okrId`.

## Testing

Tests will cover:

- simultaneous owner ID and OKR ID redaction;
- URLs containing unrelated query parameters;
- safe non-zero API errors without private payload content;
- unexpected response shape errors without raw values;
- preservation of the existing basic OKR rendering contract.

## Documentation and Release

Update the Chinese and English README, block support documentation, error contract, and changelog. Because the change modifies user-visible diagnostics and OKR rendering behavior, publish it as `v0.1.5` after full test, lint, build, and smoke verification.
