#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate side-by-side previews to visually compare candidate datasets for
alphanumeric (A-Z, a-z, 0-9) and punctuation.

Outputs SVGs and a single HTML index for quick judgment.
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.parser import normalize_medians_1024
from src.classifier import classify_glyph
from src.styler import load_style, build_rng, sample_hierarchical_style
from src.centerline import CenterlineProcessor
from src.transformer import transform_medians
from src.renderer import SvgRenderer


Point = Tuple[float, float]


def find_alnum_candidates() -> Dict[str, Path]:
    """Discover available alphanumeric dataset candidates in data/.

    Returns a mapping of human-readable label -> file path.
    """
    data_dir = ROOT / "data"
    candidates: Dict[str, Path] = {}

    # 精简展示，仅保留：Current、CamBam、FontTools 子集
    known: List[Tuple[str, str]] = [
        ("Current", "alphanumeric_medians.json"),
        ("CamBam", "alphanumeric_medians_cambam.json"),
        ("FontTools", "alphanumeric_medians_fonttools.json"),
    ]

    for label, fname in known:
        f = data_dir / fname
        if f.exists():
            candidates[label] = f

    return candidates


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Failed to load {path}: {e}")
        return None


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def render_char_svg(
    char: str,
    glyph: Dict[str, Any],
    style_json: Dict[str, Any],
    out_file: Path,
) -> bool:
    """Render a single character median pipeline to SVG.

    Returns True if success, False otherwise.
    """
    try:
        med_raw: List[List[Point]] = glyph.get("medians", [])  # type: ignore
        if not med_raw:
            return False

        med = normalize_medians_1024(med_raw)

        labels = classify_glyph(med)
        rng = build_rng(42)
        sampled: List[Dict[str, Any]] = []
        for lb in labels:
            sampled.append(
                sample_hierarchical_style(
                    style_json.get("global", {}),
                    style_json.get("stroke_types", {}),
                    lb,
                    rng,
                    rng,
                    rng,
                    style_json.get("coherence", {}),
                )
            )

        proc = CenterlineProcessor(style_json, seed=42)
        med_processed = proc.process(med)

        rep_style = sampled[0] if sampled else style_json.get("global", {})
        med_transformed = transform_medians(med_processed, rep_style)

        renderer = SvgRenderer(size_px=256, padding=8)
        renderer.render_char(
            med_transformed,
            sampled if sampled else [style_json.get("global", {}) for _ in med_transformed],
            str(out_file),
            render_mode="median_stroke",
        )
        return True
    except Exception as e:
        print(f"❌ Render {char} failed: {e}")
        return False


def generate_alnum_previews(
    candidates: Dict[str, Path],
    chars: List[str],
    out_dir: Path,
    style_path: Path,
) -> Dict[str, Dict[str, Optional[Path]]]:
    """Render selected alphanumeric chars for each candidate dataset.

    Returns mapping: dataset_label -> { char -> svg_path or None }
    """
    ensure_dir(out_dir)
    style_json = load_style(str(style_path))
    results: Dict[str, Dict[str, Optional[Path]]] = {}

    for label, path in candidates.items():
        print(f"\n== Alphanumeric: {label} ==")
        data = load_json(path)
        if not data:
            print("  ⚠️  skip: cannot load data")
            continue

        sub = out_dir / label.replace(" ", "_")
        ensure_dir(sub)

        per_char: Dict[str, Optional[Path]] = {}
        for ch in chars:
            meta = data.get(ch)
            if not meta:
                per_char[ch] = None
                print(f"  - {ch}: missing")
                continue
            out_file = sub / f"{ch}.svg"
            ok = render_char_svg(ch, meta, style_json, out_file)
            per_char[ch] = out_file if ok else None
            print(f"  - {ch}: {'ok' if ok else 'fail'}")
        results[label] = per_char

    return results


