from __future__ import annotations
from typing import List, Tuple, Dict, Any
import numpy as np
import math

Point = Tuple[float, float]


def _to_int(v: Any, d: int) -> int:
    try:
        return int(v)
    except Exception:
        return d


def _to_float(v: Any, d: float) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _length(points: List[Point]) -> float:
    if len(points) < 2:
        return 0.0
    p = np.asarray(points, dtype=float)
    d = np.diff(p, axis=0)
    return float(np.sum(np.linalg.norm(d, axis=1)))


def resample_uniform(points: List[Point], n: int) -> List[Point]:
    if not points or n <= 2:
        return points
    P = np.asarray(points, dtype=float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    if np.sum(seg) <= 1e-12:
        return points
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1]
    samples = np.linspace(0.0, total, n)
    res = []
    j = 0
    for s in samples:
        while j + 1 < len(cum) and cum[j + 1] < s:
            j += 1
        if j >= len(seg):
            res.append(tuple(P[-1]))
            continue
        r = (s - cum[j]) / max(1e-12, seg[j])
        Q = P[j] * (1 - r) + P[j + 1] * r
        res.append((float(Q[0]), float(Q[1])))
    return res


def chaikin(points: List[Point], iters: int) -> List[Point]:
    if iters <= 0 or len(points) < 3:
        return points
    pts = np.asarray(points, dtype=float)
    for _ in range(iters):
        new_pts = [pts[0]]
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            Q = 0.75 * p0 + 0.25 * p1
            R = 0.25 * p0 + 0.75 * p1
            new_pts.extend([tuple(Q), tuple(R)])
        new_pts.append(tuple(pts[-1]))
        pts = np.asarray(new_pts, dtype=float)
    return [(float(x), float(y)) for x, y in pts]


def _length_preserving_adjust(smoothed: List[Point], orig_start: Point, orig_end: Point, target_len: float) -> List[Point]:
    """Scale segment vectors to match target_len and anchor endpoints (approximate).
    1) Uniformly scale each segment vector by s = target_len / L1
    2) Linearly distribute a small translation so that last point == orig_end
    This preserves start exactly and final approximately preserves total length.
    """
    if len(smoothed) < 2:
        return smoothed
    L1 = _length(smoothed)
    if L1 <= 1e-12:
        return smoothed
    s = float(target_len / L1)
    q: List[Point] = [orig_start]
    for i in range(len(smoothed) - 1):
        dx = smoothed[i+1][0] - smoothed[i][0]
        dy = smoothed[i+1][1] - smoothed[i][1]
        q.append((q[-1][0] + s * dx, q[-1][1] + s * dy))
    # Anchor tail to original end by distributing delta
    dx_tail = orig_end[0] - q[-1][0]
    dy_tail = orig_end[1] - q[-1][1]
    n = len(q)
    if n > 1:
        out: List[Point] = []
        for i, (x, y) in enumerate(q):
            w = i / float(n - 1)
            out.append((x + w * dx_tail, y + w * dy_tail))
        return out
    return q


def length_preserving_chaikin(points: List[Point], iters: int) -> List[Point]:
    """Apply Chaikin refinement while approximately preserving total arc length and endpoints."""
    if iters <= 0 or len(points) < 3:
        return points
    L0 = _length(points)
    sm = chaikin(points, iters)
    if len(sm) < 2:
        return sm
    # early exit if change insignificant
    L1 = _length(sm)
    if abs(L1 - L0) / max(1e-9, L0) < 1e-4:
        return sm
    return _length_preserving_adjust(sm, points[0], points[-1], L0)


