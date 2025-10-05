#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Side-by-side preview: Current (left) vs New Candidate (right).
Outputs: output/preview/dual_index.html
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.parser import normalize_medians_1024
from src.classifier import classify_glyph
from src.styler import load_style, build_rng, sample_hierarchical_style
from src.centerline import CenterlineProcessor
from src.transformer import transform_medians
from src.renderer import SvgRenderer

STYLE_BASE = ROOT / 'data' / 'style_profiles.json'
STYLE_OVERRIDE = ROOT / 'output' / 'tmp' / 'style_overrides.json'
OUT_DIR = ROOT / 'output' / 'preview' / 'dual'
OUT_HTML = ROOT / 'output' / 'preview' / 'dual_index.html'

REP_CHARS = ['A','M','W','a','g','o','0','1','2','.',',','!','?']


def _load_json(p: Path) -> Optional[Dict[str, Any]]:
	try:
		with open(p, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception:
		return None


def _load_style() -> Dict[str, Any]:
	if STYLE_OVERRIDE.exists():
		return load_style(str(STYLE_OVERRIDE))
	return load_style(str(STYLE_BASE))


def _render_one(char: str, meta: Dict[str, Any], style_json: Dict[str, Any], out_file: Path) -> bool:
	try:
		med_raw = meta.get('medians', [])
		if not med_raw:
			return False
		med = normalize_medians_1024(med_raw)
		labels = classify_glyph(med)
		rng = build_rng(42)
		sampled = [
			sample_hierarchical_style(
				style_json.get('global', {}),
				style_json.get('stroke_types', {}),
				lb,
				rng, rng, rng,
				style_json.get('coherence', {})
			)
			for lb in labels
		]
		proc = CenterlineProcessor(style_json, seed=42)
		med1 = proc.process(med)
		rep_style = sampled[0] if sampled else style_json.get('global', {})
		med2 = transform_medians(med1, rep_style)
		r = SvgRenderer(size_px=256, padding=8)
		r.render_char(med2, sampled if sampled else [style_json.get('global', {}) for _ in med2], str(out_file), render_mode='median_stroke')
		return True
	except Exception:
		return False


def pick_new_candidate() -> Optional[Path]:
	candidates = [
		ROOT / 'data' / 'alphanumeric_medians_fonttools.json',
		ROOT / 'data' / 'alphanumeric_medians_cambam.json',
		ROOT / 'data' / 'alphanumeric_medians_improved.json',
	]
	for p in candidates:
		if p.exists():
			return p
	return None


def main() -> int:
	current = ROOT / 'data' / 'alphanumeric_medians.json'
	newcand = pick_new_candidate()
	if not current.exists():
		print('❌ 缺少当前数据: data/alphanumeric_medians.json')
		return 1
	if not newcand:
		print('❌ 未找到新方案数据 (fonttools/cambam/improved)')
		return 1

	left = _load_json(current) or {}
	right = _load_json(newcand) or {}
	style = _load_style()

	OUT_DIR.mkdir(parents=True, exist_ok=True)
	rows: List[str] = []
	rows.append('<!doctype html>')
	rows.append('<meta charset="utf-8">')
	rows.append('<title>Dual Preview: Current vs New</title>')
	rows.append('<style>body{font-family:system-ui,Segoe UI,Arial;margin:16px} table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:8px;vertical-align:top;text-align:center} th{background:#fafafa} .img{width:160px}</style>')
	rows.append('<h2>左: Current (data/alphanumeric_medians.json) | 右: New (' + newcand.name + ')</h2>')
	rows.append('<table>')
	rows.append('<tr><th>Char</th><th>Current</th><th>New</th></tr>')

	for ch in REP_CHARS:
		lmeta = left.get(ch)
		rmeta = right.get(ch)
		lfile = OUT_DIR / f'left_{ch}.svg'
		rfile = OUT_DIR / f'right_{ch}.svg'
		l_ok = _render_one(ch, lmeta, style, lfile) if lmeta else False
		r_ok = _render_one(ch, rmeta, style, rfile) if rmeta else False
		l_src = os.path.relpath(lfile, OUT_HTML.parent).replace('\\','/') if l_ok else ''
		r_src = os.path.relpath(rfile, OUT_HTML.parent).replace('\\','/') if r_ok else ''
		rows.append('<tr>')
		rows.append(f'<td><b>{ch}</b></td>')
		rows.append(f"<td>{('<img class=img src=\'%s\'>'%l_src) if l_ok else '<i>missing</i>'}</td>")
		rows.append(f"<td>{('<img class=img src=\'%s\'>'%r_src) if r_ok else '<i>missing</i>'}</td>")
		rows.append('</tr>')

	rows.append('</table>')
	OUT_HTML.write_text('\n'.join(rows), encoding='utf-8')
	print(f'✅ Wrote {OUT_HTML}')
	return 0


if __name__ == '__main__':
	import sys
	sys.exit(main())
