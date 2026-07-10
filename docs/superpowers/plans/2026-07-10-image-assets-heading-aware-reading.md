# Image Assets and Heading-Aware Reading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Download private docx images into safe local sidecar assets and provide heading-aware, atomic Markdown chunk reading for Codex and Claude Code.

**Architecture:** Keep Markdown conversion independent from HTTP by adding an image resolver callback. Put authenticated media downloads in a focused asset module, keep generated artifact lifecycle in the CLI, and add a pure Markdown parser/chunker used by `outline` and `chunk`.

**Tech Stack:** Python 3.11+, dataclasses, pathlib, requests, argparse, pytest, ruff, hatchling/build.

## Global Constraints

- Preserve one complete Markdown file per source.
- Keep image download opt-in at the CLI and enabled by packaged agent skills.
- Never expose image resource tokens, authenticated media URLs, cookies, or CSRF values.
- Do not fail the document read when one image cannot be downloaded.
- Do not split fenced code, tables, images, or image captions.
- Do not persist chunk Markdown files.
- Preserve existing OKR, mindnote, bitable, and embedded-sheet behavior.
- Release as `v0.1.6` with changelog-backed GitHub Release notes.

---

### Task 1: Add the Converter Image Resolution Contract

**Files:**
- Modify: `tests/test_docx_converter.py`
- Modify: `src/ixunfei_docx_reader/converters/docx_markdown.py`

**Interfaces:**
- Produces: `ImageReference`
- Produces: `ImageResolution`
- Produces: `ConversionOptions.resolve_image`
- Preserves: `[image]` when no resolver is configured

- [ ] **Step 1: Add failing tests for image metadata and callback rendering**

Create an image fixture with `image.token`, `name`, `mimeType`, `width`, `height`, `size`, and caption attributed text. Require the resolver to receive those values and return:

```python
ImageResolution(
    markdown_path="assets/docx_1/image-001.png",
    alt_text="Architecture diagram",
    asset={
        "path": "assets/docx_1/image-001.png",
        "mimeType": "image/png",
        "width": 1200,
        "height": 800,
        "sizeBytes": 1234,
        "status": "downloaded",
        "ordinal": 1,
    },
)
```

Assert Markdown contains:

```markdown
![Architecture diagram](assets/docx_1/image-001.png)
```

Also assert the asset record is present and the raw token is absent from Markdown and serialized asset metadata.

- [ ] **Step 2: Run focused tests and verify they fail**

```bash
python -m pytest tests/test_docx_converter.py -k image -q
```

Expected: FAIL because image blocks always render `[image]`.

- [ ] **Step 3: Implement the minimal converter interface**

Add immutable dataclasses:

```python
@dataclass(frozen=True)
class ImageReference:
    block_id: str
    token: str
    name: str
    mime_type: str
    width: int | None
    height: int | None
    declared_size: int | None
    caption: str


@dataclass(frozen=True)
class ImageResolution:
    markdown_path: str | None
    alt_text: str
    asset: dict[str, Any] | None = None
    warning: str | None = None
```

Extend `ConversionOptions` with:

```python
resolve_image: Callable[[ImageReference], ImageResolution] | None = None
```

Collect returned asset records and warnings in `ConversionResult`. Render `[image]` when no resolver exists or no path is returned.

- [ ] **Step 4: Run converter tests**

```bash
python -m pytest tests/test_docx_converter.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_docx_converter.py src/ixunfei_docx_reader/converters/docx_markdown.py
git commit -m "feat: add image conversion contract"
```

### Task 2: Implement Authenticated Image Asset Downloads

**Files:**
- Create: `src/ixunfei_docx_reader/assets.py`
- Create: `tests/test_image_assets.py`
- Modify: `tests/test_reader_client_vars.py`
- Modify: `src/ixunfei_docx_reader/reader.py`

