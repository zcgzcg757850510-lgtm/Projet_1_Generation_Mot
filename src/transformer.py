from __future__ import annotations
import math
from typing import List, Tuple, Dict, Any

Point = Tuple[float, float]


def _apply_affine(points: List[Point], mat: List[List[float]]) -> List[Point]:
	res: List[Point] = []
	for x, y in points:
		xn = mat[0][0] * x + mat[0][1] * y + mat[0][2]
		yn = mat[1][0] * x + mat[1][1] * y + mat[1][2]
		wn = mat[2][0] * x + mat[2][1] * y + mat[2][2]
		if wn != 0:
			xn /= wn
			yn /= wn
		res.append((xn, yn))
	return res


def _mat_identity() -> List[List[float]]:
	return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def _mat_mul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
	m = [[0.0, 0.0, 0.0] for _ in range(3)]
	for i in range(3):
		for j in range(3):
			m[i][j] = sum(a[i][k] * b[k][j] for k in range(3))
	return m


def build_affine(style: Dict[str, Any]) -> List[List[float]]:
	tilt_deg = float(style.get("geometry", {}).get("tilt_deg", 0.0))
	shear = float(style.get("geometry", {}).get("shear", 0.0))
	length_scale = float(style.get("geometry", {}).get("length_scale", 1.0))
	ang = math.radians(tilt_deg)
	cos_a, sin_a = math.cos(ang), math.sin(ang)
	R = [[cos_a, -sin_a, 0.0], [sin_a, cos_a, 0.0], [0.0, 0.0, 1.0]]
	Sx = [[length_scale, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
	Sh = [[1.0, shear, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
	M = _mat_identity()
	M = _mat_mul(Sh, M)
	M = _mat_mul(Sx, M)
	M = _mat_mul(R, M)
	return M


def transform_medians(medians: List[List[Point]], style: Dict[str, Any]) -> List[List[Point]]:
	M = build_affine(style)
	return [_apply_affine(st, M) for st in medians]


def apply_jitter(medians: List[List[Point]], style: Dict[str, Any], rng) -> List[List[Point]]:
	amp = float(style.get("randomness", {}).get("jitter_amp", 0.0))
	freq = float(style.get("randomness", {}).get("jitter_freq", 0.0))
	if amp <= 0.0 or freq <= 0.0:
		return medians
	res: List[List[Point]] = []
	for st in medians:
		new_st: List[Point] = []
		for i, (x, y) in enumerate(st):
			phase = i / max(1.0, (len(st) - 1))
			dx = amp * math.sin(2 * math.pi * freq * phase + rng.random() * 2 * math.pi)
			dy = amp * math.cos(2 * math.pi * freq * phase + rng.random() * 2 * math.pi)
			new_st.append((x + dx, y + dy))
		res.append(new_st)
	return res


def build_svg_matrix(style: Dict[str, Any]) -> Tuple[float, float, float, float, float, float]:
	"""Return (a,b,c,d,e,f) for SVG matrix(a b c d e f) from geometry style.
	Applies same order as build_affine: shear -> scaleX -> rotate; no translation.
	"""
	M = build_affine(style)
	# 2x3 extraction
	a = M[0][0]
	b = M[1][0]
	c = M[0][1]
	d = M[1][1]
	e = M[0][2]
	f = M[1][2]
	return a, b, c, d, e, f
