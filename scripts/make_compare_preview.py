#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Dict, Any, List
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.parser import normalize_medians_1024
from src.classifier import classify_glyph
from src.styler import load_style, build_rng, sample_hierarchical_style
from src.transformer import transform_medians

from src.centerline import CenterlineProcessor

BASE_STYLE = ROOT / "data" / "style_profiles.json"
OVERRIDE_STYLE = ROOT / "output" / "tmp" / "style_overrides.json"
MERGED_DEFAULT = ROOT / "mmh_pipeline" / "data" / "hanzi_data_full.json"
RAW_DIR = ROOT / "mmh_pipeline" / "data" / "mmh_raw"
BASE = ROOT / "output" / "compare"
A_DIR = BASE / "A_outlines"
B_DIR = BASE / "D2_median_fill"
CR_DIR = BASE / "B_raw_centerline"
DP_DIR = BASE / "C_processed_centerline"
OUT = BASE / "compare_preview.html"

A_DIR.mkdir(parents=True, exist_ok=True)
B_DIR.mkdir(parents=True, exist_ok=True)
CR_DIR.mkdir(parents=True, exist_ok=True)
DP_DIR.mkdir(parents=True, exist_ok=True)


def load_merged(path: Path) -> Dict[str, Any]:
	if not path.exists():
		return {}
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def load_preview_style() -> Dict[str, Any]:
	# Prefer override if exists
	if OVERRIDE_STYLE.exists():
		return load_style(str(OVERRIDE_STYLE))
	return load_style(str(BASE_STYLE))


def _to_px_block(svg: str) -> str:
	return f"<div style='margin:4px 0'>{svg}</div>"


def build_processed_svg(ch: str, merged: Dict[str, Any], style_json: Dict[str, Any], seed: int) -> str:
	meta = merged.get(ch)
	if not meta:
		return "<i>missing</i>"
	med = normalize_medians_1024(meta.get("medians", []))
	outlines = meta.get("strokes", None)

	# Simple pipeline for preview: mimic main's processed centerline
	rng = build_rng(seed)
	labels = classify_glyph(med)
	sampled = []
	for lb in labels:
		sampled.append(sample_hierarchical_style(style_json.get("global", {}), style_json.get("stroke_types", {}), lb, rng, rng, rng, style_json.get("coherence", {})))

	        # Terminals removed - use med directly
        med0 = med

	proc = CenterlineProcessor(style_json, seed=seed)
	med1 = proc.process(med0)
	# No global transform here for preview; we show centerline in normalized space

	# Render SVG stroke paths (red)
	size = 256
	pad = 12
	W = H = size
	sx = sy = (W - 2 * pad)

	def map_pt(x, y):
		return pad + x * sx, pad + (1.0 - y) * sy

	parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
			 f"<rect x='0' y='0' width='{W}' height='{H}' fill='white'/>"]
	for st in med1:
		if not st:
			continue
		x0, y0 = map_pt(*st[0])
		d = [f"M{x0:.2f},{y0:.2f}"]
		for (x, y) in st[1:]:
			X, Y = map_pt(x, y)
			d.append(f"L{X:.2f},{Y:.2f}")
		parts.append(f"<path d='{' '.join(d)}' stroke='#d33' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")
	parts.append("</svg>")
	return "".join(parts)


def make_style_variants(style_json: Dict[str, Any], n: int, jitter: float, seed: int) -> List[Dict[str, Any]]:
	rng = random.Random(seed)
	variants: List[Dict[str, Any]] = []
	for i in range(n):
		s = json.loads(json.dumps(style_json))  # deep copy
		cl = s.setdefault('centerline', {})
		# Jitter some numeric fields multiplicatively
		def jmul(v, j=jitter):
			try:
				v = float(v)
			except Exception:
				return v
			f = 1.0 + rng.uniform(-j, j)
			return max(0.0, v * f)
		# fields to jitter
		cl['start_trim'] = jmul(cl.get('start_trim', 0.02))
		cl['smooth_window'] = max(1, int(jmul(cl.get('smooth_window', 3))))
		cl['resample_points'] = max(8, int(jmul(cl.get('resample_points', 64))))
		so = cl.setdefault('start_orientation', {})
		so['angle_range_deg'] = jmul(so.get('angle_range_deg', 0.0))
		st = cl.setdefault('stroke_tilt', {})
		st['range_deg'] = jmul(st.get('range_deg', 0.0))
		ps = cl.setdefault('post_scale', {})
		ps['range'] = jmul(ps.get('range', 0.0))
		variants.append(s)
	return variants


