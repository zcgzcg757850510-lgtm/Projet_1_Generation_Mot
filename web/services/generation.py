from __future__ import annotations
import os
import time
import json
from typing import Dict, Any, List

from web.config import ROOT, OUTPUT_COMPARE, MERGED_JSON, BASE_STYLE
from web.services.files import latest_filenames_for_char
from src.parser import normalize_medians_1024
from src.classifier import classify_glyph
from src.styler import load_style, build_rng, sample_hierarchical_style
from src.centerline import CenterlineProcessor
from src.transformer import transform_medians

DEFAULT_SIZE = 256
DEFAULT_PAD = 8


_MERGED_CACHE: Dict[str, Any] | None = None


def clear_merged_cache():
    """清除合并缓存（用于重新加载）"""
    global _MERGED_CACHE
    _MERGED_CACHE = None
    print("[CACHE] 已清除合并缓存")


def load_merged_cache() -> Dict[str, Any]:
    global _MERGED_CACHE
    if _MERGED_CACHE is not None:
        return _MERGED_CACHE
    try:
        with open(MERGED_JSON, 'r', encoding='utf-8') as f:
            _MERGED_CACHE = json.load(f)
    except Exception:
        _MERGED_CACHE = {}
    
    # 🆕 标点符号系统集成（非侵入式，可通过环境变量禁用）
    try:
        from src.punctuation_loader import merge_punctuation_with_hanzi, is_punctuation_enabled
        if is_punctuation_enabled():
            _MERGED_CACHE = merge_punctuation_with_hanzi(_MERGED_CACHE)
    except Exception as e:
        # 如果标点符号系统出错，不影响现有功能
        print(f"[PUNCTUATION] ⚠️ 标点符号加载失败（不影响现有功能）: {e}")
    
    # 🆕 字母数字系统集成（非侵入式，可通过环境变量禁用）
    try:
        from src.alphanumeric_loader import merge_alphanumeric_with_hanzi, is_alphanumeric_enabled
        if is_alphanumeric_enabled():
            _MERGED_CACHE = merge_alphanumeric_with_hanzi(_MERGED_CACHE)
    except Exception as e:
        # 如果字母数字系统出错，不影响现有功能
        print(f"[ALPHANUMERIC] ⚠️ 字母数字加载失败（不影响现有功能）: {e}")
    
    return _MERGED_CACHE


def _coherence_seed(style_json: Dict[str, Any]) -> int:
    try:
        base = int(style_json.get('coherence', {}).get('seed', 131))
    except Exception:
        base = 131
    return base


def _stable_seed_for_char(ch: str, style_json: Dict[str, Any]) -> int:
    # same inputs → same seed; include codepoint to keep per-char determinism
    return ((_coherence_seed(style_json) * 1000003) ^ (ord(ch) if ch else 0)) & 0x7fffffff


def _render_centerline_svg(med: List[List[tuple]], *, size: int = DEFAULT_SIZE, pad: int = DEFAULT_PAD, color: str = '#3aa3ff') -> str:
    W = H = size
    sx = sy = (W - 2 * pad)
    def map_pt(x: float, y: float):
        return pad + x * sx, pad + (1.0 - y) * sy
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
             f"<rect x='0' y='0' width='{W}' height='{H}' fill='white'/>"]
    for st in med:
        if not st:
            continue
        x0, y0 = map_pt(st[0][0], st[0][1])
        d = [f"M{x0:.2f},{y0:.2f}"]
        for (x, y) in st[1:]:
            X, Y = map_pt(x, y)
            d.append(f"L{X:.2f},{Y:.2f}")
        parts.append(f"<path d='{' '.join(d)}' stroke='{color}' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")
    parts.append('</svg>')
    return ''.join(parts)


def quick_raw_svg(ch: str, size: int = DEFAULT_SIZE, *, style: Dict[str, Any] | None = None) -> str:
    merged = load_merged_cache()
    meta = merged.get(ch)
    if not meta:
        return '<p>无该字数据</p>'
    med = normalize_medians_1024(meta.get('medians', []))
    if style:
        med = transform_medians(med, style)
    return _render_centerline_svg(med, size=size, pad=DEFAULT_PAD, color='#3aa3ff')


def _render_centerline_svg_windowed(
    med: List[List[tuple]],
    *,
    size: int = DEFAULT_SIZE,
    pad: int = DEFAULT_PAD,
    start_region_frac: float = 0.30,
    end_region_frac: float = 0.30,
    isolate_enabled: bool = False,
    isolate_min_len: float = 0.0,
) -> str:
    """Render tri-color by windows based on total point count (not arc-length):
    start window | middle | end window. Visualizes 'judgment ranges'.
    """
    W = H = size
    sx = sy = (W - 2 * pad)
    def map_pt(x: float, y: float):
        return pad + x * sx, pad + (1.0 - y) * sy
    start_color = '#1e90ff'
    middle_color = '#282828'
    peak_color = '#dc322f'
    isolate_color = '#800080'
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
        f"<rect x='0' y='0' width='{W}' height='{H}' fill='white'/>",
    ]
    sr = max(0.0, min(0.9, float(start_region_frac)))
    er = max(0.0, min(0.9, float(end_region_frac)))
    for st in med:
        if not st or len(st) < 2:
            continue
        # arc-length based window with sub-segment split for precise比例
        import math
        N = len(st)
        nseg = N - 1
        L = [math.hypot(st[i+1][0]-st[i][0], st[i+1][1]-st[i][1]) for i in range(nseg)]
        total = sum(L)
        if total <= 1e-12:
            continue
        # Isolation: short stroke colored purple as a whole
        if isolate_enabled and total < max(0.0, float(isolate_min_len)):
            for i in range(nseg):
                x0,y0 = map_pt(st[i][0], st[i][1]); x1,y1 = map_pt(st[i+1][0], st[i+1][1])
                parts.append(f"<path d='M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}' stroke='{isolate_color}' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")
            continue
        S = [0.0]
        for d in L:
            S.append(S[-1] + d)
        start_len = max(0.0, min(total, sr * total))
        tip_len = max(0.0, min(total, (1.0 - er) * total))
        if tip_len <= start_len:
            tip_len = min(total, start_len + 0.05 * total)
        from bisect import bisect_right
        js = max(0, min(nseg - 1, bisect_right(S, start_len) - 1))
        jt = max(0, min(nseg - 1, bisect_right(S, tip_len) - 1))
        rs = 0.0 if L[js] <= 1e-12 else (start_len - S[js]) / L[js]
        rt = 0.0 if L[jt] <= 1e-12 else (tip_len - S[jt]) / L[jt]
        def lerp(p, q, t):
            return (p[0] + (q[0]-p[0]) * t, p[1] + (q[1]-p[1]) * t)
        Pstart = lerp(st[js], st[js+1], rs) if start_len > 0 else st[0]
        Ptip = lerp(st[jt], st[jt+1], rt) if tip_len < total else st[-1]
        # draw helper
        def draw_seg(p0, p1, col):
            x0,y0 = map_pt(p0[0], p0[1]); x1,y1 = map_pt(p1[0], p1[1])
            # 画成连续线段，而不是点列
            parts.append(f"<path d='M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}' stroke='{col}' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")
        # Start part
        for i in range(js):
            draw_seg(st[i], st[i+1], start_color)
        if start_len > 0:
            draw_seg(st[js], Pstart, start_color)
        # Middle part
        if js == jt:
            draw_seg(Pstart, Ptip, middle_color)
        else:
            draw_seg(Pstart, st[js+1], middle_color)
            for i in range(js+1, jt):
                draw_seg(st[i], st[i+1], middle_color)
            draw_seg(st[jt], Ptip, middle_color)
        # Tip part
        if tip_len < total:
            if jt < nseg:
                draw_seg(Ptip, st[jt+1], peak_color)
            for i in range(jt+1, nseg):
                draw_seg(st[i], st[i+1], peak_color)
    parts.append('</svg>')
    return ''.join(parts)


