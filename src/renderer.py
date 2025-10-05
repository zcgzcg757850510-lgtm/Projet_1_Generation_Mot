from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
import svgwrite

Point = Tuple[float, float]


def _eval_profile(profile: Dict[str, Any], t: float) -> float:
	# piecewise-linear interpolation over points: [[t,y], ...]
	pts = profile.get("points") or []
	if not pts:
		return 1.0
	if t <= pts[0][0]:
		return float(pts[0][1])
	for i in range(len(pts) - 1):
		t0, y0 = float(pts[i][0]), float(pts[i][1])
		t1, y1 = float(pts[i+1][0]), float(pts[i+1][1])
		if t0 <= t <= t1:
			if t1 - t0 < 1e-6:
				return y1
			r = (t - t0) / (t1 - t0)
			return y0 * (1 - r) + y1 * r
	return float(pts[-1][1])


class SvgRenderer:
	def __init__(self, size_px: int = 256, padding: int = 8):
		self.size_px = size_px
		self.padding = padding

	def _to_px(self, p: Point) -> Point:
		# Flip Y so that mathematical Y-up becomes screen Y-down
		x = self.padding + p[0] * (self.size_px - 2 * self.padding)
		y = self.padding + (1.0 - p[1]) * (self.size_px - 2 * self.padding)
		return x, y

	def render_char(self, medians: List[List[Point]], sampled_styles: List[Dict[str, Any]], filename: str,
				  outlines: Optional[List[str]] = None, rep_style: Optional[Dict[str, Any]] = None,
				  render_mode: str = "auto") -> None:
		dwg = svgwrite.Drawing(filename, size=(self.size_px, self.size_px))
		dwg.add(dwg.rect(insert=(0, 0), size=(self.size_px, self.size_px), fill="white"))

		mode = (render_mode or "auto").lower()

		# Handle outlines if requested or auto with outlines available
		if (mode == "outline") or (mode == "auto" and outlines):
			from src.transformer import build_svg_matrix
			geom_style = rep_style or {}
			a, b, c, d, e, f = build_svg_matrix(geom_style)
			sx = (self.size_px - 2 * self.padding)
			sy = (self.size_px - 2 * self.padding)
			tx = self.padding
			ty = self.padding
			sn = 1.0 / 1024.0
			A = sx * a * sn
			B = -sy * b * sn
			C = sx * c * sn
			D = -sy * d * sn
			E = tx + sx * e * sn
			F = 220  # 固定Y偏移值220
			grp = dwg.g(transform=f"matrix({A:.6f},{B:.6f},{C:.6f},{D:.6f},{E:.6f},{F:.6f})")
			for d_path in (outlines or []):
				grp.add(dwg.path(d=d_path, fill="black", stroke="none", fill_rule="nonzero"))
			dwg.add(grp)
			dwg.save()
			return

		# median_fill mode uses polygon stroker
		if mode == "median_fill":
			from src.stroker import build_stroke_polygon
			for stroke_points, style in zip(medians, sampled_styles):
				if not stroke_points:
					continue
				poly = build_stroke_polygon(stroke_points, style, samples=96)
				pts = [self._to_px(p) for p in poly]
				path_d = "M" + " ".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"
				shape = dwg.path(d=path_d, fill="black", stroke="none")
				dwg.add(shape)
			dwg.save()
			return

		# median_stroke mode: draw along medians with variable width segments and round caps
		for stroke_points, style in zip(medians, sampled_styles):
			if not stroke_points:
				continue
			th = style.get("thickness", {}) if isinstance(style, dict) else {}
			width_base = float(th.get("width_base", 0.04))
			profile = th.get("width_profile", {}) if isinstance(th, dict) else {}
			joint = th.get("joint_style", {}) if isinstance(th, dict) else {}
			join_type = joint.get("type", "round")
			linejoin = "round" if join_type == "round" else ("miter" if join_type == "miter" else "bevel")

			# segment-based coloring: 起笔(blue) | 中间(gray) | 笔锋(red)
			start_color = svgwrite.rgb(30, 144, 255)
			middle_color = svgwrite.rgb(40, 40, 40)
			peak_color = svgwrite.rgb(220, 50, 47)

			# partition by corners using angle threshold + positional windows
			corner_thresh = 35.0
			first_region = 0.30  # 前段窗口（前百分之几）
			last_region = 0.30   # 末段窗口（后百分之几）
			try:
				cfg = style.get('start_orientation', {})
				# Use corner range [min,max] if provided; fallback to single thresh
				cmin = float(cfg.get('corner_thresh_min_deg', 7.0))
				cmax = float(cfg.get('corner_thresh_max_deg', 80.0))
				corner_thresh = max(cmin, 0.0)
				first_region = float(cfg.get('first_corner_region_frac', 0.30))
				last_region = float(cfg.get('last_corner_region_frac', 0.30))
			except Exception:
				pass
			first_region = max(0.05, min(0.5, first_region))
			last_region = max(0.05, min(0.5, last_region))
			pts = stroke_points
			N = max(2, len(pts))
			def _turn(a,b,c):
				import math
				v1=(b[0]-a[0], b[1]-a[1]); v2=(c[0]-b[0], c[1]-b[1])
				n1=(v1[0]**2+v1[1]**2)**0.5; n2=(v2[0]**2+v2[1]**2)**0.5
				if n1<1e-9 or n2<1e-9: return 0.0
				cosv=(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)
				cosv=max(-1.0,min(1.0,cosv))
				# 角ABC：以 acos 定义的夹角（0..180°），不再取绝对值
				return math.degrees(math.acos(cosv))
			# 按“向量夹角”范围筛选：角度在 [cmin, cmax] 内即候选（不区分正负方向）
			cand=[i for i in range(1,len(pts)-1) if (lambda ang: (ang >= cmin and ang <= cmax))(_turn(pts[i-1],pts[i],pts[i+1]))]
			# compute length fractions per index
			import math
			if len(pts)>=2:
				lengths=[math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1)]
				total=max(1e-9, sum(lengths))
				cum=[0.0]
				for L in lengths:
					cum.append(cum[-1]+L)
				pos=lambda idx: cum[idx]/total
				first_corner = None
				for i in cand:
					if pos(i) <= first_region:
						first_corner = i
						break
				last_corner = None
				for i in reversed(cand):
					if pos(i) >= (1.0 - last_region):
						last_corner = i
						break
				# 若窗口内未命中，则逐步放宽范围：下调下限，直至 7°（或配置最小值），分别为起笔/笔锋独立搜寻
				min_deg = 7.0
				step_deg = 5.0
				try:
					min_deg = float(cfg.get('corner_min_deg', 7.0))
					step_deg = float(cfg.get('corner_search_step_deg', 5.0))
				except Exception:
					pass
				min_deg = max(1.0, min(min_deg, corner_thresh))
				step_deg = max(0.5, min(step_deg, corner_thresh))
				if first_corner is None:
					thr = cmin - step_deg
					while thr >= min_deg and first_corner is None:
						cand2 = [i for i in range(1, len(pts)-1) if (lambda ang: (ang >= thr and ang <= cmax))(_turn(pts[i-1], pts[i], pts[i+1]))]
						for i in cand2:
							if pos(i) <= first_region:
								first_corner = i
								break
						thr -= step_deg
				if last_corner is None:
					thr = cmin - step_deg
					while thr >= min_deg and last_corner is None:
						cand2 = [i for i in range(1, len(pts)-1) if (lambda ang: (ang >= thr and ang <= cmax))(_turn(pts[i-1], pts[i], pts[i+1]))]
						for i in reversed(cand2):
							if pos(i) >= (1.0 - last_region):
								last_corner = i
								break
						thr -= step_deg
			else:
				first_corner = None
				last_corner = None

			# 不强制三段：若未命中窗口的折点，则相应段与“中间段”同色（满足“颜色自然而然保持一致”）

			for i in range(N - 1):
				p0 = stroke_points[i]
				p1 = stroke_points[i+1]
				t = (i + 0.5) / float(max(1, N - 1))
				w_scale = _eval_profile(profile, t)
				# Convert normalized width_base (~0-0.1) to pixel width (heuristic factor)
				stroke_width = max(0.5, width_base * w_scale * (self.size_px * 0.08))
				x0, y0 = self._to_px(p0)
				x1, y1 = self._to_px(p1)
				path_d = f"M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}"
				# choose color by segment index
				if first_corner is not None and i <= first_corner:
					color = start_color
				elif last_corner is not None and i >= last_corner:
					color = peak_color
				else:
					color = middle_color
				seg = dwg.path(d=path_d, stroke=color, fill="none", stroke_width=stroke_width, stroke_linecap="round", stroke_linejoin=linejoin)
				dwg.add(seg)
		dwg.save()
