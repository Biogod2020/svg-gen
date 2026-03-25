import pytest
from src.agents.svg_generation.agent import SVGAgent


def test_validate_svg_structure_valid():
    svg = "<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='10' /></svg>"
    success, message = SVGAgent.validate_svg_structure(svg)
    assert success, f"Failed with message: {message}"
    assert "OK" in message


def test_validate_svg_structure_invalid_xml():
    svg = "<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='10' ></svg>"  # Missing closing tag
    success, message = SVGAgent.validate_svg_structure(svg)
    assert not success
    assert "XML" in message or "tag" in message


def test_validate_svg_structure_missing_viewbox():
    svg = "<svg><circle cx='50' cy='50' r='10' /></svg>"
    success, message = SVGAgent.validate_svg_structure(svg)
    assert not success
    assert "viewBox" in message
