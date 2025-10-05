#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 fontTools 从本地字体 (Source Sans Pro) 提取少量代表字符，
快速生成 data/alphanumeric_medians_fonttools.json 供预览对比。
"""

import os
import json
from typing import List, Tuple

FONT_PATH = 'fonts/SourceSansPro-Regular.ttf'


def extract_glyph_outline(font_path: str, char: str):
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.recordingPen import RecordingPen
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        if ord(char) not in cmap:
            font.close()
            return None, None
        glyph_name = cmap[ord(char)]
        glyph_set = font.getGlyphSet()
        if glyph_name not in glyph_set:
            font.close()
            return None, None
        pen = RecordingPen()
        glyph_set[glyph_name].draw(pen)
        units_per_em = font['head'].unitsPerEm
        font.close()
        return pen.value, units_per_em
    except Exception:
        return None, None


def outline_to_medians(outline, scale: float) -> List[List[List[int]]]:
    if not outline:
        return []
    medians: List[List[List[int]]] = []
    current: List[List[int]] = []
    for cmd, args in outline:
        if cmd == 'moveTo':
            if current and len(current) >= 2:
                medians.append(current)
            current = [[int(args[0][0] * scale), int(args[0][1] * scale)]]
        elif cmd == 'lineTo':
            current.append([int(args[0][0] * scale), int(args[0][1] * scale)])
        elif cmd in ('curveTo', 'qCurveTo'):
            for pt in args:
                current.append([int(pt[0] * scale), int(pt[1] * scale)])
        elif cmd == 'closePath':
            if current and len(current) >= 2:
                if current[0] != current[-1]:
                    current.append(current[0])
                medians.append(current)
            current = []
    if current and len(current) >= 2:
        medians.append(current)
    return medians


def normalize_to_mmh(medians: List[List[List[int]]]) -> List[List[List[int]]]:
    if not medians:
        return medians
    pts: List[Tuple[int, int]] = []
    for s in medians:
        pts.extend((x, y) for x, y in s)
    if not pts:
        return medians
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max(1, max_x - min_x)
    h = max(1, max_y - min_y)
    # 保持比例，目标框 ~600 并居中到 (512,388)
    target = 600.0
    scale = min(target / w, target / h) * 0.8
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    out: List[List[List[int]]] = []
    for stroke in medians:
        ns: List[List[int]] = []
        for x, y in stroke:
            X = (x - cx) * scale + 512.0
            Y = 900.0 - ((y - cy) * scale + 388.0)
            ns.append([int(X), int(Y)])
        out.append(ns)
    return out


def main() -> int:
    if not os.path.exists(FONT_PATH):
        print(f"❌ 字体不存在: {FONT_PATH}")
        return 1
    subset = ['A', 'M', 'W', 'a', 'g', 'o', '0', '1', '2']
    data = {}
    for ch in subset:
        outline, upm = extract_glyph_outline(FONT_PATH, ch)
        if not outline or not upm:
            print(f"⚠️  跳过 {ch}: 无轮廓")
            continue
        med = outline_to_medians(outline, scale=1000.0 / float(upm))
        if not med:
            print(f"⚠️  跳过 {ch}: 无路径")
            continue
        med = normalize_to_mmh(med)
        t = 'digit' if ch.isdigit() else ('uppercase' if ch.isupper() else 'lowercase')
        data[ch] = {
            "character": ch,
            "medians": med,
            "strokes": len(med),
            "type": t,
            "source": "source_sans_pro_fonttools_subset",
            "license": "OFL",
            "coordinate_system": "MMH",
            "extraction_method": "fonttools_outline_subset"
        }
        print(f"✅ {ch}: {len(med)} 笔画")

    out = 'data/alphanumeric_medians_fonttools.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {out} ({len(data)} 个字符)")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())


