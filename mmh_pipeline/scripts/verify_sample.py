#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, argparse
from pathlib import Path
from PIL import Image, ImageDraw


def render_char(ch_meta, size=512, margin=40):
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)
    W = H = size - 2 * margin

    def map_pt(x, y):
        return (margin + x / 1024.0 * W, margin + y / 1024.0 * H)

    for stroke in ch_meta.get("medians", []):
        for i in range(1, len(stroke)):
            p0 = map_pt(*stroke[i - 1])
            p1 = map_pt(*stroke[i])
            d.line([p0, p1], fill=0, width=4)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="hanzi_data_*.json")
    ap.add_argument("--chars", default="日日月明", help="要检查的字符（连续字符串）")
    ap.add_argument("--outdir", default="output/sanity_samples")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    data = json.load(open(args.data, "r", encoding="utf-8"))
    outdir = root / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    for ch in args.chars:
        if ch not in data:
            print(f"[MISS] {ch} not in dataset")
            continue
        img = render_char(data[ch], size=512)
        dst = outdir / f"{ch}.png"
        img.save(dst)
        print(f"[OK] {ch} -> {dst}")


if __name__ == "__main__":
    main()
