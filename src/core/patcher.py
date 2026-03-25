"""
Universal High-Precision Patcher (SOTA 3.0)
Based on Aider's tiered matching strategies and Google's diff-match-patch.
"""

import re
import math
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from diff_match_patch import diff_match_patch


class RelativeIndenter:
    """
    Aider's stateful Relative Indenter.
    Handles outdenting using a unique marker to maintain structural integrity.
    """

    def __init__(self, texts: list[str]):
        # Choose a unicode character that isn't in any of the texts
        chars = set()
        for text in texts:
            chars.update(text)

        ARROW = "←"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars):
        for codepoint in range(0x10FFFF, 0x10000, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker
        raise ValueError("Could not find a unique marker")

    def make_relative(self, text: str) -> str:
        """Transform text to use relative indents."""
        if self.marker in text:
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)
        output = []
        prev_indent = ""
        for line in lines:
            line_without_end = line.rstrip("\n\r")
            len_indent = len(line_without_end) - len(line_without_end.lstrip())
            indent = line[:len_indent]
            change = len_indent - len(prev_indent)

            if change > 0:
                cur_indent = indent[-change:]
            elif change < 0:
                cur_indent = self.marker * -change
            else:
                cur_indent = ""

            # Standardize for relative matching: relative_indent + \n + content
            output.append(cur_indent + "\n" + line[len_indent:])
            prev_indent = indent

        return "".join(output)

    def make_absolute(self, text: str, initial_indent: str = "") -> str:
        """Transform text from relative back to absolute indents."""
        lines = text.splitlines(keepends=True)
        output = []
        prev_indent = initial_indent

        # Relative format uses 2 lines per original line (dent + content)
        for i in range(0, len(lines), 2):
            dent = lines[i].rstrip("\r\n")
            non_indent = lines[i + 1]

            if dent.startswith(self.marker):
                len_outdent = len(dent)
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent

            if not non_indent.rstrip("\r\n"):
                out_line = non_indent  # Don't indent blank lines
            else:
                out_line = cur_indent + non_indent

            output.append(out_line)
            prev_indent = cur_indent

        return "".join(output)


def parse_aider_blocks(text: str) -> List[Dict[str, str]]:
    """Standardized extraction of SEARCH/REPLACE blocks."""
    blocks = []
    pattern = re.compile(
        r"<<<<<<< SEARCH\s*(.*?)\s*=======\s*(.*?)\s*>>>>>>> REPLACE", re.DOTALL
    )
    for match in pattern.finditer(text):
        blocks.append(
            {
                "search": match.group(1).strip("\n"),
                "replace": match.group(2).strip("\n"),
            }
        )
    return blocks


def fuzzy_match_dmp(
    content: str, search_block: str, replace_block: str
) -> Optional[str]:
    """SOTA 3.0: Fuzzy matching using diff-match-patch."""
    dmp = diff_match_patch()
    # Set high thresholds for safety
    dmp.Match_Threshold = 0.5
    dmp.Match_Distance = 1000

    match_pos = dmp.match_main(content, search_block, 0)
    if match_pos != -1:
        # Check if the matched chunk is reasonably similar
        matched_chunk = content[match_pos : match_pos + len(search_block)]
        lev_dist = dmp.diff_levenshtein(dmp.diff_main(matched_chunk, search_block))
        similarity = 1 - (lev_dist / max(len(search_block), 1))

        if similarity >= 0.8:
            return (
                content[:match_pos]
                + replace_block
                + content[match_pos + len(search_block) :]
            )
    return None


def do_aider_replace(
    content: str, search_block: str, replace_block: str
) -> Optional[str]:
    """SOTA 3.0: Tiered Aider-style replacement with Relative Indentation."""
    if not search_block:
        return content + "\n" + replace_block if content else replace_block

    # Normalize line endings
    content = content.replace("\r\n", "\n")
    search_block = search_block.replace("\r\n", "\n")
    replace_block = replace_block.replace("\r\n", "\n")

    # Strategy 1: Exact Match
    if search_block in content:
        return content.replace(search_block, replace_block, 1)

    # Strategy 2: Relative Indentation Match (Aider SOTA)
    ri = RelativeIndenter([content, search_block, replace_block])
    rel_content = ri.make_relative(content)
    rel_search = ri.make_relative(search_block)
    rel_replace = ri.make_relative(replace_block)

    # In relative form, we ignore the first line's absolute indent
    # because that's where the block might be shifted.
    # We look for a match of the relative structure.
    rel_search_struct = "\n".join(rel_search.splitlines()[1:])
    rel_content_lines = rel_content.splitlines()

    # We need to find where the relative structure matches in rel_content
    search_lines_count = len(search_block.splitlines())

    for i in range(len(rel_content_lines) - (search_lines_count * 2) + 1):
        # Aider relative format is 2 lines per original line (dent + content)
        # So we check 2*N lines
        potential_match = "\n".join(
            rel_content_lines[i + 1 : i + (search_lines_count * 2)]
        )
        if potential_match == rel_search_struct:
            # Found it! Now we need to apply the replacement.
            # 1. Get the absolute indent of the first matched line in the original content
            orig_lines = content.splitlines(keepends=True)
            match_start_line_idx = i // 2
            first_line = orig_lines[match_start_line_idx]
            match = re.match(r"^(\s*)", first_line)
            initial_indent = match.group(1) if match else ""

            # 2. Make the relative replacement absolute using the correct initial indent
            absolute_replace = ri.make_absolute(
                rel_replace, initial_indent=initial_indent
            )

            # 3. Splice back into content
            return (
                "".join(orig_lines[:match_start_line_idx])
                + absolute_replace
                + "".join(orig_lines[match_start_line_idx + search_lines_count :])
            )

    # Strategy 3: Fuzzy Match (DMP)
    return fuzzy_match_dmp(content, search_block, replace_block)


def apply_smart_patch(
    content: str, search_block: str, replace_block: str
) -> Tuple[str, bool]:
    """High-level patch interface."""
    if not search_block and not replace_block:
        return content, True

    res = do_aider_replace(content, search_block, replace_block)
    if res is not None:
        return res, True

    return (
        f"PATCH_FAILED: Search block not found. Even fuzzy matching (DMP) failed to locate the code chunk.",
        False,
    )
