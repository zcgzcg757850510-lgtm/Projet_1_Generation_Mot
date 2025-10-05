import json
import os
from typing import Any, Dict, List, Tuple, Optional

Point = Tuple[float, float]

_GRAPHICS_INDEX: Optional[Dict[str, Dict[str, Any]]] = None


def load_mmh_glyph(char_json_path: str) -> Dict[str, Any]:
	with open(char_json_path, "r", encoding="utf-8") as f:
		data = json.load(f)
	return data


def normalize_medians(medians: List[List[Point]]) -> List[List[Point]]:
	# Normalize to [0,1] bounding box based on medians extents
	xs: List[float] = []
	ys: List[float] = []
	for stroke in medians:
		for x, y in stroke:
			xs.append(x)
			ys.append(y)
	if not xs or not ys:
		return medians
	min_x, max_x = min(xs), max(xs)
	min_y, max_y = min(ys), max(ys)
	w = max(1e-6, max_x - min_x)
	h = max(1e-6, max_y - min_y)
	res: List[List[Point]] = []
	for stroke in medians:
		res.append([((x - min_x) / w, (y - min_y) / h) for x, y in stroke])
	return res


def normalize_medians_1024(medians: List[List[Point]]) -> List[List[Point]]:
	# Normalize MMH coordinates to [0,1]^2.
	# MMH uses a flipped Y with top-left at (0,900) and bottom-right at (1024,-124).
	# Map: x' = x / 1024; y' = (y - (-124)) / (900 - (-124)) => y' in [0,1] with 1 at top.
	if not medians:
		return medians
	x_den = 1024.0
	y_min, y_max = -124.0, 900.0
	y_den = (y_max - y_min) if (y_max - y_min) != 0 else 1024.0
	res: List[List[Point]] = []
	for stroke in medians:
		res.append([(x / x_den, (y - y_min) / y_den) for x, y in stroke])
	return res


def demo_glyph_shi() -> Dict[str, Any]:
	# A synthetic MMH-like structure for the character "十": two strokes, one horizontal, one vertical
	medians: List[List[Point]] = [
		[(0.1, 0.5), (0.9, 0.5)],
		[(0.5, 0.1), (0.5, 0.9)],
	]
	strokes_svg_paths = ["M10 50 L90 50", "M50 10 L50 90"]
	return {"medians": medians, "strokes": strokes_svg_paths}


def _load_graphics_index(mmh_dir: str) -> Optional[Dict[str, Dict[str, Any]]]:
	"""Load index from MMH graphics data.
	Preferred: graphics.txt (JSONL). Fallback: graphics.json if present.
	"""
	global _GRAPHICS_INDEX
	if _GRAPHICS_INDEX is not None:
		return _GRAPHICS_INDEX
	# Preferred JSONL
	gtxt = os.path.join(mmh_dir, "graphics.txt")
	if os.path.exists(gtxt):
		index: Dict[str, Dict[str, Any]] = {}
		with open(gtxt, "r", encoding="utf-8", errors="ignore") as f:
			for line in f:
				line = line.strip()
				if not line:
					continue
				try:
					obj = json.loads(line)
				except Exception:
					continue
				ch = obj.get("character")
				if not ch or not isinstance(ch, str):
					continue
				index[ch] = {"character": ch, "strokes": obj.get("strokes", []), "medians": obj.get("medians", [])}
		_GRAPHICS_INDEX = index
		return _GRAPHICS_INDEX
	# Fallback JSON
	graphics_path = os.path.join(mmh_dir, "graphics.json")
	if not os.path.exists(graphics_path):
		return None
	with open(graphics_path, "r", encoding="utf-8") as f:
		data = json.load(f)
	index: Dict[str, Dict[str, Any]] = {}
	if isinstance(data, list):
		for entry in data:
			ch = entry.get("character") or entry.get("char")
			if not ch:
				continue
			index[str(ch)] = entry
	elif isinstance(data, dict) and "characters" in data:
		for entry in data.get("characters", []):
			ch = entry.get("character")
			if ch:
				index[str(ch)] = entry
	_GRAPHICS_INDEX = index
	return _GRAPHICS_INDEX


def load_glyph(char: str, mmh_dir: Optional[str] = None) -> Dict[str, Any]:
	# Prefer Make Me a Hanzi graphics.json if present; else try per-codepoint JSON; else demo
	if mmh_dir:
		idx = _load_graphics_index(mmh_dir)
		if idx and char in idx:
			entry = idx[char]
			med = entry.get("medians", [])
			stk = entry.get("strokes", [])
			if med:
				med = normalize_medians(med)
			return {"medians": med, "strokes": stk}
		# fallback to per-codepoint file
		code = f"{ord(char):x}"
		candidate = os.path.join(mmh_dir, f"{code}.json")
		try:
			data = load_mmh_glyph(candidate)
			if "medians" in data:
				data["medians"] = normalize_medians(data["medians"])  # type: ignore
			return data
		except Exception:
			pass
	return demo_glyph_shi()
