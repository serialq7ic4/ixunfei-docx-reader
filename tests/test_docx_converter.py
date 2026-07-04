from collections import Counter

from ixunfei_docx_reader.converters.docx_markdown import convert_docx_client_vars


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

