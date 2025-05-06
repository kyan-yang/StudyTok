"""
Batch mode: run `python main.py path/to/file.pdf --trend "Reddit Storytime + Subway Surfers"`
to spit out one or more MP4s in the current directory.
"""
import argparse
from pathlib import Path
from app import list_trends, parse_material, generate_scripts, build_reels

def _choose_trend(name: str):
    for t in list_trends():
        if t["name"].lower() == name.lower():
            return t
    raise SystemExit(f"Trend '{name}' not found. Run without --trend to list.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", type=Path, help="Study material (PDF or .txt)")
    p.add_argument("--trend", help="Exact trend name to apply")
    args = p.parse_args()

    if not args.trend:
        print("Available trends:")
        for t in list_trends():
            print(" •", t["name"])
        return

    trend = _choose_trend(args.trend)
    chunks = parse_material(args.file)
    scripts = generate_scripts(chunks, trend)
    build_reels(scripts, trend)

if __name__ == "__main__":
    main()
