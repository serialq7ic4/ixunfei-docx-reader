from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ConversionOptions:
    expand_sheet: Callable[[str], str | list[str]] | None = None
    asset_mode: str = "placeholder"


@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    counts: Counter[str]
    assets: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Block:
    id: str
    type: str
    parent_id: str | None
    children: list[str]
    text: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class BlockTree:
    blocks: dict[str, Block]
    order: list[str]
    root_id: str | None


def convert_docx_client_vars(
    client_vars_data: dict[str, Any],
    obj_token: str,
    options: ConversionOptions | None = None,
) -> ConversionResult:
    tree = build_block_tree(client_vars_data, obj_token)
    render_options = options or ConversionOptions()
    ordered_counters: dict[str, int] = {}
    warnings: list[str] = []
    seen: set[str] = set()
    parts: list[str] = []
    if tree.root_id:
        root = tree.blocks.get(tree.root_id)
        if root and root.type == "page" and root.text:
            parts.append(f"# {root.text}")

    for block_id in tree.order:
        rendered = render_block(
            tree,
            block_id,
            0,
            seen,
            warnings,
            render_options,
            ordered_counters,
        )
        if rendered.strip():
            parts.append(rendered.strip())

    markdown = "\n\n".join(parts).strip()
    if markdown:
        markdown += "\n"
    return ConversionResult(
        markdown=markdown,
        counts=count_block_types(tree.blocks),
        assets=[],
        warnings=warnings,
    )


def build_block_tree(client_vars_data: dict[str, Any], obj_token: str) -> BlockTree:
    raw_map = client_vars_data.get("block_map", {})
    if not isinstance(raw_map, dict):
        raw_map = {}

    blocks: dict[str, Block] = {}
    for block_id, entry in raw_map.items():
        if not isinstance(entry, dict):
            continue
        data = entry.get("data", entry)
        if not isinstance(data, dict):
            data = {}
        block_type = str(data.get("type") or entry.get("type") or "unknown")
        blocks[str(block_id)] = Block(
            id=str(block_id),
            type=block_type,
            parent_id=read_parent(data, entry),
            children=read_children(data, entry),
            text=extract_text(data),
            raw=data,
        )

    root_id = find_root_id(blocks, obj_token)
    if root_id and root_id in blocks:
        root = blocks[root_id]
        order = [child_id for child_id in root.children if child_id in blocks]
    else:
        order = [block_id for block_id in blocks if block_id != root_id]
    return BlockTree(blocks=blocks, order=order, root_id=root_id)


def read_parent(data: dict[str, Any], entry: dict[str, Any]) -> str | None:
    parent = data.get("parent_id") or entry.get("parent_id")
    return str(parent) if parent else None


def read_children(data: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    raw = data.get("children", entry.get("children", []))
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, dict):
        out: list[str] = []
        for value in raw.values():
            if isinstance(value, list):
                out.extend(str(item) for item in value)
        return out
    return []


def find_root_id(blocks: dict[str, Block], obj_token: str) -> str | None:
    if obj_token in blocks:
        return obj_token
    for block_id, block in blocks.items():
        if block.type == "page":
            return block_id
    for block_id, block in blocks.items():
        if block.parent_id is None:
            return block_id
    return None


def extract_text(data: dict[str, Any]) -> str:
    text_obj = data.get("text")
    if text_obj is None:
        return ""
    if isinstance(text_obj, str):
        return text_obj.strip()
    if isinstance(text_obj, list):
        return "".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in text_obj).strip()
    if isinstance(text_obj, dict):
        initial = text_obj.get("initialAttributedTexts", {})
        if isinstance(initial, dict):
            pieces = initial.get("text", {})
            if isinstance(pieces, dict):
                return "".join(str(pieces[key]) for key in sorted(pieces, key=piece_sort_key)).strip()
    return ""


def piece_sort_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def count_block_types(blocks: dict[str, Block]) -> Counter[str]:
    return Counter(block.type for block in blocks.values())


def render_block(
    tree: BlockTree,
    block_id: str,
    depth: int,
    seen: set[str],
    warnings: list[str],
    options: ConversionOptions,
    ordered_counters: dict[str, int],
) -> str:
    if block_id in seen:
        return ""
    seen.add(block_id)
    block = tree.blocks.get(block_id)
    if block is None:
        return ""

    if block.type == "page":
        return render_children(tree, block, depth, seen, warnings, options, ordered_counters)
    if block.type.startswith("heading"):
        level_match = re.search(r"(\d+)$", block.type)
        level = min(int(level_match.group(1)) if level_match else 1, 6)
        return f"{'#' * level} {block.text}".rstrip()
    if block.type == "text":
        return block.text
    if block.type == "bullet":
        return f"{'  ' * depth}- {block.text}".rstrip()
    if block.type == "ordered":
        parent_key = block.parent_id or "__root__"
        ordered_counters[parent_key] = ordered_counters.get(parent_key, 0) + 1
        return f"{'  ' * depth}{ordered_counters[parent_key]}. {block.text}".rstrip()
    if block.type == "code":
        return f"```\n{block.text}\n```"
    if block.type == "divider":
        return "---"
    if block.type == "quote_container":
        inner = render_children(tree, block, depth, seen, warnings, options, ordered_counters)
        if not inner.strip():
            return ">"
        return "\n".join(f"> {line}" if line else ">" for line in inner.splitlines())
    if block.type == "callout":
        children = render_children(tree, block, depth, seen, warnings, options, ordered_counters)
        return "\n\n".join(part for part in ["[callout]", children.strip()] if part)
    if block.type == "sheet":
        token = str(block.raw.get("token", "") or "")
        marker = "[sheet]" if not token else f"[sheet token={token}]"
        if not token or options.expand_sheet is None:
            return marker
        expanded = options.expand_sheet(token)
        expanded_text = "\n".join(expanded) if isinstance(expanded, list) else str(expanded)
        return "\n".join(part for part in [marker, expanded_text.strip()] if part.strip())
    if block.type in {"table", "table_cell", "whiteboard", "image", "mindnote", "isv"}:
        return f"[{block.type}]"

    children = render_children(tree, block, depth, seen, warnings, options, ordered_counters)
    if block.type not in {"unknown", ""}:
        warning = f"unsupported block type: {block.type}"
        if warning not in warnings:
            warnings.append(warning)
    return "\n\n".join(part for part in [block.text, children] if part.strip())


def render_children(
    tree: BlockTree,
    block: Block,
    depth: int,
    seen: set[str],
    warnings: list[str],
    options: ConversionOptions,
    ordered_counters: dict[str, int],
) -> str:
    parts = [
        render_block(tree, child_id, depth, seen, warnings, options, ordered_counters)
        for child_id in block.children
    ]
    return "\n\n".join(part.strip() for part in parts if part.strip())