**Interfaces:**
- Produces: `ImageAssetWriter.resolve(reference: ImageReference) -> ImageResolution`
- Extends: `read_sources(..., download_images: bool = False, output_root: Path | None = None)`

- [ ] **Step 1: Add failing tests for endpoint shape and successful download**

Use a fake session that records the URL and headers and returns PNG bytes. Require:

```text
/space/api/box/stream/download/all/<token>/
?mount_node_token=<doc-token>&mount_point=docx_image
```

Assert the generated filename is `image-001.png`, the Markdown path is relative, and the manifest asset does not contain the token or URL.

- [ ] **Step 2: Add failing tests for deduplication and safe failures**

Require repeated references to the same token to reuse one file. Require an HTTP or MIME validation failure to return `[image]` plus a warning such as:

```text
image 2 download failed: http_error
```

Assert the warning excludes token, URL, response body, Cookie, and CSRF values.

- [ ] **Step 3: Run focused tests and verify they fail**

```bash
python -m pytest tests/test_image_assets.py tests/test_reader_client_vars.py -q
```

Expected: FAIL because `assets.py` and reader integration do not exist.

- [ ] **Step 4: Implement `ImageAssetWriter`**

The writer must:

- derive extensions from a fixed MIME map with a sanitized filename fallback;
- stream to `<filename>.part`;
- validate status, `Content-Type`, and common image magic bytes;
- atomically rename the complete file;
- deduplicate by in-memory token map;
- return only safe asset metadata;
- unlink partial files on failure.

- [ ] **Step 5: Integrate the resolver into docx reads**

When `download_images` is true, require `output_root`, create `assets/<result-key>/`, and pass `ImageAssetWriter.resolve` into `ConversionOptions`. Add `assets` and `warnings` to each read result. Non-docx source types keep empty lists.

- [ ] **Step 6: Run focused and full tests**

```bash
python -m pytest tests/test_image_assets.py tests/test_reader_client_vars.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/ixunfei_docx_reader/assets.py src/ixunfei_docx_reader/reader.py tests/test_image_assets.py tests/test_reader_client_vars.py
git commit -m "feat: download docx image assets"
```

### Task 3: Extend Manifest and Cleanup Lifecycle

**Files:**
- Modify: `tests/test_cli_contract.py`
- Modify: `src/ixunfei_docx_reader/cli.py`

**Interfaces:**
- Adds: `ixfdoc read --download-images`
- Adds: `ixfdoc cleanup <out-dir>`
- Extends: manifest item `assets` and `warnings`

- [ ] **Step 1: Add failing CLI contract tests**

Cover:

- `--download-images` without `--out-dir` returns `bad_args`;
- manifest includes safe asset records and warnings;
- `--cleanup` removes recorded asset files and empty generated directories;
- unrelated files under the output directory survive cleanup;
- `ixfdoc cleanup <out-dir>` reads `manifest.json` and applies the same safe cleanup.

- [ ] **Step 2: Run focused tests and verify they fail**

```bash
python -m pytest tests/test_cli_contract.py -k "download_images or cleanup" -q
```

Expected: FAIL because the flag, manifest fields, and cleanup command are missing.

- [ ] **Step 3: Implement CLI parsing and validation**

Add:

```python
read.add_argument("--download-images", action="store_true")
cleanup = subparsers.add_parser("cleanup", help="Remove generated read artifacts.")
cleanup.add_argument("out_dir")
```

Pass `output_root=out_dir` and `download_images=True` into `read_sources`.

- [ ] **Step 4: Implement safe artifact cleanup**

Normalize every generated path and verify it is under `out_dir` before deletion. Delete files first, then recorded asset directories, `assets/`, and `out_dir` only when empty. Do not follow manifest paths outside the output root.

- [ ] **Step 5: Run CLI and full tests**

```bash
python -m pytest tests/test_cli_contract.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ixunfei_docx_reader/cli.py tests/test_cli_contract.py
git commit -m "feat: manage image artifact lifecycle"
```

### Task 4: Build the Heading-Aware Atomic Markdown Chunker

