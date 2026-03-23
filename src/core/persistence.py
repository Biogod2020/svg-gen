"""
Persistence & Profile Management
Simplified for the SVG Optimization Lab.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
from .types import AgentState, AssetEntry, AssetSource, AssetVQAStatus


@dataclass
class UARCheckpoint:
    """Stores asset snapshots and VQA status."""
    assets: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class PhysicalContextManager:
    """Manages workspace artifacts (SVG files, PNG renders, logs)."""
    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.artifacts_dir = self.workspace_path / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_artifact(self, category: str, filename: str, content: str) -> Path:
        category_dir = self.artifacts_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = category_dir / filename
        artifact_path.write_text(content, encoding="utf-8")
        return artifact_path


class AssetService:
    """Tracking asset generation history."""
    def __init__(self):
        self.history = []

    def record_generation(self, asset_id: str, success: bool, metadata: dict):
        self.history.append({
            "asset_id": asset_id,
            "success": success,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        })
