# ui/frontend.py  ──  50 clean lines
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import list_trends, parse_material, generate_scripts, build_reels

import streamlit as st
from pathlib import Path
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="StudyTok", layout="centered")
st.title("📚➡️🎞️  StudyTok")

# 1 ── upload
uploaded = st.file_uploader(
    "Upload study material (PDF or .txt)", type=["pdf", "txt"]
)

# 2 ── trend dropdown (always visible once templates exist)
templates = list_trends()
trend_names = [t["name"] for t in templates]

if not trend_names:          # guard in case folder is empty
    st.warning(
        "No trend templates found in  assets/templates  — "
        "add a *.json file and restart."
    )
    st.stop()

choice = st.selectbox("Choose a social media video style", trend_names)

# 3 ── generate reels

# ── New section: choose live vs. canned scripts ──────────────
st.subheader("Generation mode")
use_canned = st.checkbox("Use pre‑generated script(s) instead of calling Groq")

canned_file = None
if use_canned:
    canned_file = st.file_uploader(
        "Upload script list (.txt = one script per line, or .json array)",
        type=["txt", "json"],
        key="canned",
    )

# ── Trigger button ───────────────────────────────────────────
if uploaded and st.button("Generate Reels"):
    # 1.  Material → chunks (always needed for filenames / reel count)
    with st.spinner("Parsing material…"):
        tmp = NamedTemporaryFile(delete=False,
                                  suffix=Path(uploaded.name).suffix)
        tmp.write(uploaded.getvalue()); tmp.close()
        chunks = parse_material(Path(tmp.name))

    # 2.  Either load canned scripts or call Groq
    if use_canned and canned_file is not None:
        st.info("Using pre‑generated script(s)…")
        data = canned_file.getvalue().decode("utf‑8")
        if canned_file.name.endswith(".json"):
            import json
            scripts = json.loads(data)
        else:  # .txt
            scripts = [line.strip() for line in data.splitlines() if line.strip()]
        # Pad / truncate to match chunk count
        scripts = (scripts + ["(empty)"] * len(chunks))[: len(chunks)]
    else:
        st.info("✍️  Writing AI-powered scripts with Groq…")
        trend = next(t for t in templates if t["name"] == choice)
        scripts = generate_scripts(chunks, trend)

    print(scripts)
    # 3.  Render
    st.info("🎞️  Rendering video…")
    trend = next(t for t in templates if t["name"] == choice)
    reels = build_reels(scripts, trend)
    st.success("Enjoy scrolling!")
    for reel in reels:
        st.video(str(reel), format="video/mp4", start_time=0) # change height


# if uploaded and st.button("Generate Reels"):
#     st.info("⏳  Parsing material…")
#     tmp = NamedTemporaryFile(delete=False,
#                               suffix=Path(uploaded.name).suffix)
#     tmp.write(uploaded.getvalue())
#     tmp.close()
#     chunks = parse_material(Path(tmp.name))

#     trend = next(t for t in templates if t["name"] == choice)

#     st.info("✍️  Writing scripts…")
#     scripts = generate_scripts(chunks, trend)

#     st.info("🎞️  Rendering video… this can take a minute")
#     reels = build_reels(scripts, trend)

#     st.success("Done!  Scroll through your reels:")
#     for reel in reels:
#         st.video(str(reel))
