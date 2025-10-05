from __future__ import annotations
from typing import Any, Dict, List, Tuple

Point = Tuple[float, float]


STROKE_TYPES = [
	"heng",  # horizontal
	"shu",   # vertical
	"pie",   # left-falling
	"na",    # right-falling
	"dian",  # dot
	"zhe",   # bend
	"gou",   # hook
	"ti"     # rising
]


def angle_of_segment(p0: Point, p1: Point) -> float:
	import math
	dx, dy = p1[0] - p0[0], p1[1] - p0[1]
	return math.degrees(math.atan2(dy, dx))


def classify_stroke(points: List[Point]) -> str:
	# Very coarse geometry heuristic for MVP
	if len(points) < 2:
		return "dian"
	ang = angle_of_segment(points[0], points[-1])
	length = ((points[-1][0] - points[0][0]) ** 2 + (points[-1][1] - points[0][1]) ** 2) ** 0.5
	if length < 0.08:
		return "dian"
	# horizontal (both directions)
	if -20 <= ang <= 20 or ang >= 160 or ang <= -160:
		return "heng"
	# vertical
	if 70 <= ang <= 110 or -110 <= ang <= -70:
		return "shu"
	# right-falling (na)
	if 20 < ang < 80:
		return "na"
	# left-falling (pie)
	if 100 < ang < 160 or -160 < ang < -100:
		return "pie"
	# Fallback
	return "heng"


def classify_glyph(medians: List[List[Point]], override_map: List[str] | None = None) -> List[str]:
	if override_map and len(override_map) == len(medians):
		return override_map
	return [classify_stroke(st) for st in medians]


def load_override_for_char(char: str, mapping_json: Dict[str, Any] | None) -> List[str] | None:
	if not mapping_json:
		return None
	m = mapping_json.get("mapping", {})
	return m.get(char)
