"""
Asset Management Utilities
Simplified for the SVG Optimization Lab.
"""

from pathlib import Path
from typing import Optional
from ...core.types import AssetEntry


def generate_figure_html(
    asset: AssetEntry,
    caption: str,
    workspace_path: Optional[Path] = None
) -> str:
    """
    Generates a simple HTML figure tag for the asset.
    """
    # SVG technical charts should use contain to avoid clipping
    if asset.local_path and asset.local_path.lower().endswith('.svg'):
        asset.crop_metadata.object_fit = "contain"

    img_tag = asset.to_img_tag(workspace_path=workspace_path)
    return f'<figure>\n{img_tag}\n<figcaption>{caption}</figcaption>\n</figure>'


def resolve_asset_path(
    asset: AssetEntry,
    workspace_path: Path
) -> Optional[Path]:
    """
    Resolves the full path of an asset.
    """
    if not asset.local_path:
        return None

    local_path = Path(asset.local_path)
    if local_path.is_absolute():
        return local_path if local_path.exists() else None

    full_path = workspace_path / local_path
    if full_path.exists():
        return full_path

    return None
