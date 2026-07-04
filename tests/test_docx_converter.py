from collections import Counter

from ixunfei_docx_reader.converters.docx_markdown import (
    ConversionOptions,
    convert_docx_client_vars,
)


def test_convert_docx_client_vars_renders_basic_markdown() -> None:
    client_vars = {
        "block_map": {
            "page_1": {
                "data": {
                    "type": "page",
                    "children": ["heading_1", "text_1", "bullet_1", "code_1"],
                    "text": {"initialAttributedTexts": {"text": {"0": "Demo Doc"}}},
                }
            },
            "heading_1": {
                "data": {
                    "type": "heading1",
                    "parent_id": "page_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "Overview"}}},
                }
            },
            "text_1": {
                "data": {
                    "type": "text",
                    "parent_id": "page_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "Hello world"}}},
                }
            },
            "bullet_1": {
                "data": {
                    "type": "bullet",
                    "parent_id": "page_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "First point"}}},
                }
            },
            "code_1": {
                "data": {
                    "type": "code",
                    "parent_id": "page_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "print('hi')"}}},
                }
            },
        }
    }

    result = convert_docx_client_vars(client_vars, "page_1")

    assert result.markdown == (
        "# Overview\n\n"
        "Hello world\n\n"
        "- First point\n\n"
        "```\n"
        "print('hi')\n"
        "```\n"
    )
    assert result.counts == Counter({"page": 1, "heading1": 1, "text": 1, "bullet": 1, "code": 1})
    assert result.assets == []
    assert result.warnings == []


def test_convert_docx_client_vars_marks_unknown_blocks_without_losing_children() -> None:
    client_vars = {
        "block_map": {
            "page_1": {"data": {"type": "page", "children": ["unknown_1"]}},
            "unknown_1": {
                "data": {
                    "type": "unsupported_widget",
                    "parent_id": "page_1",
                    "children": ["text_1"],
                }
            },
            "text_1": {
                "data": {
                    "type": "text",
                    "parent_id": "unknown_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "Nested text"}}},
                }
            },
        }
    }

    result = convert_docx_client_vars(client_vars, "page_1")

    assert result.markdown == "Nested text\n"
    assert result.warnings == ["unsupported block type: unsupported_widget"]


def test_convert_docx_client_vars_expands_sheet_blocks() -> None:
    client_vars = {
        "block_map": {
            "page_1": {"data": {"type": "page", "children": ["sheet_1"]}},
            "sheet_1": {
                "data": {
                    "type": "sheet",
                    "parent_id": "page_1",
                    "token": "shtr_fixture_sheet1",
                }
            },
        }
    }
    expanded_tokens: list[str] = []

    def expand_sheet(token: str) -> list[str]:
        expanded_tokens.append(token)
        return [
            "[sheet-meta workbook_token=shtr_fixture sheet_id=sheet1 rows=1 cols=2]",
            "Name\tValue",
        ]

    result = convert_docx_client_vars(
        client_vars,
        "page_1",
        ConversionOptions(expand_sheet=expand_sheet),
    )

    assert expanded_tokens == ["shtr_fixture_sheet1"]
    assert result.markdown == (
        "[sheet token=shtr_fixture_sheet1]\n"
        "[sheet-meta workbook_token=shtr_fixture sheet_id=sheet1 rows=1 cols=2]\n"
        "Name\tValue\n"
    )
    assert result.counts == Counter({"page": 1, "sheet": 1})
    assert result.warnings == []


def test_convert_docx_client_vars_preserves_resource_markers() -> None:
    client_vars = {
        "block_map": {
            "page_1": {
                "data": {
                    "type": "page",
                    "children": ["table_1", "image_1", "mindnote_1"],
                }
            },
            "table_1": {"data": {"type": "table", "parent_id": "page_1"}},
            "image_1": {"data": {"type": "image", "parent_id": "page_1"}},
            "mindnote_1": {"data": {"type": "mindnote", "parent_id": "page_1"}},
        }
    }

    result = convert_docx_client_vars(client_vars, "page_1")

    assert result.markdown == "[table]\n\n[image]\n\n[mindnote]\n"
    assert result.counts == Counter({"page": 1, "table": 1, "image": 1, "mindnote": 1})
    assert result.warnings == []


def test_convert_docx_client_vars_numbers_ordered_siblings() -> None:
    client_vars = {
        "block_map": {
            "page_1": {
                "data": {
                    "type": "page",
                    "children": ["ordered_1", "ordered_2"],
                }
            },
            "ordered_1": {
                "data": {
                    "type": "ordered",
                    "parent_id": "page_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "First"}}},
                }
            },
            "ordered_2": {
                "data": {
                    "type": "ordered",
                    "parent_id": "page_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "Second"}}},
                }
            },
        }
    }

    result = convert_docx_client_vars(client_vars, "page_1")

    assert result.markdown == "1. First\n\n2. Second\n"
    assert result.counts == Counter({"page": 1, "ordered": 2})
    assert result.warnings == []


def test_convert_docx_client_vars_preserves_callout_marker() -> None:
    client_vars = {
        "block_map": {
            "page_1": {"data": {"type": "page", "children": ["callout_1"]}},
            "callout_1": {
                "data": {
                    "type": "callout",
                    "parent_id": "page_1",
                    "children": ["text_1"],
                }
            },
            "text_1": {
                "data": {
                    "type": "text",
                    "parent_id": "callout_1",
                    "text": {"initialAttributedTexts": {"text": {"0": "Important note"}}},
                }
            },
        }
    }

    result = convert_docx_client_vars(client_vars, "page_1")

    assert result.markdown == "[callout]\n\nImportant note\n"
    assert result.counts == Counter({"page": 1, "callout": 1, "text": 1})
    assert result.warnings == []


def test_convert_docx_client_vars_preserves_empty_quote_marker() -> None:
    client_vars = {
        "block_map": {
            "page_1": {"data": {"type": "page", "children": ["quote_1"]}},
            "quote_1": {
                "data": {
                    "type": "quote_container",
                    "parent_id": "page_1",
                    "children": [],
                }
            },
        }
    }

    result = convert_docx_client_vars(client_vars, "page_1")

    assert result.markdown == ">\n"
    assert result.counts == Counter({"page": 1, "quote_container": 1})
    assert result.warnings == []
