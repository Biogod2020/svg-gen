"""
SVG Optimization Lab - Core Types
Streamlined for the Generate-Audit-Repair lifecycle.
"""

from typing import Optional, Literal, Any, Union, List
from enum import Enum
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from datetime import datetime
from pathlib import Path
import os
import json

from .path_utils import calculate_sha256, resolve_cas_path, get_project_root


# ============================================================================
# Core Asset Enums
# ============================================================================

class AssetSource(str, Enum):
    USER = "USER"
    AI = "AI"
    WEB = "WEB"


class AssetVQAStatus(str, Enum):
    PENDING = "PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class AssetQualityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNASSESSED = "UNASSESSED"


# ============================================================================
# Preflight & Audit Models
# ============================================================================

class AuditIssue(BaseModel):
    """Spatial audit issue with optional bounding box."""
    description: str
    box: Optional[List[float]] = Field(default=None, description="[ymin, xmin, ymax, xmax] normalized 0-1000")
    severity: Literal["low", "medium", "high"] = "medium"


class AuditResult(BaseModel):
    """Comprehensive audit result for an iteration."""
    status: AssetVQAStatus
    score: float
    issues: List[AuditIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    summary: str = ""
    thought: Optional[str] = None


class AuditCriterion(BaseModel):
    name: str
    weight: float = Field(..., description="Weight of this criterion (0-60)")
    check: str = Field(..., description="Specific validation check instruction")


class PreflightBlueprint(BaseModel):
    refined_task_directive: str
    specific_style_hints: str
    dynamic_audit_checkpoints: List[AuditCriterion]
    version: str = "2.0"

    @model_validator(mode='after')
    def normalize_weights(self) -> 'PreflightBlueprint':
        total = sum(c.weight for c in self.dynamic_audit_checkpoints)
        if total > 0:
            for c in self.dynamic_audit_checkpoints:
                c.weight = (c.weight / total) * 60.0
        return self


# ============================================================================
# Asset Models
# ============================================================================

class CropMetadata(BaseModel):
    """Visual metadata for rendering/displaying the asset."""
    left: str = Field(default="50%")
    top: str = Field(default="50%")
    zoom: float = Field(default=1.0)
    width: Optional[int] = None
    height: Optional[int] = None
    object_fit: Literal["cover", "contain", "fill"] = "contain"


class AssetEntry(BaseModel):
    """
    Unified Asset Entry (UAR)
    Records physical location, semantic metadata, and VQA audit results.
    """
    id: str
    source: AssetSource
    local_path: str
    semantic_label: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    content_hash: Optional[str] = None
    
    # Audit & Quality
    vqa_status: AssetVQAStatus = AssetVQAStatus.PENDING
    quality_level: AssetQualityLevel = AssetQualityLevel.UNASSESSED
    quality_notes: Optional[str] = None
    latest_audit: Optional[AuditResult] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Display
    crop_metadata: CropMetadata = Field(default_factory=CropMetadata)
    tags: list[str] = Field(default_factory=list)

    def to_img_tag(self, workspace_path: Optional[Union[str, Path]] = None) -> str:
        """Simple img tag generation for laboratory preview."""
        src = self.local_path
        alt = self.alt_text or self.semantic_label
        return f'<img src="{src}" alt="{alt}" data-asset-id="{self.id}">'

    def get_absolute_path(self, workspace_path: Union[str, Path]) -> Path:
        return Path(workspace_path) / self.local_path


class UniversalAssetRegistry(BaseModel):
    """
    Universal Asset Registry (UAR)
    The central authority for asset management, deduplication, and persistence.
    """
    assets: dict[str, AssetEntry] = Field(default_factory=dict)
    persist_path: Optional[str] = None

    @classmethod
    def load_from_file(cls, path: str) -> "UniversalAssetRegistry":
        p = Path(path)
        if not p.exists():
            return cls(persist_path=path)
        
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(assets=data.get("assets", {}), persist_path=path)
        except Exception as e:
            print(f"  [UAR] Load failed: {e}")
            return cls(persist_path=path)

    def _persist(self) -> None:
        if not self.persist_path:
            return
        try:
            path = Path(self.persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.model_dump_json(indent=2))
        except Exception as e:
            print(f"  [UAR] Persist failed: {e}")

    def add_asset_atomic(self, asset_id: str, content: bytes, source: AssetSource, semantic_label: str, **kwargs) -> AssetEntry:
        """
        Atomic asset registration with Content-Addressable Storage (CAS).
        """
        asset_hash = calculate_sha256(content)
        workspace_root = Path(self.persist_path).parent if self.persist_path else get_project_root()
        cas_base = workspace_root / "assets" / "cas"
        cas_path = resolve_cas_path(asset_hash, str(cas_base))
        
        cas_path.parent.mkdir(parents=True, exist_ok=True)
        if not cas_path.exists():
            with open(cas_path, "wb") as f:
                f.write(content)
            
        try:
            local_path = str(cas_path.relative_to(workspace_root))
        except ValueError:
            local_path = str(cas_path)
            
        entry = AssetEntry(
            id=asset_id,
            source=source,
            semantic_label=semantic_label,
            local_path=local_path,
            content_hash=asset_hash,
            **kwargs
        )
        self.assets[asset_id] = entry
        self._persist()
        return entry


# ============================================================================
# Minimal Agent State
# ============================================================================

class AgentState(BaseModel):
    """Simplified State for SVG Optimization Lab."""
    job_id: str
    workspace_path: str
    
    # Core components
    asset_registry: Optional[UniversalAssetRegistry] = Field(default=None, exclude=True)
    uar_path: Optional[str] = None
    
    # Telemetry
    thoughts: str = ""
    errors: list[str] = Field(default_factory=list)
    
    # Internal context manager
    _pcm: Optional[Any] = PrivateAttr(default=None)

    def initialize_uar(self) -> UniversalAssetRegistry:
        if self.asset_registry is not None:
            return self.asset_registry
        if not self.uar_path:
            self.uar_path = f"{self.workspace_path}/assets.json"
        self.asset_registry = UniversalAssetRegistry.load_from_file(self.uar_path)
        return self.asset_registry

    def get_uar(self) -> UniversalAssetRegistry:
        return self.initialize_uar()
