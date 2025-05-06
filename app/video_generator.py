"""
SnapStudy – video_generator.py  •  ElevenLabs 2025 SDK
──────────────────────────────────────────────────────
Turns study scripts into TikTok‑style reels:

• Subway‑Surfers gameplay loop
• Cyan word‑by‑word captions centred on screen
• ElevenLabs voice‑over with precise timestamps

Setup
-----
pip install --upgrade elevenlabs moviepy pillow
set ELEVENLABS_API_KEY=sk‑xxxxxxxxxxxxxxxxxxxxxxxx
ffmpeg must be on PATH
"""

from pathlib import Path
from typing import List, Tuple
import uuid, os, base64, tempfile
import numpy as np 
import re

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
)
from PIL import Image, ImageDraw, ImageFont
from elevenlabs import ElevenLabs

# ── 1. SDK client ───────────────────────────────────────────────────────
client = ElevenLabs(api_key="sk_b667599bdfdf1b1e25db7b213c843da255caf5da9f1b9394")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"            # pick any voice
MODEL_ID = "eleven_multilingual_v2"          # supports timestamps
OUTPUT_FORMAT = "mp3_44100_128"              # MoviePy‑friendly

# ── 2. Style constants ──────────────────────────────────────────────────
FONT_PATH = "arialbd.ttf"      # any bold TTF on your system
FONT_SIZE = 36
PADDING_X, PADDING_Y = 40, 20
RADIUS = 20
CYAN = (0, 207, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
_CLAUSE_RE = re.compile(r"(.*?[,.;!?]|.+$)")

# ── 3. Gameplay loops ───────────────────────────────────────────────────
_ASSETS = Path(__file__).parent.parent / "assets" / "media"
_BG_GAMEPLAY = {
    "subway_surfer": _ASSETS / "subway_surfer_loop.mp4",
    "minecraft_parkour": _ASSETS / "parkour_loop.mp4",
}

# ─────────────────────────────────────────────────────────────────────────
# 4. TTS helper – convert text → (audio file, word‑times)
# ─────────────────────────────────────────────────────────────────────────
def _tts_with_timestamps(text: str) -> Tuple[Path, List[Tuple[float, float]]]:
    """
    Returns
    -------
    audio_path : Path to MP3 written on disk
    word_times : list[(start_sec, end_sec)] aligned with text.split()
    """
    resp = client.text_to_speech.convert_with_timestamps(
        voice_id=VOICE_ID,
        model_id=MODEL_ID,
        text=text,
        output_format=OUTPUT_FORMAT,
    )

    # 4‑a  decode audio
    audio_bytes = base64.b64decode(resp.audio_base_64)
    mp3_path = Path(f"tts_{uuid.uuid4().hex}.mp3")
    mp3_path.write_bytes(audio_bytes)

    # 4‑b  build per‑word timing from character alignment
    chars = resp.alignment.characters
    starts = resp.alignment.character_start_times_seconds
    ends = resp.alignment.character_end_times_seconds

    word_times: List[Tuple[float, float]] = []
    current_start, current_end = None, None

    for ch, st, en in zip(chars, starts, ends):
        if ch.isspace():
            if current_start is not None:
                word_times.append((current_start, current_end))
                current_start = current_end = None
        else:
            if current_start is None:
                current_start = st
            current_end = en

    # push last word
    if current_start is not None:
        word_times.append((current_start, current_end))

    return mp3_path, word_times


# ─────────────────────────────────────────────────────────────────────────
# 5. Subtitle renderer – cyan “pill” per word
# ─────────────────────────────────────────────────────────────────────────

# ── helper: break a clause into wrapped lines ────────────────────────────
MAX_RATIO = 0.80   # wrap when line > 80 % of frame width

def _wrap_clause(words, font, width):
    """
    Splits the clause into multiple lines so no line exceeds MAX_RATIO * width.
    Returns:
      lines: list of lines, each a list of words
      space_w: width of a space in pixels
    """
    space_w = font.getbbox(" ")[2]
    lines = []
    line = []
    cur_width = 0
    for w in words:
        w_w = font.getbbox(w)[2]
        # If adding this word would exceed the limit, start a new line.
        if line and (cur_width + space_w + w_w) > width * MAX_RATIO:
            lines.append(line)
            line = []
            cur_width = 0
        if line:
            cur_width += space_w
        cur_width += w_w
        line.append(w)
    if line:
        lines.append(line)
    return lines, space_w


def _render_line(words, active_idx, font, space_w):
    """
    Renders a single horizontal line of words.
    If active_idx == i, that word is in CYAN; otherwise it's WHITE w/ black stroke.
    """
    sizes = [font.getbbox(w)[2:] for w in words]
    total_w = sum(w for w, _ in sizes) + space_w * max(0, len(words) - 1)
    max_h = max(h for _, h in sizes)

    img = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    x = 0
    for i, (word, (w, h)) in enumerate(zip(words, sizes)):
        color = CYAN if i == active_idx else WHITE
        draw.text(
            (x, 0),
            word,
            font=font,
            fill=color,
            stroke_width=2,
            stroke_fill=BLACK,
        )
        x += w + space_w
    return img


def _render_wrapped_clause(words, highlight_idx, font, width):
    """
    Wraps the clause into multiple lines and renders them stacked vertically.
      - highlight_idx : index of the word to highlight (cyan) or -1/None for no highlight
    Returns a single PIL.Image with all lines (centered horizontally).
    """
    lines, space_w = _wrap_clause(words, font, width)

    # Find which line holds the highlight_idx, if any
    if highlight_idx is None:
        highlight_idx = -1
    highlight_line = -1
    highlight_in_line = -1

    if highlight_idx >= 0:
        word_counter = 0
        for line_i, lwords in enumerate(lines):
            if word_counter <= highlight_idx < word_counter + len(lwords):
                highlight_line = line_i
                highlight_in_line = highlight_idx - word_counter
                break
            word_counter += len(lwords)

    # Render each line
    line_imgs = []
    max_line_width = 0
    total_height = 0
    for line_i, lwords in enumerate(lines):
        active_idx = highlight_in_line if line_i == highlight_line else -1
        line_img = _render_line(lwords, active_idx, font, space_w)
        line_imgs.append(line_img)
        max_line_width = max(max_line_width, line_img.width)
        total_height += line_img.height

    # Stack lines vertically; center them horizontally
    final_img = Image.new("RGBA", (max_line_width, total_height), (0, 0, 0, 0))
    y = 0
    for img in line_imgs:
        final_img.paste(
            img, box=((max_line_width - img.width)//2, y), mask=img
        )
        y += img.height

    return final_img

def _render_subtitles(text: str, word_times, width):
    """
    Renders stable, wrapped subtitles. It displays the full clause in white and then overlays
    only the current word in cyan during its time slot.
    This updated version ensures that the number of words computed from the text (via clause splitting)
    matches the number of provided word_times. If not, uniform timings are used as a fallback.
    """
    # Load the desired font.
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # 1) Split text into clauses using the regex pattern.
    clauses = [m.group(0).strip() for m in _CLAUSE_RE.finditer(text)]
    # Remove any empty entries.
    clauses = [clause for clause in clauses if clause]

    # 2) Calculate the total number of words in the clauses.
    total_clause_words = sum(len(clause.split()) for clause in clauses)
    
    # If the total word count from clauses doesn't match the word_times count,
    # then fallback to uniform word timings.
    if total_clause_words != len(word_times):
        total_duration = word_times[-1][1] if word_times else 0
        spw = total_duration / total_clause_words if total_clause_words else 0
        word_times = [(i * spw, (i + 1) * spw) for i in range(total_clause_words)]
    
    # 3) Build a mapping for each word to its clause and position within that clause.
    mapping = []
    for c_idx, clause in enumerate(clauses):
        for w_idx, _ in enumerate(clause.split()):
            mapping.append((c_idx, w_idx))
    
    # 4) Assign each clause a start and end timing by consuming the word_times list in order.
    clause_times = {}
    cur_idx = 0
    for c_idx, clause in enumerate(clauses):
        cwords = clause.split()
        count = len(cwords)
        # Validate there are enough word_times remaining.
        if cur_idx + count > len(word_times):
            raise ValueError("Mismatch between clause word counts and word timings. "
                             "Check text splitting logic or TTS output.")
        c_start = word_times[cur_idx][0]
        c_end = word_times[cur_idx + count - 1][1]
        clause_times[c_idx] = (c_start, c_end)
        cur_idx += count

    # 5) Generate a base subtitle clip for each clause (with white text).
    clips = []
    for c_idx, clause in enumerate(clauses):
        start, end = clause_times[c_idx]
        base_img = _render_wrapped_clause(clause.split(), -1, font, width)
        base_clip = (
            ImageClip(np.array(base_img))
            .set_start(start)
            .set_duration(end - start)
            .set_pos(("center", "center"))
        )
        clips.append(base_clip)

    # 6) For each word, create an overlay clip highlighting that word in cyan.
    for (start, end), (c_idx, w_idx) in zip(word_times, mapping):
        clause_words = clauses[c_idx].split()
        hi_img = _render_wrapped_clause(clause_words, w_idx, font, width)
        hi_clip = (
            ImageClip(np.array(hi_img))
            .set_start(start)
            .set_duration(end - start)
            .set_pos(("center", "center"))
        )
        clips.append(hi_clip)

    # 7) Composite all clips into a final video clip.
    frame_h = int(width * 16 / 9)  # assume a 16:9 frame
    return CompositeVideoClip(clips, size=(width, frame_h))

# ─────────────────────────────────────────────────────────────────────────
# 6. Public API – build reels
# ─────────────────────────────────────────────────────────────────────────
def build_reels(scripts: List[str], trend) -> List[Path]:
    reels = []

    for idx, script in enumerate(scripts, start=1):
        # background gameplay
        bg_path = _BG_GAMEPLAY[trend["style_directives"]["bg_gameplay"]]
        bg = VideoFileClip(str(bg_path)).subclip(0, 60).without_audio()

        # voice + word‑times
        audio_path, word_times = _tts_with_timestamps(script)
        audio = AudioFileClip(str(audio_path))

        words = script.split()
        # safety fallback
        if len(word_times) != len(words):
            spw = audio.duration / len(words)
            word_times = [(i * spw, (i + 1) * spw) for i in range(len(words))]

        bg = bg.subclip(0, audio.duration)
        subs = _render_subtitles(script, word_times, width=bg.w)

        reel = CompositeVideoClip([bg, subs]).set_audio(audio)
        out_path = Path(f"reel_{idx:02d}.mp4")
        reel.write_videofile(
            str(out_path),
            codec="libx264",
            audio_codec="aac",
            fps=30,
            verbose=False,
            logger=None,
        )
        reels.append(out_path)

    return reels