def _render_centerline_svg_segmented(
    med: List[List[tuple]],
    *,
    size: int = DEFAULT_SIZE,
    pad: int = DEFAULT_PAD,
    style_json: Dict[str, Any] | None = None,
) -> str:
    W = H = size
    sx = sy = (W - 2 * pad)
    def map_pt(x: float, y: float):
        return pad + x * sx, pad + (1.0 - y) * sy
    # colors: 起笔(blue) | 中间(gray) | 笔锋(red)
    start_color = '#1e90ff'
    middle_color = '#282828'
    peak_color = '#dc322f'
    corner_thresh = 35.0
    frac_fallback = 0.15
    try:
        so = (style_json or {}).get('centerline', {}).get('start_orientation', {})
        corner_thresh = float(so.get('corner_thresh_deg', 35.0))
        frac_fallback = float(so.get('frac_len', 0.15))
    except Exception:
        pass
    frac_fallback = max(0.05, min(0.35, frac_fallback))
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
        f"<rect x='0' y='0' width='{W}' height='{H}' fill='white'/>",
    ]
    import math
    for st in med:
        if not st or len(st) < 2:
            continue
        # find corners
        def turn(a,b,c):
            v1=(b[0]-a[0], b[1]-a[1]); v2=(c[0]-b[0], c[1]-b[1])
            n1=(v1[0]**2+v1[1]**2)**0.5; n2=(v2[0]**2+v2[1]**2)**0.5
            if n1<1e-9 or n2<1e-9: return 0.0
            cosv=(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)
            cosv=max(-1.0,min(1.0,cosv))
            return abs(math.degrees(math.acos(cosv)))
        corners=[i for i in range(1,len(st)-1) if turn(st[i-1],st[i],st[i+1])>=corner_thresh]
        first_corner = corners[0] if corners else None
        last_corner = corners[-1] if corners else None
        N = max(2, len(st))
        if (first_corner is None) or (last_corner is None) or (first_corner >= last_corner):
            fc = int(round(frac_fallback * (N - 1)))
            lc = int(round((1.0 - frac_fallback) * (N - 1)))
            fc = max(0, min(N - 2, fc))
            lc = max(fc + 1, min(N - 2, lc))
            first_corner, last_corner = fc, lc
        # draw segments
        for i in range(N - 1):
            x0,y0 = map_pt(st[i][0], st[i][1])
            x1,y1 = map_pt(st[i+1][0], st[i+1][1])
            if i <= first_corner:
                col = start_color
            elif i >= last_corner:
                col = peak_color
            else:
                col = middle_color
            parts.append(f"<path d='M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}' stroke='{col}' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")
    parts.append('</svg>')
    return ''.join(parts)


