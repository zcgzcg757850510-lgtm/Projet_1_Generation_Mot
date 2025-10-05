#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 hanzi_data_full.json 中按给定清单裁剪出子集。
输入清单支持：
  - 文本文件：每行 1 个或多个汉字
  - 逗号分隔字符串：--chars "我,你,他,日,月" 或 --chars "我你他"
"""
import json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "data" / "hanzi_data_full.json"

def load_chars(list_file=None, chars_csv=None):
    chars = []
    if list_file:
        with open(list_file, "r", encoding="utf-8") as f:
            for line in f:
                c = line.strip()
                if not c:
                    continue
                for ch in c:
                    if ch.strip():
                        chars.append(ch)
    if chars_csv:
        # 支持逗号分隔或直接字符串
        if "," in chars_csv:
            parts = chars_csv.split(",")
            for p in parts:
                for ch in p.strip():
                    if ch.strip():
                        chars.append(ch)
        else:
            for ch in chars_csv:
                if ch.strip():
                    chars.append(ch)
    seen, uniq = set(), []
    for ch in chars:
        if ch not in seen:
            seen.add(ch)
            uniq.append(ch)
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", default=str(FULL), help="合并后的全集 JSON 路径")
    ap.add_argument("--list_file", help="常用字清单文件（每行可包含多个汉字）")
    ap.add_argument("--chars", help="直接给字符（逗号分隔或直接多个字符）")
    ap.add_argument("--out", required=True, help="输出子集 JSON 路径")
    args = ap.parse_args()

    with open(args.full, "r", encoding="utf-8") as f:
        full = json.load(f)

    target = load_chars(args.list_file, args.chars)
    print(f"==> target chars: {len(target)}")

    subset = { ch: full[ch] for ch in target if ch in full }
    miss = [ch for ch in target if ch not in full]
    if miss:
        print(f"WARNING: {len(miss)} chars not found in full dataset (first 10): {''.join(miss[:10])}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(subset, f, ensure_ascii=False, separators=(",", ":"))
    print(f"==> wrote {out_path} (chars: {len(subset)})")

if __name__ == "__main__":
    main()