**Files:**
- Create: `src/ixunfei_docx_reader/markdown_chunks.py`
- Create: `tests/test_markdown_chunks.py`

**Interfaces:**
- Produces: `build_outline(markdown: str, target_chars: int = 12000) -> MarkdownOutline`
- Produces: `render_chunk(markdown: str, outline: MarkdownOutline, index: int) -> str`

- [ ] **Step 1: Add failing parser tests**

Require fenced code containing `# fake heading` to remain one code block and not enter the heading index. Require contiguous Markdown table rows and image paragraphs to remain atomic blocks.

- [ ] **Step 2: Add failing boundary-selection tests**

Cover:

- one title H1 plus H2 sections selects H2;
- multiple substantive H1 sections selects H1;
- oversized H2 splits at H3;
- heading-free Markdown packs by atomic blocks;
- an oversized code block remains whole;
- breadcrumb includes parent headings;
- chunk metadata lists local image paths.

- [ ] **Step 3: Run tests and verify they fail**

```bash
python -m pytest tests/test_markdown_chunks.py -q
```

Expected: FAIL because the module does not exist.

- [ ] **Step 4: Implement the pure parser and chunker**

Use immutable dataclasses for atomic blocks, headings, chunks, and outlines. Track one-based line numbers. Select the useful heading level from parsed headings, recursively split oversized sections, then pack remaining atomic blocks without slicing their text.

- [ ] **Step 5: Run chunker and full tests**

```bash
python -m pytest tests/test_markdown_chunks.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ixunfei_docx_reader/markdown_chunks.py tests/test_markdown_chunks.py
git commit -m "feat: add heading-aware markdown chunks"
```

### Task 5: Add Chunk CLI Commands and Update Agent Skills

**Files:**
- Modify: `tests/test_cli_contract.py`
- Modify: `tests/test_setup.py`
- Modify: `src/ixunfei_docx_reader/cli.py`
- Modify: `skills/codex/ixunfei-docx-reader/SKILL.md`
- Modify: `skills/claude-code/ixunfei-docx-reader/SKILL.md`
- Modify: `src/ixunfei_docx_reader/_resources/skills/codex/ixunfei-docx-reader/SKILL.md`
- Modify: `src/ixunfei_docx_reader/_resources/skills/claude-code/ixunfei-docx-reader/SKILL.md`

**Interfaces:**
- Adds: `ixfdoc outline <markdown-file> --json --target-chars <n>`
- Adds: `ixfdoc chunk <markdown-file> --index <n> --target-chars <n>`

- [ ] **Step 1: Add failing CLI tests**

Require `outline --json` to return selected heading level and chunk metadata without full chunk bodies. Require `chunk --index 1` to print a breadcrumb and the complete first chunk. Require invalid indices and nonpositive target sizes to return structured `bad_args` errors.

- [ ] **Step 2: Run focused tests and verify they fail**

```bash
python -m pytest tests/test_cli_contract.py -k "outline or chunk" -q
```

Expected: FAIL because the commands are missing.

- [ ] **Step 3: Implement `outline` and `chunk`**

Both commands read a local Markdown file and call the same chunker with the same default target size. `outline` serializes metadata only. `chunk` prints:

```markdown
[chunk 1/N breadcrumb="Document > Section"]

<original Markdown slice>
```

- [ ] **Step 4: Establish a baseline skill failure scenario**

Use a representative prompt containing a long Markdown file and local image references. Confirm the existing skill command deletes artifacts before they can be inspected and contains no instruction to read every chunk or image.

- [ ] **Step 5: Update both source skills**