def _render_processed_centerline_svg_mixed(
    med: List[List[tuple]],
    *,
    size: int = DEFAULT_SIZE,
    pad: int = DEFAULT_PAD,
    style_json: Dict[str, Any] | None = None,
    short_mask: List[bool] | None = None,
    start_region_frac: float | None = None,
    end_region_frac: float | None = None,
    fixed_info: List[Dict[str, Any]] | None = None,
    short_first_color: str = '#ff8c00',  # 橙色
    short_second_color: str = '#32cd32', # 绿色
    start_color: str = '#1e90ff',        # 起笔-蓝
    middle_color: str = '#808080',       # 中-灰
    peak_color: str = '#dc322f'          # 笔锋-红
) -> str:
    W = H = size
    sx = sy = (W - 2 * pad)
    def map_pt(x: float, y: float):
        return pad + x * sx, pad + (1.0 - y) * sy
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
        f"<rect x='0' y='0' width='{W}' height='{H}' fill='white'/>",
    ]
    debug_info: List[Dict[str, Any]] = []
    import math
    # 阈值配置（用于非短笔画的常规三段）——修复：使用更合理的角度范围
    corner_min = 35.0  # 修改：从90.0改为35.0，与centerline.py保持一致
    corner_max = 179.0
    sr = 0.30 if start_region_frac is None else float(start_region_frac)
    er = 0.30 if end_region_frac is None else float(end_region_frac)
    try:
        so = (style_json or {}).get('centerline', {}).get('start_orientation', {})
        # 优先使用UI设置的夹角范围
        if 'corner_thresh_min_deg' in so and 'corner_thresh_max_deg' in so:
            corner_min = float(so.get('corner_thresh_min_deg'))
            corner_max = float(so.get('corner_thresh_max_deg'))
        # 否则使用默认的折点检测阈值（与centerline.py保持一致）
        else:
            corner_min = float(so.get('corner_thresh_deg', 35.0))
            corner_max = 179.0  # 钝角上限
        
        if start_region_frac is None:
            sr = float(so.get('start_region_frac', sr))
        if end_region_frac is None:
            er = float(so.get('end_region_frac', er))
    except Exception:
        pass
    corner_min = max(0.1, min(corner_min, 179.0))
    corner_max = max(corner_min, min(corner_max, 179.0))
    sr = max(0.0, min(0.9, sr))
    er = max(0.0, min(0.9, er))

    def turn_angle(a, b, c) -> float:
        v1 = (b[0]-a[0], b[1]-a[1])
        v2 = (c[0]-b[0], c[1]-b[1])
        n1 = (v1[0]*v1[0] + v1[1]*v1[1]) ** 0.5
        n2 = (v2[0]*v2[0] + v2[1]*v2[1]) ** 0.5
        if n1 < 1e-9 or n2 < 1e-9:
            return 0.0
        cosv = (v1[0]*v2[0] + v1[1]*v2[1]) / (n1 * n2)
        cosv = max(-1.0, min(1.0, cosv))
        inner = abs(math.degrees(math.acos(cosv)))  # 内角 [0,180]
        ext = 180.0 - inner                         # 外角 [0,180]
        if ext < 0.0: ext = 0.0
        if ext > 180.0: ext = 180.0
        return ext

    def draw_seg(p0, p1, col):
        x0, y0 = map_pt(p0[0], p0[1]); x1, y1 = map_pt(p1[0], p1[1])
        parts.append(f"<path d='M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}' stroke='{col}' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")

    for idx, st in enumerate(med):
        if not st or len(st) < 2:
            continue
        N = len(st)
        # 短笔画：强制单折点，两段着色（橙/绿）
        is_short = bool(short_mask[idx]) if (short_mask is not None and idx < len(short_mask)) else False
        if is_short:
            if N == 2:
                draw_seg(st[0], st[1], short_first_color)
                debug_info.append({'stroke': idx, 'is_short': True, 'short_split_idx': 0, 'short_angle': None, 'first_idx': None, 'last_idx': None, 'first_angle': None, 'last_angle': None})
                continue
            # 选择全局最大折角作为"唯一折点"，若无有效折点，则取中点
            best_i = 1
            best_ang = -1.0
            for i in range(1, N-1):
                ang = turn_angle(st[i-1], st[i], st[i+1])
                if ang > best_ang:
                    best_ang = ang; best_i = i
            split_i = best_i if best_ang > 0.5 else max(1, (N-1)//2)
            # 左段：0..split_i 橙色；右段：split_i..end 绿色
            for i in range(0, split_i):
                draw_seg(st[i], st[i+1], short_first_color)
            for i in range(split_i, N-1):
                draw_seg(st[i], st[i+1], short_second_color)
            debug_info.append({'stroke': idx, 'is_short': True, 'short_split_idx': split_i, 'short_angle': round(float(best_ang), 1) if best_ang >= 0 else None, 'first_idx': None, 'last_idx': None, 'first_angle': None, 'last_angle': None})
            continue

        # 普通笔画：按三段着色；折点搜索受 Raw 三色窗口约束
        # 计算弧长累积（点级别）
        import math
        L = [math.hypot(st[i+1][0]-st[i][0], st[i+1][1]-st[i][1]) for i in range(N-1)]
        total = sum(L)
        if total <= 1e-12:
            continue
        SP = [0.0]
        for d in L:
            SP.append(SP[-1] + d)
        start_len = max(0.0, min(total, sr * total))
        tip_len = max(0.0, min(total, (1.0 - er) * total))
        if tip_len <= start_len:
            tip_len = min(total, start_len + 0.05 * total)
        # 在前窗口内寻找首折点；在后窗口内寻找末折点
        # 修改规则：首端取"第一个满足条件"的点，末端取"最后一个满足条件"的点；不做全局回退
        angles = [0.0]*N
        for i in range(1, N-1):
            angles[i] = turn_angle(st[i-1], st[i], st[i+1])
        # 若提供固定分段信息（来自原图），优先使用
        use_fixed = bool(fixed_info is not None and idx < len(fixed_info))
        if use_fixed:
            fi = fixed_info[idx] or {}
            first_corner = fi.get('first_idx', None)
            last_corner = fi.get('last_idx', None)
        else:
            first_corner = None
            for i in range(1, N-1):
                if SP[i] > start_len:
                    break
                if corner_min <= angles[i] <= corner_max:
                    first_corner = i
                    break
            last_corner = None
            for i in range(N-2, 0, -1):
                if SP[i] < tip_len:
                    break
                if corner_min <= angles[i] <= corner_max:
                    last_corner = i
                    break
        # 改进退化规则：
        # - 两端都缺失 → 全灰
        # - 仅缺首折点 → 仅红端着色，其余灰
        # - 仅缺末折点 → 仅蓝端着色，其余灰
        # - 两端都有且 first<last → 蓝|灰|红
        has_first = (first_corner is not None)
        has_last = (last_corner is not None)
        # 新退化：窗口内各自独立判定，缺一段则该端不着色（灰）
        if has_first and has_last and first_corner is not None and last_corner is not None and first_corner < last_corner:
            for i in range(N - 1):
                if i < first_corner:
                    col = start_color
                elif i >= last_corner:
                    col = peak_color
                else:
                    col = middle_color
                draw_seg(st[i], st[i+1], col)
            debug_info.append({'stroke': idx, 'is_short': False, 'first_idx': int(first_corner), 'last_idx': int(last_corner), 'first_angle': round(float(angles[first_corner]),1), 'last_angle': round(float(angles[last_corner]),1)})
            continue
        # 单端存在：只着色该端，其余灰
        if has_first and (not has_last):
            for i in range(N - 1):
                col = start_color if i < first_corner else middle_color
                draw_seg(st[i], st[i+1], col)
            debug_info.append({'stroke': idx, 'is_short': False, 'first_idx': int(first_corner), 'last_idx': None, 'first_angle': round(float(angles[first_corner]),1), 'last_angle': None})
            continue
        if has_last and (not has_first):
            for i in range(N - 1):
                col = peak_color if i >= last_corner else middle_color
                draw_seg(st[i], st[i+1], col)
            debug_info.append({'stroke': idx, 'is_short': False, 'first_idx': None, 'last_idx': int(last_corner), 'first_angle': None, 'last_angle': round(float(angles[last_corner]),1)})
            continue
        # 两端都缺失：全灰
        for i in range(N - 1):
            draw_seg(st[i], st[i+1], middle_color)
        debug_info.append({'stroke': idx, 'is_short': False, 'first_idx': None, 'last_idx': None, 'first_angle': None, 'last_angle': None})
        continue
    parts.append('</svg>')
    return ''.join(parts), debug_info


def _load_style_with_fallback(path: str, label: str) -> Dict[str, Any]:
    try:
        return load_style(path)
    except FileNotFoundError:
        print(f"[STYLE] ⚠️ {label} 样式文件缺失: {path}")
        return {}
    except Exception as e:
        print(f"[STYLE] ⚠️ 读取{label}样式失败: {e}")
        return {}


def _load_base_style() -> Dict[str, Any]:
    return _load_style_with_fallback(BASE_STYLE, '基础')


def _merge_styles(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    if not base:
        return dict(override) if override else {}
    if not override:
        return dict(base)

    def _merge_dict(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            result = dict(a)
            for k, v in b.items():
                result[k] = _merge_dict(result.get(k), v) if k in result else v
            return result
        return b if b is not None else a

    return _merge_dict(base, override)


def build_processed_centerline_svg(
    ch: str,
    size: int = DEFAULT_SIZE,
    *,
    geom_style: Dict[str, Any] | None = None,
    style_full: Dict[str, Any] | None = None,
    seed: int | None = None,
) -> str:
    merged = load_merged_cache()
    meta = merged.get(ch)
    if not meta:
        return ''
    med = normalize_medians_1024(meta.get('medians', []))
    style: Dict[str, Any] = _load_base_style()

    if style_full and os.path.exists(style_full):
        ov = _load_style_with_fallback(style_full, '覆盖')
        style = _merge_styles(style, ov)
    if seed is None:
        seed = _stable_seed_for_char(ch, style)
    rng = build_rng(seed)
    labels = classify_glyph(med)
    sampled = [sample_hierarchical_style(style.get('global', {}), style.get('stroke_types', {}), lb, rng, rng, rng, style.get('coherence', {})) for lb in labels]
    proc = CenterlineProcessor(style_full or {}, seed=seed)
    med1 = proc.process(med)
    if geom_style:
        med1 = transform_medians(med1, geom_style)
    try:
        return _render_centerline_svg_segmented(med1, size=size, pad=DEFAULT_PAD, style_json=style_full)
    except Exception:
        return _render_centerline_svg(med1, size=size, pad=DEFAULT_PAD, color='#d33')


def cleanup_single_type_svg_files(image_type: str, max_files_per_dir: int = 20):
    """清理特定类型的SVG文件，保持该目录最多max_files_per_dir个文件"""
    import glob
    
    # 映射图像类型到目录
    type_to_dir = {
        'A': os.path.join(OUTPUT_COMPARE, 'A_outlines'),
        'B': os.path.join(OUTPUT_COMPARE, 'B_raw_centerline'),
        'C': os.path.join(OUTPUT_COMPARE, 'C_processed_centerline'),
        'D1': os.path.join(OUTPUT_COMPARE, 'D1_grid_transform'),
        'D2': os.path.join(OUTPUT_COMPARE, 'D2_median_fill')
    }
    
    if image_type not in type_to_dir:
        print(f"🧹 [CLEANUP] 无效的图像类型: {image_type}")
        return
    
    dir_path = type_to_dir[image_type]
    print(f"🧹 [CLEANUP] 清理单个类型 {image_type} 的SVG文件: {dir_path}, 最大保留数量: {max_files_per_dir}")
    
    if not os.path.exists(dir_path):
        print(f"🧹 [CLEANUP] 目录不存在: {dir_path}")
        return
        
    # 获取所有SVG文件，按修改时间排序
    svg_files = glob.glob(os.path.join(dir_path, '*.svg'))
    if not svg_files:
        print(f"🧹 [CLEANUP] 目录中没有SVG文件: {dir_path}")
        return
    
    # 按修改时间排序（最新的在前）
    svg_files.sort(key=os.path.getmtime, reverse=True)
    
    if len(svg_files) <= max_files_per_dir:
        print(f"🧹 [CLEANUP] 文件数量({len(svg_files)})未超过限制({max_files_per_dir})，无需清理")
        return
    
    # 删除多余的文件
    files_to_delete = svg_files[max_files_per_dir:]
    print(f"🧹 [CLEANUP] 需要删除 {len(files_to_delete)} 个旧文件")
    
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"🧹 [CLEANUP] 已删除: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"🧹 [CLEANUP] 删除失败 {os.path.basename(file_path)}: {str(e)}")

def cleanup_old_svg_files(max_files_per_dir: int = 20):
    """清理旧的SVG文件，保持每个目录最多max_files_per_dir个文件"""
    import glob
    
    print(f"🧹 [CLEANUP] 开始清理所有SVG文件，最大保留数量: {max_files_per_dir}")
    
    dirs_to_clean = [
        os.path.join(OUTPUT_COMPARE, 'A_outlines'),
        os.path.join(OUTPUT_COMPARE, 'B_raw_centerline'), 
        os.path.join(OUTPUT_COMPARE, 'C_processed_centerline'),
        os.path.join(OUTPUT_COMPARE, 'D1_grid_transform'),
        os.path.join(OUTPUT_COMPARE, 'D2_median_fill'),
        os.path.join(OUTPUT_COMPARE, '.temp')  # Dossier temporaire pour fichiers de travail
    ]
    
    for dir_path in dirs_to_clean:
        if not os.path.exists(dir_path):
            print(f"🧹 [CLEANUP] 目录不存在: {dir_path}")
            continue
            
        # 获取所有SVG文件，按修改时间排序
        svg_files = glob.glob(os.path.join(dir_path, '*.svg'))
        print(f"🧹 [CLEANUP] {dir_path}: 发现 {len(svg_files)} 个文件")
        
        if len(svg_files) <= max_files_per_dir:
            print(f"🧹 [CLEANUP] {dir_path}: 文件数量({len(svg_files)})未超限，无需清理")
            continue
            
        # 按修改时间排序，最新的在前
        svg_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        
        # 删除超出限制的旧文件
        files_to_remove = svg_files[max_files_per_dir:]
        print(f"🧹 [CLEANUP] {dir_path}: 需要删除 {len(files_to_remove)} 个旧文件")
        
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"🧹 [CLEANUP] 已删除: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"🧹 [CLEANUP] 删除失败: {file_path} - {e}")
    
    print(f"🧹 [CLEANUP] SVG文件清理完成")


def generate_abcd(
    ch: str,
    style_override_path: str | None = None,
    grid_state: Dict[str, Any] | None = None,
    use_grid_deformation: bool = False,
) -> Dict[str, str]:
    # 注意：文件清理已移至API层面，避免重复清理
    
    # 调试日志：检查传入的网格变形参数
    print(f"[GENERATE_ABCD] ===== 字符 '{ch}' 生成参数 =====")
    print(f"[GENERATE_ABCD] grid_state 参数: {grid_state is not None}")
    print(f"[GENERATE_ABCD] use_grid_deformation 参数: {use_grid_deformation}")
    if grid_state:
        print(f"[GENERATE_ABCD] grid_state 包含的键: {grid_state.keys()}")
        print(f"[GENERATE_ABCD] controlPoints 数量: {len(grid_state.get('controlPoints', []))}")
    print(f"[GENERATE_ABCD] =======================================")
    
    merged = load_merged_cache()
    meta = merged.get(ch)
    if not meta:
        raise RuntimeError('char not found in merged data')
    style: Dict[str, Any] = _load_base_style()

    if style_override_path and os.path.exists(style_override_path):
        ov = _load_style_with_fallback(style_override_path, '覆盖')
        style = _merge_styles(style, ov)
    med = normalize_medians_1024(meta.get('medians', []))
    seed = _stable_seed_for_char(ch, style)
    rng = build_rng(seed)
    labels = classify_glyph(med)
    sampled = [sample_hierarchical_style(style.get('global', {}), style.get('stroke_types', {}), lb, rng, rng, rng, style.get('coherence', {})) for lb in labels]
    
    # 先用原始参数生成D1（用户风格化版本）
    proc_d1 = CenterlineProcessor(style, seed=seed)
    med_d1 = proc_d1.process(med)
    
    # 后面会生成D0（基线版本）使用清理后的参数
    med_proc = med_d1  # D列默认显示D1

    # 采用高精度时间戳（含毫秒），尽量避免命名冲突与浏览器缓存
    ts = time.strftime('%Y%m%d-%H%M%S') + f"-{int((time.time()%1)*1000):03d}"
    name_A = f"{ts}_{ch}_A.svg"    # A专用文件名
    name_B = f"{ts}_{ch}_B.svg"    # B专用文件名  
    name_C = f"{ts}_{ch}_C.svg"    # C专用文件名
    name_D1 = f"{ts}_{ch}_D1.svg"  # D1专用文件名（变形版）
    # name_D1_base = f"{ts}_{ch}_D1_base.svg"  # D1基础版本（无变形） - 不再需要保存
    name_D2 = f"{ts}_{ch}_D2.svg"  # D2专用文件名

    from src.renderer import SvgRenderer
    outlines = meta.get('strokes', None)
    renderer = SvgRenderer(size_px=256, padding=8)

    outA = os.path.join(OUTPUT_COMPARE, 'A_outlines', name_A)          # A窗口: 轮廓
    outB = os.path.join(OUTPUT_COMPARE, 'B_raw_centerline', name_B)     # B窗口: 原始中轴  
    outC = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', name_C)  # C窗口: 处理中轴
    # outD1_base = os.path.join(OUTPUT_COMPARE, 'D1_grid_transform', name_D1_base)  # 基础D1 - 不再需要保存
    outD1 = os.path.join(OUTPUT_COMPARE, 'D1_grid_transform', name_D1)           # 最终D1
    outD2 = os.path.join(OUTPUT_COMPARE, 'D2_median_fill', name_D2)            # D2窗口: 中轴填充
    for p in (os.path.dirname(outA), os.path.dirname(outB), os.path.dirname(outC), os.path.dirname(outD1), os.path.dirname(outD2)):
        os.makedirs(p, exist_ok=True)

    rep_style = (sampled[0] if sampled else style.get('global', {}))
    # A窗口: 轮廓 (outlines)
    try:
        pts = transform_medians(med, rep_style)
        renderer.render_char(pts, sampled, outA, outlines=outlines, rep_style=(sampled[0] if sampled else style.get('global', {})), render_mode='auto')
    except Exception:
        with open(outA, 'w', encoding='utf-8') as f: f.write(quick_raw_svg(ch))

    # B窗口: 原始中轴 (raw centerline with tri-color windows)
    try:
        sr = float(style.get('centerline', {}).get('start_orientation', {}).get('start_region_frac', 0.30))
    except Exception:
        sr = 0.30
    try:
        er = float(style.get('centerline', {}).get('start_orientation', {}).get('end_region_frac', 0.30))
    except Exception:
        er = 0.30
    # isolation controls (from style if present)
    try:
        iso_on = bool(style.get('centerline', {}).get('start_orientation', {}).get('isolate_on', False)
                       or style.get('preview', {}).get('isolate_on', False))
    except Exception:
        iso_on = False
    try:
        iso_min = float(style.get('centerline', {}).get('start_orientation', {}).get('isolate_min_len',
                               style.get('preview', {}).get('isolate_min_len', 0.0)))
    except Exception:
        iso_min = 0.0
    with open(outB, 'w', encoding='utf-8') as f: f.write(_render_centerline_svg_windowed(transform_medians(med, rep_style), size=DEFAULT_SIZE, pad=DEFAULT_PAD, start_region_frac=sr, end_region_frac=er, isolate_enabled=iso_on, isolate_min_len=iso_min))

    # D1窗口: 网格变形 (基础版本 + 变形版本)
    print(f"[DEBUG ENTRY] D1 generation - use_grid_deformation: {use_grid_deformation}")
    print(f"[DEBUG ENTRY] D1 generation - grid_state type: {type(grid_state)}")
    print(f"[DEBUG ENTRY] D1 generation - grid_state: {grid_state}")
    try:
        pts_d1 = transform_medians(med_d1, rep_style)
        
        # 使用与generate_single_type相同的着色逻辑：基于D0基线分段信息
        # 短笔画遮罩处理
        iso_on_d1 = False
        iso_min_d1 = 0.0
        try:
            so = style.get('centerline', {}).get('start_orientation', {})
            iso_on_d1 = bool(so.get('isolate_on', False) or style.get('preview', {}).get('isolate_on', False))
            iso_min_d1 = float(so.get('isolate_min_len', style.get('preview', {}).get('isolate_min_len', 0.0)))
        except Exception:
            pass
        
        short_mask_d1 = []
        if iso_on_d1 and iso_min_d1 > 0.0:
            med_raw_t_d1 = transform_medians(med, rep_style)
            import math
            for st in med_raw_t_d1:
                if not st or len(st) < 2:
                    short_mask_d1.append(False)
                    continue
                total = 0.0
                for i in range(len(st) - 1):
                    dx = st[i+1][0] - st[i][0]
                    dy = st[i+1][1] - st[i][1]
                    total += math.hypot(dx, dy)
                short_mask_d1.append(total < iso_min_d1)
        else:
            short_mask_d1 = [False] * len(pts_d1)

        # 构建D0基线风格用于获取分段信息
        style_base_d1 = dict(style)
        if 'centerline' in style_base_d1:
            style_base_d1['centerline'] = dict(style_base_d1['centerline'])
            if 'start_orientation' in style_base_d1['centerline']:
                style_base_d1['centerline']['start_orientation'] = dict(style_base_d1['centerline']['start_orientation'])
        if 'preview' in style_base_d1:
            style_base_d1['preview'] = dict(style_base_d1['preview'])
        
        try:
            cl_d1 = style_base_d1.setdefault('centerline', {})
            cl_d1['start_trim'] = 0.0
            cl_d1['end_trim'] = 0.0
            cl_d1['protect_end_k'] = 0
            cl_d1['chaikin_iters'] = 0
            cl_d1['resample_points'] = 0
            cl_d1['smooth_window'] = 1
            cl_d1.setdefault('stroke_tilt', {})['range_deg'] = 0.0
            cl_d1.setdefault('post_scale', {})['range'] = 0.0
            cl_d1.setdefault('stroke_move', {})['offset'] = 0.0
            so0_d1 = cl_d1.setdefault('start_orientation', {})
            so0_d1['angle_range_deg'] = 0.0
            so0_d1['end_angle_range_deg'] = 0.0
            so0_d1['end_frac_len'] = 1.0
            so0_d1.pop('corner_thresh_min_deg', None)
            so0_d1.pop('corner_thresh_max_deg', None)
            so0_d1['corner_thresh_deg'] = 35.0
            so0_d1.pop('frac_len', None)
            so0_d1.pop('isolate_on', None)
            so0_d1.pop('isolate_min_len', None)
            so0_d1.pop('start_region_frac', None)
            so0_d1.pop('end_region_frac', None)
            so0_d1.pop('fix_segments', None)
            if 'preview' in style_base_d1:
                preview_d1 = style_base_d1['preview']
                preview_d1.pop('fix_segments', None)
        except Exception:
            pass

        # 生成D0基线版本获取分段信息
        proc_base_d1 = CenterlineProcessor(style_base_d1, seed=seed)
        med_base_d1 = proc_base_d1.process(med)
        pts_proc0_d1 = transform_medians(med_base_d1, rep_style)
        svg_text0_d1, dbg0_d1 = _render_processed_centerline_svg_mixed(
            pts_proc0_d1, size=DEFAULT_SIZE, pad=DEFAULT_PAD,
            style_json=None, short_mask=short_mask_d1,
            start_region_frac=None,
            end_region_frac=None
        )

        # 使用D0的分段信息对D1着色，确保与"全部"一致
        so_cfg_d1 = style.get('centerline', {}).get('start_orientation', {}) if isinstance(style, dict) else {}
        preview_cfg_d1 = style.get('preview', {}) if isinstance(style, dict) else {}
        corner_range_enabled_d1 = ('corner_thresh_min_deg' in so_cfg_d1 and 'corner_thresh_max_deg' in so_cfg_d1)
        if not corner_range_enabled_d1:
            corner_range_enabled_d1 = bool(preview_cfg_d1.get('corner_range_on', False))

        fixed_info_to_use_d1 = None if corner_range_enabled_d1 else dbg0_d1

        d1_base_svg, _debug_info_d1 = _render_processed_centerline_svg_mixed(
            pts_d1, size=DEFAULT_SIZE, pad=DEFAULT_PAD,
            style_json=style, short_mask=short_mask_d1,
            start_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('start_region_frac'),
            end_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('end_region_frac'),
            fixed_info=fixed_info_to_use_d1
        )

        # 不再保存基础版本文件，直接在内存中处理

        d1_final_svg = d1_base_svg
        if grid_state:  # 修复：与generate_single_type保持一致，只检查grid_state是否存在
            print(f"[DEBUG] Applying grid deformation - grid_state exists")
            print(f"[DEBUG] grid_state keys: {list(grid_state.keys()) if grid_state else 'None'}")
            if grid_state and 'controlPoints' in grid_state:
                print(f"[DEBUG] controlPoints count: {len(grid_state['controlPoints'])}")
            try:
                from web.services.grid_transform import apply_smooth_grid_deformation
                print(f"[DEBUG] D1 base SVG length: {len(d1_base_svg)}")
                d1_final_svg = apply_smooth_grid_deformation(d1_base_svg, grid_state)
                print(f"[DEBUG] D1 final SVG length: {len(d1_final_svg)}")
                print(f"[DEBUG] Deformation applied: {d1_final_svg != d1_base_svg}")
            except Exception as deform_err:
                print(f"[D1] 网格变形失败，使用未变形版本: {deform_err}")
                import traceback
                traceback.print_exc()
                d1_final_svg = d1_base_svg
        else:
            print(f"[DEBUG] Skipping grid deformation - no grid_state provided")

        with open(outD1, 'w', encoding='utf-8') as f:
            f.write(d1_final_svg)
    except Exception:
        with open(outD1, 'w', encoding='utf-8') as f: 
            f.write('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')

    # D2窗口: 中轴填充 (median fill)
    try:
        pts = transform_medians(med, rep_style)
        renderer.render_char(pts, sampled, outD2, render_mode='median_fill')
    except Exception:
        with open(outD2, 'w', encoding='utf-8') as f: f.write('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
    # C窗口: 处理中轴 (processed centerline)
    try:
        pts_proc = transform_medians(med_d1, rep_style)  # 使用D1中轴线
        # 基于 Raw 的"短边全紫"判断，为 D 列短笔画强制单折点（橙/绿）
        iso_on = False
        iso_min = 0.0
        try:
            so = style.get('centerline', {}).get('start_orientation', {})
            iso_on = bool(so.get('isolate_on', False) or style.get('preview', {}).get('isolate_on', False))
            iso_min = float(so.get('isolate_min_len', style.get('preview', {}).get('isolate_min_len', 0.0)))
        except Exception:
            pass
        short_mask: List[bool] = []
        if iso_on and iso_min > 0.0:
            med_raw_t = transform_medians(med, rep_style)
            import math
            for st in med_raw_t:
                if not st or len(st) < 2:
                    short_mask.append(False)
                    continue
                total = 0.0
                for i in range(len(st)-1):
                    dx = st[i+1][0]-st[i][0]; dy = st[i+1][1]-st[i][1]
                    total += math.hypot(dx, dy)
                short_mask.append(total < iso_min)
        else:
            short_mask = [False] * len(pts_proc)

        # 暂时跳过C单独渲染，等待D0完成后统一处理
        svg_text = ""
        debug_info = []
        processed_debug = debug_info
        
    except Exception as e:
        # C窗口生成异常处理
        # 回退到简单单色线（极端情况下）
        with open(outC, 'w', encoding='utf-8') as f:
            f.write(build_processed_centerline_svg(ch, size=DEFAULT_SIZE, geom_style=rep_style, style_full=style, seed=seed))
        processed_debug = []

    # 生成基线原图（原始参数：禁用起笔/中间/笔锋细化）
    try:
        import copy as _copy
        # 使用浅拷贝代替深拷贝以提高性能
        style_base = dict(style)
        if 'centerline' in style_base:
            style_base['centerline'] = dict(style_base['centerline'])
            if 'start_orientation' in style_base['centerline']:
                style_base['centerline']['start_orientation'] = dict(style_base['centerline']['start_orientation'])
        if 'preview' in style_base:
            style_base['preview'] = dict(style_base['preview'])
        try:
            # 开始D0参数清理
            cl = style_base.setdefault('centerline', {})
            
            # 记录清理前的笔锋参数
            original_so = cl.get('start_orientation', {})
            # 记录清理前的笔锋参数
            
            cl['start_trim'] = 0.0
            cl['end_trim'] = 0.0
            cl['protect_end_k'] = 0
            cl['chaikin_iters'] = 0
            cl['resample_points'] = 0
            cl['smooth_window'] = 1
            cl.setdefault('stroke_tilt', {})['range_deg'] = 0.0
            cl.setdefault('post_scale', {})['range'] = 0.0
            cl.setdefault('stroke_move', {})['offset'] = 0.0  # 禁用笔画移动
            so0 = cl.setdefault('start_orientation', {})
            so0['angle_range_deg'] = 0.0
            
            # 记录笔锋参数清理过程
            # 记录笔锋参数清理过程
            
            # 清理笔锋相关参数，确保D0不受笔锋界面影响
            so0['end_angle_range_deg'] = 0.0  # 禁用笔锋角度调整
            so0['end_frac_len'] = 1.0         # 重置笔锋长度比例为默认值
            
            # 笔锋参数清理完成
            # 移除所有角度范围相关的UI参数，使用固定默认值
            so0.pop('corner_thresh_min_deg', None)
            so0.pop('corner_thresh_max_deg', None)
            so0['corner_thresh_deg'] = 35.0  # 使用固定的默认折点阈值
            # 移除其他可能影响D0的参数
            so0.pop('frac_len', None)
            so0.pop('isolate_on', None)
            so0.pop('isolate_min_len', None)
            so0.pop('start_region_frac', None)  # 移除原始中轴三色窗口参数
            so0.pop('end_region_frac', None)    # 移除原始中轴三色窗口参数
            so0.pop('fix_segments', None)       # 移除分段边界冻结参数
            # 清理preview配置
            if 'preview' in style_base:
                preview = style_base['preview']
                preview.pop('fix_segments', None)
                preview.pop('corner_range_on', None)
                preview.pop('corner_min', None)
                preview.pop('corner_max', None)
            
            # D0配置完成

        except Exception as e:
            # 参数清理异常处理
            pass
        
        # 创建CenterlineProcessor
        proc0 = CenterlineProcessor(style_base, seed=seed)
        # CenterlineProcessor配置完成
        # 开始处理D0中轴线
        med0 = proc0.process(med)
        # D0中轴线处理完成
        pts_proc0 = transform_medians(med0, rep_style)
        svg_text0, dbg0 = _render_processed_centerline_svg_mixed(
            pts_proc0, size=DEFAULT_SIZE, pad=DEFAULT_PAD,
            style_json=None, short_mask=short_mask,
            start_region_frac=None,
            end_region_frac=None
        )
        name0 = f"{ts}_{ch}_C_orig.svg"  # Fichier de base pour C (temporaire)
        temp_dir = os.path.join(OUTPUT_COMPARE, '.temp')
        os.makedirs(temp_dir, exist_ok=True)
        outD0 = os.path.join(temp_dir, name0)
        with open(outD0, 'w', encoding='utf-8') as f:
            f.write(svg_text0)
        # D1使用D0的分段信息，确保颜色完全一致
        # 若启用了"夹角范围"，则不使用D0的固定分段，让UI角度范围生效
        so_cfg = style.get('centerline', {}).get('start_orientation', {}) if isinstance(style, dict) else {}
        corner_range_enabled = ('corner_thresh_min_deg' in so_cfg and 'corner_thresh_max_deg' in so_cfg)
        preview_cfg = style.get('preview', {}) if isinstance(style, dict) else {}
        if not corner_range_enabled:
            corner_range_enabled = bool(preview_cfg.get('corner_range_on', False))
        fixed_info_to_use = None if corner_range_enabled else dbg0
        svg_text_d1, debug_info_d1 = _render_processed_centerline_svg_mixed(
            pts_proc, size=DEFAULT_SIZE, pad=DEFAULT_PAD,
            style_json=style, short_mask=short_mask,
            start_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('start_region_frac'),
            end_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('end_region_frac'),
            fixed_info=fixed_info_to_use
        )
        with open(outC, 'w', encoding='utf-8') as f:
            f.write(svg_text_d1)
        processed_debug = debug_info_d1
    except Exception:
        # 回退到简单单色线（极端情况下）
        with open(outC, 'w', encoding='utf-8') as f:
            f.write(build_processed_centerline_svg(ch, size=DEFAULT_SIZE, geom_style=rep_style, style_full=style, seed=seed))
        processed_debug = []

    # 优化文件存在性检查，减少等待时间
    targets = [outA, outB, outC, outD1, outD2] + ([outD0] if 'outD0' in locals() else [])
    for _ in range(10):  # 减少到0.5s最大等待时间
        if all(os.path.exists(p) for p in targets):
            break
        time.sleep(0.05)

    try:
        from flask import url_for
        result = {
            'A': url_for('serve_outlines', filename=name_A),                 # A窗口: 轮廓
            'B': url_for('serve_raw_centerline', filename=name_B),           # B窗口: 原始中轴
            'C': url_for('serve_processed_centerline_c', filename=name_C),   # C窗口: 处理中轴
            'D1': url_for('serve_grid_transform', filename=name_D1),         # D1窗口: 网格变形（变形后）
            # 'D1_base': url_for('serve_grid_transform', filename=name_D1_base),  # 不再返回基础版本
            'D2': url_for('serve_median_fill', filename=name_D2),            # D2窗口: 中轴填充
            'angles': processed_debug,
            'version': ts
        }
        return result
    except RuntimeError:
        # 在非Flask上下文中返回文件路径
        result = {
            'A': f'/compare/A_outlines/{name_A}',
            'B': f'/compare/B_raw_centerline/{name_B}',
            'C': f'/compare/C_processed_centerline/{name_C}',
            'D1': f'/compare/D1_grid_transform/{name_D1}',
            # 'D1_base': f'/compare/D1_grid_transform/{name_D1_base}',  # 不再返回基础版本
            'D2': f'/compare/D2_median_fill/{name_D2}',
            'angles': processed_debug,
            'version': ts
        }
        return result


def generate_single_type(ch: str, image_type: str, style_override_path: str = None, grid_state: Dict[str, Any] | None = None):
    """
    生成单个类型的图像，真正只生成请求的类型
    
    Args:
        ch (str): 要生成的字符
        image_type (str): 图像类型 ('A', 'B', 'C', 'D1', 'D2')
        style_override_path (str, optional): 样式覆盖文件路径
    
    Returns:
        dict: 包含生成的图像URL的字典
    """
    print(f"🎯 [SINGLE] 开始生成单个类型: {image_type} for 字符: {ch}")
    
    # 验证类型
    if image_type not in ['A', 'B', 'C', 'D1', 'D2']:
        raise ValueError(f"无效的图像类型: {image_type}")
    
    # Note: Le nettoyage est fait dans web/app.py avant l'appel à cette fonction
    
    # 复杂类型 (C, D1) 需要med_d1，但现在实现真正的单独生成
    if image_type in ['C', 'D1']:
        print(f"🎯 [SINGLE] 独立生成复杂类型: {image_type}")
        
        try:
            # 基础初始化 (类似于generate_abcd，但只生成需要的类型)
            import time
            from src.parser import load_glyph
            from src.classifier import classify_glyph  
            from src.styler import sample_hierarchical_style
            from src.centerline import CenterlineProcessor
            from src.transformer import transform_medians
            from src.parser import normalize_medians_1024
            from src.renderer import SvgRenderer
            from src.styler import build_rng
            
            # 加载字符数据 - 使用merged cache而不是load_glyph
            merged = load_merged_cache()
            meta = merged.get(ch)
            if not meta:
                raise Exception(f"字符 '{ch}' 数据未找到")
            
            # 加载样式
            style = _load_base_style()
            if style_override_path and os.path.exists(style_override_path):
                ov = _load_style_with_fallback(style_override_path, '覆盖')
                style = _merge_styles(style, ov)
            
            # 基础处理
            med = normalize_medians_1024(meta.get('medians', []))
            seed = _stable_seed_for_char(ch, style)
            rng = build_rng(seed)
            labels = classify_glyph(med)
            sampled = [sample_hierarchical_style(style.get('global', {}), style.get('stroke_types', {}), lb, rng, rng, rng, style.get('coherence', {})) for lb in labels]
            
            # 创建med_d1 (nécessaire pour C et D1)
            proc_d1 = CenterlineProcessor(style, seed=seed)
            med_d1 = proc_d1.process(med)
            
            # 生成时间戳和文件名
            ts = time.strftime('%Y%m%d-%H%M%S') + f"-{int((time.time()%1)*1000):03d}"
            filename = f"{ts}_{ch}_{image_type}.svg"
            
            if image_type == 'C':
                # C类型: 处理中轴 - 与"全部"流程一致，使用D0基线分段信息上色
                output_dir = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)

                try:
                    rep_style = (sampled[0] if sampled else style.get('global', {}))

                    # 处理后的中轴线（D1）
                    proc = CenterlineProcessor(style, seed=seed)
                    med_processed = proc.process(med)
                    pts_processed = transform_medians(med_processed, rep_style)

                    # 短笔画遮罩（与generate_abcd一致）
                    iso_on = False
                    iso_min = 0.0
                    try:
                        so = style.get('centerline', {}).get('start_orientation', {})
                        iso_on = bool(so.get('isolate_on', False) or style.get('preview', {}).get('isolate_on', False))
                        iso_min = float(so.get('isolate_min_len', style.get('preview', {}).get('isolate_min_len', 0.0)))
                    except Exception:
                        pass
                    short_mask: List[bool] = []
                    if iso_on and iso_min > 0.0:
                        med_raw_t = transform_medians(med, rep_style)
                        import math
                        for st in med_raw_t:
                            if not st or len(st) < 2:
                                short_mask.append(False)
                                continue
                            total = 0.0
                            for i in range(len(st)-1):
                                dx = st[i+1][0]-st[i][0]; dy = st[i+1][1]-st[i][1]
                                total += math.hypot(dx, dy)
                            short_mask.append(total < iso_min)
                    else:
                        short_mask = [False] * len(pts_processed)

                    # 构建D0基线风格（禁用所有用户变换），获取分段信息
                    style_base = dict(style)
                    if 'centerline' in style_base:
                        style_base['centerline'] = dict(style_base['centerline'])
                        if 'start_orientation' in style_base['centerline']:
                            style_base['centerline']['start_orientation'] = dict(style_base['centerline']['start_orientation'])
                    if 'preview' in style_base:
                        style_base['preview'] = dict(style_base['preview'])
                    try:
                        cl = style_base.setdefault('centerline', {})
                        cl['start_trim'] = 0.0
                        cl['end_trim'] = 0.0
                        cl['protect_end_k'] = 0
                        cl['chaikin_iters'] = 0
                        cl['resample_points'] = 0
                        cl['smooth_window'] = 1
                        cl.setdefault('stroke_tilt', {})['range_deg'] = 0.0
                        cl.setdefault('post_scale', {})['range'] = 0.0
                        cl.setdefault('stroke_move', {})['offset'] = 0.0
                        so0 = cl.setdefault('start_orientation', {})
                        so0['angle_range_deg'] = 0.0
                        so0['end_angle_range_deg'] = 0.0
                        so0['end_frac_len'] = 1.0
                        so0.pop('corner_thresh_min_deg', None)
                        so0.pop('corner_thresh_max_deg', None)
                        so0['corner_thresh_deg'] = 35.0
                        so0.pop('frac_len', None)
                        so0.pop('isolate_on', None)
                        so0.pop('isolate_min_len', None)
                        so0.pop('start_region_frac', None)
                        so0.pop('end_region_frac', None)
                        so0.pop('fix_segments', None)
                        if 'preview' in style_base:
                            preview = style_base['preview']
                            preview.pop('fix_segments', None)
                            preview.pop('corner_range_on', None)
                            preview.pop('corner_min', None)
                            preview.pop('corner_max', None)
                    except Exception:
                        pass

                    proc0 = CenterlineProcessor(style_base, seed=seed)
                    med0 = proc0.process(med)
                    pts_proc0 = transform_medians(med0, rep_style)
                    svg_text0, dbg0 = _render_processed_centerline_svg_mixed(
                        pts_proc0, size=DEFAULT_SIZE, pad=DEFAULT_PAD,
                        style_json=None, short_mask=short_mask,
                        start_region_frac=None,
                        end_region_frac=None
                    )

                    # 使用D0的分段信息对D1着色，确保与"全部"一致
                    so_cfg = style.get('centerline', {}).get('start_orientation', {}) if isinstance(style, dict) else {}
                    preview_cfg = style.get('preview', {}) if isinstance(style, dict) else {}
                    corner_range_enabled = ('corner_thresh_min_deg' in so_cfg and 'corner_thresh_max_deg' in so_cfg)
                    if not corner_range_enabled:
                        corner_range_enabled = bool(preview_cfg.get('corner_range_on', False))

                    fixed_info_to_use = None if corner_range_enabled else dbg0

                    svg_text_d1, _debug_info_d1 = _render_processed_centerline_svg_mixed(
                        pts_processed, size=DEFAULT_SIZE, pad=DEFAULT_PAD,
                        style_json=style, short_mask=short_mask,
                        start_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('start_region_frac'),
                        end_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('end_region_frac'),
                        fixed_info=fixed_info_to_use
                    )

                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(svg_text_d1)
                except Exception:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
                
            elif image_type == 'D1':
                # D1类型: 网格变形 - 目标：由"现有C图"通过网格变形得到D1（不重新上色，不依赖D0）
                output_dir = os.path.join(OUTPUT_COMPARE, 'D1_grid_transform')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)
                
                try:
                    # 优先读取最近生成的C图，保证与界面显示的C颜色/样式完全一致
                    svg_c = None
                    try:
                        latest = latest_filenames_for_char(ch) or {}
                        c_name = latest.get('C')
                        if c_name:
                            c_path = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', c_name)
                            if os.path.exists(c_path):
                                with open(c_path, 'r', encoding='utf-8') as cf:
                                    svg_c = cf.read()
                    except Exception:
                        svg_c = None

                    # 若没有现成的C文件，则临时生成一个C（但依然不引入D0着色）
                    if not svg_c:
                        rep_style = (sampled[0] if sampled else style.get('global', {}))
                        proc = CenterlineProcessor(style, seed=seed)
                        med_processed = proc.process(med)
                        pts_processed = transform_medians(med_processed, rep_style)
                        svg_c = _render_centerline_svg_windowed(
                            pts_processed,
                            size=DEFAULT_SIZE, pad=DEFAULT_PAD,
                            start_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('start_region_frac', 0.30),
                            end_region_frac=style.get('centerline', {}).get('start_orientation', {}).get('end_region_frac', 0.30),
                            isolate_enabled=False,
                            isolate_min_len=0.0
                        )

                    # 若提供grid_state，则对C应用网格变形，输出为D1
                    if grid_state:
                        from web.services.grid_transform import apply_grid_deformation_to_svg
                        try:
                            # Phase 2：以矢量warp+可选栅格化双线性下采样，保证边缘平滑
                            # 使用改进的变形算法
                            from web.services.grid_transform import apply_smooth_grid_deformation
                            svg_d1 = apply_smooth_grid_deformation(svg_c, grid_state)
                        except Exception as e:
                            print(f"[D1] 网格变形失败，回退为未变形C: {e}")
                            svg_d1 = svg_c
                    else:
                        svg_d1 = svg_c

                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(svg_d1)
                        
                except Exception as e:
                    print(f"❌ [D1] 生成失败: {e}")
                    with open(output_path, 'w', encoding='utf-8') as f: 
                        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
            
            # 构造返回结果
            try:
                from flask import url_for
                if image_type == 'C':
                    url = url_for('serve_processed_centerline_c', filename=filename)
                elif image_type == 'D1':
                    url = url_for('serve_grid_transform', filename=filename)
            except RuntimeError:
                # 非Flask上下文
                folder_map = {
                    'C': 'C_processed_centerline',
                    'D1': 'D1_grid_transform'
                }
                url = f'/compare/{folder_map[image_type]}/{filename}'
            
            result = {
                image_type: url,
                'version': ts,
                'angles': []
            }
            
            print(f"✅ [SINGLE] 独立生成复杂类型 {image_type} 成功: {url}")
            return result
            
        except Exception as e:
            print(f"❌ [SINGLE] 独立生成复杂类型 {image_type} 失败: {str(e)}")
            raise Exception(f"生成 {image_type} 类型失败: {str(e)}")
    
    # 简单类型 A, B, D2 - 实现真正的独立生成
    print(f"⚡ [SINGLE] 独立生成类型: {image_type}")
    
    try:
        # 基础初始化 (从 generate_abcd 复制)
        import time
        from src.parser import load_glyph
        from src.classifier import classify_glyph  
        from src.styler import sample_hierarchical_style
        from src.centerline import CenterlineProcessor
        from src.transformer import transform_medians
        from src.parser import normalize_medians_1024
        from src.renderer import SvgRenderer
        from src.styler import build_rng
        
        # 加载字符数据 - 使用与generate_abcd相同的方法
        merged = load_merged_cache()
        meta = merged.get(ch)
        # Debug log removed
        if not meta:
            raise RuntimeError('char not found in merged data')
        
        # 加载样式
        style = _load_base_style()
        if style_override_path and os.path.exists(style_override_path):
            ov = _load_style_with_fallback(style_override_path, '覆盖')
            style = _merge_styles(style, ov)
        
        # 基础处理
        med = normalize_medians_1024(meta.get('medians', []))
        seed = _stable_seed_for_char(ch, style)
        rng = build_rng(seed)
        labels = classify_glyph(med)
        sampled = [sample_hierarchical_style(style.get('global', {}), style.get('stroke_types', {}), lb, rng, rng, rng, style.get('coherence', {})) for lb in labels]
        
        # 生成时间戳和文件名
        ts = time.strftime('%Y%m%d-%H%M%S') + f"-{int((time.time()%1)*1000):03d}"
        filename = f"{ts}_{ch}_{image_type}.svg"
        
        # 根据类型生成
        if image_type == 'A':
            # A类型: 轮廓
            outlines = meta.get('strokes', None)
            renderer = SvgRenderer(size_px=256, padding=8)
            rep_style = (sampled[0] if sampled else style.get('global', {}))
            
            output_dir = os.path.join(OUTPUT_COMPARE, 'A_outlines')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            pts = transform_medians(med, rep_style)
            renderer.render_char(pts, sampled, output_path, outlines=outlines, rep_style=rep_style, render_mode='auto')
            
        elif image_type == 'B':
            # B类型: 原始中轴
            # _render_centerline_svg_windowed is defined in this file
            
            output_dir = os.path.join(OUTPUT_COMPARE, 'B_raw_centerline')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            rep_style = (sampled[0] if sampled else style.get('global', {}))
            sr = float(style.get('centerline', {}).get('start_orientation', {}).get('start_region_frac', 0.30))
            er = float(style.get('centerline', {}).get('start_orientation', {}).get('end_region_frac', 0.30))
            iso_on = bool(style.get('centerline', {}).get('start_orientation', {}).get('isolate_on', False) or style.get('preview', {}).get('isolate_on', False))
            iso_min = float(style.get('centerline', {}).get('start_orientation', {}).get('isolate_min_len', style.get('preview', {}).get('isolate_min_len', 0.0)))
            
            svg_content = _render_centerline_svg_windowed(
                transform_medians(med, rep_style), 
                size=DEFAULT_SIZE, pad=DEFAULT_PAD, 
                start_region_frac=sr, end_region_frac=er, 
                isolate_enabled=iso_on, isolate_min_len=iso_min
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
                
        elif image_type == 'D2':
            # D2类型: 中轴填充
            renderer = SvgRenderer(size_px=256, padding=8)
            rep_style = (sampled[0] if sampled else style.get('global', {}))
            
            output_dir = os.path.join(OUTPUT_COMPARE, 'D2_median_fill')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            pts = transform_medians(med, rep_style)
            renderer.render_char(pts, sampled, output_path, render_mode='median_fill')
        
        # 构造返回结果
        try:
            from flask import url_for
            if image_type == 'A':
                url = url_for('serve_outlines', filename=filename)
            elif image_type == 'B':
                url = url_for('serve_raw_centerline', filename=filename)
            elif image_type == 'D2':
                url = url_for('serve_median_fill', filename=filename)
        except RuntimeError:
            # 非Flask上下文
            folder_map = {
                'A': 'A_outlines',
                'B': 'B_raw_centerline', 
                'D2': 'D2_median_fill'
            }
            url = f'/compare/{folder_map[image_type]}/{filename}'
        
        result = {
            image_type: url,
            'version': ts,
            'angles': []
        }
        
        print(f"✅ [SINGLE] 独立生成 {image_type} 成功: {url}")
        return result
        
    except Exception as e:
        print(f"❌ [SINGLE] 独立生成 {image_type} 失败: {str(e)}")
        raise Exception(f"生成 {image_type} 类型失败: {str(e)}")