def _load_minimal_from_raw(chars: List[str]) -> Dict[str, Any]:
	"""Load only required characters from mmh_raw/graphics.txt to reduce memory.
	Fallback to {} if raw not available.
	"""
	gtxt = RAW_DIR / "graphics.txt"
	if not gtxt.exists() or not chars:
		return {}
	need = set(chars)
	out: Dict[str, Any] = {}
	with open(gtxt, "r", encoding="utf-8", errors="ignore") as f:
		for line in f:
			if len(out) == len(need):
				break
			line = line.strip()
			if not line:
				continue
			try:
				obj = json.loads(line)
			except Exception:
				continue
			ch = obj.get("character")
			if ch in need and ch not in out:
				out[ch] = {"character": ch, "strokes": obj.get("strokes", []), "medians": obj.get("medians", [])}
	return out


def main():
	style_json = load_preview_style()
	pc_variants = int(style_json.get('preview', {}).get('pc_variants', 1))
	pc_jitter = float(style_json.get('preview', {}).get('pc_jitter', 0.12))

	asvgs = {p.name.split('_',1)[-1]: p for p in A_DIR.glob("*.svg")}
	bsvgs = {p.name.split('_',1)[-1]: p for p in B_DIR.glob("*.svg")}
	keys = sorted(set(asvgs.keys()) | set(bsvgs.keys()))
	chars: List[str] = [Path(k).stem for k in keys]

	# Minimal merged data for appearing chars to reduce memory
	merged = _load_minimal_from_raw(chars)
	if not merged:
		merged = load_merged(MERGED_DEFAULT)

	html = [
		"<!doctype html>",
		"<meta charset='utf-8'>",
		"<title>Compare Preview</title>",
		"<style>body{font-family:system-ui,Segoe UI,Arial;margin:16px} table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:8px;vertical-align:top} th{background:#fafafa} .img{width:240px;max-width:100%} .name{font-size:12px;color:#555} .stack>div{margin:6px 0}</style>",
		"<h3>Compare: A_outlines | Raw Centerline | Processed Centerline | D2_median_fill</h3>",
		"<table>",
		"<tr><th>#</th><th>A_outlines</th><th>Raw Centerline</th><th>Processed Centerline</th><th>D2_median_fill</th></tr>",
	]

	for i, k in enumerate(keys, 1):
		a = asvgs.get(k)
		b = bsvgs.get(k)
		ch = Path(k).stem
		# Raw centerline (no variants); also save to disk
		raw_style = {**style_json, 'centerline': {**style_json.get('centerline', {}), 'start_orientation': {'angle_range_deg': 0.0, 'frac_len': style_json.get('centerline', {}).get('start_orientation', {}).get('frac_len', 0.05)}}}
		raw_svg = build_processed_svg(ch, merged, raw_style, seed=123)
		fname = (a.name if a else (b.name if b else f"{i:03d}_{ch}.svg"))
		(CR_DIR / fname).write_text(raw_svg, encoding="utf-8")

		# Processed centerline (single default); also save to disk
		proc_svg = build_processed_svg(ch, merged, style_json, seed=456)
		(DP_DIR / fname).write_text(proc_svg, encoding="utf-8")

		# Build row using saved files via absolute routes
		a_rel = ("/A_outlines/" + a.name) if a else None
		b_rel = ("/D2_median_fill/" + b.name) if b else None
		c_rel = "/B_raw_centerline/" + fname
		d_rel = "/C_processed_centerline/" + fname
		row = [
			f"<tr><td>{i}</td>",
			f"<td>{('<img class=img src=\"'+a_rel+'\">' if a_rel else '<i>missing</i>')}<div class=name>{k}</div></td>",
			f"<td><img class=img src=\"{c_rel}\"><div class=name>{k}</div></td>",
			f"<td><img class=img src=\"{d_rel}\"><div class=name>{k}</div></td>",
			f"<td>{('<img class=img src=\"'+b_rel+'\">' if b_rel else '<i>missing</i>')}<div class=name>{k}</div></td></tr>",
		]
		html.extend(row)

	html.append("</table>")
	OUT.parent.mkdir(parents=True, exist_ok=True)
	OUT.write_text("\n".join(html), encoding="utf-8")
	print(f"Wrote {OUT}")


if __name__ == "__main__":
	main()
