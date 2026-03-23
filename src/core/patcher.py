"""
Universal High-Precision Patcher
Refined based on gemini-cli and aider matching strategies.
"""

import re
import math
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from difflib import SequenceMatcher

class StuckDetector:
    """
    Detects if a QA loop is stuck by tracking progress.
    """
    def __init__(self):
        self.last_hashes = {} # advice_id -> last_content_hash

    def _get_hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def check_progress(self, advice_id: str, current_content: str) -> bool:
        """
        Returns True if progress is being made (content changed since last time for this advice).
        Returns False if we are repeating the same advice on the same content.
        """
        c_hash = self._get_hash(current_content)
        
        if advice_id not in self.last_hashes:
            self.last_hashes[advice_id] = c_hash
            return True
            
        if self.last_hashes[advice_id] == c_hash:
            return False # STUCK
            
        self.last_hashes[advice_id] = c_hash
        return True

def parse_aider_blocks(text: str) -> List[Dict[str, str]]:
    """
    Standardized extraction of SEARCH/REPLACE blocks from LLM responses.
    Handles multiple blocks and ignores surrounding text/noise.
    """
    blocks = []
    # Pattern to match: <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE
    pattern = re.compile(
        r'<<<<<<< SEARCH\s*(.*?)\s*=======\s*(.*?)\s*>>>>>>> REPLACE', 
        re.DOTALL
    )
    
    for match in pattern.finditer(text):
        blocks.append({
            "search": match.group(1),
            "replace": match.group(2)
        })
    return blocks

def do_aider_replace(content: str, search_block: str, replace_block: str) -> Optional[str]:
    """
    Core Aider-style block replacement algorithm.
    Ported and simplified from aider.coders.editblock_coder.
    """
    if not search_block:
        # If SEARCH is empty, it's an append or new file operation
        return content + "\n" + replace_block if content else replace_block

    # Standardize line endings for internal processing
    content = content.replace('\r\n', '\n')
    search_block = search_block.replace('\r\n', '\n')
    replace_block = replace_block.replace('\r\n', '\n')

    # 1. Try Exact Match
    if search_block in content:
        return content.replace(search_block, replace_block, 1)

    # 2. Try match after stripping leading/trailing whitespace from each line
    whole_lines = content.splitlines(keepends=True)
    part_lines = search_block.splitlines(keepends=True)
    replace_lines = replace_block.splitlines(keepends=True)

    res = replace_part_with_missing_leading_whitespace(whole_lines, part_lines, replace_lines)
    if res:
        return res

    # 3. Last resort: Fuzzy matching based on edit distance
    res = replace_closest_edit_distance(whole_lines, search_block, part_lines, replace_lines)
    if res:
        return res

    return None

def replace_part_with_missing_leading_whitespace(whole_lines, part_lines, replace_lines):
    num_part_lines = len(part_lines)
    if num_part_lines == 0: return None

    for i in range(len(whole_lines) - num_part_lines + 1):
        target_chunk = whole_lines[i : i + num_part_lines]
        
        # Check if non-whitespace characters match exactly
        if all(t.strip() == p.strip() for t, p in zip(target_chunk, part_lines)):
            # Try to preserve the indentation of the target
            match = re.match(r"^(\s*)", target_chunk[0])
            target_indent = match.group(1) if match else ""
            
            # Simple re-indentation of replace lines
            new_replace = []
            for r in replace_lines:
                if r.strip():
                    new_replace.append(target_indent + r.lstrip())
                else:
                    new_replace.append("\n") # Keep empty lines clean
            
            return "".join(whole_lines[:i] + new_replace + whole_lines[i + num_part_lines :])
    return None

def replace_closest_edit_distance(whole_lines, part, part_lines, replace_lines):
    similarity_thresh = 0.8
    max_similarity = 0
    best_range = None

    # Look for a chunk of similar length (within 20% range)
    scale = 0.2
    num_part_lines = len(part_lines)
    min_len = math.floor(num_part_lines * (1 - scale))
    max_len = math.ceil(num_part_lines * (1 + scale))

    for length in range(max(1, min_len), max_len + 1):
        for i in range(len(whole_lines) - length + 1):
            chunk = "".join(whole_lines[i : i + length])
            similarity = SequenceMatcher(None, chunk, part).ratio()

            if similarity > max_similarity:
                max_similarity = similarity
                best_range = (i, i + length)

    if max_similarity >= similarity_thresh and best_range:
        i, j = best_range
        return "".join(whole_lines[:i] + replace_lines + whole_lines[j:])
    
    return None

def apply_smart_patch(content: str, search_block: str, replace_block: str) -> Tuple[str, bool]:
    """Tiered patching strategy: Aider Core (Exact -> Whitespace -> Fuzzy)"""
    if not search_block and not replace_block:
        return content, True

    # 执行 Aider 风格的高级物理替换
    res = do_aider_replace(content, search_block, replace_block)
    if res is not None:
        return res, True

    return f"PATCH_FAILED: Search block not found in the target content. Similarity score was too low.", False
