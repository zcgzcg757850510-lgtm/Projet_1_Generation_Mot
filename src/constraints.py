from __future__ import annotations
import math
from typing import List, Tuple, Dict, Any

Point = Tuple[float, float]


def _snap_value(v: float, grid: float) -> float:
	if grid <= 1e-9:
		return v
	return round(v / grid) * grid


def apply_snap_grid(medians: List[List[Point]], size: float, strength: float) -> List[List[Point]]:
	if size <= 1e-9 or strength <= 1e-6:
		return medians
	res: List[List[Point]] = []
	alpha = max(0.0, min(1.0, strength))
	for st in medians:
		new_st: List[Point] = []
		for x, y in st:
			sx = _snap_value(x, size)
			sy = _snap_value(y, size)
			nx = x * (1.0 - alpha) + sx * alpha
			ny = y * (1.0 - alpha) + sy * alpha
			new_st.append((nx, ny))
		res.append(new_st)
	return res


def _clamp_len(dx: float, dy: float, max_len: float) -> Tuple[float, float]:
	L = math.hypot(dx, dy)
	if L <= max_len or L <= 1e-9:
		return dx, dy
	s = max_len / L
	return dx * s, dy * s


def apply_anchor_lock(reference: List[List[Point]], current: List[List[Point]], max_offset: float, strength: float) -> List[List[Point]]:
	if strength <= 1e-6:
		return current
	res: List[List[Point]] = []
	alpha = max(0.0, min(1.0, strength))
	for st_ref, st_cur in zip(reference, current):
		if not st_cur:
			res.append(st_cur)
			continue
		new_st = list(st_cur)
		# start anchor
		dx0 = st_ref[0][0] - st_cur[0][0]
		dy0 = st_ref[0][1] - st_cur[0][1]
		dx0, dy0 = _clamp_len(dx0, dy0, max_offset)
		new_st[0] = (st_cur[0][0] + dx0 * alpha, st_cur[0][1] + dy0 * alpha)
		# end anchor
		dxn = st_ref[-1][0] - st_cur[-1][0]
		dyn = st_ref[-1][1] - st_cur[-1][1]
		dxn, dyn = _clamp_len(dxn, dyn, max_offset)
		new_st[-1] = (st_cur[-1][0] + dxn * alpha, st_cur[-1][1] + dyn * alpha)
		res.append(new_st)
	return res


def _nearest_point_on_segment(px: float, py: float, a: Point, b: Point) -> Tuple[float, float, float]:
	# returns (qx, qy, t) the nearest point q on segment ab to p, and param t in [0,1]
	ax, ay = a
	bx, by = b
	dx, dy = bx - ax, by - ay
	len2 = dx * dx + dy * dy
	if len2 <= 1e-12:
		return ax, ay, 0.0
	t = ((px - ax) * dx + (py - ay) * dy) / len2
	if t < 0.0:
		t = 0.0
	elif t > 1.0:
		t = 1.0
	qx, qy = ax + t * dx, ay + t * dy
	return qx, qy, t


def apply_collision_avoidance(medians: List[List[Point]], min_distance: float, strength: float, iterations: int = 2) -> List[List[Point]]:
	if min_distance <= 1e-9 or strength <= 1e-6:
		return medians
	pts = [list(st) for st in medians]
	alpha = max(0.0, min(1.0, strength))

	# Precompute bounding boxes for each stroke to quickly cull far strokes
	def _bbox(st: List[Point]) -> Tuple[float, float, float, float]:
		xs = [p[0] for p in st]
		ys = [p[1] for p in st]
		return (min(xs), min(ys), max(xs), max(ys))

	bboxes: List[Tuple[float, float, float, float]] = [
		_bbox(st) if st else (0.0, 0.0, 0.0, 0.0) for st in pts
	]
	inflate = max(0.0, min_distance * 1.25)

	# Deterministic alternating push to break symmetry for identical overlaps
	for it in range(max(1, iterations)):
		for i, st in enumerate(pts):
			for j, (x, y) in enumerate(st):
				# local tangent approx
				vx, vy = 0.0, 0.0
				if len(st) >= 2:
					if j == 0:
						nx, ny = st[1][0] - x, st[1][1] - y
					elif j == len(st) - 1:
						nx, ny = x - st[-2][0], y - st[-2][1]
					else:
						nx, ny = st[j+1][0] - st[j-1][0], st[j+1][1] - st[j-1][1]
					vx, vy = -ny, nx  # normal
				# Accumulate repulsion
				drx, dry = 0.0, 0.0
				for si, other in enumerate(pts):
					if si == i or not other:
						continue
					# Quick bbox cull: skip if point is farther than min_distance from bbox inflated region
					bx0, by0, bx1, by1 = bboxes[si]
					# expand bbox
					bx0i, by0i, bx1i, by1i = bx0 - inflate, by0 - inflate, bx1 + inflate, by1 + inflate
					if x < bx0i:
						dx = bx0i - x
					elif x > bx1i:
						dx = x - bx1i
					else:
						dx = 0.0
					if y < by0i:
						dy = by0i - y
					elif y > by1i:
						dy = y - by1i
					else:
						dy = 0.0
					if (dx*dx + dy*dy) >= (min_distance * min_distance):
						continue
					best_dx, best_dy, best_dist = 0.0, 0.0, 1e9
					for k in range(len(other) - 1):
						q0, q1 = other[k], other[k+1]
						qx, qy, _ = _nearest_point_on_segment(x, y, q0, q1)
						dxq, dyq = x - qx, y - qy
						d = math.hypot(dxq, dyq)
						if d < best_dist:
							best_dist = d
							best_dx, best_dy = dxq, dyq
					if best_dist < min_distance:
						if best_dist <= 1e-9:
							# Symmetry break: alternate up/down by stroke index and iteration
							best_dx, best_dy = (0.0, (1 if (i + it) % 2 == 0 else -1) * min_distance)
						overlap = (min_distance - max(best_dist, 1e-9))
						scale = alpha * overlap / max(best_dist, 1e-9) * 0.5
						drx += best_dx * scale
						dry += best_dy * scale
				# project onto normal to preserve stroke shape
				mag = math.hypot(vx, vy)
				if mag > 1e-9:
					nx, ny = vx / mag, vy / mag
					proj = drx * nx + dry * ny
					drx, dry = nx * proj, ny * proj
				st[j] = (x + drx, y + dry)
	return pts
