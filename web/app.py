from __future__ import annotations
from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, make_response, jsonify
from flask_cors import CORS
import threading
import logging
import subprocess
import sys
import os
import time
import json
from typing import List, Dict, Any
from web.routes.api import api_bp
from web.config import ROOT, OUTPUT_COMPARE, MERGED_JSON, BASE_STYLE
from web.services.files import latest_filenames_for_char, clean_compare_ab_only, clean_compare_all
from web.services.generation import generate_abcd, quick_raw_svg, build_processed_centerline_svg
from web.services.style import build_style_override, defaults_from_cookies

# moved to web.config

# 设置日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

LAST_BUILD_VERSION: str = "-"
BUILDING: bool = False

# 日志功能已移除

def _preview_version() -> str:
    try:
        p = os.path.join(OUTPUT_COMPARE, 'compare_preview.html')
        if os.path.exists(p):
            return time.strftime('%Y%m%d-%H%M%S', time.localtime(os.path.getmtime(p)))
    except Exception:
        pass
    return LAST_BUILD_VERSION

def _latest_compare_mtime() -> float:
    latest = 0.0
    for sub in ('A_outlines', 'D2_median_fill'):
        base = os.path.join(OUTPUT_COMPARE, sub)
        if not os.path.exists(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.lower().endswith('.svg'):
                    continue
                try:
                    latest = max(latest, os.path.getmtime(os.path.join(root, fn)))
                except Exception:
                    pass
    return latest

def _find_latest_for_char(ch: str) -> Dict[str, Any]:
    return latest_filenames_for_char(ch)

_MERGED_CACHE: Dict[str, Any] | None = None
def _load_merged_cache() -> Dict[str, Any]:
    from web.services.generation import load_merged_cache
    return load_merged_cache()

def _quick_raw_svg(ch: str, size: int = 220) -> str:
    return quick_raw_svg(ch, size)

def _build_processed_centerline_svg(ch: str, size: int = 220) -> str:
    return build_processed_centerline_svg(ch, size)

def generate_abcd(
    ch: str,
    style_override_path: str | None = None,
    *,
    grid_state: Dict[str, Any] | None = None,
    use_grid_deformation: bool = False
) -> Dict[str, str]:
    from web.services.generation import generate_abcd as _impl
    return _impl(
        ch,
        style_override_path=style_override_path,
        grid_state=grid_state,
        use_grid_deformation=use_grid_deformation,
    )
HTML = None

# Optional HTML override file to allow frontend edits without restarting server
HTML_PATH = os.path.join(ROOT, 'web', 'ui.html')

def get_html_template() -> str:
    try:
        if os.path.exists(HTML_PATH):
            with open(HTML_PATH, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception:
        pass
    return HTML

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)


# 日志功能已移除

logging.getLogger('werkzeug').setLevel(logging.WARNING)

@app.after_request
def add_no_cache_headers(resp):
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


def clean_compare_svgs() -> None:
    from web.services.files import clean_compare_ab_only
    clean_compare_ab_only()


def build_style_override_legacy(form: Dict[str, Any], cookies: Dict[str, Any], prefer_form: bool=False) -> str:
    """Create a temp style JSON with overrides from UI toggles; return path.
    prefer_form=True means: missing checkboxes are treated as False (explicit uncheck),
    instead of falling back to cookies.
    """
    def get_bool(name: str, default: bool=False) -> bool:
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

    with open(BASE_STYLE, 'r', encoding='utf-8') as f:
        style = json.load(f)

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
    resample_on = get_bool('resample_on', False)
    resample = int(get_num('resample', 64))
    tilt = get_bool('tilt', False)
    tilt_k = int(get_num('tilt_k', 3))
    tilt_range = get_num('tilt_range', 1.5)
    scale = get_bool('scale', False)
    scale_range = get_num('scale_range', 0.03)
    pcv = get_bool('pcv', False)
    pcjitter = get_num('pcjitter', 0.12)

    # preview: Raw tri-color window (start/end fractions)
    raw_window_on = get_bool('raw_window_on', False)
    raw_start_frac = get_num('raw_start_frac', 0.30)
    raw_end_frac = get_num('raw_end_frac', 0.30)
    # corner angle range from UI only (no backend defaults)
    corner_range_on = get_bool('corner_range_on', False)
    def _get_opt_num_ui(name: str):
        v = (request.form.get(name) or (None if prefer_form else cookies.get(name)) or '').strip()
        try:
            return float(v)
        except Exception:
            return None
    ui_corner_min = _get_opt_num_ui('corner_min')
    ui_corner_max = _get_opt_num_ui('corner_max')

    cl = style.setdefault('centerline', {})
    # Always keep start enabled by default; remove UI control
    cl['disable_start'] = False
    cl['start_trim'] = float(start_trim if start_trim_on else 0.0)
    cl['end_trim'] = float(end_trim if end_trim_on else 0.0)

    cl['chaikin_iters'] = int(chaikin if chaikin_on else 0)
    cl['smooth_window'] = int(smooth if smooth_on else 1)
    cl['resample_points'] = int(resample if resample_on else 0)
    so = cl.setdefault('start_orientation', {})
    so['angle_range_deg'] = float(start_angle if start_angle_on else 0.0)
    # 🔧 修复：添加缺失的frac_len参数
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
    # Raw tri-color window from UI
    if raw_window_on:
        so['start_region_frac'] = float(max(0.0, min(0.9, raw_start_frac)))
        so['end_region_frac'] = float(max(0.0, min(0.9, raw_end_frac)))
    else:
        so.pop('start_region_frac', None)
        so.pop('end_region_frac', None)

    cl.setdefault('stroke_tilt', {})['first_k'] = int(tilt_k)
    cl.setdefault('stroke_tilt', {})['range_deg'] = float(tilt_range if tilt else 0.0)
    cl.setdefault('post_scale', {})['range'] = float(scale_range if scale else 0.0)

    style.setdefault('preview', {})['pc_variants'] = 3 if pcv else 1
    style['preview']['pc_jitter'] = float(pcjitter)

    cookie_vals = {
        'start_angle_on': '1' if start_angle_on else '0',
        'start_angle': str(start_angle),
        'start_trim_on': '1' if start_trim_on else '0', 'start_trim': str(start_trim),
        'end_angle_on': '1' if end_angle_on else '0',
        'end_angle': str(end_angle),
        'end_trim_on': '1' if end_trim_on else '0', 'end_trim': str(end_trim),
        'chaikin_on': '1' if chaikin_on else '0', 'chaikin': str(chaikin),
        'smooth_on': '1' if smooth_on else '0', 'smooth': str(smooth),
        'resample_on': '1' if resample_on else '0', 'resample': str(resample),
        'tilt': '1' if tilt else '0', 'tilt_k': str(tilt_k), 'tilt_range': str(tilt_range),
        'scale': '1' if scale else '0', 'scale_range': str(scale_range),
        'pcv': '1' if pcv else '0', 'pcjitter': str(pcjitter),

        'raw_window_on': '1' if raw_window_on else '0',
        'raw_start_frac': str(raw_start_frac),
        'raw_end_frac': str(raw_end_frac)
    }
    cookie_vals['corner_range_on'] = '1' if corner_range_on else '0'
    if corner_range_on and (ui_corner_min is not None):
        cookie_vals['corner_min'] = str(ui_corner_min)
    if corner_range_on and (ui_corner_max is not None):
        cookie_vals['corner_max'] = str(ui_corner_max)

    tmp_dir = os.path.join(ROOT, 'output', 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, 'style_overrides.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(style, f, ensure_ascii=False, separators=(',', ':'))
    return path, cookie_vals


def run_main_generate(ch: str, style_path: str) -> int:
    args = [
        sys.executable, '-m', 'src.main',
        '--text', ch,
        '--seed', '131',
        '--merged-json', MERGED_JSON,
        '--style', style_path,
        '--outdir', os.path.join('output', 'compare'),
        '--compare',
    ]
    # 生成命令执行
    try:
        code = subprocess.call(args)
        return code
    except Exception as e:
        return 1


def rebuild_preview() -> int:
    try:
        sys.path.insert(0, ROOT)
        # 先用脚本生成 compare_preview.html（A/B 基础）
        import scripts.make_compare_preview as builder  # type: ignore
        builder.main()
        # 再确保 C/D 写入指定文件夹
        try:
            with open(os.path.join(OUTPUT_COMPARE, 'compare_preview.html'), 'r', encoding='utf-8') as f:
                html = f.read()
            # 简单提取页面中的文件名（NNN_字.svg），生成对应 C/D
            import re
            names = set(re.findall(r">(\d{3}_.+?\.svg)<", html))
            for name in names:
                ch = name.split('_',1)[-1].rsplit('.',1)[0]
                svgC = _quick_raw_svg(ch)
                svgD = _build_processed_centerline_svg(ch)
                if svgC:
                    pC = os.path.join(OUTPUT_COMPARE, 'B_raw_centerline', name)
                    os.makedirs(os.path.dirname(pC), exist_ok=True)
                    with open(pC, 'w', encoding='utf-8') as fc:
                        fc.write(svgC)
                if svgD:
                    pD = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', name)
                    os.makedirs(os.path.dirname(pD), exist_ok=True)
                    with open(pD, 'w', encoding='utf-8') as fd:
                        fd.write(svgD)
        except Exception as ee:
            pass
        return 0
    except Exception as e:
        return 1


# Build the form block separately to keep HTML cleaner
FORM_BLOCK = """
  <form method=\"post\" class=\"card\" onsubmit=\"setTimeout(()=>refreshPreview(),400);\">
    <div class=\"grid\">
      <label>字符：<input type=\"text\" name=\"char\" maxlength=\"1\" required placeholder=\"一\" value=\"{{last_char}}\"/></label>
      <div style=\"display:flex;gap:10px;align-items:center;flex-wrap:nowrap;overflow-x:auto\">
        <button type=\"submit\">生成对比</button>
        <button type=\"button\" onclick=\"restart()\">重启服务</button>
        <button type=\"button\" onclick=\"refreshPreview()\">刷新预览</button>
      </div>
    </div>
    <fieldset>
      <legend>中轴细化功能开关</legend>
      <div class=\"grid\">

        <label><input type=\"checkbox\" name=\"disable_start\" {{ 'checked' if disable_start else '' }}/> 取消起笔（裁掉首段）</label>
        <label><input type=\"checkbox\" name=\"start_ori\" {{ 'checked' if start_ori else '' }}/> 起笔方向</label>
        <label>角度±deg：<input type=\"number\" step=\"0.1\" name=\"start_angle\" value=\"{{start_angle}}\"></label>
        <label>起笔长度frac：<input type=\"number\" step=\"0.01\" name=\"start_frac\" value=\"{{start_frac}}\"></label>
        <label>trim start：<input type=\"number\" step=\"0.01\" name=\"start_trim\" value=\"{{start_trim}}\"></label>
        <label>trim end：<input type=\"number\" step=\"0.01\" name=\"end_trim\" value=\"{{end_trim}}\"></label>
        <label>保护起点K：<input type=\"number\" step=\"1\" name=\"keep_start\" value=\"{{keep_start}}\"></label>
        <label>保护终点K：<input type=\"number\" step=\"1\" name=\"keep_end\" value=\"{{keep_end}}\"></label>
        <label>chaikin：<input type=\"number\" step=\"1\" name=\"chaikin\" value=\"{{chaikin}}\"></label>
        <label>smooth：<input type=\"number\" step=\"1\" name=\"smooth\" value=\"{{smooth}}\"></label>
        <label>resample：<input type=\"number\" step=\"1\" name=\"resample\" value=\"{{resample}}\"></label>
        <label><input type=\"checkbox\" name=\"tilt\" {{ 'checked' if tilt else '' }}/> 笔画倾斜</label>
        <label>前K笔：<input type=\"number\" step=\"1\" name=\"tilt_k\" value=\"{{tilt_k}}\"></label>
        <label>倾斜±deg：<input type=\"number\" step=\"0.1\" name=\"tilt_range\" value=\"{{tilt_range}}\"></label>
        <label><input type=\"checkbox\" name=\"scale\" {{ 'checked' if scale else '' }}/> 笔画缩放</label>
        <label>缩放±：<input type=\"number\" step=\"0.01\" name=\"scale_range\" value=\"{{scale_range}}\"></label>
        <label><input type=\"checkbox\" name=\"pcv\" {{ 'checked' if pcv else '' }}/> Processed Centerline 变体x3</label>
        <label>变体抖动：<input type=\"number\" step=\"0.01\" name=\"pcjitter\" value=\"{{pcjitter}}\"></label>
      </div>
      <div class=\"help\">说明：未勾选功能将自动禁用或取0值；参数留空时使用默认。变体x3 会在预览中把 Processed Centerline 一列堆叠三条不同参数的中轴。</div>
    </fieldset>
  </form>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ch = (request.form.get('char') or '').strip()
        if len(ch) != 1:
            ctx = _defaults_from_cookies(request.cookies)
            return render_template_string(get_html_template(), ts=int(time.time()*1000), version=_preview_version(), form_block=render_template_string(FORM_BLOCK, **ctx), **ctx)
        clean_compare_svgs()
        style_path, cookie_vals = build_style_override(request.form, request.cookies, prefer_form=True)
        code = run_main_generate(ch, style_path)
        code |= rebuild_preview()
        resp = redirect(url_for('index', ts=int(time.time()*1000)))
        resp.set_cookie('last_char', ch, max_age=3600*24*365)
        for k, v in cookie_vals.items():
            resp.set_cookie(k, v, max_age=3600*24*365)
        resp.set_cookie('version', _preview_version(), max_age=3600*24*365)
        return resp
    ts = request.args.get('ts', str(int(time.time()*1000)))
    ctx = _defaults_from_cookies(request.cookies)
    ver = _preview_version()
    return render_template_string(get_html_template(), ts=ts, version=ver, form_block=render_template_string(FORM_BLOCK, **ctx), **ctx)


def _defaults_from_cookies(cookies) -> Dict[str, Any]:
    return defaults_from_cookies(cookies)


@app.route('/gen', methods=['GET', 'POST'])
def generate():
    try:
        if request.method == 'POST':
            # Handle POST request with grid state
            data = request.get_json()
            if data:
                ch = data.get('ch', data.get('char', request.args.get('ch', '分')))
                grid_state = data.get('grid_state', data.get('gridState'))
                gen_type = data.get('type', 'ABCD')
                logger.info(f"POST request - char: {ch}, type: {gen_type}, grid_state: {grid_state is not None}")
            else:
                ch = request.args.get('ch', '分')
                grid_state = None
                gen_type = request.args.get('type', 'ABCD')
        else:
            # Handle GET request
            ch = request.args.get('ch', request.args.get('char', '分'))
            grid_state = None
            gen_type = request.args.get('type', 'ABCD')
        
        logger.info(f"Generating for character: {ch}, type: {gen_type}")
        
        # Handle D2 generation specifically
        if gen_type == 'D2':
            return handle_d2_generation(ch, grid_state)
        
        # Clean existing SVG files before generation
        clean_compare_all()
        logger.info("Cleaned existing SVG files")
        
        # Build style parameters
        style_path, cookie_vals = build_style_override({}, request.cookies, prefer_form=False)
        
        # Create base_params dictionary
        base_params = {'style_path': style_path}
        
        # Add grid state to parameters if provided
        if grid_state:
            base_params['grid_state'] = grid_state
            logger.info(f"Added grid_state to base_params")
        
        # Generate ABCD comparison
        result = generate_abcd(ch, style_override_path=base_params.get('style_path'))
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Generation failed'}), 500
            
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def handle_d2_generation(ch, grid_state):
    """处理D2生成请求"""
    try:
        logger.info(f"开始D2生成 - 字符: {ch}")
        
        # Build style parameters
        style_path, cookie_vals = build_style_override({}, request.cookies, prefer_form=False)
        
        # Create base_params dictionary
        base_params = {'style_path': style_path}
        
        # Add grid state to parameters if provided
        if grid_state:
            base_params['grid_state'] = grid_state
            logger.info(f"D2生成包含网格状态")
        
        # Try to find existing D1 file first
        import glob
        d1_pattern = os.path.join('output', 'compare', 'C_processed_centerline', f"*_{ch}_d1.svg")
        d1_files = glob.glob(d1_pattern)
        
        if d1_files:
            # Use the most recent D1 file
            d1_path = max(d1_files, key=os.path.getmtime)
            logger.info(f"使用现有D1文件: {d1_path}")
        else:
            # Generate D1 if not found
            logger.info("未找到现有D1文件，开始生成D1...")
            result = generate_abcd(
                ch,
                style_override_path=style_path,
                grid_state=None,
                use_grid_deformation=False,
            )

            if not result or not result.get('D1'):
                logger.error("D1生成失败，无法继续D2生成")
                return jsonify({'success': False, 'error': 'D1生成失败，无法继续D2生成'})

            # Get D1 file path from result
            d1_url = result.get('D1')
            if not d1_url:
                logger.error("D1文件URL不存在，无法生成D2")
                return jsonify({'success': False, 'error': 'D1文件URL不存在，无法生成D2'})

            # Convert URL to file path
            if d1_url.startswith('/compare/C_processed_centerline/'):
                d1_filename = d1_url.replace('/compare/C_processed_centerline/', '')
            elif d1_url.startswith('/C_processed_centerline/'):
                d1_filename = d1_url.replace('/C_processed_centerline/', '')
            else:
                logger.error(f"无法解析D1文件路径: {d1_url}")
                return jsonify({'success': False, 'error': f'无法解析D1文件路径: {d1_url}'})

            # URL decode the filename to handle Chinese characters
            import urllib.parse
            d1_filename = urllib.parse.unquote(d1_filename)
            d1_path = os.path.join('output', 'compare', 'C_processed_centerline', d1_filename)
        
        if not os.path.exists(d1_path):
            logger.error(f"D1文件不存在: {d1_path}")
            return jsonify({'success': False, 'error': f'D1文件不存在: {d1_path}'})
        
        # Apply grid transformation if grid_state is provided
        if grid_state:
            try:
                # 统一调用高质量网格变形函数
                from web.services.grid_transform import apply_grid_deformation_to_svg
                
                # Read D1 SVG content
                with open(d1_path, 'r', encoding='utf-8') as f:
                    d1_content = f.read()
                
                # Apply grid transformation
                d2_content = apply_grid_deformation_to_svg(d1_content, grid_state)
                
                # Save D2 file
                d2_filename = f"{time.strftime('%Y%m%d_%H%M%S')}_{ch}_d2.svg"
                d2_dir = os.path.join('output', 'compare', 'C_processed_centerline')
                os.makedirs(d2_dir, exist_ok=True)
                d2_path = os.path.join(d2_dir, d2_filename)
                
                with open(d2_path, 'w', encoding='utf-8') as f:
                    f.write(d2_content)
                
                logger.info(f"D2生成成功: {d2_path}")
                
                return jsonify({
                    'success': True,
                    'filename': d2_filename,
                    'filepath': d2_path.replace('\\', '/'),
                    'file_path': d2_path.replace('\\', '/'),
                    'message': 'D2生成成功'
                })
                
            except Exception as e:
                logger.error(f"网格变形处理失败: {str(e)}")
                return jsonify({'success': False, 'error': f'网格变形处理失败: {str(e)}'})
        else:
            # No grid transformation, just copy D1 as D2
            d2_filename = f"{time.strftime('%Y%m%d_%H%M%S')}_{ch}_d2.svg"
            d2_dir = os.path.join('output', 'compare', 'C_processed_centerline')
            os.makedirs(d2_dir, exist_ok=True)
            d2_path = os.path.join(d2_dir, d2_filename)
            
            import shutil
            shutil.copy2(d1_path, d2_path)
            
            logger.info(f"D2生成成功(复制D1): {d2_path}")
            
            return jsonify({
                'success': True,
                'filename': d2_filename,
                'filepath': d2_path.replace('\\', '/'),
                'file_path': d2_path.replace('\\', '/'),
                'message': 'D2生成成功(无网格变形)'
            })
            
    except Exception as e:
        logger.error(f"D2生成失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_grid_state', methods=['POST'])
def save_grid_state():
    """保存网格状态到临时文件"""
    try:
        data = request.get_json()
        
        # 确保输出目录存在
        temp_dir = os.path.join('output', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存网格状态
        grid_state_file = os.path.join(temp_dir, 'grid_state.json')
        with open(grid_state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("网格状态已保存到临时文件")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"保存网格状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_d2', methods=['POST'])
def save_d2():
    try:
        data = request.get_json() or {}
        
        # 完全自动参数收集：后端自动获取字符和所有其他参数
        char = data.get('char', None)
        
        # 如果前端未传递字符，从最新D1文件中推断字符
        if not char:
            # 尝试从最新的D1文件推断当前字符
            import glob
            d1_pattern = os.path.join('output', 'compare', 'C_processed_centerline', "*_d1.svg")
            d1_files = glob.glob(d1_pattern)
            if d1_files:
                # 获取最新的D1文件
                latest_d1 = max(d1_files, key=os.path.getmtime)
                # 从文件名中提取字符
                filename = os.path.basename(latest_d1)
                # 文件名格式: 时间戳_字符_d1.svg
                parts = filename.split('_')
                if len(parts) >= 2:
                    char = parts[1]  # 获取字符部分
                    logger.info(f"从最新D1文件推断字符: {char}")
                else:
                    char = '的'
                    logger.info("无法从D1文件名推断字符，使用默认字符")
            else:
                char = '的'
                logger.info("未找到D1文件，使用默认字符")
        
        logger.info(f"收到D2生成请求: 字符={char}")
        
        # 后端自动收集网格状态和画布尺寸
        # 从session、文件或其他持久化存储中获取
        grid_state = {}
        canvas_dimensions = {'width': 800, 'height': 600}
        
        # 尝试从临时文件获取最新的网格状态
        try:
            import json
            grid_state_file = os.path.join('output', 'temp', 'grid_state.json')
            if os.path.exists(grid_state_file):
                with open(grid_state_file, 'r', encoding='utf-8') as f:
                    saved_state = json.load(f)
                    grid_state = saved_state.get('grid_state', {})
                    canvas_dimensions = saved_state.get('canvas_dimensions', {'width': 800, 'height': 600})
                    logger.info("从临时文件获取网格状态")
            else:
                logger.info("未找到网格状态文件，使用默认状态")
        except Exception as e:
            logger.warning(f"读取网格状态文件失败: {e}")
        
        # 向后兼容：如果前端传递了参数，优先使用前端数据
        if 'grid_state' in data and data['grid_state']:
            grid_state = data.get('grid_state', {})
            canvas_dimensions = data.get('canvas_dimensions', {'width': 800, 'height': 600})
            logger.info("使用前端传递的网格状态（兼容模式）")
        
        # 记录最终使用的状态
        if grid_state and grid_state.get('controlPoints'):
            logger.info("将应用网格变形效果")
        else:
            logger.info("无网格变形状态，生成标准D2")
        
        if grid_state:
            logger.info(f"网格状态详情:")
            logger.info(f"  - 控制点数量: {len(grid_state.get('controlPoints', []))}")
            logger.info(f"  - 网格尺寸: {grid_state.get('size', '未知')}")
            logger.info(f"  - 变形强度: {grid_state.get('deformStrength', '未知')}")
        else:
            logger.info("无网格变形状态，生成标准D2")
        
        logger.info(f"画布尺寸: {canvas_dimensions['width']}x{canvas_dimensions['height']}")
        
        # 自动搜索D1文件
        import glob
        d1_pattern = os.path.join('output', 'compare', 'C_processed_centerline', f"*{char}*_d1.svg")
        d1_files = glob.glob(d1_pattern)
        logger.info(f"搜索D1文件: 模式={d1_pattern}, 找到={len(d1_files)}个文件")
        
        if not d1_files:
            # 如果没有D1文件，尝试自动生成
            logger.info(f"未找到D1文件，尝试自动生成...")
            try:
                # 调用生成接口自动生成D0/D1
                from web.services.generation import generate_character_svg
                result = generate_character_svg(char, {})
                if result.get('D1') or result.get('D'):
                    logger.info("D1文件自动生成成功，重新搜索...")
                    d1_files = glob.glob(d1_pattern)
                    if not d1_files:
                        return jsonify({
                            'success': False,
                            'error': f'自动生成D1文件失败，请先手动生成对比'
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'未找到字符 "{char}" 的D1文件，且自动生成失败，请先生成对比'
                    })
            except Exception as e:
                logger.error(f"自动生成D1失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'未找到字符 "{char}" 的D1文件，请先生成对比'
                })
        
        # 获取最新D1文件
        latest_d1 = max(d1_files, key=os.path.getmtime)
        logger.info(f"使用D1文件: {latest_d1}")
        
        # 读取D1内容
        try:
            with open(latest_d1, 'r', encoding='utf-8') as f:
                d1_content = f.read()
            logger.info(f"D1文件读取成功，内容长度: {len(d1_content)}")
        except Exception as e:
            logger.error(f"读取D1文件失败: {e}")
            return jsonify({
                'success': False,
                'error': f'读取D1文件失败: {str(e)}'
            })
        
        # 生成D2文件名
        import time
        ts = time.strftime('%Y%m%d-%H%M%S') + f"-{int((time.time()%1)*1000):03d}"
        d2_filename = f"{ts}_{char}_d2.svg"
        d2_filepath = os.path.join('output', 'compare', 'C_processed_centerline', d2_filename)
        
        # 应用网格变形生成D2
        try:
            from web.services.grid_transform import transform_d1_to_d2
            
            # 使用网格变形算法处理D1内容，传递画布尺寸
            d2_content = transform_d1_to_d2(d1_content, grid_state, canvas_dimensions)
            logger.info(f"网格变形处理完成，内容长度: {len(d2_content)}")
            
            # 保存D2文件
            with open(d2_filepath, 'w', encoding='utf-8') as f:
                f.write(d2_content)
            logger.info(f"D2文件生成成功: {d2_filepath}")
            
            return jsonify({
                'success': True,
                'file_path': d2_filepath,
                'filename': d2_filename,
                'char': char,
                'has_deformation': bool(grid_state),
                'auto_generated_d1': len(d1_files) == 0  # 标记是否自动生成了D1
            })
            
        except Exception as e:
            logger.error(f"保存D2文件失败: {e}")
            return jsonify({
                'success': False,
                'error': f'保存D2文件失败: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"D2生成接口异常: {str(e)}")
        return jsonify({'success': False, 'error': f'接口异常: {str(e)}'})


@app.route('/api/gen', methods=['POST'])
def api_generate():
    """生成字符的所有变体 - 新的API接口"""
    print("="*50)
    print(f"[API/GEN] 收到生成请求!")
    try:
        data = request.get_json()
        print(f"[API/GEN] 请求数据: {data}")
        if not data:
            return jsonify({'error': '请求数据格式错误'}), 400
            
        char = data.get('char', '').strip()
        print(f"[API/GEN] 字符: {char}")
        
        if not char:
            return jsonify({'error': '字符不能为空'}), 400
        
        if len(char) != 1:
            return jsonify({'error': '请输入单个字符'}), 400
            
        # 在生成前强制清理所有旧文件
        print(f"🔧 [API] api_generate: 准备清理SVG文件")
        try:
            from web.services.generation import cleanup_old_svg_files
            cleanup_old_svg_files(max_files_per_dir=0)  # 完全清空
            print(f"🔧 [API] api_generate: 清理完成，开始生成")
        except Exception as cleanup_error:
            print(f"🔧 [API] 清理失败: {cleanup_error}")
            # 继续执行，不因清理失败而中断
        
        # 获取当前样式配置
        style_path, _ = build_style_override({}, request.cookies, prefer_form=False)

        # 获取网格状态 - 优先从请求体，然后尝试文件
        grid_state = data.get('grid_state')
        
        if not grid_state:
            # 回退到文件读取（兼容性）
            from web.services.grid_state import load_grid_state
            grid_state = load_grid_state()
            print(f"[DEBUG] Grid state from file - grid_state: {bool(grid_state)}")
        else:
            print(f"[DEBUG] Grid state from request - grid_state: {bool(grid_state)}")

        # 生成所有变体，传入网格状态（generate_abcd内部会自行判断是否应用变形）
        urls = generate_abcd(
            char,
            style_override_path=style_path,
            grid_state=grid_state,
            use_grid_deformation=bool(grid_state),  # 保持参数兼容性，但实际逻辑在generate_abcd中
        )
        
        if urls:
            return jsonify({
                'success': True,
                'urls': urls,
                'message': '生成成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '生成失败'
            }), 500
            
    except Exception as e:
        logger.error(f"生成失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gen_single', methods=['POST'])
def api_generate_single():
    """生成单个类型的图像"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据格式错误'}), 400
            
        char = data.get('char', '').strip()
        image_type = data.get('type', '').strip()
        
        if not char:
            return jsonify({'error': '字符不能为空'}), 400
        
        if len(char) != 1:
            return jsonify({'error': '请输入单个字符'}), 400
            
        if image_type not in ['A', 'B', 'C', 'D1', 'D2']:
            return jsonify({'error': '无效的图像类型'}), 400
            
        # 在生成前强制清理该类型的旧文件
        print(f"🔧 [API] api_generate_single: 准备清理SVG文件 (类型: {image_type})")
        try:
            from web.services.generation import cleanup_single_type_svg_files
            cleanup_single_type_svg_files(image_type, max_files_per_dir=0)  # 完全清空该类型
            print(f"🔧 [API] api_generate_single: 清理完成，开始生成")
        except Exception as cleanup_error:
            print(f"🔧 [API] 清理失败: {cleanup_error}")
            # 继续执行，不因清理失败而中断
        
        # 获取当前样式配置
        style_path, _ = build_style_override({}, request.cookies, prefer_form=False)
        
        # 生成单个类型的图像（支持可选的grid_state）
        from web.services.generation import generate_single_type
        grid_state = data.get('grid_state')
        urls = generate_single_type(char, image_type, style_override_path=style_path, grid_state=grid_state)

        # 如果生成C图，并且启用了chaikin/smooth等细化功能，则立即触发一次C生成以刷新角度数据
        if image_type == 'C' and urls.get('C'):
            try:
                generate_abcd(char, style_override_path=style_path)
            except Exception as e:
                logger.warning(f"重生成ABCD以同步角度数据失败: {e}")
        
        if urls:
            # generate_single_type 已经返回了正确的类型
            url = urls.get(image_type)
            if url:
                return jsonify({
                    'success': True,
                    'url': url,
                    # 'base_url': urls.get('D1_base') if image_type == 'D1' else None,  # 不再返回基础版本
                    'message': f'{image_type}图生成成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'未找到{image_type}图像URL'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'{image_type}图生成失败'
            }), 500
            
    except Exception as e:
        logger.error(f"单个图像生成失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/gen_legacy', methods=['GET', 'POST'])
def generate_legacy():
    """Legacy generation endpoint for backward compatibility"""
    try:
        ch = request.args.get('ch', '分')
        base_params = {}
        style_path, cookie_vals = build_style_override(base_params, request.cookies, prefer_form=False)
        print(f"[FLASK_DEBUG] 样式参数文件路径: {style_path}")
        urls = None
        err_msg = None
        try:
            urls = generate_abcd(ch, style_override_path=style_path)
            # 不再在生成接口内重建预览，避免与静态文件读写竞争导致连接重置
        except Exception as e:
            err_msg = str(e)
            pass
        finally:
            BUILDING = False
        if not urls:
            return jsonify({'error': err_msg or 'generate failed'}), 500
        resp = make_response(jsonify(urls))
        resp.set_cookie('last_char', ch, max_age=3600*24*365)
        for k, v in cookie_vals.items():
            resp.set_cookie(k, v, max_age=3600*24*365)
        resp.set_cookie('version', _preview_version(), max_age=3600*24*365)
        return resp
    except Exception as e:
        logger.error(f"Legacy generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_d0_svg')
def get_d0_svg():
    """获取D0 SVG内容用于网格变形"""
    ch = (request.args.get('ch') or '').strip()
    if len(ch) != 1:
        return jsonify({'error': 'param ch must be 1 char'}), 400
    
    try:
        # 使用当前参数生成D0 SVG
        style_path, _ = build_style_override({}, request.cookies, prefer_form=False)
        urls = generate_abcd(ch, style_override_path=style_path)
        
        if not urls:
            return jsonify({'error': 'Generation failed'}), 500
        
        # 首先尝试使用D0 URL
        d0_url = urls.get('D0')
        d0_path = None
        
        if d0_url:
            # 从URL中提取文件名
            filename = d0_url.split('/')[-1]
            d0_path = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', filename)
        
        # 如果D0文件不存在，尝试查找以_orig.svg结尾的文件
        if not d0_path or not os.path.exists(d0_path):
            d_dir = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline')
            if os.path.exists(d_dir):
                # 查找最新的_orig.svg文件（D0文件）
                orig_files = [f for f in os.listdir(d_dir) if f.endswith('_orig.svg') and ch in f]
                if orig_files:
                    # 按修改时间排序，取最新的
                    orig_files.sort(key=lambda x: os.path.getmtime(os.path.join(d_dir, x)), reverse=True)
                    d0_path = os.path.join(d_dir, orig_files[0])
        
        if not d0_path or not os.path.exists(d0_path):
            return jsonify({'error': 'D0 SVG file not found'}), 404
        
        with open(d0_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        return jsonify({
            'svg_content': svg_content,
            'url': d0_url,
            'character': ch
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/preview')
def preview():
    p = os.path.join(OUTPUT_COMPARE, 'compare_preview.html')
    if not os.path.exists(p):
        return '<p>还没有生成预览，请先在上方输入单字并点击生成。</p>'
    # Set strong no-cache headers and append latest mtime as anti-cache param in HTML itself
    mtime = _latest_compare_mtime()
    with open(p, 'r', encoding='utf-8') as f:
        html = f.read()
    # Inject a meta tag with version query to bust cache of <img> if needed (browsers may cache aggressively)
    meta = f"<meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\"><meta name=\"x-preview-ts\" content=\"{int(mtime)}\">"
    if '<meta charset' in html:
        html = html.replace("<meta charset='utf-8'>", "<meta charset='utf-8'>" + meta)
    else:
        html = meta + html
    resp = make_response(html)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/quick_raw')
def quick_raw():
    ch = (request.args.get('ch') or '').strip()
    if len(ch) != 1:
        return '<p>请输入单个汉字</p>', 400
    svg = _quick_raw_svg(ch)
    return f"<!doctype html><meta charset='utf-8'><title>Quick Raw</title>{svg}"

@app.route('/status')
def status():
    ch = (request.args.get('ch') or '').strip()
    files = _find_latest_for_char(ch) if len(ch) == 1 else {}
    return {'building': BUILDING, 'version': _preview_version(), 'files': files}


@app.route('/find_d_files')
def find_d_files():
    ch = (request.args.get('ch') or '').strip()
    file_type = (request.args.get('type') or '').strip()
    
    if len(ch) != 1:
        return {'files': []}
    
    d_dir = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline')
    if not os.path.exists(d_dir):
        return {'files': []}
    
    try:
        files = os.listdir(d_dir)
        matching_files = []
        
        # 收集所有匹配的文件
        for filename in files:
            if not filename.endswith('.svg'):
                continue
                
            # 对于d1类型，查找包含字符和"d1"的SVG文件
            if file_type == 'd1' and f"_{ch}_d1" in filename and filename.endswith('.svg'):
                matching_files.append(filename)
            elif file_type == 'orig' and f"_{ch}_orig" in filename and filename.endswith('.svg'):
                matching_files.append(filename)
            elif file_type == 'd2' and f"_{ch}_d2" in filename and filename.endswith('.svg'):
                matching_files.append(filename)
        
        # 如果找到匹配文件，返回最新的（按文件名中时间戳排序）
        if matching_files:
            # 按文件名中的时间戳排序，最新的在前
            # 文件名格式：YYYYMMDD-HHMMSS-mmm_字符_类型.svg
            def extract_timestamp(filename):
                try:
                    # 提取文件名开头的时间戳部分
                    timestamp_part = filename.split('_')[0]
                    return timestamp_part
                except:
                    return '00000000-000000-000'
            
            matching_files.sort(key=extract_timestamp, reverse=True)
            latest_file = matching_files[0]
            print(f"[FIND_D_FILES] 找到 {len(matching_files)} 个{file_type}文件，按时间戳排序返回最新的: {latest_file}")
            return {'files': [latest_file]}
                
    except Exception as e:
        print(f"Error finding D files: {e}")
        
    return {'files': []}


@app.route('/api/list-d-files')
def list_d_files():
    """列出C_processed_centerline目录中的所有文件"""
    d_dir = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline')
    if not os.path.exists(d_dir):
        return {'files': []}
    
    try:
        files = os.listdir(d_dir)
        svg_files = [f for f in files if f.endswith('.svg')]
        return {'files': svg_files}
    except Exception as e:
        print(f"Error listing D files: {e}")
        return {'files': []}


# 日志路由已移除


@app.route('/restart', methods=['POST'])
def restart():
    # 服务器重启请求
    python = sys.executable
    script = os.path.join(ROOT, 'web', 'app.py')
    os.execv(python, [python, script])


@app.route('/A_outlines/<path:filename>')
def serve_outlines(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'A_outlines', filename)
    if not os.path.exists(full):
        pass
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'A_outlines'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp


@app.route('/rebuild', methods=['POST'])
def rebuild_endpoint():
    code = rebuild_preview()
    return ("ok", 200) if code == 0 else ("err", 500)


@app.route('/B_raw_centerline/<path:filename>')
def serve_raw_centerline(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'B_raw_centerline', filename)
    if not os.path.exists(full):
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'B_raw_centerline'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/C_processed_centerline/<path:filename>')
def serve_processed_centerline_c(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', filename)
    if not os.path.exists(full):
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'C_processed_centerline'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/D1_grid_transform/<path:filename>')
def serve_grid_transform(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'D1_grid_transform', filename)
    if not os.path.exists(full):
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'D1_grid_transform'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/D2_median_fill/<path:filename>')
def serve_median_fill(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'D2_median_fill', filename)
    if not os.path.exists(full):
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'D2_median_fill'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp

# Ancienne route pour compatibilité
@app.route('/B_raw_centerline/<path:filename>')
def serve_raw_centerline_old(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'B_raw_centerline', filename)
    if not os.path.exists(full):
        pass
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'B_raw_centerline'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp


@app.route('/C_processed_centerline/<path:filename>')
def serve_processed_centerline(filename: str):
    full = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', filename)
    if not os.path.exists(full):
        return ("not found", 404)
    resp = make_response(send_from_directory(os.path.join(OUTPUT_COMPARE, 'C_processed_centerline'), filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    return resp


# --- 路由别名：支持 /compare/... 与 /@compare/... 前缀 ---
@app.route('/compare/A_outlines/<path:filename>')
def serve_outlines_compare(filename: str):
    return serve_outlines(filename)

@app.route('/compare/D2_median_fill/<path:filename>')
def serve_median_fill_compare(filename: str):
    return serve_median_fill(filename)

@app.route('/compare/B_raw_centerline/<path:filename>')
def serve_raw_centerline_compare(filename: str):
    return serve_raw_centerline(filename)

@app.route('/compare/C_processed_centerline/')
def list_processed_centerline_files():
    """列出C_processed_centerline目录下的所有文件"""
    try:
        directory = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline')
        if not os.path.exists(directory):
            return "Directory not found", 404
        
        files = []
        for filename in os.listdir(directory):
            if filename.endswith('.svg'):
                files.append(filename)
        
        # 生成简单的HTML列表供前端解析
        html = '<html><body>'
        for filename in sorted(files):
            html += f'<a href="{filename}">{filename}</a><br>'
        html += '</body></html>'
        
        return html
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/compare/C_processed_centerline/<path:filename>')
def serve_processed_centerline_compare(filename: str):
    return serve_processed_centerline(filename)

@app.route('/@compare/A_outlines/<path:filename>')
def serve_outlines_at_compare(filename: str):
    return serve_outlines(filename)

@app.route('/@compare/D2_median_fill/<path:filename>')
def serve_median_fill_at_compare(filename: str):
    return serve_median_fill(filename)

@app.route('/@compare/B_raw_centerline/<path:filename>')
def serve_raw_centerline_at_compare(filename: str):
    return serve_raw_centerline(filename)

@app.route('/@compare/C_processed_centerline/<path:filename>')
def serve_processed_centerline_at_compare(filename: str):
    return serve_processed_centerline(filename)

@app.route('/output/compare/C_processed_centerline/<path:filename>')
def serve_output_processed_centerline(filename: str):
    return serve_processed_centerline(filename)


@app.route('/save_grid_template', methods=['POST'])
def save_grid_template():
    """保存网格变形模板"""
    try:
        data = request.get_json()
        template_name = data.get('templateName', '').strip()
        template_data = data.get('templateData', {})
        
        if not template_name:
            return jsonify({'success': False, 'error': '模板名称不能为空'}), 400
        
        # 创建保存目录
        template_dir = os.path.join(ROOT, 'output', 'grid_templates')
        os.makedirs(template_dir, exist_ok=True)
        
        # 保存模板数据到文件
        template_file = os.path.join(template_dir, f'{template_name}.json')
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        
        print(f"[GRID_TEMPLATE] 已保存网格变形模板 '{template_name}' 到 {template_file}")
        return jsonify({'success': True, 'message': f'变形模板 {template_name} 已保存'})
        
    except Exception as e:
        print(f"[GRID_TEMPLATE] 保存变形模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/load_grid_template')
def load_grid_template():
    """加载网格变形模板"""
    try:
        template_name = request.args.get('templateName', '').strip()
        
        if not template_name:
            return jsonify({'success': False, 'error': '模板名称不能为空'}), 400
        
        template_file = os.path.join(ROOT, 'output', 'grid_templates', f'{template_name}.json')
        
        if not os.path.exists(template_file):
            return jsonify({'success': False, 'error': '没有找到变形模板'})
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        print(f"[GRID_TEMPLATE] 已加载网格变形模板 '{template_name}'")
        return jsonify({'success': True, 'templateData': template_data})
        
    except Exception as e:
        print(f"[GRID_TEMPLATE] 加载变形模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/list_grid_templates')
def list_grid_templates():
    """获取所有可用的网格变形模板"""
    try:
        template_dir = os.path.join(ROOT, 'output', 'grid_templates')
        
        if not os.path.exists(template_dir):
            return jsonify({'success': True, 'templates': []})
        
        templates = []
        for filename in os.listdir(template_dir):
            if filename.endswith('.json'):
                template_name = filename[:-5]  # 移除.json后缀
                template_file = os.path.join(template_dir, filename)
                
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    templates.append({
                        'name': template_name,
                        'gridSize': template_data.get('gridSize', 4),
                        'timestamp': template_data.get('timestamp', '未知'),
                        'description': template_data.get('description', '无描述')
                    })
                except Exception:
                    continue  # 跳过损坏的模板文件
        
        # 按时间戳排序
        templates.sort(key=lambda x: x['timestamp'], reverse=True)
        
        print(f"[GRID_TEMPLATE] 找到 {len(templates)} 个变形模板")
        return jsonify({'success': True, 'templates': templates})
        
    except Exception as e:
        print(f"[GRID_TEMPLATE] 获取模板列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    """将SVG转换为PDF"""
    try:
        data = request.get_json()
        svg_url = data.get('svg_url')
        
        if not svg_url:
            return jsonify({'success': False, 'error': '缺少SVG URL'}), 400
        
        print(f"[PDF] 开始生成PDF，SVG URL: {svg_url}")
        
        # 从URL获取SVG文件路径
        # SVG URL格式: /compare/articles/article_xxx.svg
        svg_filename = svg_url.split('/')[-1]
        svg_path = os.path.join('output', 'compare', 'articles', svg_filename)
        
        if not os.path.exists(svg_path):
            return jsonify({'success': False, 'error': f'SVG文件不存在: {svg_path}'}), 404
        
        # 生成PDF文件名
        pdf_filename = svg_filename.replace('.svg', '.pdf')
        pdf_path = os.path.join('output', 'compare', 'articles', pdf_filename)
        
        # 方法1: 尝试使用cairosvg将SVG转换为PDF
        try:
            import cairosvg
            
            # 读取SVG内容
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # 转换为PDF
            cairosvg.svg2pdf(
                bytestring=svg_content.encode('utf-8'),
                write_to=pdf_path,
                output_width=794,  # A4宽度
                output_height=1123  # A4高度
            )
            
            print(f"[PDF] PDF生成成功 (cairosvg): {pdf_path}")
            
            # 返回PDF URL
            pdf_url = f"/compare/articles/{pdf_filename}"
            
            return jsonify({
                'success': True,
                'pdf_url': pdf_url,
                'pdf_path': pdf_path,
                'method': 'cairosvg'
            })
            
        except (ImportError, OSError) as e:
            print(f"[PDF] cairosvg方法失败: {e}")
            
            # 方法2: 生成HTML包装的SVG文件作为替代方案
            try:
                # 读取SVG内容
                with open(svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # 创建HTML包装的文件
                html_filename = svg_filename.replace('.svg', '_printable.html')
                html_path = os.path.join('output', 'compare', 'articles', html_filename)
                
                # 清理SVG内容，确保正确的XML格式
                import html
                svg_content = html.escape(svg_content).replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#x27;', "'")
                
                # 生成可打印的HTML文件
                html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文章预览</title>
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: white;
            font-family: Arial, sans-serif;
        }}
        .svg-container {{
            width: 210mm;
            height: 297mm;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid #ddd;
            background: white;
        }}
        svg {{
            max-width: 100%;
            max-height: 100%;
            display: block;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .svg-container {{
                border: none;
            }}
        }}
        .print-instructions {{
            position: fixed;
            top: 10px;
            right: 10px;
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            color: #666;
        }}
        @media print {{
            .print-instructions {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="print-instructions">
        Press Ctrl+P to print or save as PDF
    </div>
    <div class="svg-container">
        {svg_content}
    </div>
    <script>
        function autoPrint() {{
            if (window.location.search.includes('autoprint=true')) {{
                setTimeout(function() {{
                    window.print();
                }}, 1000);
            }}
        }}
        window.addEventListener('load', autoPrint);
    </script>
</body>
</html>'''
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"[PDF] HTML替代方案生成成功: {html_path}")
                
                # 返回HTML URL
                html_url = f"/compare/articles/{html_filename}"
                
                return jsonify({
                    'success': True,
                    'pdf_url': html_url,
                    'pdf_path': html_path,
                    'method': 'html_fallback',
                    'message': 'PDF生成功能不可用，已生成可打印的HTML文件。您可以在浏览器中打开并使用"打印"功能保存为PDF。'
                })
                
            except Exception as html_error:
                print(f"[PDF] HTML替代方案也失败: {html_error}")
                return jsonify({
                    'success': False, 
                    'error': f'PDF生成失败，HTML替代方案也失败: {str(html_error)}',
                    'suggestion': '请尝试手动下载SVG文件，然后使用在线转换工具转换为PDF'
                }), 500
                
        except Exception as e:
            print(f"[PDF] PDF转换失败: {e}")
            return jsonify({'success': False, 'error': f'PDF转换失败: {str(e)}'}), 500
            
    except Exception as e:
        print(f"[PDF] PDF生成请求处理失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/generate_font_sample', methods=['POST'])
def generate_font_sample():
    """生成字体样例的API端点"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        # 获取参数 (支持两种命名格式)
        font_type = data.get('font_type') or data.get('fontType', 'D1')
        font_size = int(data.get('font_size') or data.get('fontSize', 40))
        line_spacing = int(data.get('line_spacing') or data.get('lineSpacing', 40))
        char_spacing = int(data.get('char_spacing') or data.get('charSpacing', 30))
        sample_text = data.get('sample_text') or data.get('sampleText', '春江潮水连海平海上明月共潮生')
        
        print(f"[SAMPLE] Paramètres reçus: type={font_type}, size={font_size}, line={line_spacing}, char={char_spacing}")
        
        # 生成字体样例SVG
        sample_svg = generate_font_sample_svg(sample_text, font_type, font_size, line_spacing, char_spacing)
        
        if not sample_svg:
            return jsonify({'success': False, 'error': 'SVG样例生成失败'}), 500
        
        # 使用绝对路径确保文件保存正确
        font_samples_dir = os.path.join(os.getcwd(), 'web', 'assets', 'font-samples')
        
        # 确保目录存在
        os.makedirs(font_samples_dir, exist_ok=True)
        
        # 清理旧的样例文件
        try:
            import glob
            old_files = glob.glob(os.path.join(font_samples_dir, f'sample_{font_type}_*.svg'))
            for old_file in old_files:
                try:
                    os.remove(old_file)
                    print(f"[SAMPLE] 删除旧文件: {os.path.basename(old_file)}")
                except Exception as e:
                    print(f"[SAMPLE] 删除文件失败: {e}")
            
            if old_files:
                print(f"[SAMPLE] 清理了 {len(old_files)} 个旧的 {font_type} 样例文件")
            else:
                print(f"[SAMPLE] 没有找到需要清理的 {font_type} 样例文件")
                
        except Exception as e:
            print(f"[SAMPLE] 清理旧文件时出错: {e}")
        
        # 保存新的样例文件
        timestamp = int(time.time() * 1000)
        sample_filename = f"sample_{font_type}_{timestamp}.svg"
        sample_path = os.path.join(font_samples_dir, sample_filename)
        
        print(f"[SAMPLE] 保存新样例文件到: {sample_path}")
        
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write(sample_svg)
            
        print(f"[SAMPLE] 新样例文件保存成功: {sample_filename}")
        
        result = {
            'success': True,
            'sample_url': f'/assets/font-samples/{sample_filename}',
            'sample_path': sample_path,
            'message': f'{font_type}字体样例生成成功'
        }
        
        return jsonify(result)
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/generate_article', methods=['POST'])
def generate_article():
    """生成文章图片的API端点"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
        
        if len(text) > 100:
            return jsonify({'success': False, 'error': '文本长度不能超过100个字符'}), 400
        
        # 获取参数
        font_size = int(data.get('fontSize', 40))
        line_spacing = int(data.get('lineSpacing', 40))
        char_spacing = int(data.get('charSpacing', 30))
        background_type = data.get('backgroundType', 'a4')
        font_type = data.get('fontType', 'D1')  # 新增字体类型参数
        reference_char = data.get('referenceChar', '一')
        
        # 清除SVG缓存文件
        clear_svg_cache()
        
        # 清除旧的文章SVG文件
        clear_article_svgs()
        
        # 生成文章SVG
        article_svg = compose_article_svg(text, None, font_size, line_spacing, char_spacing, background_type, font_type)
        
        if not article_svg:
            return jsonify({'success': False, 'error': 'SVG合成失败'}), 500
        
        # 保存SVG文件
        timestamp = int(time.time() * 1000)
        svg_filename = f"article_{timestamp}.svg"
        svg_path = os.path.join(OUTPUT_COMPARE, 'articles', svg_filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(svg_path), exist_ok=True)
        
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(article_svg)
        
        result = {
            'success': True,
            'svg_url': f'/compare/articles/{svg_filename}',
            'svg_path': svg_path,
            'message': f'文章SVG生成成功，包含{len(text)}个字符'
        }
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_article_image(text: str, font_size: int, line_spacing: int, char_spacing: int, background_type: str, reference_char: str):
    """生成文章图片的核心函数"""
    try:
        import io
        import base64
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # 创建输出目录
        article_dir = os.path.join(OUTPUT_COMPARE, 'articles')
        os.makedirs(article_dir, exist_ok=True)
        
        # 设置画布大小 (A4比例)
        canvas_width = 800
        canvas_height = 1000
        
        # 创建背景 - 如果是下划线纸张，先创建带下划线的背景图像
        if background_type == 'lined':
            # 创建带下划线的背景
            bg_color = (252, 252, 252)
            bg_img = Image.new('RGB', (canvas_width, canvas_height), bg_color)
            bg_draw = ImageDraw.Draw(bg_img)
            
            # 绘制下划线到背景
            line_color = (220, 220, 220)
            line_interval = font_size + line_spacing
            y = margin + font_size + 5
            
            while y < canvas_height - margin:
                bg_draw.line([(margin, y), (canvas_width - margin, y)], fill=line_color, width=1)
                y += line_interval
            
            # 使用带下划线的背景作为基础
            img = bg_img.copy()
        elif background_type == 'a4':
            # A4纸背景
            bg_color = (254, 254, 254)
            img = Image.new('RGB', (canvas_width, canvas_height), bg_color)
        else:
            # 默认白色背景
            bg_color = (255, 255, 255)
            img = Image.new('RGB', (canvas_width, canvas_height), bg_color)
        
        # 获取当前用户的风格设置用于生成字符
        style_path, _ = build_style_override({}, request.cookies, prefer_form=False)
        
        # 计算布局
        margin = 60
        start_x = margin
        start_y = margin
        current_x = start_x
        current_y = start_y
        
        draw = ImageDraw.Draw(img)
        
        chars_per_line = min(15, (canvas_width - 2 * margin) // (font_size + char_spacing))
        
        # 为每个字符生成SVG并转换为图像
        generated_chars = {}
        
        for i, char in enumerate(text):
            if char in [' ', '\n', '\t']:
                # 处理空白字符
                if char == '\n' or current_x + font_size > canvas_width - margin:
                    current_x = start_x
                    current_y += font_size + line_spacing
                else:
                    current_x += char_spacing
                continue
            
            # 检查是否需要换行
            if current_x + font_size > canvas_width - margin:
                current_x = start_x
                current_y += font_size + line_spacing
            
            # 生成单个字符的SVG
            if char not in generated_chars:
                try:
                    # 使用现有的生成逻辑生成单个字符
                    char_result = generate_single_char_for_article(char, style_path)
                    if char_result:
                        generated_chars[char] = char_result
                except Exception as e:
                    print(f"生成字符 '{char}' 时出错: {e}")
                    # 使用默认字体作为后备
                    try:
                        # 尝试使用系统字体
                        font = ImageFont.truetype("msyh.ttc", font_size) if os.name == 'nt' else ImageFont.load_default()
                        draw.text((current_x, current_y), char, fill=(0, 0, 0), font=font)
                    except:
                        # 最后的后备方案
                        draw.text((current_x, current_y), char, fill=(0, 0, 0))
                    current_x += font_size + char_spacing
                    continue
            
            # 直接在画布上绘制文字，避免任何透明度或粘贴问题
            if char in generated_chars:
                # 使用系统字体直接绘制到画布上
                try:
                    if os.name == 'nt':
                        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", font_size)
                    else:
                        font = ImageFont.load_default()
                    
                    # 直接绘制黑色文字到画布
                    draw.text((current_x, current_y), char, fill=(0, 0, 0), font=font)
                    print(f"直接绘制字符: {char} 在位置 ({current_x}, {current_y})")
                    
                except Exception as font_error:
                    print(f"字体加载失败，使用默认绘制: {font_error}")
                    draw.text((current_x, current_y), char, fill=(0, 0, 0))
            else:
                # 如果字符生成失败，直接绘制
                try:
                    if os.name == 'nt':
                        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", font_size)
                    else:
                        font = ImageFont.load_default()
                    draw.text((current_x, current_y), char, fill=(0, 0, 0), font=font)
                except:
                    draw.text((current_x, current_y), char, fill=(0, 0, 0))
            
            current_x += font_size + char_spacing
        
        # 完全移除下划线绘制，避免任何遮盖问题
        # 下划线将通过背景图案实现，而不是在最终图像上绘制
        
        # 保存图像
        timestamp = int(time.time() * 1000)
        filename = f"article_{timestamp}.png"
        filepath = os.path.join(article_dir, filename)
        img.save(filepath, 'PNG', quality=95)
        
        # 返回结果
        image_url = f"/articles/{filename}"
        
        return {
            'success': True,
            'imageUrl': image_url,
            'filename': filename
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"生成文章图片时出错: {str(e)}"
        }


def clear_svg_cache():
    """清除SVG和PNG缓存文件"""
    try:
        import glob
        import os
        
        # 清除所有对比SVG文件
        compare_dirs = [
            os.path.join(OUTPUT_COMPARE, 'A_outlines'),
            os.path.join(OUTPUT_COMPARE, 'B_raw_centerline'),
            os.path.join(OUTPUT_COMPARE, 'C_processed_centerline'),
            os.path.join(OUTPUT_COMPARE, 'D1_grid_transform'),
            os.path.join(OUTPUT_COMPARE, 'D2_median_fill')
        ]
        
        total_cleared = 0
        
        # 清除SVG文件
        for dir_path in compare_dirs:
            if os.path.exists(dir_path):
                svg_files = glob.glob(os.path.join(dir_path, '*.svg'))
                for file_path in svg_files:
                    try:
                        os.remove(file_path)
                        total_cleared += 1
                    except:
                        pass
        
        # 特别清理遗留的D1_base文件
        d1_dir = os.path.join(OUTPUT_COMPARE, 'D1_grid_transform')
        if os.path.exists(d1_dir):
            d1_base_files = glob.glob(os.path.join(d1_dir, '*_D1_base.svg'))
            for file_path in d1_base_files:
                try:
                    os.remove(file_path)
                    total_cleared += 1
                    print(f"[CACHE] 清除遗留的D1_base文件: {os.path.basename(file_path)}")
                except:
                    pass
        
        # 清除PNG文件
        png_dirs = [
            os.path.join('output', 'samples', 'A_outlines'),
            os.path.join('output', 'samples', 'D2_median_fill')
        ]
        
        for dir_path in png_dirs:
            if os.path.exists(dir_path):
                png_files = glob.glob(os.path.join(dir_path, '*.png'))
                for file_path in png_files:
                    try:
                        os.remove(file_path)
                        total_cleared += 1
                    except:
                        pass
        
        print(f"[CACHE] 清除了 {total_cleared} 个缓存文件")
        return total_cleared
        
    except Exception as e:
        print(f"[CACHE] 清除缓存失败: {e}")
        return 0


def clear_article_svgs():
    """清除旧的文章SVG文件"""
    try:
        import glob
        import os
        
        articles_dir = os.path.join(OUTPUT_COMPARE, 'articles')
        if os.path.exists(articles_dir):
            svg_files = glob.glob(os.path.join(articles_dir, 'article_*.svg'))
            total_cleared = 0
            
            for file_path in svg_files:
                try:
                    os.remove(file_path)
                    total_cleared += 1
                except:
                    pass
            
            print(f"[ARTICLE] 清除了 {total_cleared} 个旧文章SVG文件")
            return total_cleared
        
        return 0
        
    except Exception as e:
        print(f"[ARTICLE] 清除文章SVG失败: {e}")
        return 0


def extract_svg_content(svg_file_path: str) -> str:
    """提取SVG文件的内容，去除外层svg标签，并将所有线条颜色改为纯黑色"""
    try:
        with open(svg_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取<svg>标签内的内容
        import re
        # 匹配<svg...>到</svg>之间的内容
        svg_match = re.search(r'<svg[^>]*>(.*?)</svg>', content, re.DOTALL)
        if svg_match:
            svg_content = svg_match.group(1).strip()
        else:
            svg_content = content
        
        # 将所有stroke颜色改为纯黑色 #000000
        # 匹配 stroke='#颜色' 或 stroke="#颜色" 格式
        svg_content = re.sub(r"stroke=['\"]#[0-9a-fA-F]{6}['\"]", "stroke='#000000'", svg_content)
        svg_content = re.sub(r"stroke=['\"]#[0-9a-fA-F]{3}['\"]", "stroke='#000000'", svg_content)
        
        # 也处理可能的颜色名称
        color_names = ['blue', 'red', 'gray', 'grey', 'green', 'yellow', 'purple', 'orange', 'pink', 'brown']
        for color in color_names:
            svg_content = re.sub(rf"stroke=['\"]#{color}['\"]", "stroke='#000000'", svg_content, flags=re.IGNORECASE)
            svg_content = re.sub(rf"stroke=['\"]#{color}['\"]", "stroke='#000000'", svg_content, flags=re.IGNORECASE)
        
        return svg_content
            
    except Exception as e:
        print(f"[SVG] 提取SVG内容失败: {e}")
        return ""


def generate_font_sample_svg(sample_text: str, font_type: str = 'D1', 
                           font_size: int = 40, line_spacing: int = 40, 
                           char_spacing: int = 30) -> str:
    """生成字体样例SVG"""
    try:
        print(f"[SAMPLE] 生成字体样例，文本: {sample_text}, 字体类型: {font_type}")
        
        # 样例区域尺寸
        sample_width = 400
        sample_height = 200
        margin = 20
        
        # 加载网格变形状态（如果存在）
        from web.services.grid_state import load_grid_state, has_grid_deformation
        grid_state = load_grid_state()
        use_grid = has_grid_deformation()
        
        print(f"[SAMPLE] ===== 网格变形调试信息 =====")
        print(f"[SAMPLE] grid_state 是否存在: {grid_state is not None}")
        print(f"[SAMPLE] use_grid 标志: {use_grid}")
        if grid_state:
            print(f"[SAMPLE] grid_state 包含的键: {grid_state.keys()}")
            print(f"[SAMPLE] controlPoints 数量: {len(grid_state.get('controlPoints', []))}")
            print(f"[SAMPLE] 检测到网格变形状态，将应用到D1字体生成")
        else:
            print(f"[SAMPLE] 未检测到网格变形状态")
        print(f"[SAMPLE] =================================")
        
        # 生成样例文本中每个字符的SVG
        char_svgs = {}
        unique_chars = list(set(sample_text))
        
        # 构建样式覆盖参数
        try:
            style_override_path, cookie_vals = build_style_override({}, request.cookies, prefer_form=False)
        except:
            style_override_path = None
        
        for char in unique_chars:
            if char.strip():  # 跳过空白字符
                try:
                    from web.services.generation import generate_abcd
                    
                    # 传递网格变形参数
                    urls = generate_abcd(
                        char, 
                        style_override_path=style_override_path,
                        grid_state=grid_state,
                        use_grid_deformation=use_grid
                    )
                    
                    if urls and font_type in urls:
                        svg_url = urls[font_type]
                        svg_path = svg_url.split('/')[-1]
                        
                        # 根据字体类型确定目录
                        if font_type == 'D1':
                            svg_dir = 'D1_grid_transform'
                        elif font_type == 'D2':
                            svg_dir = 'D2_median_fill'
                        else:
                            svg_dir = 'C_processed_centerline'
                        
                        svg_full_path = os.path.join('output', 'compare', svg_dir, svg_path)
                        
                        # 检查文件是否存在
                        import glob
                        pattern = os.path.join('output', 'compare', svg_dir, f'*{char}_{font_type}.svg')
                        matches = glob.glob(pattern)
                        if matches:
                            svg_full_path = matches[-1]
                        
                        if os.path.exists(svg_full_path):
                            char_svgs[char] = extract_svg_content(svg_full_path)
                            print(f"[SAMPLE] 成功提取字符SVG ({font_type}): {char}")
                        else:
                            print(f"[SAMPLE] SVG文件不存在: {svg_full_path}")
                            
                except Exception as e:
                    print(f"[SAMPLE] 字符{char}生成失败: {e}")
        
        # 创建样例SVG
        sample_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" 
                             width="{sample_width}" height="{sample_height}" 
                             viewBox="0 0 {sample_width} {sample_height}">
        <rect x="0" y="0" width="{sample_width}" height="{sample_height}" fill="white" stroke="#e0e0e0" stroke-width="1"/>
        '''
        
        # 排列字符
        x_pos = margin
        y_pos = margin + font_size
        max_chars_per_line = (sample_width - 2 * margin) // char_spacing
        
        char_count = 0
        for char in sample_text:
            if char in char_svgs:
                # 检查是否需要换行
                if char_count > 0 and char_count % max_chars_per_line == 0:
                    y_pos += line_spacing
                    x_pos = margin
                
                # 添加字符SVG
                sample_svg += f'''
                <g transform="translate({x_pos}, {y_pos - font_size}) scale({font_size/256})">
                    {char_svgs[char]}
                </g>
                '''
                
                x_pos += char_spacing
                char_count += 1
            elif char == ' ':
                # 空格
                x_pos += char_spacing // 2
            elif char == '\n':
                # 换行
                y_pos += line_spacing
                x_pos = margin
        
        sample_svg += '</svg>'
        
        print(f"[SAMPLE] 样例SVG生成完成，包含 {len(char_svgs)} 个字符")
        return sample_svg
        
    except Exception as e:
        print(f"[SAMPLE] 生成字体样例失败: {e}")
        import traceback
        traceback.print_exc()
        return ""


def extract_svg_bbox(svg_content: str) -> tuple:
    """
    提取SVG内容的实际边界框
    返回 (min_x, min_y, max_x, max_y)
    """
    import re
    import xml.etree.ElementTree as ET
    
    try:
        # 解析SVG
        root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{svg_content}</svg>')
        
        # 收集所有坐标
        all_x = []
        all_y = []
        
        # 解析path元素
        for path in root.findall('.//{http://www.w3.org/2000/svg}path'):
            d = path.get('d', '')
            # 提取所有数字坐标
            coords = re.findall(r'[-+]?[0-9]*\.?[0-9]+', d)
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    all_x.append(float(coords[i]))
                    all_y.append(float(coords[i + 1]))
        
        # 解析line元素
        for line in root.findall('.//{http://www.w3.org/2000/svg}line'):
            x1 = float(line.get('x1', 0))
            y1 = float(line.get('y1', 0))
            x2 = float(line.get('x2', 0))
            y2 = float(line.get('y2', 0))
            all_x.extend([x1, x2])
            all_y.extend([y1, y2])
        
        if all_x and all_y:
            return (min(all_x), min(all_y), max(all_x), max(all_y))
        else:
            # 如果无法解析，返回默认256x256
            return (0, 0, 256, 256)
    except Exception as e:
        print(f"[BBOX] 提取边界框失败: {e}")
        return (0, 0, 256, 256)


def compose_article_svg(text: str, style_path: str, font_size: int = 40, 
                       line_spacing: int = 40, char_spacing: int = 30,
                       background_type: str = 'a4', font_type: str = 'D1') -> str:
    """合成文章SVG - 直接调用/gen接口"""
    try:
        print(f"[COMPOSE] 开始合成文章SVG，文本长度: {len(text)}, 字体类型: {font_type}")
        
        # A4尺寸 (210x297mm at 96dpi)
        a4_width = 794  # 210mm * 96dpi / 25.4
        a4_height = 1123  # 297mm * 96dpi / 25.4
        margin = 60
        
        # 加载网格变形状态（如果存在）
        from web.services.grid_state import load_grid_state, has_grid_deformation
        grid_state = load_grid_state()
        use_grid = has_grid_deformation()
        
        print(f"[COMPOSE] ===== 网格变形调试信息 =====")
        print(f"[COMPOSE] grid_state 是否存在: {grid_state is not None}")
        print(f"[COMPOSE] use_grid 标志: {use_grid}")
        if grid_state:
            print(f"[COMPOSE] grid_state 包含的键: {grid_state.keys()}")
            print(f"[COMPOSE] controlPoints 数量: {len(grid_state.get('controlPoints', []))}")
            if grid_state.get('controlPoints'):
                # 显示第一个和最后一个控制点
                cps = grid_state['controlPoints']
                print(f"[COMPOSE] 第一个控制点: {cps[0]}")
                print(f"[COMPOSE] 最后一个控制点: {cps[-1]}")
            print(f"[COMPOSE] 检测到网格变形状态，将应用到D1字体生成")
        else:
            print(f"[COMPOSE] 未检测到网格变形状态")
        print(f"[COMPOSE] =================================")
        
        # 1. 使用/gen接口逻辑生成所有字符的SVG (根据字体类型选择D1或D2)
        char_svgs = {}  # {char: {'content': svg_content, 'bbox': (min_x, min_y, max_x, max_y)}}
        unique_chars = list(set(text))  # 去重优化
        
        # 构建样式覆盖参数
        try:
            style_override_path, cookie_vals = build_style_override({}, request.cookies, prefer_form=False)
        except:
            # 非请求上下文时使用默认样式
            style_override_path = style_path
        
        for char in unique_chars:
            if char.strip():  # 跳过空白字符
                try:
                    # 直接调用generate_abcd，就像/gen接口一样
                    from web.services.generation import generate_abcd
                    
                    # 传递网格变形参数
                    urls = generate_abcd(
                        char, 
                        style_override_path=style_override_path,
                        grid_state=grid_state,
                        use_grid_deformation=use_grid
                    )
                    
                    # 根据字体类型选择相应的SVG文件
                    if urls and font_type in urls:
                        svg_url = urls[font_type]
                        # 修复路径解析 - 直接使用文件名
                        svg_path = svg_url.split('/')[-1]  # 提取文件名
                        
                        # 根据字体类型确定目录
                        if font_type == 'D1':
                            svg_dir = 'D1_grid_transform'
                        elif font_type == 'D2':
                            svg_dir = 'D2_median_fill'
                        else:
                            svg_dir = 'C_processed_centerline'  # 默认
                        
                        svg_full_path = os.path.join('output', 'compare', svg_dir, svg_path)
                        print(f"[COMPOSE] {font_type}文件路径: {svg_full_path}")
                        print(f"[COMPOSE] {font_type} URL: {svg_url}")
                        
                        # 检查文件是否存在
                        import glob
                        pattern = os.path.join('output', 'compare', svg_dir, f'*{char}_{font_type}.svg')
                        matches = glob.glob(pattern)
                        if matches:
                            svg_full_path = matches[-1]  # 使用最新的文件
                            print(f"[COMPOSE] 找到匹配文件: {svg_full_path}")
                        
                        if os.path.exists(svg_full_path):
                            svg_content = extract_svg_content(svg_full_path)
                            # 提取实际边界框
                            bbox = extract_svg_bbox(svg_content)
                            char_svgs[char] = {
                                'content': svg_content,
                                'bbox': bbox
                            }
                            bbox_width = bbox[2] - bbox[0]
                            bbox_height = bbox[3] - bbox[1]
                            print(f"[COMPOSE] 成功提取字符SVG ({font_type}): {char}, bbox: {bbox_width:.1f}x{bbox_height:.1f}")
                        else:
                            print(f"[COMPOSE] SVG文件不存在: {svg_full_path}")
                    else:
                        print(f"[COMPOSE] 字符{char}的{font_type}类型SVG未生成")
                            
                except Exception as e:
                    print(f"[COMPOSE] 字符{char}生成失败: {e}")
        
        # 2. 创建文章SVG画布
        article_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" 
                              width="{a4_width}" height="{a4_height}" 
                              viewBox="0 0 {a4_width} {a4_height}">
        <rect x="0" y="0" width="{a4_width}" height="{a4_height}" fill="white"/>
        '''
        
        # 根据背景类型添加背景元素
        if background_type == 'lined':
            # 添加下划线背景
            line_spacing_bg = font_size + line_spacing  # 使用与文字相同的行间距
            y_start = margin + font_size + 5  # 稍微向下偏移，避免与文字重叠
            
            # 生成横线
            y_pos = y_start
            while y_pos < a4_height - margin:
                article_svg += f'''
        <line x1="{margin}" y1="{y_pos}" x2="{a4_width - margin}" y2="{y_pos}" 
              stroke="#e0e0e0" stroke-width="1" opacity="0.8"/>'''
                y_pos += line_spacing_bg
        
        print(f"[COMPOSE] 背景类型: {background_type}")
        
        # 3. 布局字符SVG - 使用实际边界框计算
        current_x = margin
        current_y = margin + font_size
        max_width = a4_width - 2 * margin
        
        for i, char in enumerate(text):
            if char == '\n':
                # 换行
                current_x = margin
                current_y += font_size + line_spacing
                continue
            elif char.strip() == '':
                # 空格
                current_x += font_size // 2
                continue
            
            # 添加字符SVG
            if char in char_svgs:
                char_data = char_svgs[char]
                if char_data and char_data['content']:
                    # 获取字符的实际边界框
                    bbox = char_data['bbox']
                    bbox_width = bbox[2] - bbox[0]
                    bbox_height = bbox[3] - bbox[1]
                    
                    # 计算缩放比例
                    # 目标是让字符的实际内容适应font_size
                    scale = font_size / max(bbox_width, bbox_height)
                    
                    # 计算缩放后的实际宽度（用于布局）
                    scaled_width = bbox_width * scale
                    scaled_height = bbox_height * scale
                    
                    # 检查是否需要自动换行
                    if current_x + scaled_width > max_width:
                        current_x = margin
                        current_y += font_size + line_spacing
                    
                    # 计算偏移量，使字符居中对齐
                    offset_x = bbox[0] * scale
                    offset_y = bbox[1] * scale
                    
                    # 添加变换后的字符SVG
                    article_svg += f'''
        <g transform="translate({current_x - offset_x}, {current_y - font_size - offset_y}) scale({scale})">
            {char_data['content']}
        </g>'''
                    print(f"[COMPOSE] 添加字符: {char} at ({current_x}, {current_y}), scaled_width={scaled_width:.1f}")
                    
                    # 根据实际宽度移动光标
                    current_x += scaled_width + char_spacing
            else:
                # 如果字符没有SVG，使用默认宽度
                current_x += font_size + char_spacing
        
        # 4. 关闭SVG标签
        article_svg += '\n</svg>'
        
        print(f"[COMPOSE] 文章SVG合成完成，包含{len(char_svgs)}个字符")
        return article_svg
        
    except Exception as e:
        print(f"[COMPOSE] SVG合成失败: {e}")
        return ""


def generate_single_char_for_article(char: str, style_path: str):
    """为文章生成单个字符的图像 - 使用D1 SVG渲染"""
    try:
        print(f"[ARTICLE] 生成字符: {char}")
        
        # 方法1: 尝试使用现有的D1 SVG生成逻辑
        try:
            # 调用现有的生成逻辑，获取D1 SVG
            from web.services.generation import generate_abcd
            import time
            
            # 直接调用generate_abcd生成ABCD四种版本
            result = generate_abcd(char, style_path)
            
            if result and 'C_processed_centerline' in result:
                d1_svg_url = result['C_processed_centerline']
                # 从URL获取实际文件路径
                d1_svg_path = d1_svg_url.replace('/compare/C_processed_centerline/', '')
                d1_svg_full_path = os.path.join(OUTPUT_COMPARE, 'C_processed_centerline', d1_svg_path)
                
                if os.path.exists(d1_svg_full_path):
                    print(f"[ARTICLE] 找到D1 SVG: {d1_svg_full_path}")
                    
                    # 使用CairoSVG转换为PNG
                    try:
                        import cairosvg
                        import io
                        
                        print(f"[ARTICLE] 使用CairoSVG转换...")
                        png_data = cairosvg.svg2png(url=d1_svg_full_path, output_width=256, output_height=256)
                        img = Image.open(io.BytesIO(png_data))
                        print(f"[ARTICLE] CairoSVG转换成功: {char}")
                        return img
                        
                    except ImportError:
                        print(f"[ARTICLE] CairoSVG未安装，使用后备方案")
                    except Exception as e:
                        print(f"[ARTICLE] CairoSVG转换失败: {e}")
        
        except Exception as e:
            print(f"[ARTICLE] D1生成失败: {e}")
        
        # 方法2: 后备方案 - 使用系统字体
        print(f"[ARTICLE] 使用系统字体后备方案: {char}")
        from PIL import Image, ImageDraw, ImageFont
        
        size = 256
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            # 使用系统字体
            font_size = int(size * 0.8)
            if os.name == 'nt':
                # Windows系统字体
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    "C:/Windows/Fonts/simhei.ttf",  # 黑体
                ]
                font = None
                for font_path in font_paths:
                    try:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size)
                            break
                    except:
                        continue
                
                if font is None:
                    font = ImageFont.load_default()
            else:
                font = ImageFont.load_default()
            
            # 计算文本位置居中
            bbox = draw.textbbox((0, 0), char, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            
            # 绘制字符
            draw.text((x, y), char, fill=(0, 0, 0, 255), font=font)
            print(f"[ARTICLE] 系统字体渲染成功: {char}")
            
            return img
            
        except Exception as font_error:
            print(f"字体渲染失败: {font_error}")
            # 绘制简单占位符
            char_size = int(size * 0.6)
            offset = (size - char_size) // 2
            draw.rectangle([offset, offset, offset + char_size, offset + char_size], 
                         fill=(100, 100, 100, 255))
            draw.text((offset + 10, offset + 10), char, fill=(255, 255, 255, 255))
            return img
        
    except Exception as e:
        print(f"生成单个字符时出错: {e}")
        return None


def convert_svg_to_png(svg_path: str, size: int = 256):
    """将SVG文件转换为PNG图像"""
    try:
        from PIL import Image
        import cairosvg
        import io
        
        print(f"开始转换SVG到PNG: {svg_path}")
        
        # 使用cairosvg将SVG转换为PNG，不设置背景色让其保持透明
        png_data = cairosvg.svg2png(
            url=svg_path, 
            output_width=size, 
            output_height=size
        )
        
        print(f"cairosvg转换完成，数据大小: {len(png_data)} bytes")
        
        # 创建PIL图像
        img = Image.open(io.BytesIO(png_data))
        print(f"PIL图像创建成功，模式: {img.mode}, 尺寸: {img.size}")
        
        # 确保图像为RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print(f"转换为RGBA模式")
        
        return img
        
    except ImportError:
        print("cairosvg not available, trying alternative method")
        return convert_svg_alternative(svg_path, size)
        
    except Exception as e:
        print(f"SVG转PNG时出错: {e}")
        return convert_svg_alternative(svg_path, size)


def convert_svg_alternative(svg_path: str, size: int = 256):
    """SVG转PNG的替代方法"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        print(f"使用替代方法转换SVG: {svg_path}")
        
        # 创建透明背景图像
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 读取SVG内容并尝试提取字符
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            print(f"SVG内容长度: {len(svg_content)}")
            
            # 检查是否包含路径数据
            if '<path' in svg_content:
                print("SVG包含路径数据，使用系统字体渲染")
                
                # 尝试从文件名提取字符
                import os
                filename = os.path.basename(svg_path)
                char_match = filename.split('_')[0] if '_' in filename else filename.replace('.svg', '')
                
                if char_match and len(char_match) == 1:
                    try:
                        # 使用系统字体渲染字符
                        font_size = int(size * 0.8)
                        if os.name == 'nt':
                            font = ImageFont.truetype("msyh.ttc", font_size)
                        else:
                            font = ImageFont.load_default()
                        
                        # 计算文本位置居中
                        bbox = draw.textbbox((0, 0), char_match, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        x = (size - text_width) // 2
                        y = (size - text_height) // 2
                        
                        # 绘制黑色字符
                        draw.text((x, y), char_match, fill=(0, 0, 0, 255), font=font)
                        print(f"成功渲染字符: {char_match}")
                        
                    except Exception as font_error:
                        print(f"字体渲染失败: {font_error}")
                        # 绘制简单占位符
                        char_size = int(size * 0.6)
                        offset = (size - char_size) // 2
                        draw.rectangle([offset, offset, offset + char_size, offset + char_size], 
                                     fill=(0, 0, 0, 255))
                else:
                    print("无法从文件名提取字符，绘制占位符")
                    char_size = int(size * 0.6)
                    offset = (size - char_size) // 2
                    draw.rectangle([offset, offset, offset + char_size, offset + char_size], 
                                 fill=(0, 0, 0, 255))
            else:
                print("SVG不包含路径数据")
                return None
            
        except Exception as read_error:
            print(f"读取SVG文件失败: {read_error}")
            return None
        
        print(f"替代方法转换完成，图像模式: {img.mode}")
        return img
        
    except Exception as e:
        print(f"替代SVG转换方法失败: {e}")
        return None


@app.route('/compare/articles/<path:filename>')
def serve_article_compare(filename: str):
    """提供文章SVG文件"""
    article_dir = os.path.join(OUTPUT_COMPARE, 'articles')
    if not os.path.exists(os.path.join(article_dir, filename)):
        return ("not found", 404)
    
    resp = make_response(send_from_directory(article_dir, filename, max_age=0))
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['Content-Type'] = 'image/svg+xml'
    return resp

@app.route('/articles/<path:filename>')
def serve_article(filename: str):
    """提供文章图片文件 - 兼容旧路径"""
    return serve_article_compare(filename)


@app.route('/test-auto-preview')
def test_auto_preview():
    """测试自动预览功能的页面"""
    try:
        test_page_path = os.path.join(ROOT, 'web', 'test-auto-preview.html')
        if os.path.exists(test_page_path):
            with open(test_page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return "Test page not found", 404
    except Exception as e:
        return f"Error loading test page: {str(e)}", 500


@app.route('/assets/font-samples/<path:filename>')
def serve_font_samples(filename: str):
    """服务字体样例文件"""
    import os
    from flask import send_from_directory, abort
    
    # 使用绝对路径
    font_samples_dir = os.path.join(os.getcwd(), 'web', 'assets', 'font-samples')
    full_path = os.path.join(font_samples_dir, filename)
    
    print(f"[FONT_SAMPLE] 请求文件: {filename}")
    print(f"[FONT_SAMPLE] 完整路径: {full_path}")
    print(f"[FONT_SAMPLE] 文件存在: {os.path.exists(full_path)}")
    
    if not os.path.exists(full_path):
        print(f"[FONT_SAMPLE] 文件不存在: {full_path}")
        abort(404)
    
    try:
        resp = make_response(send_from_directory(font_samples_dir, filename, max_age=0))
        resp.headers['Cache-Control'] = 'no-store'
        resp.headers['Content-Type'] = 'image/svg+xml'
        print(f"[FONT_SAMPLE] 成功服务文件: {filename}")
        return resp
    except Exception as e:
        print(f"[FONT_SAMPLE] 服务文件失败: {e}")
        abort(500)


def cleanup_old_font_samples():
    """清理所有旧的字体样例文件"""
    try:
        import glob
        font_samples_dir = os.path.join(os.getcwd(), 'web', 'assets', 'font-samples')
        
        if not os.path.exists(font_samples_dir):
            print("[CLEANUP] 字体样例目录不存在，跳过清理")
            return
            
        # 清理所有样例文件
        all_sample_files = glob.glob(os.path.join(font_samples_dir, 'sample_*.svg'))
        
        if all_sample_files:
            for file_path in all_sample_files:
                try:
                    os.remove(file_path)
                    print(f"[CLEANUP] 删除旧样例文件: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"[CLEANUP] 删除文件失败: {e}")
            
            print(f"[CLEANUP] 启动时清理了 {len(all_sample_files)} 个旧的字体样例文件")
        else:
            print("[CLEANUP] 没有找到需要清理的字体样例文件")
            
    except Exception as e:
        print(f"[CLEANUP] 清理旧样例文件时出错: {e}")


if __name__ == '__main__':
    # 启动时清理旧的字体样例文件
    cleanup_old_font_samples()
    
    port = int(os.environ.get('PORT', '8766'))
    # Enable auto-reload on code/data changes so browser refresh reflects updates without manual restart
    extra_files = [
        MERGED_JSON,
        BASE_STYLE,
        # 注意：不要监听 output/tmp/style_overrides.json，否则每次生成都会触发热重启，导致二次点击时连接重置
        os.path.join(ROOT, 'scripts', 'make_compare_preview.py'),
        os.path.join(ROOT, 'web', 'ui.html'),
        os.path.join(ROOT, 'web', 'app.py'),
    ]
    extra_files = [p for p in extra_files if os.path.exists(p)]
    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=True, extra_files=extra_files)
