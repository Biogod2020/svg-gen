import pytest
from src.core.patcher import apply_smart_patch


def test_apply_smart_patch_indent_shift():
    content = '    <g>\n        <circle cx="10" cy="10" r="5" />\n    </g>'

    # LLM returns 0-indented block
    search = '<circle cx="10" cy="10" r="5" />'
    replace = '<circle cx="20" cy="20" r="10" />'

    new_content, success = apply_smart_patch(content, search, replace)

    assert success
    # Should preserve original indentation
    assert '        <circle cx="20" cy="20" r="10" />' in new_content


def test_apply_smart_patch_fuzzy():
    content = '<svg>\n  <path d="M10 10 L20 20" stroke="black" />\n</svg>'

    # LLM makes a minor typo in SEARCH (e.g. missing a space)
    search = '<path d="M10 10L20 20" stroke="black" />'
    replace = '<path d="M10 10 L30 30" stroke="red" />'

    new_content, success = apply_smart_patch(content, search, replace)

    assert success
    assert 'stroke="red"' in new_content

def test_apply_smart_patch_complex_indent():
    content = """
    <g>
        <rect x="0" y="0" />
        <g transform="scale(2)">
            <circle cx="5" cy="5" />
        </g>
    </g>
    """
    
    # LLM returns a block with different absolute indents but SAME relative indents
    search = """
<rect x="0" y="0" />
<g transform="scale(2)">
    <circle cx="5" cy="5" />
</g>
    """.strip()
    
    replace = """
<rect x="10" y="10" />
<g transform="scale(3)">
    <circle cx="5" cy="5" />
</g>
    """.strip()
    
    new_content, success = apply_smart_patch(content, search, replace)
    
    assert success
    assert 'transform="scale(3)"' in new_content
    # Check if nested circle's relative indent was preserved
    assert '            <circle cx="5" cy="5" />' in new_content