Replace the immediate `--cleanup` workflow with:

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<source>" --out-dir "$out" --expand-sheets --download-images --print-manifest
ixfdoc outline "<generated-markdown>" --json
ixfdoc chunk "<generated-markdown>" --index 1
# Repeat for every chunk and inspect every referenced local image.
ixfdoc cleanup "$out"
```

State explicitly that answers must incorporate text, tables, code blocks, and visual image content. Keep cleanup as the final step even when analysis fails.

- [ ] **Step 6: Synchronize packaged resources and test installation**

Ensure the two `_resources` skill files exactly match their source counterparts. Run:

```bash
python -m pytest tests/test_setup.py tests/test_cli_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/ixunfei_docx_reader/cli.py tests/test_cli_contract.py tests/test_setup.py skills src/ixunfei_docx_reader/_resources/skills
git commit -m "feat: add structured agent reading workflow"
```

### Task 6: Document and Version the Feature Release

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/block-support.md`
- Modify: `docs/error-contract.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/ixunfei_docx_reader/__init__.py`

**Interfaces:**
- Produces: package version `0.1.6`
- Produces: changelog section `v0.1.6 - 2026-07-10`

- [ ] **Step 1: Update bilingual usage documentation**

Document the image sidecar layout, `--download-images`, `outline`, `chunk`, explicit cleanup workflow, image failure behavior, and the fact that chunking does not create split Markdown files.

- [ ] **Step 2: Update block and error contracts**

Change image support from placeholder-only to downloaded local asset when enabled. Add safe image warning categories and state that media tokens and authenticated URLs are never emitted.

- [ ] **Step 3: Add the changelog entry**

Use:

```markdown
## v0.1.6 - 2026-07-10

### Added

- Added authenticated download of docx image blocks into local sidecar assets.
- Added heading-aware `outline` and `chunk` commands that preserve code, tables, and images as atomic blocks.
- Added explicit artifact cleanup for agent reading workflows.

### Changed

- Updated Codex and Claude Code skills to read every dynamic chunk and inspect every downloaded image before cleanup.

### Security

- Kept image resource tokens and authenticated media URLs out of Markdown, manifests, warnings, and filenames.
```

- [ ] **Step 4: Bump version declarations**

Set both package declarations to `0.1.6`.

- [ ] **Step 5: Run documentation and static checks**

```bash
git diff --check
python -m ixunfei_docx_reader.cli --version
python -m ruff check .
```

Expected: no diff errors, version output contains `0.1.6`, and ruff passes.

- [ ] **Step 6: Commit**

```bash
git add README.md README.en.md docs/block-support.md docs/error-contract.md CHANGELOG.md pyproject.toml src/ixunfei_docx_reader/__init__.py
git commit -m "chore: release v0.1.6"
```

### Task 7: Verify, Push, and Publish

**Files:**
- Verify: entire repository
- Create locally: `dist/*`

**Interfaces:**
- Produces: Git tag `v0.1.6`
- Produces: GitHub Release `v0.1.6` with changelog notes, wheel, and source distribution

- [ ] **Step 1: Run complete verification**

```bash
python -m compileall -q src
python -m pytest -q
python -m ruff check .
rm -rf dist build
python -m build
scripts/smoke.sh
```

Expected: every command exits zero.

- [ ] **Step 2: Run an authorized end-to-end sample**

Read the approved sample with `--download-images`, verify 14 local image assets, inspect the manifest for token leakage, run `outline`, read representative first/middle/last chunks, validate image files, then run explicit cleanup.

- [ ] **Step 3: Confirm artifacts and repository state**

```bash
git status --short --branch
ls -lh dist
python -m zipfile -l dist/ixunfei_docx_reader-0.1.6-py3-none-any.whl
```

- [ ] **Step 4: Push through the local proxy**

```bash
HTTPS_PROXY=http://127.0.0.1:7890 \
HTTP_PROXY=http://127.0.0.1:7890 \
ALL_PROXY=socks5://127.0.0.1:7890 \
git push origin main
```

- [ ] **Step 5: Tag, push, and publish**

Create and push `v0.1.6`, wait for the release workflow, and set the GitHub Release body from the `v0.1.6` changelog section. Verify wheel, source distribution, and non-empty notes.
