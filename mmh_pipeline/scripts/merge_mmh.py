#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 Make Me a Hanzi 的数据合并成一个便于查询的大 JSON：
  - 首选：解析 mmh_pipeline/data/mmh_raw/graphics.txt（逐行 JSON，含 character/strokes/medians）
  - 回退：旧结构 data/*.json + graphics/*.svg
  - 输出：mmh_pipeline/data/hanzi_data_full.json
"""
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "mmh_raw"
OUT = ROOT / "data" / "hanzi_data_full.json"


def load_entries_from_graphics_txt():
    entries = {}
    gtxt = RAW / "graphics.txt"
    if not gtxt.exists():
        return entries
    with open(gtxt, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # 非法行忽略
                continue
            ch = obj.get("character")
            if not ch or not isinstance(ch, str):
                continue
            entries[ch] = {
                "character": ch,
                "strokes": obj.get("strokes", []),
                "medians": obj.get("medians", []),
                # 可选附加信息
                "radical": obj.get("radical"),
                "structure": obj.get("structure"),
            }
    return entries


def load_entries_from_legacy_dirs():
    # 兼容旧仓库结构：data/*.json + graphics/*.svg
    data_dir = RAW / "data"
    graphics_dir = RAW / "graphics"
    entries = {}
    if data_dir.exists():
        for p in sorted(data_dir.glob("*.json")):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    ch = obj.get("character")
                    if not ch:
                        continue
                    entries[ch] = {
                        "character": ch,
                        "strokes": obj.get("strokes", []),
                        "medians": obj.get("medians", []),
                        "radical": obj.get("radical"),
                        "structure": obj.get("structure"),
                    }
    # 可选：附上 SVG 文本
    if graphics_dir.exists():
        for svg in sorted(graphics_dir.glob("*.svg")):
            name = svg.stem
            try:
                text = svg.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            m = re.search(r'unicode="(.?)"', text)
            if m:
                ch = m.group(1)
            else:
                ch = name if len(name) == 1 else None
            if ch and ch in entries:
                entries[ch]["svg"] = text
    return entries


def main():
    if not RAW.exists():
        print("ERROR: raw repo not found. Run scripts/get_mmh.sh (or get_mmh.ps1) first.", file=sys.stderr)
        sys.exit(1)

    print("==> Loading from graphics.txt ...")
    entries = load_entries_from_graphics_txt()
    print(f"    entries: {len(entries)}")

    if not entries:
        print("==> Fallback to legacy directories ...")
        entries = load_entries_from_legacy_dirs()
        print(f"    entries(legacy): {len(entries)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))
    print(f"==> Wrote {OUT} (chars: {len(entries)})")


if __name__ == "__main__":
    main()
