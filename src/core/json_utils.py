"""
Robust JSON Parsing Utilities

This module provides functions to robustly extract and parse JSON from LLM text responses,
handling common issues like Markdown code fences, trailing commas, and malformed strings.
"""

import json
import re
from typing import Any, Dict, List, Optional
from json_repair import repair_json


def extract_json_from_text(text: str) -> str:
    """
    Extracts the JSON-like part of the text.
    Handles markdown blocks and prose.
    """
    if not text:
        return ""

    # 1. Clean up <thought> blocks
    text = re.sub(r"<thought>[\s\S]*?</thought>", "", text).strip()

    # 2. Extract from markdown code fences
    fences = re.findall(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text, re.IGNORECASE)
    if fences:
        return fences[-1].strip()  # Take the last block

    return text.strip()


def parse_json_robust(text: str, default: Any = None) -> Any:
    """
    SOTA 3.0: Robust JSON parsing using json-repair.
    Handles truncated JSON, unescaped control characters, and malformed structures.
    """
    if not text:
        return default

    clean_text = extract_json_from_text(text)

    try:
        # return_objects=True returns a Python object directly
        # ensure_ascii=False preserves CJK and other non-latin chars
        # skip_json_loads=True speeds up when we know it might be broken
        return repair_json(clean_text, return_objects=True, ensure_ascii=False)
    except Exception as e:
        print(f"[JSON Parser] Critical failure: {e}")
        return default


def parse_json_list_robust(text: str) -> List[Dict]:
    result = parse_json_robust(text, default=[])
    return result if isinstance(result, list) else []


def parse_json_dict_robust(text: str) -> Dict:
    result = parse_json_robust(text, default={})
    return result if isinstance(result, dict) else {}
