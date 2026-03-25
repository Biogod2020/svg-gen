import pytest
from src.core.json_utils import parse_json_dict_robust


def test_json_repair_basic():
    # Missing closing brace
    text = '{"name": "Alice", "age": 30'
    result = parse_json_dict_robust(text)
    assert result == {"name": "Alice", "age": 30}


def test_json_with_control_chars():
    # JSON with unescaped control character (newline in string)
    text = '{"thought": "Line 1\nLine 2"}'
    result = parse_json_dict_robust(text)
    # json-repair should handle this
    assert result["thought"] == "Line 1\nLine 2"


def test_json_wrapped_in_prose():
    text = 'Here is the result: ```json\n{"id": 1}\n``` and some more text.'
    result = parse_json_dict_robust(text)
    assert result == {"id": 1}
