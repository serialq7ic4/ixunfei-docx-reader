# OKR Reader Safety Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent OKR owner IDs and raw API payloads from leaking through diagnostics or command errors.

**Architecture:** Keep the existing exact-link OKR read path and `aggr_detail` endpoint unchanged. Extend URL redaction to accept all sensitive identifiers from an OKR URL, and replace payload interpolation with small error-summary helpers that expose structure but not private values.

**Tech Stack:** Python 3.11+, argparse, requests, pytest, ruff, hatchling/build.

## Global Constraints

- Do not add period listing, selection, or all-period reading.
- Continue requiring `okrId` or `okr_id` in the provided URL.
- Do not change normal Objective/KR rendering.
- Do not include raw remote payload values in errors.
- Do not expose the owner ID or OKR ID in `inspect` output.
- Release the user-visible safety fixes as `v0.1.5`.

---

### Task 1: Redact All OKR URL Identifiers

**Files:**
- Modify: `tests/test_cli_contract.py`
- Modify: `src/ixunfei_docx_reader/cli.py`

**Interfaces:**
- Consumes: `inspect_remote_source(source: str) -> dict[str, object]`
- Produces: `redacted_remote_source(path: str, netloc: str, query: str, tokens: list[str]) -> str`

- [ ] **Step 1: Update the OKR inspect test to require owner-ID redaction**

```python
def test_inspect_okr_url_reports_safe_route_summary() -> None:
    owner_id = "1000000000000000000"
    okr_id = "2000000000000000000"
    source = (
        f"https://tenant.xfchat.iflytek.com/okr/user/{owner_id}/"
        f"?lang=zh-CN&okrId={okr_id}&open_in_browser=true&type=my"
    )

    result = run_module("inspect", source, "--json")

    assert result.returncode == 0
    assert owner_id not in result.stdout
    assert okr_id not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["sourceRef"] == (
        "https://tenant.xfchat.iflytek.com/okr/user/<redacted>/"
        "?lang=zh-CN&okrId=<redacted>&open_in_browser=true&type=my"
    )
```

- [ ] **Step 2: Run the focused test and verify the current implementation fails**

Run:

```bash
python -m pytest tests/test_cli_contract.py::test_inspect_okr_url_reports_safe_route_summary -q
```

Expected: FAIL because the owner ID remains in `sourceRef`.

- [ ] **Step 3: Generalize URL redaction and collect the OKR owner ID**

```python
def redacted_remote_source(
    path: str,
    netloc: str,
    query: str,
    tokens: list[str],
) -> str:
    redacted_path = path
    redacted_query = query
    for token in tokens:
        if not token:
            continue
        redacted_path = redacted_path.replace(token, "<redacted>")
        redacted_query = redacted_query.replace(token, "<redacted>")
    suffix = f"?{redacted_query}" if redacted_query else ""
    return f"https://{netloc}{redacted_path}{suffix}"
```

In `inspect_remote_source`, extract `/okr/user/<owner-id>/`, retain the OKR ID as the diagnostic token, and pass both values to `redacted_remote_source`.

- [ ] **Step 4: Run the focused test and full CLI contract tests**

Run:

```bash
python -m pytest tests/test_cli_contract.py::test_inspect_okr_url_reports_safe_route_summary -q
python -m pytest tests/test_cli_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ixunfei_docx_reader/cli.py tests/test_cli_contract.py
git commit -m "fix: redact okr owner identifiers"
```

### Task 2: Remove Raw OKR Payloads From Errors

**Files:**
- Modify: `tests/test_okr_reader.py`
- Modify: `src/ixunfei_docx_reader/reader.py`

**Interfaces:**
- Consumes: `read_okr(session: requests.Session, source: str)`
- Produces: `okr_response_error(operation: str, payload: object) -> str`

- [ ] **Step 1: Add failing tests for non-zero and malformed OKR responses**

```python
def test_read_okr_nonzero_response_does_not_expose_payload() -> None:
    session = PayloadSession(
        {
            "code": 403,
            "message": "private failure",
            "okr_detail_data": {"objective_list": [{"name": "secret objective"}]},
        }
    )

    with pytest.raises(RuntimeError) as exc_info:
        reader.read_okr(session, OKR_URL)

    message = str(exc_info.value)
    assert message == "OKR aggr_detail failed with code 403."
    assert "private failure" not in message
    assert "secret objective" not in message


def test_read_okr_unexpected_shape_reports_keys_not_values() -> None:
    session = PayloadSession({"code": 0, "data": ["secret value"], "trace": "private trace"})

    with pytest.raises(RuntimeError) as exc_info:
        reader.read_okr(session, OKR_URL)

    message = str(exc_info.value)
    assert message == "OKR aggr_detail returned an unexpected payload shape; keys: code, data, trace."
    assert "secret value" not in message
    assert "private trace" not in message
```

