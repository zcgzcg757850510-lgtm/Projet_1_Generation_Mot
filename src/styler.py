from __future__ import annotations
import json
import random
from typing import Any, Dict, Optional


def _clamp(v: float, lo: float, hi: float) -> float:
	return max(lo, min(hi, v))


def _sample_param(spec: Dict[str, Any], rng: random.Random) -> float:
	mean = float(spec.get("mean", 0.0))
	range_vals = spec.get("range", [mean, mean])
	lo, hi = float(range_vals[0]), float(range_vals[1])
	dist = spec.get("distribution", "uniform")
	if dist == "normal":
		# heuristic: 3-sigma spans given range
		sigma = (hi - lo) / 6.0 if hi > lo else 0.0
		v = rng.gauss(mean, sigma)
		return _clamp(v, lo, hi)
	return rng.uniform(lo, hi)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
	out: Dict[str, Any] = dict(base)
	for k, v in override.items():
		if isinstance(v, dict) and isinstance(out.get(k), dict):
			out[k] = _deep_merge(out[k], v)  # type: ignore
		else:
			out[k] = v
	return out


def load_style(path: str) -> Dict[str, Any]:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def build_rng(seed: Optional[int]) -> random.Random:
	r = random.Random()
	if seed is not None:
		r.seed(seed)
	return r


def sample_style_for_stroke(global_style: Dict[str, Any], stroke_style: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
	merged = _deep_merge(global_style, stroke_style)

	def sample_inplace(node: Dict[str, Any]):
		for k, v in list(node.items()):
			if isinstance(v, dict) and set(v.keys()) >= {"mean", "range"}:
				node[k] = _sample_param(v, rng)
			elif isinstance(v, dict):
				sample_inplace(v)
			# else keep literal
	
	sampled = json.loads(json.dumps(merged))
	sample_inplace(sampled)
	return sampled


def style_layers(style_json: Dict[str, Any]) -> tuple:
	global_layer = style_json.get("global", {})
	stroke_types = style_json.get("stroke_types", {})
	return global_layer, stroke_types


def _blend_numeric(a: Any, b: Any, c: Any, wg: float, wc: float, ws: float) -> Any:
	# Blend floats; recursively blend dicts; otherwise, prefer stroke-level value `c`.
	if isinstance(a, (int, float)) and isinstance(b, (int, float)) and isinstance(c, (int, float)):
		return float(wg) * float(a) + float(wc) * float(b) + float(ws) * float(c)
	if isinstance(a, dict) and isinstance(b, dict) and isinstance(c, dict):
		keys = set(a.keys()) | set(b.keys()) | set(c.keys())
		out: Dict[str, Any] = {}
		for k in keys:
			va, vb, vc = a.get(k), b.get(k), c.get(k)
			if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and isinstance(vc, (int, float)):
				out[k] = _blend_numeric(va, vb, vc, wg, wc, ws)
			elif isinstance(va, dict) and isinstance(vb, dict) and isinstance(vc, dict):
				out[k] = _blend_numeric(va, vb, vc, wg, wc, ws)
			else:
				# Non-numeric: prefer stroke-level structure
				out[k] = vc if vc is not None else (vb if vb is not None else va)
		return out
	# Fallback: prefer stroke-level
	return c if c is not None else (b if b is not None else a)


def sample_hierarchical_style(global_layer: Dict[str, Any], stroke_types: Dict[str, Any], label: str,
								rng_g: random.Random, rng_c: random.Random, rng_s: random.Random,
								coherence: Dict[str, Any]) -> Dict[str, Any]:
	stroke_style = stroke_types.get(label, {})
	g = sample_style_for_stroke(global_layer, stroke_style, rng_g)
	c = sample_style_for_stroke(global_layer, stroke_style, rng_c)
	s = sample_style_for_stroke(global_layer, stroke_style, rng_s)
	per_char = float(coherence.get("per_char_variability", 0.2))
	per_stroke = float(coherence.get("per_stroke_variability", 0.25))
	wg = max(0.0, 1.0 - per_char - per_stroke)
	wc = _clamp(per_char, 0.0, 1.0)
	ws = _clamp(per_stroke, 0.0, 1.0)
	return _blend_numeric(g, c, s, wg, wc, ws)


def interpolate_styles(a: Dict[str, Any], b: Dict[str, Any], t: float) -> Dict[str, Any]:
	"""Interpolate two sampled style dicts. Numeric fields are linearly blended; dicts are recursed; others pick by t."""
	t = _clamp(t, 0.0, 1.0)
	if isinstance(a, (int, float)) and isinstance(b, (int, float)):
		return (1.0 - t) * float(a) + t * float(b)  # type: ignore
	if isinstance(a, dict) and isinstance(b, dict):
		keys = set(a.keys()) | set(b.keys())
		out: Dict[str, Any] = {}
		for k in keys:
			va, vb = a.get(k), b.get(k)
			if isinstance(va, dict) and isinstance(vb, dict):
				out[k] = interpolate_styles(va, vb, t)
			elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
				out[k] = (1.0 - t) * float(va) + t * float(vb)
			else:
				out[k] = vb if t >= 0.5 else va
		return out
	return b if t >= 0.5 else a  # type: ignore
