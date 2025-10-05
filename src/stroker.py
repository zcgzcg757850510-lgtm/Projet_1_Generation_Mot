from __future__ import annotations
from typing import List, Tuple, Dict, Any
import numpy as np
import math
from .pressure import compute_pressure_scale
from .pen_tip import compute_nib_taper

Point = Tuple[float, float]


def _eval_profile(profile: Dict[str, Any], t: float) -> float:
	pts = profile.get("points") or []
	if not pts:
		return 1.0
	if t <= pts[0][0]:
		return float(pts[0][1])
	for i in range(len(pts) - 1):
		t0, y0 = float(pts[i][0]), float(pts[i][1])
		t1, y1 = float(pts[i + 1][0]), float(pts[i + 1][1])
		if t0 <= t <= t1:
			if t1 - t0 < 1e-9:
				return y1
			r = (t - t0) / (t1 - t0)
			return y0 * (1 - r) + y1 * r
	return float(pts[-1][1])


def _resample_polyline(points: List[Point], num_samples: int = 128) -> List[Point]:
	if not points:
		return []
	P = np.asarray(points, dtype=float)
	diff = np.diff(P, axis=0)
	seg = np.linalg.norm(diff, axis=1)
	if len(seg) == 0 or np.sum(seg) <= 1e-12:
		return points
	cum = np.concatenate([[0.0], np.cumsum(seg)])
	total = cum[-1]
	samples = np.linspace(0.0, total, num_samples)
	res = []
	j = 0
	for s in samples:
		while j + 1 < len(cum) and cum[j + 1] < s:
			j += 1
		if j >= len(seg):
			res.append(tuple(P[-1]))
			continue
		den = seg[j] if seg[j] > 1e-12 else 1.0
		r = (s - cum[j]) / den
		Q = P[j] * (1 - r) + P[j + 1] * r
		res.append((float(Q[0]), float(Q[1])))
	return res


def _to_float(v: Any, default: float) -> float:
	try:
		return float(v)
	except Exception:
		return default


def build_stroke_polygon(points: List[Point], style: Dict[str, Any], samples: int = 128) -> List[Point]:
	if len(points) < 2:
		return points
	resampled = _resample_polyline(points, num_samples=samples)
	P = np.asarray(resampled, dtype=float)
	# tangents
	dP = np.gradient(P, axis=0)
	norms = np.linalg.norm(dP, axis=1).reshape(-1, 1)
	norms[norms < 1e-9] = 1.0
	tangent = dP / norms
	# normals (perpendicular)
	normal = np.stack([-tangent[:, 1], tangent[:, 0]], axis=1)

	th = style.get("thickness", {}) if isinstance(style, dict) else {}
	width_base = _to_float(th.get("width_base", 0.04), 0.04)
	profile_w = th.get("width_profile", {}) if isinstance(th, dict) else {}

	# parameterization
	ts = np.linspace(0.0, 1.0, len(P))

	# pressure + nib taper
	pressure_scale = compute_pressure_scale(ts, style)
	nib_scale = compute_nib_taper(ts, style)
	w_scale = np.array([_eval_profile(profile_w, float(t)) for t in ts], dtype=float)

	# final half widths
	w_half = width_base * w_scale * pressure_scale * nib_scale * 0.5
	w_half = np.clip(w_half, 0.0015, 0.12)

	left = P + normal * w_half.reshape(-1, 1)
	right = P - normal * w_half.reshape(-1, 1)
	poly = np.vstack([left, right[::-1]])
	return [(float(x), float(y)) for x, y in poly]
