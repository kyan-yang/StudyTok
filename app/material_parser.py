"""
Parses user‑supplied study material (PDF or plain text) into
roughly 20‑second 'nuggets' so each reel is digestible.

Heavy lifting is isolated here to keep `main.py` clean.
"""
from pathlib import Path
from typing import List

from pypdf import PdfReader

MAX_CHARS = 1_200  # ~20 s of narration @ 150 wpm

def _pdf_to_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def parse_material(file_path: Path) -> List[str]:
    """Return a list of text chunks <= MAX_CHARS each."""
    ext = file_path.suffix.lower()
    raw_text = _pdf_to_text(file_path) if ext == ".pdf" else Path(file_path).read_text()
    # Simple greedy splitter
    chunks, buf = [], []
    for word in raw_text.split():
        buf.append(word)
        if sum(len(w) + 1 for w in buf) > MAX_CHARS:
            chunks.append(" ".join(buf[:-1]))
            buf = [word]
    if buf:
        chunks.append(" ".join(buf))
    return chunks