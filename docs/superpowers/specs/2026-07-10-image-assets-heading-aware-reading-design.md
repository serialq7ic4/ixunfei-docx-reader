# Image Assets and Heading-Aware Reading Design

## Goal

Upgrade docx reading so a generated Markdown file references downloaded local images, while agents read long documents in heading-aware chunks without splitting the final Markdown artifact.

## Confirmed Decisions

- `ixfdoc read` continues to produce one complete Markdown file per source.
- `--download-images` downloads docx image blocks into sidecar asset directories.
- Markdown uses relative local image links.
- Agent skills inspect every downloaded image that appears in the chunks they read.
- Reading chunks are computed dynamically and are not persisted as separate Markdown files.
- A document with one title-level H1 normally splits at H2; documents with multiple substantive H1 sections may split at H1.
- Oversized sections split at the next heading level, then fall back to atomic block packing.
- Fenced code, Markdown tables, images, and their captions remain atomic.
- Image download failure preserves the document body and emits a safe warning.
- Cleanup removes only files and directories recorded as generated artifacts.

## Non-Goals

- OCR, image caption generation, or visual reasoning inside the `ixfdoc` Python package.
- Rewriting document images or changing their resolution.
- Persisting one Markdown file per chunk.
- Uploading private images to a third-party service.
- Changing OKR, mindnote, bitable, or embedded-sheet routing.

## Architecture

### Image Conversion Contract

`docx_markdown.py` will expose an image reference object containing the block ID, resource token, filename, MIME type, dimensions, declared size, and caption. `ConversionOptions` will accept an optional image resolver callback.

Without a resolver, image blocks retain the current `[image]` placeholder. With a resolver, the converter renders the resolver's relative Markdown path and adds its safe asset record to `ConversionResult.assets`. Resource tokens are input-only and never appear in Markdown, manifest records, warnings, or filenames.

### Authenticated Asset Download

A focused `assets.py` module will own:

- MIME-to-extension selection;
- deterministic `image-001.ext` naming;
- token-based deduplication within one document read;
- authenticated download requests;
- response MIME and file-magic validation;
- safe warning construction;
- generated-path tracking.

The verified private endpoint shape is:

```text
<document-origin>/space/api/box/stream/download/all/<resource-token>/
  ?mount_node_token=<document-token>&mount_point=docx_image
```

Requests reuse the existing cookie-backed session, CSRF headers, document origin, and referer. The endpoint URL and resource token must not be included in exceptions exposed to users.

### Output Layout and Manifest

For a remote docx result keyed as `docx_1`, output uses:

```text
<out-dir>/
  docx-1.md
  manifest.json
  assets/
    docx_1/
      image-001.png
      image-002.png
```

Markdown references `assets/docx_1/image-001.png`. Each manifest item may include an `assets` list with only:

- relative or local generated path;
- MIME type;
- width and height;
- downloaded byte size;
- status;
- ordinal.

No resource token, authenticated URL, Cookie, CSRF value, or response payload is stored.

`--cleanup` remains backward compatible and removes Markdown, manifest, and recorded assets. A new explicit `ixfdoc cleanup <out-dir>` command supports the agent workflow, where artifacts must remain available until text and images have been inspected.

### Heading-Aware Chunking

A new `markdown_chunks.py` module parses Markdown into atomic blocks before selecting chunk boundaries. The parser recognizes:

- ATX headings outside fenced code;
- fenced code blocks;
- Markdown table runs;
- image paragraphs;
- paragraphs and list runs.

The chunker builds a heading stack and selects the highest useful section level:

1. Use H1 when the document has multiple substantive H1 sections.
2. Otherwise use H2 when available.
3. Otherwise use the first available heading level.
4. If no headings exist, pack atomic blocks by target character count.

Sections above the target size recursively split at deeper headings. Remaining oversized content is packed by atomic blocks. A single atomic block may exceed the target rather than being truncated.

Each chunk exposes:

- one-based index;
- breadcrumb;
- start and end line;
- character count;
- referenced local image paths.

The complete Markdown remains unchanged.

### CLI Reading Workflow

Add:

```bash
ixfdoc read <source> --out-dir <dir> --download-images --print-manifest
ixfdoc outline <markdown-file> --json
ixfdoc chunk <markdown-file> --index <n>
ixfdoc cleanup <out-dir>
```

`outline` returns chunk metadata without returning all private document text. `chunk` prints one chunk and includes its breadcrumb. `--target-chars` defaults to a practical agent-reading size and is shared by both commands.

The Codex and Claude Code skills will:

1. read into a temporary directory without `--cleanup`;
2. inspect the manifest and generated Markdown;
3. call `outline`;
4. read every chunk with `chunk`;
5. visually inspect every referenced local image;
6. synthesize the answer from text, tables, code, and images;
7. call `ixfdoc cleanup` after analysis.

## Error Handling and Privacy

- Image download failures produce a placeholder and a warning, not a failed document read.
- Warnings identify only the image ordinal and safe failure class.
- HTTP response bodies from media failures are never interpolated into errors.
- Partial files use a temporary suffix and are atomically renamed after validation.
- A failed or interrupted image does not appear as a successful manifest asset.
- Cleanup validates that recorded paths are descendants of the output directory before deletion.

## Testing

Tests will cover:

- image metadata extraction and callback rendering;
- caption handling and placeholder compatibility;
- authenticated endpoint request shape;
- MIME extension selection, file validation, deduplication, and safe failures;
- manifest records without tokens or authenticated URLs;
- cleanup of Markdown, manifest, and assets while preserving unrelated files;
- heading detection outside code fences;
- H1/H2/H3 selection and recursive splitting;
- atomic code, table, and image blocks;
- breadcrumb and image-path metadata;
- CLI `outline`, `chunk`, and `cleanup` contracts;
- packaged Codex and Claude Code skill workflow.

## Documentation and Release

Update both READMEs, block support, error contract, changelog, packaged skills, and version declarations. Publish the user-visible feature set as `v0.1.6` with non-empty release notes derived from `CHANGELOG.md`.
