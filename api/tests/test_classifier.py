from classifier import extract_json


def test_extract_json_strips_markdown_fences():
    raw = '```json\n{"category": "billing"}\n```'
    cleaned = extract_json(raw)
    assert cleaned == '{"category": "billing"}'


def test_extract_json_leaves_plain_json_untouched():
    raw = '{"category": "billing"}'
    cleaned = extract_json(raw)
    assert cleaned == '{"category": "billing"}'