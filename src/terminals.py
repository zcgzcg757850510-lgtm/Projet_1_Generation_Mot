from __future__ import annotations
import math
from typing import List, Tuple, Dict, Any

Point = Tuple[float, float]


def _norm(vx: float, vy: float) -> Tuple[float, float]:
	len_v = math.hypot(vx, vy)
	if len_v <= 1e-9:
		return 0.0, 0.0
	return vx / len_v, vy / len_v


def _rotate(vx: float, vy: float, ang_rad: float) -> Tuple[float, float]:
	c, s = math.cos(ang_rad), math.sin(ang_rad)
	return vx * c - vy * s, vx * s + vy * c


def _add(p: Point, v: Tuple[float, float]) -> Point:
	return p[0] + v[0], p[1] + v[1]


def _lerp(a: Point, b: Point, t: float) -> Point:
	return a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t


def _ensure_list(points: List[Point]) -> List[Point]:
	return list(points)


def _entry(points: List[Point], params: Dict[str, Any]) -> List[Point]:
	if not points:
		return points
	if not params.get("enable", True):
		return points
	length = float(params.get("length", 0.0))
	ang_deg = float(params.get("angle_deg", 0.0))
	curv = float(params.get("curvature", 0.0))
	p0 = points[0]
	p1 = points[1] if len(points) > 1 else (p0[0] + 1e-4, p0[1])
	dirx, diry = _norm(p0[0] - p1[0], p0[1] - p1[1])
	rvx, rvy = _rotate(dirx, diry, math.radians(ang_deg))
	ext = _add(p0, (-rvx * length, -rvy * length))
	# clamp length relative to stroke extent (simple heuristic handled by caller style)
	mid = _lerp(ext, p0, _clamp01(curv))
	# Insert two points for smoother hook
	return [ext, mid] + points  # type: ignore


def _exit(points: List[Point], params: Dict[str, Any]) -> List[Point]:
	if not points:
		return points
	if not params.get("enable", True):
		return points
	length = float(params.get("length", 0.0))
	ang_deg = float(params.get("angle_deg", 0.0))
	curv = float(params.get("curvature", 0.0))
	pn = points[-1]
	pn1 = points[-2] if len(points) > 1 else (pn[0] - 1e-4, pn[1])
	dirx, diry = _norm(pn[0] - pn1[0], pn[1] - pn1[1])
	rvx, rvy = _rotate(dirx, diry, math.radians(ang_deg))
	ext = _add(pn, (rvx * length, rvy * length))
	mid = _lerp(pn, ext, _clamp01(curv))
	return points + [mid, ext]  # type: ignore


def _clamp01(v: float) -> float:
	return max(0.0, min(1.0, v))


def apply_terminals_per_stroke(medians: List[List[Point]], sampled_styles: List[Dict[str, Any]]) -> List[List[Point]]:
	res: List[List[Point]] = []
	for pts, st in zip(medians, sampled_styles):
		term = st.get("terminals", {}) if isinstance(st, dict) else {}
		entry = term.get("entry_hook", {}) if isinstance(term, dict) else {}
		exit_t = term.get("exit_tail", {}) if isinstance(term, dict) else {}
		pts2 = _entry(_ensure_list(pts), entry)
		pts3 = _exit(pts2, exit_t)
		res.append(pts3)
	return res
