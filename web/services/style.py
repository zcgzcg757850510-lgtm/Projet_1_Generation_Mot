from __future__ import annotations
from typing import Dict, Any
import os
import json
from web.config import ROOT, BASE_STYLE


def build_style_override(form: Dict[str, Any], cookies: Dict[str, Any], prefer_form: bool = False) -> str:
    """Create a temp style JSON with overrides from UI toggles; return path.
    prefer_form=True means: missing checkboxes are treated as False (explicit uncheck),
    instead of falling back to cookies.
    """
    def get_bool(name: str, default: bool = False) -> bool:
        if prefer_form:
            return (name in form)
        if name in form:
            return True
        val = cookies.get(name)
        return (val == '1') if val is not None else default

    def get_num(name: str, default: float) -> float:
        v = (form.get(name) or (None if prefer_form else cookies.get(name)) or '')
        try:
            return float(v)
        except Exception:
            return default

    try:
        with open(BASE_STYLE, 'r', encoding='utf-8') as f:
            style = json.load(f)
    except FileNotFoundError:
        style = {}
    except Exception as e:
        print(f"[STYLE] ⚠️ 读取基础样式失败: {e}")
        style = {}
    base_style_loaded = bool(style)

    start_angle_on = get_bool('start_angle_on', False)
    start_angle = get_num('start_angle', 1.0)
    start_trim_on = get_bool('start_trim_on', False)
    start_trim = get_num('start_trim', 0.02)
    # 笔锋功能（与起笔功能对应）
    end_angle_on = get_bool('end_angle_on', False)
    end_angle = get_num('end_angle', 1.0)
    # middle/peak toggles (default OFF)
    end_trim_on = get_bool('end_trim_on', False)
    end_trim = get_num('end_trim', 0.0)

    chaikin_on = get_bool('chaikin_on', False)
    chaikin = int(get_num('chaikin', 1))
    smooth_on = get_bool('smooth_on', False)
    smooth = int(get_num('smooth', 3))
    tilt = get_bool('tilt', False)
    tilt_range = get_num('tilt_range', 0.0)
    move_on = get_bool('move_on', False)
    move_offset = get_num('move_offset', 0.0)
    pcv = get_bool('pcv', False)
    pcjitter = get_num('pcjitter', 0.12)

    # preview: Raw tri-color window (start/end fractions)
    raw_window_on = get_bool('raw_window_on', False)
    raw_start_frac = get_num('raw_start_frac', 0.30)
    raw_end_frac = get_num('raw_end_frac', 0.30)
    # isolation for Raw: whole-stroke purple for short strokes
    isolate_on = get_bool('isolate_on', False)
    isolate_min_len = get_num('isolate_min_len', 0.0)
    # corner angle range from UI only (no backend defaults)
    corner_range_on = get_bool('corner_range_on', False)
    def _get_opt_num_ui(name: str):
        v = (form.get(name) or (None if prefer_form else cookies.get(name)) or '').strip()
        try:
            return float(v)
        except Exception:
            return None
    ui_corner_min = _get_opt_num_ui('corner_min')
    ui_corner_max = _get_opt_num_ui('corner_max')
    fix_segments = get_bool('fix_segments', False)

    cl = style.setdefault('centerline', {})
    # Always keep start enabled by default; remove UI control
    cl['disable_start'] = False
    cl['start_trim'] = float(start_trim if start_trim_on else 0.0)
    cl['end_trim'] = float(end_trim if end_trim_on else 0.0)
    # 裁剪参数设置完成
    # 重要：避免保护起点抵消“起笔角度/裁剪起点”的效果
    cl['protect_start_k'] = 0

    cl['chaikin_iters'] = int(chaikin if chaikin_on else 0)
    cl['smooth_window'] = int(smooth if smooth_on else 1)
    cl['resample_points'] = 0  # 重采样功能已移除
    so = cl.setdefault('start_orientation', {})
    # UI 勾选后，使用用户值；未勾选则为 0（禁用）
    so['angle_range_deg'] = float(start_angle if start_angle_on else 0.0)
    # 旋转覆盖整个第一段
    so['frac_len'] = 1.0 if start_angle_on else 0.0
    
    # 笔锋角度配置（与起笔角度对应）
    so['end_angle_range_deg'] = float(end_angle if end_angle_on else 0.0)
    so['end_frac_len'] = 1.0 if end_angle_on else 0.0
    # corner angle range (min/max) strictly from UI when enabled; otherwise remove to avoid defaults
    if corner_range_on and (ui_corner_min is not None) and (ui_corner_max is not None):
        so['corner_thresh_min_deg'] = float(ui_corner_min)
        so['corner_thresh_max_deg'] = float(ui_corner_max)
    else:
        so.pop('corner_thresh_min_deg', None)
        so.pop('corner_thresh_max_deg', None)
    
    # 设置折点检测阈值（默认35度，钝角）
    so['corner_thresh_deg'] = 35.0
    
    # Fix segments switch (used by D 列以冻结分段边界)
    if fix_segments:
        so['fix_segments'] = True
    else:
        so.pop('fix_segments', None)
    # Mirror angle-range inputs into preview for D列逻辑读取（不改变启用条件，仅作为数据通道）
    style.setdefault('preview', {})['corner_range_on'] = bool(corner_range_on)
    if ui_corner_min is not None:
        style['preview']['corner_min'] = float(ui_corner_min)
    if ui_corner_max is not None:
        style['preview']['corner_max'] = float(ui_corner_max)
    style['preview']['fix_segments'] = bool(fix_segments)
    # Raw tri-color window from UI
    if raw_window_on:
        so['start_region_frac'] = float(max(0.0, min(0.9, raw_start_frac)))
        so['end_region_frac'] = float(max(0.0, min(0.9, raw_end_frac)))
    else:
        so.pop('start_region_frac', None)
        so.pop('end_region_frac', None)
    # Isolation settings (also mirror into preview for C列驱动)
    if isolate_on:
        so['isolate_on'] = True
        so['isolate_min_len'] = float(max(0.0, isolate_min_len))
        style.setdefault('preview', {})['isolate_on'] = True
        style['preview']['isolate_min_len'] = float(max(0.0, isolate_min_len))
    else:
        so.pop('isolate_on', None)
        so.pop('isolate_min_len', None)
        if 'preview' in style:
            style['preview'].pop('isolate_on', None)
            style['preview'].pop('isolate_min_len', None)

    # 倾斜：直接使用角度范围（-180~180）作为最终角度
    cl.setdefault('stroke_tilt', {})['range_deg'] = float(tilt_range if tilt else 0.0)
    # 删除缩放功能
    if 'post_scale' in cl:
        cl['post_scale']['range'] = 0.0
    cl.setdefault('stroke_move', {})['offset'] = float(move_offset if move_on else 0.0)

    style.setdefault('preview', {})['pc_variants'] = 3 if pcv else 1
    style['preview']['pc_jitter'] = float(pcjitter)

    if not base_style_loaded:
        print('[STYLE] ⚠️ 使用默认配置生成样式覆盖，部分设置可能缺失')

    cookie_vals = {
        'start_angle_on': '1' if start_angle_on else '0',
        'start_angle': str(start_angle),
        'start_trim_on': '1' if start_trim_on else '0', 'start_trim': str(start_trim),
        'end_angle_on': '1' if end_angle_on else '0',
        'end_angle': str(end_angle),
        'end_trim_on': '1' if end_trim_on else '0', 'end_trim': str(end_trim),
        'chaikin_on': '1' if chaikin_on else '0', 'chaikin': str(chaikin),
        'smooth_on': '1' if smooth_on else '0', 'smooth': str(smooth),
        'tilt': '1' if tilt else '0', 'tilt_range': str(tilt_range),
        'move_on': '1' if move_on else '0', 'move_offset': str(move_offset),
        'pcv': '1' if pcv else '0', 'pcjitter': str(pcjitter),

        'raw_window_on': '1' if raw_window_on else '0',
        'raw_start_frac': str(raw_start_frac),
        'raw_end_frac': str(raw_end_frac),
        'isolate_on': '1' if isolate_on else '0', 'isolate_min_len': str(isolate_min_len),
        'fix_segments': '1' if fix_segments else '0'
    }
    cookie_vals['corner_range_on'] = '1' if corner_range_on else '0'
    if corner_range_on and (ui_corner_min is not None):
        cookie_vals['corner_min'] = str(ui_corner_min)
    if corner_range_on and (ui_corner_max is not None):
        cookie_vals['corner_max'] = str(ui_corner_max)

    # write override json to tmp
    tmp_dir = os.path.join(ROOT, 'output', 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, 'style_overrides.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(style, f, ensure_ascii=False, separators=(',', ':'))
    return path, cookie_vals


def defaults_from_cookies(cookies) -> Dict[str, Any]:
    def gb(name: str, d=False):
        v = cookies.get(name)
        return (v == '1') if v is not None else d
    def gn(name: str, d: float):
        v = cookies.get(name)
        try:
            return float(v) if v is not None else d
        except:
            return d
    
    # URL decode the last_char cookie to handle Chinese characters properly
    last_char_raw = cookies.get('last_char', '')
    try:
        from urllib.parse import unquote
        last_char_decoded = unquote(last_char_raw) if last_char_raw else ''
    except:
        last_char_decoded = last_char_raw
    
    return dict(
        last_char=last_char_decoded,
        start_angle_on=gb('start_angle_on'), start_angle=gn('start_angle',1.0),
        start_trim_on=gb('start_trim_on'), start_trim=gn('start_trim',0.02), 
        end_trim_on=gb('end_trim_on'), end_trim=gn('end_trim',0.0),
        end_angle_on=gb('end_angle_on'), end_angle=gn('end_angle',1.0),
        chaikin_on=gb('chaikin_on'), chaikin=int(gn('chaikin',1)), 
        smooth_on=gb('smooth_on'), smooth=int(gn('smooth',3)),
        tilt=gb('tilt',True), tilt_k=int(gn('tilt_k',3)), tilt_range=gn('tilt_range',1.5),
        scale=gb('scale',True), scale_range=gn('scale_range',0.03),
        move_on=gb('move_on'), move_offset=gn('move_offset',0.0),
        pcv=gb('pcv', False), pcjitter=gn('pcjitter',0.12),

        corner_range_on=gb('corner_range_on', False),
        corner_min=gn('corner_min', 35.0), corner_max=gn('corner_max', 179.0),
        fix_segments=gb('fix_segments', False),
        raw_window_on=gb('raw_window_on', False),
        raw_start_frac=gn('raw_start_frac', 0.30), raw_end_frac=gn('raw_end_frac', 0.30),
        isolate_on=gb('isolate_on', False),
        isolate_min_len=gn('isolate_min_len', 0.0)
    )