The test helper must still serve the CSRF endpoint and return the supplied payload for `aggr_detail`.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
python -m pytest tests/test_okr_reader.py -q
```

Expected: FAIL because current exceptions interpolate the complete payload.

- [ ] **Step 3: Add a safe response-summary helper**

```python
def okr_response_error(operation: str, payload: object) -> str:
    if not isinstance(payload, dict):
        return f"{operation} returned an unexpected payload type: {type(payload).__name__}."
    code = payload.get("code")
    if code not in {0, None}:
        return f"{operation} failed with code {code}."
    keys = ", ".join(sorted(str(key) for key in payload))
    return f"{operation} returned an unexpected payload shape; keys: {keys or '(none)'}."
```

Use this helper for both non-zero responses and invalid detail shapes. Do not change successful rendering.

- [ ] **Step 4: Run OKR and full test suites**

Run:

```bash
python -m pytest tests/test_okr_reader.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ixunfei_docx_reader/reader.py tests/test_okr_reader.py
git commit -m "fix: sanitize okr remote errors"
```

### Task 3: Document and Version the Safety Release

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/block-support.md`
- Modify: `docs/error-contract.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/ixunfei_docx_reader/__init__.py`

**Interfaces:**
- Produces: package version `0.1.5`
- Produces: changelog section `v0.1.5 - 2026-07-10`

- [ ] **Step 1: Update documentation**

Document that:

- OKR reads use exactly the `okrId` in the supplied URL.
- Unrelated query parameters are ignored.
- `inspect` redacts both OKR owner and period identifiers.
- remote OKR errors do not echo raw API payloads.

- [ ] **Step 2: Move the existing Unreleased contribution entry into `v0.1.5` and add security notes**

```markdown
## v0.1.5 - 2026-07-10

### Added

- Added bilingual contribution guidelines plus GitHub issue and pull request templates with privacy-safe reporting requirements.

### Security

- Redacted both owner IDs and OKR IDs from `ixfdoc inspect` OKR source summaries.
- Stopped including raw OKR API payloads in remote read errors.
```

- [ ] **Step 3: Bump both version declarations**

Set:

```toml
version = "0.1.5"
```

and:

```python
__version__ = "0.1.5"
```

- [ ] **Step 4: Run documentation and version checks**

Run:

```bash
git diff --check
python -m ixunfei_docx_reader.cli --version
python -m ruff check .
```

Expected: no diff errors, version output contains `0.1.5`, and ruff passes.

- [ ] **Step 5: Commit**

```bash
git add README.md README.en.md docs/block-support.md docs/error-contract.md CHANGELOG.md pyproject.toml src/ixunfei_docx_reader/__init__.py
git commit -m "chore: release v0.1.5"
```

### Task 4: Verify, Push, and Publish

**Files:**
- Verify: entire repository
- Create locally: `dist/*`

**Interfaces:**
- Produces: Git tag `v0.1.5`
- Produces: GitHub Release `v0.1.5` with changelog notes, wheel, and source distribution

- [ ] **Step 1: Run the complete release verification**

```bash
python -m compileall -q src
python -m pytest -q
python -m ruff check .
rm -rf dist build
python -m build
scripts/smoke.sh
```

Expected: every command exits zero.

- [ ] **Step 2: Confirm repository state and package artifacts**

```bash
git status --short --branch
ls -lh dist
python -m zipfile -l dist/ixunfei_docx_reader-0.1.5-py3-none-any.whl
```

Expected: only ignored build artifacts are present and the wheel contains the package and bundled skills.

- [ ] **Step 3: Push commits through the configured local proxy**

```bash
HTTPS_PROXY=http://127.0.0.1:7890 \
HTTP_PROXY=http://127.0.0.1:7890 \
ALL_PROXY=socks5://127.0.0.1:7890 \
git push origin main
```

- [ ] **Step 4: Tag and push the release**

```bash
git tag v0.1.5
HTTPS_PROXY=http://127.0.0.1:7890 \
HTTP_PROXY=http://127.0.0.1:7890 \
ALL_PROXY=socks5://127.0.0.1:7890 \
git push origin v0.1.5
```

- [ ] **Step 5: Wait for the release workflow and set non-empty release notes**

Use the `v0.1.5` changelog section as the GitHub Release body, then verify the release includes:

- `ixunfei_docx_reader-0.1.5-py3-none-any.whl`
- `ixunfei_docx_reader-0.1.5.tar.gz`
- non-empty release notes