def generate_punct_previews(
    punct_path: Path,
    chars: List[str],
    out_dir: Path,
    style_path: Path,
) -> Dict[str, Optional[Path]]:
    """Render punctuation chars using punctuation dataset.
    Returns mapping: char -> svg_path or None
    """
    ensure_dir(out_dir)
    data = load_json(punct_path)
    if not data:
        print(f"⚠️  punctuation: cannot load {punct_path}")
        return {}

    style_json = load_style(str(style_path))
    results: Dict[str, Optional[Path]] = {}
    for ch in chars:
        meta = data.get(ch)
        if not meta:
            results[ch] = None
            print(f"  - {ch}: missing")
            continue
        # Windows-safe filename: use only codepoint hex
        out_file = out_dir / f"{ord(ch):04x}.svg"
        ok = render_char_svg(ch, meta, style_json, out_file)
        results[ch] = out_file if ok else None
        print(f"  - {ch}: {'ok' if ok else 'fail'}")
    return results


def build_index_html(
    alnum_results: Dict[str, Dict[str, Optional[Path]]],
    alnum_chars: List[str],
    punct_results: Dict[str, Optional[Path]],
    punct_chars: List[str],
    out_file: Path,
) -> None:
    lines: List[str] = []
    lines.append("<!doctype html>")
    lines.append("<meta charset='utf-8'>")
    lines.append("<title>Candidate Preview</title>")
    lines.append("<style>body{font-family:system-ui,Segoe UI,Arial;margin:16px} h2{margin-top:24px} table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:8px;vertical-align:top;text-align:center} th{background:#fafafa;position:sticky;top:0} .img{width:160px;max-width:100%}</style>")
    base_dir = out_file.parent
    def _src_for(p: Optional[Path]) -> str:
        if not p:
            return ""
        try:
            rel = p.relative_to(base_dir)
            return rel.as_posix()
        except Exception:
            import os as _os
            return _os.path.relpath(str(p), str(base_dir)).replace('\\', '/')

    # Alphanumeric section
    if alnum_results:
        labels = list(alnum_results.keys())
        lines.append("<h2>Alphanumeric Candidates</h2>")
        lines.append("<table>")
        header = ["<tr><th>Char</th>"] + [f"<th>{label}</th>" for label in labels] + ["</tr>"]
        lines.append("".join(header))
        for ch in alnum_chars:
            row: List[str] = [f"<tr><td><b>{ch}</b></td>"]
            for label in labels:
                p = alnum_results.get(label, {}).get(ch)
                src = _src_for(p)
                cell = f"<img class=img src='{src}'>" if p else "<i>missing</i>"
                row.append(f"<td>{cell}</td>")
            row.append("</tr>")
            lines.append("".join(row))
        lines.append("</table>")

    # Punctuation section
    if punct_results:
        lines.append("<h2>Punctuation</h2>")
        lines.append("<table>")
        lines.append("<tr><th>Char</th><th>Preview</th></tr>")
        for ch in punct_chars:
            p = punct_results.get(ch)
            src = _src_for(p)
            cell = f"<img class=img src='{src}'>" if p else "<i>missing</i>"
            lines.append(f"<tr><td><b>{ch}</b></td><td>{cell}</td></tr>")
        lines.append("</table>")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ Wrote preview index: {out_file}")


def main() -> int:
    # Representative sample set for quick visual judgment
    alnum_chars: List[str] = [
        # Uppercase with diagonals/verticals
        "A", "M", "W",
        # Lowercase with bowls/loops
        "a", "g", "o",
        # Digits
        "0", "1", "2",
    ]
    punct_chars: List[str] = [
        ".", ",", "!", "?", ":", ";", "-", "(", ")", "[", "]", "&", "@", "#", "/", "\\",
    ]

    style_path = ROOT / "data" / "style_profiles.json"
    out_base = ROOT / "output" / "preview"
    ensure_dir(out_base)

    # Alphanumeric candidates
    alnum_candidates = find_alnum_candidates()
    alnum_out = out_base / "alphanumeric"
    alnum_results = generate_alnum_previews(alnum_candidates, alnum_chars, alnum_out, style_path)

    # Punctuation (single dataset for now)
    punct_path = ROOT / "data" / "punctuation_medians.json"
    punct_out = out_base / "punctuation"
    punct_results = generate_punct_previews(punct_path, punct_chars, punct_out, style_path)

    # Build index
    index_file = out_base / "index.html"
    build_index_html(alnum_results, alnum_chars, punct_results, punct_chars, index_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


