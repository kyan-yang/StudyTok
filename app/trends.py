"""
Manages the catalog of Gen‑Z trend templates.

New trends are added manually by dropping a JSON file in /assets/templates.
Each template defines:
    • name              – human‑readable title
    • description       – short explanation shown in the UI
    • system_prompt     – priming text injected into the LLM
    • style_directives  – dict of style flags (subtitles, bg_gameplay, etc.)
"""
from pathlib import Path
import json
from typing import Dict, List

_TEMPLATE_DIR = Path(__file__).parent.parent / "assets" / "templates"

class TrendTemplate(dict):
    """Typed dict wrapper so IDEs give autocompletion."""
    name: str
    description: str
    system_prompt: str
    style_directives: Dict[str, str]

def _load_template(path: Path) -> TrendTemplate:
    with open(path, "r", encoding="utf‑8") as f:
        return TrendTemplate(json.load(f))

def list_trends() -> List[TrendTemplate]:
    """Return all available trend templates, sorted by filename."""
    return sorted(
        (_load_template(p) for p in _TEMPLATE_DIR.glob("*.json")),
        key=lambda t: t["name"].lower(),
    )
