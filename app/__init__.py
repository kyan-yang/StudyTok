"""
SnapStudy package namespace.
Exposes high‑level façade functions for the UI layer.
"""

from .trends import list_trends
from .material_parser import parse_material
from .script_generator import generate_scripts
from .video_generator import build_reels

__all__ = [
    "list_trends",
    "parse_material",
    "generate_scripts",
    "build_reels",
]