def smooth_moving_avg(points: List[Point], window: int) -> List[Point]:
    if window <= 1 or len(points) < 3:
        return points
    pts = np.asarray(points, dtype=float)
    k = np.ones(window, dtype=float) / float(window)
    pad = window // 2
    pad_left = pts[:pad][::-1]
    pad_right = pts[-pad:][::-1] if pad > 0 else pts[:0]
    tmp = np.concatenate([pad_left, pts, pad_right], axis=0)
    xs = np.convolve(tmp[:, 0], k, mode="same")[pad:-pad or None]
    ys = np.convolve(tmp[:, 1], k, mode="same")[pad:-pad or None]
    return [(float(x), float(y)) for x, y in zip(xs, ys)]


def trim_polyline_by_length(points: List[Point], start_frac: float, end_frac: float) -> List[Point]:
    # Trim small fractions of length at start/end; fractions are in [0,0.4]
    start_frac = max(0.0, min(0.4, start_frac))
    end_frac = max(0.0, min(0.4, end_frac))
    if start_frac <= 1e-6 and end_frac <= 1e-6:
        return points
    if len(points) < 2:
        return points
    P = np.asarray(points, dtype=float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    total = float(np.sum(seg))
    if total <= 1e-12:
        return points
    target_start = total * start_frac
    target_end = total * end_frac

    # Walk from start
    acc = 0.0
    i = 0
    while i < len(seg) and acc + seg[i] < target_start:
        acc += seg[i]
        i += 1
    if i >= len(P) - 1:
        return points
    r = (target_start - acc) / max(1e-12, seg[i])
    start_pt = P[i] * (1 - r) + P[i + 1] * r

    # Walk from end
    acc = 0.0
    j = len(seg) - 1
    while j >= 0 and acc + seg[j] < target_end:
        acc += seg[j]
        j -= 1
    if j < 0:
        return points
    r = (target_end - acc) / max(1e-12, seg[j])
    end_pt = P[j + 1] * (1 - r) + P[j] * r

    out = [tuple(start_pt)]
    out.extend([tuple(p) for p in P[i + 1:j + 1]])
    out.append(tuple(end_pt))
    return out if len(out) >= 2 else points


def trim_first_segment_by_fraction(points: List[Point], start_frac_seg1: float, corner_thresh_deg: float) -> List[Point]:
    """Trim only within the first segment (start → first corner).
    Removes a fraction of the first-segment arc-length from the head.
    """
    if len(points) < 2 or start_frac_seg1 <= 1e-9:
        return points
    start_frac_seg1 = max(0.0, min(1.0, float(start_frac_seg1)))
    # find first segment end idx by corner threshold
    corners = _find_corner_indices(points, max(1.0, float(corner_thresh_deg)))
    seg1_end_idx = (corners[0] if corners else len(points)-1)
    seg1_end_idx = max(1, min(seg1_end_idx, len(points)-1))
    P = np.asarray(points[:seg1_end_idx+1], dtype=float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    total = float(np.sum(seg))
    if total <= 1e-12:
        return points
    target = total * start_frac_seg1
    acc = 0.0
    i = 0
    while i < len(seg) and acc + seg[i] < target:
        acc += seg[i]
        i += 1
    if i >= len(P) - 1:
        # removed entire first segment → new start at seg1_end
        new_start = tuple(P[-1])
        out = [tuple(new_start)]
        out.extend([tuple(p) for p in np.asarray(points, dtype=float)[seg1_end_idx+1:]])
        return out if len(out) >= 2 else points
    r = (target - acc) / max(1e-12, seg[i])
    new_start = P[i] * (1 - r) + P[i + 1] * r
    out = [tuple(new_start)]
    # continue from the next vertex after the new_start within seg1 and rest of stroke
    out.extend([tuple(p) for p in P[i+1:]])
    out.extend(points[seg1_end_idx+1:])
    return out if len(out) >= 2 else points


def trim_last_segment_by_fraction(points: List[Point], end_frac_seg3: float, corner_thresh_deg: float) -> List[Point]:
    """基于第三段（笔锋段）的弧长比例裁剪终点
    
    重要：只在第三段内进行裁剪，折点位置保持不变
    
    Args:
        points: 笔画点集
        end_frac_seg3: 第三段弧长的裁剪比例 (0.0-1.0)
        corner_thresh_deg: 折点检测的角度阈值
    
    Returns:
        裁剪后的点集，折点位置不变
    """
    # 终点裁剪算法 - 只在第三段内裁剪
    
    if len(points) < 2 or end_frac_seg3 <= 1e-6:
        # 点数太少或裁剪比例太小，直接返回
        return points
    
    # 限制裁剪比例在 [0, 1] 范围内
    end_frac_seg3 = max(0.0, min(1.0, float(end_frac_seg3)))
    
    # 找到折点
    corners = _find_corner_indices(points, max(1.0, float(corner_thresh_deg)))
    # 角点检测完成
    
    # 确定第三段的开始位置（最后一个折点，如果没有折点则从起点开始）
    if corners:
        seg3_start_idx = corners[-1]
        if seg3_start_idx >= len(points) - 1:
            seg3_start_idx = len(points) - 2
    else:
        seg3_start_idx = 0
    
    # 确定第三段起始位置
    
    # 如果第三段太短（少于2个点），不进行裁剪
    if seg3_start_idx >= len(points) - 1:
        # 第三段太短，跳过裁剪
        return points
    
    # 计算第三段的长度（从最后一个折点到终点）
    seg3_points = points[seg3_start_idx:]
    P = np.asarray(seg3_points, dtype=float)
    seg_lengths = np.linalg.norm(np.diff(P, axis=0), axis=1)
    seg3_total_length = float(np.sum(seg_lengths))
    
    # 计算第三段总长度
    
    if seg3_total_length <= 1e-12:
        # 第三段长度太小，跳过裁剪
        return points
    
    # 计算要裁剪的长度（第三段弧长的 end_frac_seg3 比例）
    target_trim_length = seg3_total_length * end_frac_seg3
    # 计算目标裁剪长度
    
    # 从第三段终点开始向前累积长度，找到裁剪位置
    accumulated_length = 0.0
    
    # 从第三段的最后一段开始向前遍历
    for i in range(len(seg_lengths) - 1, -1, -1):
        segment_length = seg_lengths[i]
        # 从终点向前累积长度
        
        if accumulated_length + segment_length >= target_trim_length:
            # 裁剪点在当前线段内
            remaining_trim = target_trim_length - accumulated_length
            # 找到裁剪位置所在的线段
            
            if remaining_trim <= 1e-12:
                # 裁剪点正好在线段起点
                cut_idx_in_seg3 = i
                result = list(points[:seg3_start_idx + cut_idx_in_seg3 + 1])
                # 裁剪点在线段起点
            else:
                # 在线段内插值找到精确裁剪点
                t = 1.0 - (remaining_trim / segment_length)  # 从线段起点的比例
                cut_point = P[i] * (1 - t) + P[i + 1] * t
                
                # 构建结果：保留到第三段内的第i个点，然后添加裁剪点
                result = list(points[:seg3_start_idx + i + 1])
                result.append(tuple(cut_point))
                # 线段内插值裁剪
            
            return result if len(result) >= 2 else points
        
        accumulated_length += segment_length
    
    # 如果裁剪长度超过整个第三段，裁剪到第三段起点
    result = points[:seg3_start_idx + 1] if seg3_start_idx + 1 >= 2 else points
    # 裁剪长度超过第三段，裁剪到第三段起点
    return result


def protect_endpoints(points: List[Point], keep_start: int, keep_end: int, original: List[Point]) -> List[Point]:
    if len(points) != len(original):
        pts = list(points)
        pts[0] = original[0]
        pts[-1] = original[-1]
        return pts
    pts = list(points)
    k0 = max(0, min(keep_start, len(pts) - 1))
    k1 = max(0, min(keep_end, len(pts) - 1))
    for i in range(k0):
        pts[i] = original[i]
    for i in range(1, k1 + 1):
        pts[-i] = original[-i]
    return pts


def process_medians(medians: List[List[Point]], style_json: Dict[str, Any]) -> List[List[Point]]:
    cfg = style_json.get("centerline", {}) if isinstance(style_json, dict) else {}
    resample_n = _to_int(cfg.get("resample_points", 0), 0)
    chaikin_iters = _to_int(cfg.get("chaikin_iters", 1), 1)
    smooth_win = _to_int(cfg.get("smooth_window", 3), 3)
    start_trim = _to_float(cfg.get("start_trim", 0.0), 0.0)
    end_trim = _to_float(cfg.get("end_trim", 0.0), 0.0)
    keep_start = _to_int(cfg.get("protect_start_k", 2), 2)
    keep_end = _to_int(cfg.get("protect_end_k", 2), 2)
    disable_start = bool(cfg.get("disable_start", True))

    # If explicitly取消起笔: enforce minimum start_trim
    if disable_start:
        start_trim = max(start_trim, 0.02)  # 默认至少裁掉首 2% 长度

    out: List[List[Point]] = []
    for st in medians:
        orig = st
        pts = st
        if start_trim > 0.0 or end_trim > 0.0:
            pts = trim_polyline_by_length(pts, start_trim, end_trim)
        if chaikin_iters > 0:
            pts = chaikin(pts, chaikin_iters)
        # 重采样功能已移除
        if smooth_win > 1:
            pts = smooth_moving_avg(pts, smooth_win)
        pts = protect_endpoints(pts, keep_start, keep_end, orig)
        out.append(pts)
    return out

# New helpers for rotation/scale

def _rotate_points(points: List[Point], angle_deg: float, origin: Point) -> List[Point]:
    if abs(angle_deg) < 1e-9:
        return points
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    ox, oy = origin
    out: List[Point] = []
    for x, y in points:
        dx, dy = x - ox, y - oy
        xr = ox + ca * dx - sa * dy
        yr = oy + sa * dx + ca * dy
        out.append((xr, yr))
    return out


def _bbox_center(points: List[Point]) -> Point:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)))


