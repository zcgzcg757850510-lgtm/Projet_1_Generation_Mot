from __future__ import annotations
import argparse
import json
import os
from typing import Any, Dict, List, Optional
import random
import numpy as np

from src.parser import load_glyph, normalize_medians_1024
from src.classifier import classify_glyph, load_override_for_char
from src.styler import load_style, style_layers, build_rng, sample_hierarchical_style
from src.transformer import transform_medians
from src.renderer import SvgRenderer

from src.constraints import apply_snap_grid, apply_anchor_lock, apply_collision_avoidance
from src.centerline import CenterlineProcessor


def ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def load_stroke_mapping(path: Optional[str]) -> Optional[Dict[str, Any]]:
	if not path:
		return None
	if not os.path.exists(path):
		return None
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def _ascii_safe(s: str) -> str:
	try:
		return s.encode("ascii", errors="backslashreplace").decode("ascii")
	except Exception:
		return s


def _read_text_file(path: str) -> str:
	with open(path, "r", encoding="utf-8") as f:
		content = f.read()
	# remove whitespace to keep only characters
	return "".join(ch for ch in content if not ch.isspace())


def render_text(text: str, style_json: Dict[str, Any], mapping_json: Optional[Dict[str, Any]], merged_data: Optional[Dict[str, Any]],
			   outdir: str, seed: Optional[int], render_mode: str) -> None:
	ensure_dir(outdir)
	global_layer, stroke_types = style_json.get("global", {}), style_json.get("stroke_types", {})
	coherence = style_json.get("coherence", {})
	seed_eff = seed if seed is not None else coherence.get("seed")
	master_rng = build_rng(seed_eff)
	renderer = SvgRenderer(size_px=256, padding=8)
	per_label_global_rng: Dict[str, random.Random] = {}

	render_cfg = style_json.get("render", {}) if isinstance(style_json, dict) else {}


	processor = CenterlineProcessor(style_json, seed=master_rng.randrange(1 << 30))

	for idx, ch in enumerate(text):
		if merged_data and ch in merged_data:
			meta = merged_data[ch]
			medians = normalize_medians_1024(meta.get("medians", []))
			outlines = meta.get("strokes", None)
		else:
			glyph = load_glyph(ch, None)
			medians = glyph.get("medians", [])
			outlines = glyph.get("strokes", None)

		override = load_override_for_char(ch, mapping_json)
		stroke_labels = classify_glyph(medians, override)

		char_seed = master_rng.randrange(1 << 30)
		char_rng = random.Random(char_seed)

		sampled_styles: List[Dict[str, Any]] = []
		for label in stroke_labels:
			if label not in per_label_global_rng:
				per_label_global_rng[label] = random.Random(master_rng.randrange(1 << 30))
			global_rng = per_label_global_rng[label]
			stroke_rng = random.Random(master_rng.randrange(1 << 30))
			final_style = sample_hierarchical_style(global_layer, stroke_types, label, global_rng, char_rng, stroke_rng, coherence)
			sampled_styles.append(final_style)

		# Step 1: terminals removed - use medians directly
		pts0 = medians
		# Step 2-4: Centerline processor (start-orientation, refine, tilt+scale)
		pts1 = processor.process(pts0)
		# Step 5: global transform
		rep_style = sampled_styles[0] if sampled_styles else global_layer
		pts2 = transform_medians(pts1, rep_style)

		out_path = os.path.join(outdir, f"{idx:03d}_{ch}.svg")
		if outlines:
			renderer.render_char(pts2, sampled_styles, out_path, outlines=outlines, rep_style=rep_style, render_mode=render_mode)
		else:
			renderer.render_char(pts2, sampled_styles, out_path, render_mode=render_mode)
		print(f"Saved {_ascii_safe(out_path)}")


def main():
	parser = argparse.ArgumentParser(description="MMH controllable handwriting generator (SVG)")
	parser.add_argument("--text", type=str, default="十", help="要生成的文本")
	parser.add_argument("--text-file", type=str, default=None, help="从文件读取文本（UTF-8），忽略空白字符")
	parser.add_argument("--limit", type=int, default=None, help="可选：仅取前 N 个字符进行生成")
	parser.add_argument("--style", type=str, default="data/style_profiles.json", help="风格配置 JSON 路径")
	parser.add_argument("--stroke-map", type=str, default="data/stroke_types.json", help="笔画映射 JSON 路径（可选）")
	parser.add_argument("--merged-json", type=str, default=None, help="mmh_pipeline 合并后的 JSON（可选）")
	parser.add_argument("--outdir", type=str, default="output/samples", help="输出目录或比较模式下的父目录")
	parser.add_argument("--seed", type=int, default=None, help="随机种子（可选）")
	parser.add_argument("--median-fill", action="store_true", help="忽略 outlines，使用中轴多边形填充渲染")
	parser.add_argument("--compare", action="store_true", help="对比渲染：同时输出 A_outlines 与 D2_median_fill 两套")
	args = parser.parse_args()

	if args.text_file and os.path.exists(args.text_file):
		text = _read_text_file(args.text_file)
	else:
		text = args.text
	if args.limit is not None:
		text = text[: args.limit]

	style_json = load_style(args.style)
	mapping_json = load_stroke_mapping(args.stroke_map)

	merged_data: Optional[Dict[str, Any]] = None
	if args.merged_json and os.path.exists(args.merged_json):
		with open(args.merged_json, "r", encoding="utf-8") as f:
			merged_data = json.load(f)

	if args.compare:
		out_a = os.path.join(args.outdir, "A_outlines")
		out_b = os.path.join(args.outdir, "D2_median_fill")
		render_text(text, style_json, mapping_json, merged_data, out_a, args.seed, render_mode="auto")
		render_text(text, style_json, mapping_json, merged_data, out_b, args.seed, render_mode="median_fill")
	else:
		mode = "median_fill" if args.median_fill else "auto"
		render_text(text, style_json, mapping_json, merged_data, args.outdir, args.seed, render_mode=mode)


if __name__ == "__main__":
	main()
