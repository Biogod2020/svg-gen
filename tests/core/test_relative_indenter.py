import pytest
from src.core.patcher import RelativeIndenter


def test_relative_indenter_basic():
    # Original nested code
    original = "    def foo():\n        return 1"

    # Block from LLM (potentially 0-indented)
    block = "def foo():\n    return 1"

    ri = RelativeIndenter([original, block])

    rel_original = ri.make_relative(original)
    rel_block = ri.make_relative(block)

    # Extract structural parts (ignoring the absolute indent of the first line)
    # The first 'dent' in relative form is the absolute indent of the first line.
    struct_original = "\n".join(rel_original.splitlines()[1:])
    struct_block = "\n".join(rel_block.splitlines()[1:])

    assert struct_original == struct_block


def test_relative_indenter_outdent():
    text = "    if True:\n        print(1)\n    print(2)"
    ri = RelativeIndenter([text])

    rel = ri.make_relative(text)
    # Check for presence of the marker (default ←)
    assert "←" in rel

    # Verify round-trip
    abs_text = ri.make_absolute(rel)
    assert abs_text == text