def _scale_points(points: List[Point], scale: float, origin: Point) -> List[Point]:
    if abs(scale - 1.0) < 1e-9:
        return points
    ox, oy = origin
    out: List[Point] = []
    for x, y in points:
        dx, dy = x - ox, y - oy
        xs = ox + scale * dx
        ys = oy + scale * dy
        out.append((xs, ys))
    return out


def _move_points(points: List[Point], dx: float, dy: float) -> List[Point]:
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return points
    out: List[Point] = []
    for x, y in points:
        out.append((x + dx, y + dy))
    return out


def apply_start_orientation(points: List[Point], angle_deg: float, frac_len: float) -> List[Point]:
    """Rotate the leading fraction of the stroke around the start point to form a subtle start direction."""
    if len(points) < 2 or abs(angle_deg) < 1e-9 or frac_len <= 1e-6:
        return points
    P = np.asarray(points, dtype=float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    total = float(np.sum(seg))
    if total <= 1e-12:
        return points
    target = total * max(0.0, min(0.4, frac_len))
    acc = 0.0
    cut_idx = 0
    for i, s in enumerate(seg):
        if acc + s >= target:
            cut_idx = i + 1
            break
        acc += s
    cut_idx = max(1, min(cut_idx, len(points) - 1))
    head = _rotate_points(points[:cut_idx + 1], angle_deg, origin=points[0])
    tail = points[cut_idx + 1:]
    return head + tail


def _turn_angle_abs_deg(a: Point, b: Point, c: Point) -> float:
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(v1[0], v1[1])
    n2 = math.hypot(v2[0], v2[1])
    if n1 < 1e-12 or n2 < 1e-12:
        return 0.0
    dot = (v1[0]*v2[0] + v1[1]*v2[1]) / (n1*n2)
    dot = max(-1.0, min(1.0, dot))
    ang = math.degrees(math.acos(dot))
    return float(abs(ang))


def _turn_angle_outer_deg(a: Point, b: Point, c: Point) -> float:
    """Return outer angle in degrees (180 - inner angle)."""
    ang_in = _turn_angle_abs_deg(a, b, c)
    ext = 180.0 - ang_in
    if ext < 0.0:
        ext = 0.0
    if ext > 180.0:
        ext = 180.0
    return float(ext)





def _find_corner_indices(points: List[Point], thresh_deg: float) -> List[int]:
    if len(points) < 3:
        return []
    idxs = []
    for i in range(1, len(points)-1):
        # 使用钝角判断，与前端期望一致
        if _turn_angle_outer_deg(points[i-1], points[i], points[i+1]) >= thresh_deg:
            idxs.append(i)
    return idxs


def apply_start_orientation_segmented(points: List[Point], angle_deg: float, seg1_frac: float, corner_thresh_deg: float) -> List[Point]:
    """Rotate only within the first segment (start → first corner).
    - Rotation pivots at the first corner (end of segment-1). When no corner, no rotation.
    - seg1_frac is the fraction of segment-1 length to be rotated from the start (default 1.0).
    """
    if len(points) < 2 or abs(angle_deg) < 1e-9:
        return points
    corners = _find_corner_indices(points, max(1.0, float(corner_thresh_deg)))
    
    # 如果没有折点，不进行旋转
    if not corners:
        return points
    
    # 确定第一段的结束位置（第一个折点）
    seg1_end_idx = corners[0]
    if seg1_end_idx <= 0:
        seg1_end_idx = 1
    
    # 围绕第一个折点旋转
    pivot = points[seg1_end_idx]
    
    # 计算第一段的总长度
    P = np.asarray(points[:seg1_end_idx+1], dtype=float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    total = float(np.sum(seg))
    if total <= 1e-12:
        return points
    
    # 计算要旋转的长度比例
    frac = max(0.0, min(1.0, float(seg1_frac)))
    target = total * frac
    acc = 0.0
    cut_idx = 0
    for i, s in enumerate(seg):
        if acc + s >= target:
            cut_idx = i + 1
            break
        acc += s
    cut_idx = max(1, min(cut_idx, seg1_end_idx))
    
    # 旋转第一段（从起点到cut_idx），围绕pivot旋转
    head_rot = _rotate_points(points[:cut_idx + 1], angle_deg, origin=pivot)
    # 保持后续所有点不变
    out = head_rot + points[cut_idx + 1:]
    
    return out


def apply_end_orientation_segmented(points: List[Point], angle_deg: float, seg3_frac: float, corner_thresh_deg: float) -> List[Point]:
    """Rotate only within the last segment (last corner → end).
    - Rotation pivots at the last corner (start of segment-3). When no corner, no rotation.
    - seg3_frac is the fraction of segment-3 length to be rotated from the end (default 1.0).
    """
    if len(points) < 2 or abs(angle_deg) < 1e-9:
        return points
    corners = _find_corner_indices(points, max(1.0, float(corner_thresh_deg)))
    
    # 如果没有折点，不进行旋转
    if not corners:
        return points
    
    # 确定第三段的开始位置（最后一个折点）
    seg3_start_idx = corners[-1]
    if seg3_start_idx >= len(points) - 1:
        seg3_start_idx = len(points) - 2
    
    # 围绕最后一个折点旋转
    pivot = points[seg3_start_idx]
    
    # 计算第三段的总长度
    P = np.asarray(points[seg3_start_idx:], dtype=float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    total = float(np.sum(seg))
    if total <= 1e-12:
        return points
    
    # 计算要旋转的长度比例
    frac = max(0.0, min(1.0, float(seg3_frac)))
    target = total * frac
    acc = 0.0
    cut_idx = len(points) - 1
    for i in range(len(seg) - 1, -1, -1):
        if acc + seg[i] >= target:
            cut_idx = seg3_start_idx + i + 1
            break
        acc += seg[i]
    cut_idx = min(len(points) - 1, max(seg3_start_idx + 1, cut_idx))
    
    # 旋转第三段（从cut_idx到终点），围绕pivot旋转
    tail_rot = _rotate_points(points[cut_idx:], angle_deg, origin=pivot)
    # 保持前面的所有点不变
    out = points[:cut_idx] + tail_rot
    
    return out


def per_stroke_tilt_and_scale(medians: List[List[Point]], cfg: Dict[str, Any], rng: np.random.RandomState | None) -> List[List[Point]]:
    if rng is None:
        rng = np.random.RandomState()
    tilt_cfg = cfg.get("stroke_tilt", {}) if isinstance(cfg, dict) else {}
    first_k = int(tilt_cfg.get("first_k", 3))
    tilt_range = float(tilt_cfg.get("range_deg", 2.0))  # +/- range
    # Sample first_k tilt angles from uniform(-range, +range)
    k = min(first_k, len(medians))
    first_angles = [float(rng.uniform(-tilt_range, tilt_range)) for _ in range(k)]
    median_angle = float(np.median(first_angles)) if first_angles else 0.0
    angles: List[float] = []
    for i in range(len(medians)):
        if i < k:
            angles.append(first_angles[i])
        else:
            angles.append(median_angle)

    # optional post scale per stroke
    scale_cfg = cfg.get("post_scale", {}) if isinstance(cfg, dict) else {}
    s_range = float(scale_cfg.get("range", 0.03))  # +/- percent around 1
    scales = [1.0 + float(rng.uniform(-s_range, s_range)) for _ in range(len(medians))]

    out: List[List[Point]] = []
    for st, ang, sc in zip(medians, angles, scales):
        origin = _bbox_center(st)
        pts = _rotate_points(st, ang, origin)
        pts = _scale_points(pts, sc, origin)
        out.append(pts)
    return out


class CenterlineProcessor:
    """Maintainable, encapsulated centerline pipeline with explicit stages.

    Stages (can be toggled independently via style_json['centerline'] values):
      - start_orientation_stage
      - trim_protect_stage
      - chaikin_stage
      - resample_stage
      - smooth_stage
      - tilt_stage (first_k random, others median)
      - scale_stage (small per-stroke scale around bbox center)
    """

    def __init__(self, style_json: Dict[str, Any], seed: int | None = None):
        self.style_json = style_json
        self.cfg = style_json.get("centerline", {}) if isinstance(style_json, dict) else {}
        self.rng = np.random.RandomState(None if seed is None else seed)

    # ---- stages ----
    def start_orientation_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        """起笔角度调整阶段"""
        so_cfg = self.cfg.get("start_orientation", {}) if isinstance(self.cfg, dict) else {}
        angle_range = float(so_cfg.get("angle_range_deg", 0.0))
        frac_len = float(so_cfg.get("frac_len", 0.0))
        seg_corner_deg = float(so_cfg.get("corner_thresh_deg", 35.0))
        
        # 笔锋角度追踪
        end_angle_range = float(so_cfg.get("end_angle_range_deg", 0.0))
        end_frac_len = float(so_cfg.get("end_frac_len", 0.0))
        print(f"[CENTERLINE DEBUG] start_orientation_stage - 笔锋参数: end_angle_range_deg={end_angle_range}, end_frac_len={end_frac_len}")
        
        if angle_range <= 1e-6 or frac_len <= 1e-6:
            print(f"[CENTERLINE DEBUG] 起笔角度跳过: angle_range={angle_range}, frac_len={frac_len}")
            return medians
        
        # 🔧 修改语义：将 angle_range_deg 视为“实际旋转角度（度）”，不再随机取 ±range
        fixed_angle = float(angle_range)
        
        out: List[List[Point]] = []
        for st in medians:
            # 所有笔画使用相同的固定角度（不在这里应用折点平滑）
            out.append(apply_start_orientation_segmented(
                st, fixed_angle, frac_len, seg_corner_deg
            ))
        return out

    def end_orientation_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        start_cfg = self.cfg.get("start_orientation", {}) if isinstance(self.cfg, dict) else {}
        angle_range = float(start_cfg.get("end_angle_range_deg", 0.0))
        # 默认旋转整个第三段
        frac_len = float(start_cfg.get("end_frac_len", 1.0))
        seg_corner_deg = float(start_cfg.get("corner_thresh_deg", 35.0))
        
        print(f"[CENTERLINE DEBUG] end_orientation_stage - 笔锋角度参数: end_angle_range_deg={angle_range}, end_frac_len={frac_len}")
        print(f"[CENTERLINE DEBUG] end_orientation_stage - 完整配置: {start_cfg}")
        
        if angle_range <= 1e-6:
            print(f"[CENTERLINE DEBUG] 笔锋角度跳过: angle_range={angle_range} <= 1e-6")
            return medians
        
        print(f"[CENTERLINE DEBUG] 笔锋角度将被应用: angle_range={angle_range} > 1e-6")
        
        # 🔧 修改语义：将 end_angle_range_deg 视为“实际旋转角度（度）”，不再随机取 ±range
        fixed_angle = float(angle_range)
        
        out: List[List[Point]] = []
        for st in medians:
            # 所有笔画使用相同的固定角度
            out.append(apply_end_orientation_segmented(
                st, fixed_angle, frac_len, seg_corner_deg
            ))
        return out

    def trim_protect_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        cfg = self.cfg
        start_trim = float(cfg.get("start_trim", 0.0))
        end_trim = float(cfg.get("end_trim", 0.0))
        keep_start = int(cfg.get("protect_start_k", 2))
        keep_end = int(cfg.get("protect_end_k", 2))
        disable_start = bool(cfg.get("disable_start", True))
        if disable_start:
            start_trim = max(start_trim, 0.02)
        seg_corner_deg = float(cfg.get("start_orientation", {}).get("corner_thresh_deg", 35.0)) if isinstance(cfg, dict) else 35.0
        
        # 开始裁剪和端点保护阶段
        
        out: List[List[Point]] = []
        for i, st in enumerate(medians):
            orig = st
            pts = st
            # 处理笔画
            
            # 按"第一段比例"裁剪起点
            if start_trim > 0.0:
                pts = trim_first_segment_by_fraction(pts, start_trim, seg_corner_deg)
                # 起点裁剪完成
                
            # 末端裁剪：基于第三段（笔锋段）的弧长比例
            if end_trim > 0.0:
                # 应用终点裁剪
                pts_before = len(pts)
                pts = trim_last_segment_by_fraction(pts, end_trim, seg_corner_deg)
                # 终点裁剪完成
                
            # 如果进行了裁剪，不要重新保护端点
            if start_trim > 0.0 or end_trim > 0.0:
                # 有裁剪时跳过端点保护
                out.append(pts)
            else:
                pts = protect_endpoints(pts, keep_start, keep_end, orig)
                out.append(pts)
                
        # 裁剪和保护阶段完成
        return out

    def chaikin_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        iters = int(self.cfg.get("chaikin_iters", 1))
        if iters <= 0:
            return medians
        # 使用长度保持版Chaikin，避免弧长缩短
        return [length_preserving_chaikin(st, iters) for st in medians]

    def resample_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        # 重采样功能已移除，直接返回原始数据
        return medians



    def smooth_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        win = int(self.cfg.get("smooth_window", 3))
        if win <= 1:
            return medians
        return [smooth_moving_avg(st, win) for st in medians]

    def tilt_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        """旧的倾斜阶段 - 已被模块化变换系统替代，直接跳过"""
        # 🔧 修复：禁用旧的倾斜机制，避免与模块化变换冲突
        return medians

    def scale_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        sc_range = float(self.cfg.get("post_scale", {}).get("range", 0.0)) if isinstance(self.cfg, dict) else 0.0
        if sc_range <= 1e-6:
            return medians
        out: List[List[Point]] = []
        for st in medians:
            sc = 1.0 + float(self.rng.uniform(-sc_range, sc_range))
            origin = _bbox_center(st)
            out.append(_scale_points(st, sc, origin))
        return out

    def move_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        move_cfg = self.cfg.get("stroke_move", {}) if isinstance(self.cfg, dict) else {}
        offset = float(move_cfg.get("offset", 0.0))
        if abs(offset) <= 1e-6:
            return medians
        out: List[List[Point]] = []
        for st in medians:
            out.append(_move_points(st, 0.0, offset))  # 只在Y轴方向移动
        return out

    # ---- orchestrator ----
    def process(self, medians: List[List[Point]]) -> List[List[Point]]:
        pts = medians
        
        # 🔧 修复：在任何几何修改前保存原始中心点
        self._original_centers = [_bbox_center(stroke) for stroke in pts]
        
        pts = self.start_orientation_stage(pts)      # 起笔角度
        pts = self.end_orientation_stage(pts)        # 笔锋角度
        pts = self.trim_protect_stage(pts)           # 裁剪起点/终点

        # 使用新的模块化变换系统（现在会使用原始中心点）
        pts = self._apply_modular_transforms(pts)
        
        return pts
    
    def _apply_modular_transforms(self, medians: List[List[Point]]) -> List[List[Point]]:
        """使用模块化变换系统处理笔画"""
        from .transforms import TransformManager
        
        # 创建变换管理器
        transform_manager = TransformManager()
        
        result = []
        for i, stroke in enumerate(medians):
            # 构建变换配置，使用原始中心点
            config = self._build_transform_config(i)
            
            # 应用变换
            transformed_stroke = transform_manager.apply_transforms(stroke, config)
            result.append(transformed_stroke)
        
        return result
    
    def _build_transform_config(self, stroke_index: int = 0) -> dict:
        """构建变换配置字典"""
        config = {}
        
        # Chaikin平滑配置
        chaikin_iters = int(self.cfg.get("chaikin_iters", 0))
        if chaikin_iters > 0:
            config["chaikin_smooth"] = {
                "method": "chaikin",
                "iterations": chaikin_iters,
                "enabled": True
            }
        
        # 移动平均平滑配置
        smooth_window = int(self.cfg.get("smooth_window", 1))
        if smooth_window > 1:
            config["moving_average_smooth"] = {
                "method": "moving_average", 
                "window": smooth_window,
                "enabled": True
            }
        
        # 移动变换配置
        move_cfg = self.cfg.get("stroke_move", {}) if isinstance(self.cfg, dict) else {}
        move_offset = float(move_cfg.get("offset", 0.0))
        if abs(move_offset) > 1e-6:
            config["move"] = {
                "dx": 0.0,
                "dy": move_offset,
                "enabled": True
            }
        
        # 倾斜变换配置 - 使用统一倾斜角度和原始中心点
        tilt_cfg = self.cfg.get("stroke_tilt", {}) if isinstance(self.cfg, dict) else {}
        tilt_angle = float(tilt_cfg.get("range_deg", 0.0))
        if abs(tilt_angle) > 1e-6:
            # 使用用户给定的绝对角度（度）
            self._unified_tilt_angle = tilt_angle
            # 使用原始中心点而非当前笔画中心点
            original_center = None
            if hasattr(self, '_original_centers') and stroke_index < len(self._original_centers):
                original_center = self._original_centers[stroke_index]
            
            config["tilt"] = {
                "angle_deg": self._unified_tilt_angle,
                "center_point": original_center,  # 传递原始中心点
                "enabled": True
            }
        
        # 缩放变换配置
        # 删除缩放阶段（保持 1.0）
        
        return config
