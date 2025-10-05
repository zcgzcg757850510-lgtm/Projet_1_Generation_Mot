"""
网格变形处理模块
用于在D1生成过程中应用网格变形
"""

import re
import json
import math
import io
import base64
from typing import List, Tuple, Optional, Dict, Any


def parse_svg_path(path_data: str) -> List[Tuple[str, List[float]]]:
    """解析SVG路径数据"""
    commands = re.findall(r'[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*', path_data)
    parsed = []
    
    for cmd in commands:
        cmd_type = cmd[0]
        coords_str = cmd[1:].strip()
        if coords_str:
            # 支持科学计数与更宽松格式，避免解析失败造成折线
            coords = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?', coords_str)]
        else:
            coords = []
        parsed.append((cmd_type, coords))
    
    return parsed


def build_svg_path(commands: List[Tuple[str, List[float]]]) -> str:
    """重建SVG路径数据"""
    result = []
    for cmd_type, coords in commands:
        if coords:
            # 使用更高精度并在数值之间添加空格，减少量化造成的折线感
            coords_str = ' '.join(f'{x:.4f}' for x in coords)
            result.append(f'{cmd_type}{coords_str}')
        else:
            result.append(cmd_type)
    return ''.join(result)


def bilinear_interpolation(x: float, y: float, 
                          p00: Tuple[float, float], p10: Tuple[float, float],
                          p01: Tuple[float, float], p11: Tuple[float, float]) -> Tuple[float, float]:
    """双线性插值计算"""
    # 计算插值权重
    fx = x - math.floor(x)
    fy = y - math.floor(y)
    
    # 双线性插值
    result_x = (p00[0] * (1-fx) * (1-fy) + 
                p10[0] * fx * (1-fy) + 
                p01[0] * (1-fx) * fy + 
                p11[0] * fx * fy)
    
    result_y = (p00[1] * (1-fx) * (1-fy) + 
                p10[1] * fx * (1-fy) + 
                p01[1] * (1-fx) * fy + 
                p11[1] * fx * fy)
    
    return (result_x, result_y)


def deform_point_catmull_rom_coons(x: float, y: float, grid_state: Dict[str, Any]) -> Tuple[float, float]:
    """
    使用Catmull-Rom + Coons Patch算法对单个点应用网格变形（与前端一致）
    
    Args:
        x, y: SVG坐标 (0-256)
        grid_state: 网格状态数据
    
    Returns:
        变形后的坐标 (x, y)
    """
    control_points = grid_state.get('controlPoints', [])
    size = grid_state.get('size', 4)
    
    if not control_points or size < 2:
        return (x, y)
    
    # 前端坐标系参数
    canvas_width = 800.0
    canvas_height = 600.0
    center_x = canvas_width / 2
    center_y = canvas_height / 2
    grid_width = 300
    grid_height = 300
    grid_start_x = center_x - grid_width / 2
    grid_start_y = center_y - grid_height / 2
    
    # SVG区域（网格中央80%）
    svg_grid_width = grid_width * 0.8
    svg_grid_height = grid_height * 0.8
    svg_grid_start_x = center_x - svg_grid_width / 2
    svg_grid_start_y = center_y - svg_grid_height / 2
    
    # 将SVG坐标转换为网格坐标系
    svg_to_grid_x = svg_grid_start_x + (x / 256.0) * svg_grid_width
    svg_to_grid_y = svg_grid_start_y + (y / 256.0) * svg_grid_height
    
    # 计算在网格中的相对位置 (0-1范围)
    cells = size - 1
    u = (svg_to_grid_x - grid_start_x) / grid_width
    v = (svg_to_grid_y - grid_start_y) / grid_height
    
    # 确保在有效范围内
    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))
    
    # 使用Coons Patch插值
    try:
        result_pos = coons_patch_interpolation(u, v, control_points, size, grid_start_x, grid_start_y, grid_width, grid_height)
        
        # 转换回SVG坐标系
        result_grid_x, result_grid_y = result_pos
        result_svg_x = (result_grid_x - svg_grid_start_x) / svg_grid_width * 256.0
        result_svg_y = (result_grid_y - svg_grid_start_y) / svg_grid_height * 256.0
        
        return (result_svg_x, result_svg_y)
        
    except Exception:
        return (x, y)


def coons_patch_interpolation(u: float, v: float, control_points: list, size: int, 
                            grid_start_x: float, grid_start_y: float, 
                            grid_width: float, grid_height: float) -> tuple:
    """
    Coons Patch插值算法（与前端JavaScript版本一致）
    """
    def get_control_point(row, col):
        """安全获取控制点"""
        row = max(0, min(size - 1, row))
        col = max(0, min(size - 1, col))
        idx = row * size + col
        if 0 <= idx < len(control_points):
            return control_points[idx]
        return {'x': grid_start_x + col * grid_width / (size - 1), 
                'y': grid_start_y + row * grid_height / (size - 1)}
    
    def catmull_rom_to_bezier(p0, p1, p2, p3):
        """Catmull-Rom样条转贝塞尔曲线"""
        c1_x = p1['x'] + (p2['x'] - p0['x']) / 6
        c1_y = p1['y'] + (p2['y'] - p0['y']) / 6
        c2_x = p2['x'] - (p3['x'] - p1['x']) / 6
        c2_y = p2['y'] - (p3['y'] - p1['y']) / 6
        
        return [
            {'x': p1['x'], 'y': p1['y']},
            {'x': c1_x, 'y': c1_y},
            {'x': c2_x, 'y': c2_y},
            {'x': p2['x'], 'y': p2['y']}
        ]
    
    def bezier_eval(bz, t):
        """贝塞尔曲线求值"""
        it = 1 - t
        b0 = it * it * it
        b1 = 3 * it * it * t
        b2 = 3 * it * t * t
        b3 = t * t * t
        
        return {
            'x': bz[0]['x'] * b0 + bz[1]['x'] * b1 + bz[2]['x'] * b2 + bz[3]['x'] * b3,
            'y': bz[0]['y'] * b0 + bz[1]['y'] * b1 + bz[2]['y'] * b2 + bz[3]['y'] * b3
        }
    
    # 计算当前位置对应的网格行列
    cells = size - 1
    grid_u = u * cells
    grid_v = v * cells
    
    gx = int(grid_u)
    gy = int(grid_v)
    
    # 确保在有效范围内
    gx = max(0, min(cells - 1, gx))
    gy = max(0, min(cells - 1, gy))
    
    # 获取当前单元格的四个控制点
    p00 = get_control_point(gy, gx)
    p10 = get_control_point(gy, gx + 1)
    p01 = get_control_point(gy + 1, gx)
    p11 = get_control_point(gy + 1, gx + 1)
    
    # 获取用于Catmull-Rom插值的扩展控制点
    # 顶边
    ta = get_control_point(gy, gx - 1)
    tb = p00
    tc = p10
    td = get_control_point(gy, gx + 2)
    
    # 底边
    ba = get_control_point(gy + 1, gx - 1)
    bb = p01
    bc = p11
    bd = get_control_point(gy + 1, gx + 2)
    
    # 左边
    la = get_control_point(gy - 1, gx)
    lb = p00
    lc = p01
    ld = get_control_point(gy + 2, gx)
    
    # 右边
    ra = get_control_point(gy - 1, gx + 1)
    rb = p10
    rc = p11
    rd = get_control_point(gy + 2, gx + 1)
    
    # 生成四条边的贝塞尔曲线
    top_bz = catmull_rom_to_bezier(ta, tb, tc, td)
    bottom_bz = catmull_rom_to_bezier(ba, bb, bc, bd)
    left_bz = catmull_rom_to_bezier(la, lb, lc, ld)
    right_bz = catmull_rom_to_bezier(ra, rb, rc, rd)
    
    # 计算单元格内的相对位置
    local_u = grid_u - gx
    local_v = grid_v - gy
    
    # Coons Patch插值
    # 边界插值
    top_pt = bezier_eval(top_bz, local_u)
    bottom_pt = bezier_eval(bottom_bz, local_u)
    left_pt = bezier_eval(left_bz, local_v)
    right_pt = bezier_eval(right_bz, local_v)
    
    # 角点
    corner_00 = p00
    corner_10 = p10
    corner_01 = p01
    corner_11 = p11
    
    # Coons Patch公式
    # C(u,v) = (1-v)*C(u,0) + v*C(u,1) + (1-u)*C(0,v) + u*C(1,v) 
    #          - [(1-u)*(1-v)*C(0,0) + u*(1-v)*C(1,0) + (1-u)*v*C(0,1) + u*v*C(1,1)]
    
    result_x = ((1 - local_v) * top_pt['x'] + local_v * bottom_pt['x'] +
                (1 - local_u) * left_pt['x'] + local_u * right_pt['x'] -
                ((1 - local_u) * (1 - local_v) * corner_00['x'] +
                 local_u * (1 - local_v) * corner_10['x'] +
                 (1 - local_u) * local_v * corner_01['x'] +
                 local_u * local_v * corner_11['x']))
    
    result_y = ((1 - local_v) * top_pt['y'] + local_v * bottom_pt['y'] +
                (1 - local_u) * left_pt['y'] + local_u * right_pt['y'] -
                ((1 - local_u) * (1 - local_v) * corner_00['y'] +
                 local_u * (1 - local_v) * corner_10['y'] +
                 (1 - local_u) * local_v * corner_01['y'] +
                 local_u * local_v * corner_11['y']))
    
    return (result_x, result_y)


def deform_point(x: float, y: float, grid_state: Dict[str, Any]) -> Tuple[float, float]:
    """
    对单个点应用网格变形 - 使用改进的Catmull-Rom + Coons算法，带安全坐标限制
    """
    # 应用变形
    new_x, new_y = deform_point_catmull_rom_coons(x, y, grid_state)
    
    # 安全限制：防止极端坐标值，但允许足够的变形空间
    # 使用更宽松的限制，避免截断变形的笔画
    safe_x = max(-500, min(800, new_x))
    safe_y = max(-500, min(800, new_y))
    
    return (safe_x, safe_y)


def has_grid_deformation(grid_state):
    """
    检查网格状态是否包含实际变形
    
    Args:
        grid_state: 网格状态字典
    
    Returns:
        bool: 是否有变形
    """
    if not grid_state or 'controlPoints' not in grid_state:
        return False
    
    control_points = grid_state['controlPoints']
    for point in control_points:
        if 'originalX' in point and 'originalY' in point:
            dx = abs(point['x'] - point['originalX'])
            dy = abs(point['y'] - point['originalY'])
            if dx > 0.1 or dy > 0.1:
                return True
    
    return False


def transform_d1_to_d2(d1_content: str, grid_state: Dict[str, Any], canvas_dimensions: Dict[str, int] = None) -> str:
    """将D1 SVG应用网格变形生成D2 SVG
    
    Args:
        d1_content: D1 SVG内容
        grid_state: 网格状态数据
    
    Returns:
        变形后的D2 SVG内容
    """
    import sys
    print(f"[D1_TO_D2] 🚀 开始将D1转换为D2", flush=True)
    print(f"[D1_TO_D2] 网格状态: {grid_state}", flush=True)
    print(f"[D1_TO_D2] 画布尺寸: {canvas_dimensions}", flush=True)
    sys.stdout.flush()
    
    if not grid_state:
        print("[D1_TO_D2] ❌ 无网格状态，D2=D1", flush=True)
        sys.stdout.flush()
        return d1_content
    
    if not has_grid_deformation(grid_state):
        print("[D1_TO_D2] ❌ 无网格变形，D2=D1", flush=True)
        sys.stdout.flush()
        return d1_content
    
    print("[D1_TO_D2] ✅ 检测到网格变形，开始应用变形", flush=True)
    sys.stdout.flush()
    
    # 优先尝试图像级变形，失败则使用改进的路径级变形
    try:
        result = apply_image_based_grid_deformation(d1_content, grid_state, canvas_dimensions)
        if result and len(result) > 100:
            return result
    except Exception as e:
        print(f"[D1_TO_D2] 图像级变形失败: {e}", flush=True)
    
    # 回退到改进的路径级变形（确保平滑）
    print("[D1_TO_D2] 使用改进的路径级变形", flush=True)
    return apply_smooth_grid_deformation(d1_content, grid_state, canvas_dimensions)


def convert_svg_shapes_to_paths(svg_content: str) -> str:
    """
    将SVG基本形状转换为path元素，以便进行变形处理
    """
    import re
    
    def convert_circle_to_path(match):
        """将circle转换为path"""
        circle_str = match.group(0)
        
        # 提取属性
        cx_match = re.search(r'cx="([^"]*)"', circle_str)
        cy_match = re.search(r'cy="([^"]*)"', circle_str)
        r_match = re.search(r'r="([^"]*)"', circle_str)
        
        if not (cx_match and cy_match and r_match):
            return circle_str
        
        try:
            cx = float(cx_match.group(1))
            cy = float(cy_match.group(1))
            r = float(r_match.group(1))
        except ValueError:
            return circle_str
        
        # 生成圆形路径 (使用4个贝塞尔弧)
        path_d = f"M{cx-r},{cy} A{r},{r} 0 0,1 {cx},{cy-r} A{r},{r} 0 0,1 {cx+r},{cy} A{r},{r} 0 0,1 {cx},{cy+r} A{r},{r} 0 0,1 {cx-r},{cy} Z"
        
        # 保留其他属性，替换为path
        other_attrs = re.sub(r'\s*(cx|cy|r)="[^"]*"', '', circle_str)
        other_attrs = other_attrs.replace('<circle', '').replace('>', '').strip()
        
        return f'<path d="{path_d}" {other_attrs}>'
    
    def convert_rect_to_path(match):
        """将rect转换为path（只转换有描边或填充的rect，跳过背景）"""
        rect_str = match.group(0)
        
        # 跳过纯背景矩形（只有fill="white"或类似的）
        if 'fill="white"' in rect_str and 'stroke' not in rect_str:
            return rect_str
        
        # 提取属性
        x_match = re.search(r'x="([^"]*)"', rect_str)
        y_match = re.search(r'y="([^"]*)"', rect_str)
        w_match = re.search(r'width="([^"]*)"', rect_str)
        h_match = re.search(r'height="([^"]*)"', rect_str)
        
        if not (x_match and y_match and w_match and h_match):
            return rect_str
        
        try:
            x = float(x_match.group(1))
            y = float(y_match.group(1))
            w = float(w_match.group(1))
            h = float(h_match.group(1))
        except ValueError:
            return rect_str
        
        # 生成矩形路径
        path_d = f"M{x},{y} L{x+w},{y} L{x+w},{y+h} L{x},{y+h} Z"
        
        # 保留其他属性，替换为path
        other_attrs = re.sub(r'\s*(x|y|width|height)="[^"]*"', '', rect_str)
        other_attrs = other_attrs.replace('<rect', '').replace('>', '').strip()
        
        return f'<path d="{path_d}" {other_attrs}>'
    
    # 应用转换
    result = svg_content
    result = re.sub(r'<circle[^>]*>', convert_circle_to_path, result)
    result = re.sub(r'<rect[^>]*(?:stroke|fill="(?!white")[^"]*")[^>]*>', convert_rect_to_path, result)  # 转换有描边或非白色填充的rect
    
    return result


def apply_grid_deformation_to_svg(svg_content: str,
                                  grid_state: Dict[str, Any],
                                  canvas_dimensions: Dict[str, int] = None,
                                  rasterize: bool = True,
                                  supersample: int = 2048,
                                  final_size: int = 256) -> str:
    """
    对SVG内容应用网格变形（内部函数）
    
    Args:
        svg_content: 原始SVG内容
        grid_state: 网格状态数据
    
    Returns:
        变形后的SVG内容
    """
    print(f"[GRID_DEBUG] 开始应用网格变形到SVG")
    print(f"[GRID_DEBUG] SVG内容长度: {len(svg_content)}")
    print(f"[GRID_DEBUG] 网格状态: {grid_state}")
    print(f"[GRID_DEBUG] 网格状态类型: {type(grid_state)}")
    
    # 首先将基本形状转换为路径
    print("[GRID_DEBUG] 转换基本形状为路径...")
    svg_content = convert_svg_shapes_to_paths(svg_content)
    print(f"[GRID_DEBUG] 转换后SVG长度: {len(svg_content)}")
    
    # 强制输出到控制台，确保调试信息可见
    import sys
    sys.stdout.flush()
    
    if not grid_state:
        print("[GRID_DEBUG] 网格状态为空，跳过变形")
        return svg_content
        
    if not isinstance(grid_state, dict):
        print(f"[GRID_DEBUG] 网格状态不是字典类型: {type(grid_state)}，跳过变形")
        return svg_content
        
    if 'controlPoints' not in grid_state:
        print("[GRID_DEBUG] 网格状态中没有controlPoints，跳过变形")
        return svg_content
    
    # 检查是否有实际的变形
    control_points = grid_state.get('controlPoints', [])
    if not control_points:
        print("[GRID_DEBUG] 控制点列表为空，跳过变形")
        return svg_content
        
    print(f"[GRID_DEBUG] 控制点数据: {control_points[:2]}...")  # 只显示前2个控制点
    
    print(f"[GRID_DEBUG] 检查控制点变形情况，共{len(control_points)}个控制点")
    
    # 检查是否有实际的变形
    has_deformation = False
    deformation_count = 0
    
    # 计算标准网格位置用于对比
    size = grid_state.get('size', 4)
    print(f"[GRID_DEBUG] 网格尺寸: {size}×{size}")
    
    # 使用前端传递的实际画布尺寸
    if canvas_dimensions:
        canvas_width = canvas_dimensions['width']
        canvas_height = canvas_dimensions['height']
    else:
        canvas_width = 800
        canvas_height = 600
    
    center_x = canvas_width / 2
    center_y = canvas_height / 2
    grid_width = 300
    grid_height = 300
    grid_start_x = center_x - grid_width / 2  # 250
    grid_start_y = center_y - grid_height / 2  # 175
    
    print(f"[GRID_DEBUG] 网格参数: 中心({center_x},{center_y}), 起始({grid_start_x},{grid_start_y}), 尺寸({grid_width}×{grid_height})")
    
    for i, point in enumerate(control_points):
        # 计算该控制点的标准位置
        row = i // size
        col = i % size
        standard_x = grid_start_x + col * grid_width / (size - 1)
        standard_y = grid_start_y + row * grid_height / (size - 1)
        
        # 检查是否偏离标准位置
        dx = abs(point['x'] - standard_x)
        dy = abs(point['y'] - standard_y)
        
        if dx > 5.0 or dy > 5.0:  # 允许5像素的误差
            has_deformation = True
            deformation_count += 1
            print(f"[GRID_DEBUG] 控制点{i}有变形: 当前({point['x']:.1f},{point['y']:.1f}) vs 标准({standard_x:.1f},{standard_y:.1f}), 偏差({dx:.1f},{dy:.1f})")
    
    print(f"[GRID_DEBUG] 变形控制点数量: {deformation_count}/{len(control_points)}")
    
    if not has_deformation:
        print("[GRID_DEBUG] 所有控制点都在标准位置，跳过变形")
        print("[GRID_DEBUG] 提示：要应用网格变形，请先在网格变形界面调整控制点")
        return svg_content
    
    def _sample_line(p0, p1, step_px=0.25):
        import math
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dist = math.hypot(dx, dy)
        n = max(4, int(dist / max(0.1, step_px)) + 1)
        return [(p0[0] + dx * t, p0[1] + dy * t) for t in [i/(n-1) for i in range(n)]]

    def _sample_quad(p0, p1, p2, samples=96):
        # Quadratic Bezier
        pts = []
        for i in range(samples):
            t = i / (samples - 1)
            mt = 1 - t
            x = mt*mt*p0[0] + 2*mt*t*p1[0] + t*t*p2[0]
            y = mt*mt*p0[1] + 2*mt*t*p1[1] + t*t*p2[1]
            pts.append((x, y))
        return pts

    def _sample_cubic(p0, p1, p2, p3, samples=128):
        # Cubic Bezier
        pts = []
        for i in range(samples):
            t = i / (samples - 1)
            mt = 1 - t
            x = (mt**3)*p0[0] + 3*(mt**2)*t*p1[0] + 3*mt*(t**2)*p2[0] + (t**3)*p3[0]
            y = (mt**3)*p0[1] + 3*(mt**2)*t*p1[1] + 3*mt*(t**2)*p2[1] + (t**3)*p3[1]
            pts.append((x, y))
        return pts

    def transform_path_data(match):
        # 高质量采样：将原路径采样为致密折线，再逐点应用网格变形
        path_data = match.group(1)
        commands = parse_svg_path(path_data)
        if not commands:
            return match.group(0)

        current = (0.0, 0.0)
        start_point = None
        sampled = []
        for cmd_type, coords in commands:
            t = cmd_type
            # 统一处理为绝对坐标（假定大多数为绝对命令；相对命令简单转绝对）
            if t == 'M':
                if len(coords) >= 2:
                    current = (coords[0], coords[1])
                    start_point = current
                    sampled.append(current)
                # 后续额外的坐标当作直线到达
                for i in range(2, len(coords), 2):
                    nxt = (coords[i], coords[i+1])
                    seg = _sample_line(current, nxt)
                    sampled.extend(seg[1:])
                    current = nxt
            elif t == 'm':
                if len(coords) >= 2:
                    current = (current[0] + coords[0], current[1] + coords[1])
                    start_point = current
                    sampled.append(current)
                for i in range(2, len(coords), 2):
                    nxt = (current[0] + coords[i], current[1] + coords[i+1])
                    seg = _sample_line(current, nxt)
                    sampled.extend(seg[1:])
                    current = nxt
            elif t in ('L', 'l'):
                for i in range(0, len(coords), 2):
                    if i + 1 >= len(coords): break
                    x = coords[i] + (0 if t=='L' else current[0])
                    y = coords[i+1] + (0 if t=='L' else current[1])
                    nxt = (x if t=='L' else x, y if t=='L' else y)
                    if t=='l':
                        nxt = (coords[i] + current[0], coords[i+1] + current[1])
                    seg = _sample_line(current, nxt)
                    sampled.extend(seg[1:])
                    current = nxt
            elif t in ('H', 'h'):
                for i in range(len(coords)):
                    x = coords[i] + (0 if t=='H' else current[0])
                    nxt = (x if t=='H' else x, current[1])
                    if t=='h':
                        nxt = (coords[i] + current[0], current[1])
                    seg = _sample_line(current, nxt)
                    sampled.extend(seg[1:])
                    current = nxt
            elif t in ('V', 'v'):
                for i in range(len(coords)):
                    y = coords[i] + (0 if t=='V' else current[1])
                    nxt = (current[0], y if t=='V' else y)
                    if t=='v':
                        nxt = (current[0], coords[i] + current[1])
                    seg = _sample_line(current, nxt)
                    sampled.extend(seg[1:])
                    current = nxt
            elif t in ('Q', 'q') and len(coords) >= 4:
                for i in range(0, len(coords), 4):
                    if i + 3 >= len(coords): break
                    cx = coords[i] + (0 if t=='Q' else current[0])
                    cy = coords[i+1] + (0 if t=='Q' else current[1])
                    ex = coords[i+2] + (0 if t=='Q' else current[0])
                    ey = coords[i+3] + (0 if t=='Q' else current[1])
                    quad_pts = _sample_quad(current, (cx, cy), (ex, ey))
                    sampled.extend(quad_pts[1:])
                    current = (ex, ey)
            elif t in ('C', 'c') and len(coords) >= 6:
                for i in range(0, len(coords), 6):
                    if i + 5 >= len(coords): break
                    c1x = coords[i] + (0 if t=='C' else current[0])
                    c1y = coords[i+1] + (0 if t=='C' else current[1])
                    c2x = coords[i+2] + (0 if t=='C' else current[0])
                    c2y = coords[i+3] + (0 if t=='C' else current[1])
                    ex = coords[i+4] + (0 if t=='C' else current[0])
                    ey = coords[i+5] + (0 if t=='C' else current[1])
                    cubic_pts = _sample_cubic(current, (c1x, c1y), (c2x, c2y), (ex, ey))
                    sampled.extend(cubic_pts[1:])
                    current = (ex, ey)
            elif t in ('Z', 'z') and start_point is not None:
                seg = _sample_line(current, start_point)
                sampled.extend(seg[1:])
                current = start_point
            else:
                # 其他命令(A/S/T等)暂不特殊处理，尽量保持原样坐标变换
                new_coords = []
                for i in range(0, len(coords), 2):
                    if i + 1 < len(coords):
                        x, y = coords[i], coords[i + 1]
                        new_coords.extend([x, y])
                if new_coords:
                    # 当作直线连接
                    for i in range(0, len(new_coords), 2):
                        nxt = (new_coords[i], new_coords[i+1])
                        seg = _sample_line(current, nxt)
                        sampled.extend(seg[1:])
                        current = nxt

        # 对采样点应用网格变形并构建路径（M + 多个L）
        if not sampled:
            return match.group(0)
        deformed = [deform_point(px, py, grid_state) for (px, py) in sampled]
        # 构建致密折线路径
        d_parts = []
        first = deformed[0]
        d_parts.append(f'M{first[0]:.4f} {first[1]:.4f}')
        for (x, y) in deformed[1:]:
            d_parts.append(f'L{x:.4f} {y:.4f}')
        return f'd="{"".join(d_parts)}"'
    
    def transform_path_data_single_quote(match):
        # 复用相同的致密采样逻辑
        double_match_like = type('obj', (object,), {'group': lambda self, idx: f'd="{match.group(1)}"' })()
        converted = transform_path_data(re.match(r'd="([^"]*)"', double_match_like.group(0))) if False else None
        # 直接调用上面的双引号处理：
        return transform_path_data(type('obj', (object,), {'group': lambda self, idx: match.group(idx) })())
    
    # 替换所有path元素的d属性（支持单引号和双引号）
    result = re.sub(r'd="([^"]*)"', transform_path_data, svg_content)
    result = re.sub(r"d='([^']*)'", transform_path_data_single_quote, result)
    
    # 应用裁剪逻辑：移动裁剪中心到文字中心，确保固定尺寸
    try:
        result = apply_cropping_logic(result)
    except Exception as e:
        print(f"[CROP_DEBUG] 裁剪失败，返回原始变形结果: {e}")
        # 如果裁剪失败，至少确保SVG有基本的尺寸属性
        if 'width=' not in result and 'height=' not in result:
            result = re.sub(r'<svg([^>]*?)>', r'<svg\1 width="256" height="256">', result)
    
    # 可选：将变形后的SVG栅格化为高分辨率，再双线性下采样，包装为<image>，获得与Canvas相近的平滑边缘
    if rasterize:
        try:
            import io
            import base64
            try:
                import cairosvg
            except ImportError:
                print('[RASTER] 警告: 未安装cairosvg，返回矢量SVG')
                return result
            from PIL import Image
            Resampling = getattr(Image, 'Resampling', Image)
            # 高分辨率渲染
            png_data = cairosvg.svg2png(bytestring=result.encode('utf-8'),
                                        output_width=supersample,
                                        output_height=supersample)
            img = Image.open(io.BytesIO(png_data)).convert('RGBA')
            # 下采样（双线性）
            # 与窗口Canvas观感对齐：使用双线性缩放
            img_small = img.resize((final_size, final_size), resample=Resampling.BILINEAR)
            # 贴白底
            bg = Image.new('RGB', (final_size, final_size), 'white')
            bg.paste(img_small, mask=img_small.split()[3] if img_small.mode == 'RGBA' else None)
            out = io.BytesIO()
            bg.save(out, format='PNG')
            b64 = base64.b64encode(out.getvalue()).decode('ascii')
            wrapper = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{final_size}" height="{final_size}" '
                f'viewBox="0 0 {final_size} {final_size}">\n'
                f'<image href="data:image/png;base64,{b64}" x="0" y="0" width="{final_size}" height="{final_size}"/>\n'
                f'</svg>'
            )
            return wrapper
        except Exception as e:
            print(f"[RASTER] 栅格化失败，返回矢量SVG: {e}")
            return result
    else:
        return result


def calculate_svg_bounds(svg_content: str) -> Tuple[float, float, float, float]:
    """
    计算SVG内容的边界框
    
    Returns:
        (min_x, min_y, max_x, max_y)
    """
    import re
    
    # 提取所有路径数据
    path_data_list = re.findall(r'd="([^"]*)"', svg_content) + re.findall(r"d='([^']*)'", svg_content)
    
    if not path_data_list:
        print("[CROP_DEBUG] 警告: 未找到任何路径数据")
        return (0, 0, 256, 256)  # 返回默认边界
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for path_data in path_data_list:
        try:
            commands = parse_svg_path(path_data)
            
            for cmd_type, coords in commands:
                # 处理坐标对
                for i in range(0, len(coords), 2):
                    if i + 1 < len(coords):
                        x, y = coords[i], coords[i + 1]
                        if not (math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y)):
                            min_x = min(min_x, x)
                            min_y = min(min_y, y)
                            max_x = max(max_x, x)
                            max_y = max(max_y, y)
        except Exception as e:
            print(f"[CROP_DEBUG] 解析路径数据时出错: {e}")
            continue
    
    # 检查是否找到有效边界
    if min_x == float('inf') or min_y == float('inf'):
        print("[CROP_DEBUG] 警告: 未找到有效坐标，使用默认边界")
        return (0, 0, 256, 256)
    
    return (min_x, min_y, max_x, max_y)


def apply_cropping_logic(svg_content: str) -> str:
    """
    应用裁剪逻辑：移动裁剪中心到文字中心，确保固定尺寸，取消边界限制
    
    Args:
        svg_content: 变形后的SVG内容
    
    Returns:
        裁剪后的SVG内容
    """
    print("[CROP_DEBUG] 开始应用裁剪逻辑")
    
    # 计算文字的实际边界
    min_x, min_y, max_x, max_y = calculate_svg_bounds(svg_content)
    
    # 计算文字中心
    text_center_x = (min_x + max_x) / 2
    text_center_y = (min_y + max_y) / 2
    
    print(f"[CROP_DEBUG] 文字边界: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")
    print(f"[CROP_DEBUG] 文字中心: ({text_center_x:.1f}, {text_center_y:.1f})")
    
    # 固定输出尺寸
    output_size = 256
    crop_size = output_size
    
    # 计算新的viewBox，确保包含所有内容
    # 方法1: 以文字中心为基础
    center_based_x = text_center_x - crop_size / 2
    center_based_y = text_center_y - crop_size / 2
    
    # 方法2: 确保包含所有边界
    # 添加小边距以确保内容不会被截断
    margin = 10
    boundary_based_x = min_x - margin
    boundary_based_y = min_y - margin
    boundary_width = (max_x - min_x) + 2 * margin
    boundary_height = (max_y - min_y) + 2 * margin
    
    # 使用更智能的viewBox计算 - 确保包含所有内容
    content_width = max_x - min_x
    content_height = max_y - min_y
    
    # 计算需要的最小尺寸（加上边距）
    required_width = content_width + 2 * margin
    required_height = content_height + 2 * margin
    
    # 使用足够大的尺寸来包含所有内容，但不小于标准尺寸
    final_crop_size = max(crop_size, required_width, required_height)
    
    # 如果内容超出标准尺寸很多，限制最大尺寸避免过大的SVG
    max_allowed_size = crop_size * 2  # 最大允许是标准尺寸的2倍
    if final_crop_size > max_allowed_size:
        print(f"[CROP_DEBUG] 内容过大，限制到最大尺寸: {max_allowed_size}")
        final_crop_size = max_allowed_size
    
    # 计算viewBox位置 - 优化的居中算法，支持视觉居中
    # 使用内容的实际边界来计算更精确的中心位置
    actual_content_center_x = (min_x + max_x) / 2
    actual_content_center_y = (min_y + max_y) / 2
    
    # 视觉居中调整：对于中文字符，可能需要微调
    # 检查内容分布的不对称性
    content_width = max_x - min_x
    content_height = max_y - min_y
    
    # 如果内容明显偏向一侧，进行视觉居中调整
    asymmetry_threshold = 0.15  # 15%的不对称阈值
    
    # 水平不对称检查
    left_space = actual_content_center_x - min_x
    right_space = max_x - actual_content_center_x
    if content_width > 50:  # 只对足够大的内容进行调整
        horizontal_asymmetry = abs(left_space - right_space) / content_width
        if horizontal_asymmetry > asymmetry_threshold:
            # 轻微调整以改善视觉平衡
            adjustment = (right_space - left_space) * 0.1  # 10%的调整
            actual_content_center_x += adjustment
            print(f"[CROP_DEBUG] 水平视觉居中调整: {adjustment:+.1f}px")
    
    # 垂直不对称检查
    top_space = actual_content_center_y - min_y
    bottom_space = max_y - actual_content_center_y
    if content_height > 50:  # 只对足够大的内容进行调整
        vertical_asymmetry = abs(top_space - bottom_space) / content_height
        if vertical_asymmetry > asymmetry_threshold:
            # 轻微调整以改善视觉平衡
            adjustment = (bottom_space - top_space) * 0.1  # 10%的调整
            actual_content_center_y += adjustment
            print(f"[CROP_DEBUG] 垂直视觉居中调整: {adjustment:+.1f}px")
    
    # 计算viewBox，使内容在最终图像中居中
    new_viewbox_x = actual_content_center_x - final_crop_size / 2
    new_viewbox_y = actual_content_center_y - final_crop_size / 2
    
    print(f"[CROP_DEBUG] 实际内容中心: ({actual_content_center_x:.1f}, {actual_content_center_y:.1f})")
    print(f"[CROP_DEBUG] 几何中心: ({text_center_x:.1f}, {text_center_y:.1f})")
    print(f"[CROP_DEBUG] 中心偏差: ({actual_content_center_x - text_center_x:.1f}, {actual_content_center_y - text_center_y:.1f})")
    
    # 最终验证：确保所有内容都在viewBox内
    viewbox_left = new_viewbox_x
    viewbox_right = new_viewbox_x + final_crop_size
    viewbox_top = new_viewbox_y
    viewbox_bottom = new_viewbox_y + final_crop_size
    
    # 如果还有内容超出，调整viewBox位置
    if min_x < viewbox_left:
        adjustment = viewbox_left - min_x + margin
        new_viewbox_x -= adjustment
        print(f"[CROP_DEBUG] 调整viewBox左边界: -{adjustment:.1f}")
    
    if max_x > viewbox_right:
        adjustment = max_x - viewbox_right + margin
        new_viewbox_x += adjustment
        print(f"[CROP_DEBUG] 调整viewBox右边界: +{adjustment:.1f}")
    
    if min_y < viewbox_top:
        adjustment = viewbox_top - min_y + margin
        new_viewbox_y -= adjustment
        print(f"[CROP_DEBUG] 调整viewBox上边界: -{adjustment:.1f}")
    
    if max_y > viewbox_bottom:
        adjustment = max_y - viewbox_bottom + margin
        new_viewbox_y += adjustment
        print(f"[CROP_DEBUG] 调整viewBox下边界: +{adjustment:.1f}")
    
    crop_size = final_crop_size
    
    if final_crop_size > 256 * 1.2:
        print(f"[CROP_DEBUG] 使用扩展viewBox: {final_crop_size:.1f} (标准: 256)")
    
    print(f"[CROP_DEBUG] 新viewBox: ({new_viewbox_x:.1f}, {new_viewbox_y:.1f}, {crop_size}, {crop_size})")
    print(f"[CROP_DEBUG] ViewBox包含: ({new_viewbox_x:.1f}, {new_viewbox_y:.1f}) 到 ({new_viewbox_x + crop_size:.1f}, {new_viewbox_y + crop_size:.1f})")
    print(f"[CROP_DEBUG] 内容边界: ({min_x:.1f}, {min_y:.1f}) 到 ({max_x:.1f}, {max_y:.1f})")
    
    # 完全重构SVG标签，避免重复属性
    svg_match = re.search(r'<svg([^>]*?)>', svg_content)
    if svg_match:
        existing_attrs = svg_match.group(1)
        
        # 提取必要的命名空间属性
        xmlns_match = re.search(r'xmlns[^=]*="[^"]*"', existing_attrs)
        xmlns_attr = xmlns_match.group(0) if xmlns_match else 'xmlns="http://www.w3.org/2000/svg"'
        
        # 构建全新的SVG标签，只包含必要属性
        new_svg_tag = f'<svg {xmlns_attr} width="{output_size}" height="{output_size}" viewBox="{new_viewbox_x:.2f} {new_viewbox_y:.2f} {crop_size} {crop_size}">'
        result = svg_content.replace(svg_match.group(0), new_svg_tag)
        
            # 智能处理背景：只在没有自定义背景时添加白色背景
        has_custom_background = False
        
        # 检查是否有非白色的背景元素（path或rect）
        custom_bg_patterns = [
            r'<path[^>]*fill="(?!white|#ffffff|#fff)[^"]*"[^>]*>',  # 非白色填充的path
            r'<rect[^>]*fill="(?!white|#ffffff|#fff)[^"]*"[^>]*>',  # 非白色填充的rect
        ]
        
        for pattern in custom_bg_patterns:
            if re.search(pattern, result):
                has_custom_background = True
                print(f"[CROP_DEBUG] 检测到自定义背景，保留原始背景")
                break
        
        if not has_custom_background:
            # 只有在没有自定义背景时才添加白色背景
            # 移除现有的白色背景矩形
            result = re.sub(r'<rect[^>]*fill=[\'"]white[\'"][^>]*/?>', '', result)
            
            # 添加新的白色背景矩形
            svg_end = result.find('>', result.find('<svg')) + 1
            white_bg = f'<rect x="{new_viewbox_x:.2f}" y="{new_viewbox_y:.2f}" width="{crop_size}" height="{crop_size}" fill="white"/>'
            result = result[:svg_end] + white_bg + result[svg_end:]
            print(f"[CROP_DEBUG] 添加白色背景")
        else:
            # 有自定义背景时，只移除多余的白色背景，保留变形后的背景
            print(f"[CROP_DEBUG] 保留自定义背景，不添加白色背景")
    else:
        print("[CROP_DEBUG] 警告: 未找到SVG标签")
        return svg_content
    
    print(f"[CROP_DEBUG] 裁剪完成，输出尺寸: {output_size}x{output_size}")
    
    return result


def load_grid_state_from_request(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    从请求数据中加载网格状态
    
    Args:
        request_data: 请求数据，可能包含grid_state字段
    
    Returns:
        网格状态数据或None
    """
    print(f"[GRID_DEBUG] 检查请求数据中的网格状态: {list(request_data.keys())}")
    
    grid_state = request_data.get('grid_state')
    if not grid_state:
        print("[GRID_DEBUG] 未找到grid_state字段")
        return None
    
    print(f"[GRID_DEBUG] 原始grid_state类型: {type(grid_state)}")
    print(f"[GRID_DEBUG] 原始grid_state内容: {grid_state}")
    
    # 如果是字符串，尝试解析JSON
    if isinstance(grid_state, str):
        try:
            grid_state = json.loads(grid_state)
            print(f"[GRID_DEBUG] JSON解析成功: {type(grid_state)}")
        except json.JSONDecodeError as e:
            print(f"[GRID_DEBUG] JSON解析失败: {e}")
            return None
    
    # 验证必要字段
    if not isinstance(grid_state, dict):
        print(f"[GRID_DEBUG] grid_state不是字典类型: {type(grid_state)}")
        return None
    
    required_fields = ['controlPoints', 'size']
    for field in required_fields:
        if field not in grid_state:
            print(f"[GRID_DEBUG] 缺少必要字段: {field}")
            return None
    
    # 检查变形强度字段，如果没有则设置默认值
    if 'deformStrength' not in grid_state:
        grid_state['deformStrength'] = 1.0
        print(f"[GRID_DEBUG] 设置默认变形强度: 1.0")
    
    print(f"[GRID_DEBUG] 网格状态验证成功:")
    print(f"  - 控制点数量: {len(grid_state['controlPoints'])}")
    print(f"  - 网格尺寸: {grid_state['size']}")
    print(f"  - 变形强度: {grid_state['deformStrength']}")
    
    # 验证控制点数量与网格尺寸匹配
    expected_points = grid_state['size'] * grid_state['size']
    actual_points = len(grid_state['controlPoints'])
    if actual_points != expected_points:
        print(f"[GRID_DEBUG] 警告: 控制点数量({actual_points})与网格尺寸({grid_state['size']}x{grid_state['size']}={expected_points})不匹配")
    
    return grid_state


def apply_image_based_grid_deformation(svg_content: str, grid_state: Dict[str, Any], 
                                     canvas_dimensions: Dict[str, int] = None,
                                     supersample: int = 3, final_size: int = 256) -> str:
    """
    图像级网格变形 - 与前端算法一致
    使用与前端相同的Catmull-Rom + Coons Patch算法
    """
    import sys
    print(f"[IMAGE_DEFORM] 🚀 开始图像级网格变形", flush=True)
    sys.stdout.flush()
    
    if not grid_state or not has_grid_deformation(grid_state):
        print("[IMAGE_DEFORM] 无网格变形，返回原始SVG", flush=True)
        return svg_content
    
    try:
        # 导入依赖
        try:
            import cairosvg
        except ImportError:
            print('[IMAGE_DEFORM] 警告: 未安装cairosvg，回退到路径级变形')
            return apply_grid_deformation_to_svg(svg_content, grid_state, canvas_dimensions)
        
        try:
            from PIL import Image
        except ImportError:
            print('[IMAGE_DEFORM] 警告: 未安装PIL，回退到路径级变形')
            return apply_grid_deformation_to_svg(svg_content, grid_state, canvas_dimensions)
        
        # 步骤1: SVG转为高分辨率图像
        print("[IMAGE_DEFORM] 步骤1: SVG转高分辨率图像")
        base_size = final_size * supersample
        png_data = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=base_size,
            output_height=base_size
        )
        source_img = Image.open(io.BytesIO(png_data)).convert('RGBA')
        print(f"[IMAGE_DEFORM] 源图像尺寸: {source_img.size}")
        
        # 步骤2: 应用网格变形
        print("[IMAGE_DEFORM] 步骤2: 应用网格变形")
        deformed_img = apply_catmull_rom_coons_deformation(
            source_img, grid_state, canvas_dimensions, base_size
        )
        
        # 步骤3: 下采样到目标尺寸
        print("[IMAGE_DEFORM] 步骤3: 下采样到目标尺寸")
        if deformed_img.size != (final_size, final_size):
            # 使用高质量双线性重采样
            Resampling = getattr(Image, 'Resampling', Image)
            deformed_img = deformed_img.resize((final_size, final_size), resample=Resampling.BILINEAR)
        
        # 步骤4: 贴白底并转换为base64
        print("[IMAGE_DEFORM] 步骤4: 生成最终SVG")
        bg = Image.new('RGB', (final_size, final_size), 'white')
        bg.paste(deformed_img, mask=deformed_img.split()[3] if deformed_img.mode == 'RGBA' else None)
        
        # 转换为PNG base64
        out = io.BytesIO()
        bg.save(out, format='PNG', quality=95)
        b64 = base64.b64encode(out.getvalue()).decode('ascii')
        
        # 包装为SVG
        result_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{final_size}" height="{final_size}" '
            f'viewBox="0 0 {final_size} {final_size}">\n'
            f'<rect x="0" y="0" width="{final_size}" height="{final_size}" fill="white"/>\n'
            f'<image href="data:image/png;base64,{b64}" x="0" y="0" width="{final_size}" height="{final_size}"/>\n'
            f'</svg>'
        )
        
        print(f"[IMAGE_DEFORM] ✅ 图像级变形完成")
        return result_svg
        
    except Exception as e:
        print(f"[IMAGE_DEFORM] ❌ 图像级变形失败: {e}")
        print(f"[IMAGE_DEFORM] 回退到路径级变形")
        return apply_grid_deformation_to_svg(svg_content, grid_state, canvas_dimensions)


def apply_catmull_rom_coons_deformation(source_img, grid_state: Dict[str, Any], 
                                       canvas_dimensions: Dict[str, int] = None, 
                                       img_size: int = 768):
    """
    应用Catmull-Rom + Coons Patch变形算法（与前端一致）
    """
    from PIL import Image, ImageDraw
    import numpy as np
    
    # 获取网格参数
    size = grid_state.get('size', 4)
    control_points = grid_state.get('controlPoints', [])
    
    if not control_points or len(control_points) != size * size:
        return source_img
    
    # 简化坐标系统：直接使用图像坐标系
    # 源图像就是SVG渲染的结果，直接在图像坐标系中工作
    print(f"[DEFORM_DEBUG] 源图像尺寸: {source_img.size}, 目标尺寸: {img_size}")
    
    # 网格覆盖整个图像
    grid_width = img_size
    grid_height = img_size
    grid_start_x = 0
    grid_start_y = 0
    
    # 创建输出图像
    output_img = Image.new('RGBA', (img_size, img_size), (255, 255, 255, 0))
    
    # 辅助函数
    def clamp_index(v, lo, hi):
        return max(lo, min(hi, v))
    
    def get_control_point(r, c):
        idx = r * size + c
        if 0 <= idx < len(control_points):
            return control_points[idx]
        return None
    
    def catmull_rom_to_bezier(p0, p1, p2, p3):
        """Catmull-Rom到Bezier转换"""
        c1 = {'x': p1['x'] + (p2['x'] - p0['x']) / 6, 'y': p1['y'] + (p2['y'] - p0['y']) / 6}
        c2 = {'x': p2['x'] - (p3['x'] - p1['x']) / 6, 'y': p2['y'] - (p3['y'] - p1['y']) / 6}
        return [
            {'x': p1['x'], 'y': p1['y']}, c1, c2, {'x': p2['x'], 'y': p2['y']}
        ]
    
    def bezier_eval(bz, t):
        """评估Bezier曲线上的点"""
        it = 1 - t
        b0 = it * it * it
        b1 = 3 * it * it * t
        b2 = 3 * it * t * t
        b3 = t * t * t
        return {
            'x': bz[0]['x'] * b0 + bz[1]['x'] * b1 + bz[2]['x'] * b2 + bz[3]['x'] * b3,
            'y': bz[0]['y'] * b0 + bz[1]['y'] * b1 + bz[2]['y'] * b2 + bz[3]['y'] * b3
        }
    
    # 网格单元变形
    cells = max(1, size - 1)
    SUBDIV = 20  # 高质量细分
    
    source_array = np.array(source_img)
    output_array = np.zeros_like(source_array)
    
    for gy in range(cells):
        for gx in range(cells):
            # 源图像区域
            src_x1 = (gx / cells) * img_size
            src_y1 = (gy / cells) * img_size
            src_x2 = ((gx + 1) / cells) * img_size
            src_y2 = ((gy + 1) / cells) * img_size
            
            # 四角控制点
            p00 = get_control_point(gy, gx)
            p10 = get_control_point(gy, gx + 1)
            p01 = get_control_point(gy + 1, gx)
            p11 = get_control_point(gy + 1, gx + 1)
            
            if not all([p00, p10, p01, p11]):
                continue
            
            # 构建四条边界Bezier曲线
            # 顶边
            ta = get_control_point(gy, clamp_index(gx - 1, 0, size - 1))
            tb = p00
            tc = p10
            td = get_control_point(gy, clamp_index(gx + 2, 0, size - 1))
            top_bz = catmull_rom_to_bezier(ta, tb, tc, td)
            
            # 底边
            ba = get_control_point(gy + 1, clamp_index(gx - 1, 0, size - 1))
            bb = p01
            bc = p11
            bd = get_control_point(gy + 1, clamp_index(gx + 2, 0, size - 1))
            bottom_bz = catmull_rom_to_bezier(ba, bb, bc, bd)
            
            # 左边
            la = get_control_point(clamp_index(gy - 1, 0, size - 1), gx)
            lb = p00
            lc = p01
            ld = get_control_point(clamp_index(gy + 2, 0, size - 1), gx)
            left_bz = catmull_rom_to_bezier(la, lb, lc, ld)
            
            # 右边
            ra = get_control_point(clamp_index(gy - 1, 0, size - 1), gx + 1)
            rb = p10
            rc = p11
            rd = get_control_point(clamp_index(gy + 2, 0, size - 1), gx + 1)
            right_bz = catmull_rom_to_bezier(ra, rb, rc, rd)
            
            def coons_patch(u, v):
                """Coons曲面插值"""
                top = bezier_eval(top_bz, u)
                bottom = bezier_eval(bottom_bz, u)
                left = bezier_eval(left_bz, v)
                right = bezier_eval(right_bz, v)
                
                # 双线性混合
                blend_uv = {
                    'x': p00['x'] * (1 - u) * (1 - v) + p10['x'] * u * (1 - v) + 
                         p01['x'] * (1 - u) * v + p11['x'] * u * v,
                    'y': p00['y'] * (1 - u) * (1 - v) + p10['y'] * u * (1 - v) + 
                         p01['y'] * (1 - u) * v + p11['y'] * u * v
                }
                
                return {
                    'x': top['x'] * (1 - v) + bottom['x'] * v + left['x'] * (1 - u) + 
                         right['x'] * u - blend_uv['x'],
                    'y': top['y'] * (1 - v) + bottom['y'] * v + left['y'] * (1 - u) + 
                         right['y'] * u - blend_uv['y']
                }
            
            # 细分渲染
            for vstep in range(SUBDIV):
                v0 = vstep / SUBDIV
                v1 = (vstep + 1) / SUBDIV
                sy0 = src_y1 + (src_y2 - src_y1) * v0
                sy1 = src_y1 + (src_y2 - src_y1) * v1
                
                for ustep in range(SUBDIV):
                    u0 = ustep / SUBDIV
                    u1 = (ustep + 1) / SUBDIV
                    sx0 = src_x1 + (src_x2 - src_x1) * u0
                    sx1 = src_x1 + (src_x2 - src_x1) * u1
                    
                    # 目标四角
                    d00 = coons_patch(u0, v0)
                    d10 = coons_patch(u1, v0)
                    d01 = coons_patch(u0, v1)
                    d11 = coons_patch(u1, v1)
                    
                    # 使用三角形仿射变换（与前端一致）
                    try:
                        # 源四角点（图像坐标）
                        src_quad = [
                            (sx0, sy0), (sx1, sy0), (sx0, sy1), (sx1, sy1)
                        ]
                        
                        # 目标四角点（前端画布坐标转图像坐标）
                        def canvas_to_img(cx, cy):
                            # 前端网格坐标系参数（与前端一致）
                            if canvas_dimensions:
                                canvas_width = canvas_dimensions.get('width', 800)
                                canvas_height = canvas_dimensions.get('height', 600)
                            else:
                                canvas_width = 800
                                canvas_height = 600
                            
                            center_x = canvas_width / 2
                            center_y = canvas_height / 2
                            frontend_grid_width = 300
                            frontend_grid_height = 300
                            frontend_grid_start_x = center_x - frontend_grid_width / 2
                            frontend_grid_start_y = center_y - frontend_grid_height / 2
                            
                            # SVG在前端网格中央，占据80%的网格区域
                            svg_area_width = frontend_grid_width * 0.8
                            svg_area_height = frontend_grid_height * 0.8
                            svg_area_start_x = center_x - svg_area_width / 2
                            svg_area_start_y = center_y - svg_area_height / 2
                            
                            # 将前端画布坐标映射到图像坐标（0-img_size）
                            rel_x = (cx - svg_area_start_x) / svg_area_width
                            rel_y = (cy - svg_area_start_y) / svg_area_height
                            img_x = rel_x * img_size
                            img_y = rel_y * img_size
                            return (img_x, img_y)
                        
                        dst_quad = [
                            canvas_to_img(d00['x'], d00['y']),
                            canvas_to_img(d10['x'], d10['y']),
                            canvas_to_img(d01['x'], d01['y']),
                            canvas_to_img(d11['x'], d11['y'])
                        ]
                        
                        # 绘制两个三角形
                        triangles = [
                            # 三角形1: (0,1,2) -> 左上三角
                            (src_quad[0], src_quad[1], src_quad[2], 
                             dst_quad[0], dst_quad[1], dst_quad[2]),
                            # 三角形2: (3,2,1) -> 右下三角
                            (src_quad[3], src_quad[2], src_quad[1], 
                             dst_quad[3], dst_quad[2], dst_quad[1])
                        ]
                        
                        for src_tri, dst_tri in triangles:
                            draw_image_triangle_affine_numpy(
                                source_array, output_array, img_size,
                                src_tri[0], src_tri[1], src_tri[2],
                                dst_tri[0], dst_tri[1], dst_tri[2]
                            )
                    
                    except Exception as e:
                        continue  # 跳过有问题的像素块
    
    return Image.fromarray(output_array)


def draw_image_triangle_affine_numpy(source_array, output_array, img_size,
                                    src_p0, src_p1, src_p2,
                                    dst_p0, dst_p1, dst_p2):
    """
    NumPy版本的三角形仿射变换（与前端drawImageTriangleAffine一致）
    """
    import numpy as np
    
    # 转换为numpy数组
    sx0, sy0 = src_p0
    sx1, sy1 = src_p1
    sx2, sy2 = src_p2
    dx0, dy0 = dst_p0
    dx1, dy1 = dst_p1
    dx2, dy2 = dst_p2
    
    # 计算源三角形的仿射变换矩阵
    # 源矩阵A
    ax = sx1 - sx0
    bx = sx2 - sx0
    ay = sy1 - sy0
    by = sy2 - sy0
    
    det = ax * by - bx * ay
    if abs(det) < 1e-10:
        return  # 退化三角形，跳过
    
    inv_det = 1.0 / det
    # A^-1
    a11 = by * inv_det
    a12 = -bx * inv_det
    a21 = -ay * inv_det
    a22 = ax * inv_det
    
    # 目标矩阵B
    ux = dx1 - dx0
    vx = dx2 - dx0
    uy = dy1 - dy0
    vy = dy2 - dy0
    
    # M = B * A^-1
    m11 = ux * a11 + vx * a21
    m12 = ux * a12 + vx * a22
    m21 = uy * a11 + vy * a21
    m22 = uy * a12 + vy * a22
    
    # e = d0 - M * s0
    e = dx0 - (m11 * sx0 + m12 * sy0)
    f = dy0 - (m21 * sx0 + m22 * sy0)
    
    # 计算目标三角形的边界框
    min_x = max(0, int(min(dx0, dx1, dx2)))
    max_x = min(img_size - 1, int(max(dx0, dx1, dx2)) + 1)
    min_y = max(0, int(min(dy0, dy1, dy2)))
    max_y = min(img_size - 1, int(max(dy0, dy1, dy2)) + 1)
    
    if min_x >= max_x or min_y >= max_y:
        return
    
    # 点在三角形内的判断函数
    def point_in_triangle(x, y, x0, y0, x1, y1, x2, y2):
        # 使用重心坐标
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-10:
            return False
        
        a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / denom
        b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / denom
        c = 1 - a - b
        
        return a >= 0 and b >= 0 and c >= 0
    
    # 遍历目标三角形内的每个像素
    for dy in range(min_y, max_y + 1):
        for dx in range(min_x, max_x + 1):
            # 检查点是否在三角形内
            if point_in_triangle(dx, dy, dx0, dy0, dx1, dy1, dx2, dy2):
                # 反向变换找到源像素位置
                # 应用逆变换: src = M^-1 * (dst - e)
                dst_x = dx - e
                dst_y = dy - f
                
                # 计算M的逆矩阵
                m_det = m11 * m22 - m12 * m21
                if abs(m_det) < 1e-10:
                    continue
                
                inv_m_det = 1.0 / m_det
                inv_m11 = m22 * inv_m_det
                inv_m12 = -m12 * inv_m_det
                inv_m21 = -m21 * inv_m_det
                inv_m22 = m11 * inv_m_det
                
                src_x = inv_m11 * dst_x + inv_m12 * dst_y + sx0
                src_y = inv_m21 * dst_x + inv_m22 * dst_y + sy0
                
                # 双线性插值采样
                src_x_int = int(src_x)
                src_y_int = int(src_y)
                
                if (0 <= src_x_int < img_size - 1 and 
                    0 <= src_y_int < img_size - 1):
                    
                    # 双线性插值
                    fx = src_x - src_x_int
                    fy = src_y - src_y_int
                    
                    # 四个邻近像素
                    p00 = source_array[src_y_int, src_x_int]
                    p10 = source_array[src_y_int, src_x_int + 1]
                    p01 = source_array[src_y_int + 1, src_x_int]
                    p11 = source_array[src_y_int + 1, src_x_int + 1]
                    
                    # 双线性插值计算
                    pixel = (p00 * (1 - fx) * (1 - fy) + 
                            p10 * fx * (1 - fy) + 
                            p01 * (1 - fx) * fy + 
                            p11 * fx * fy)
                    
                    output_array[dy, dx] = pixel.astype(np.uint8)


def apply_smooth_grid_deformation(svg_content: str, grid_state: Dict[str, Any], 
                                 canvas_dimensions: Dict[str, int] = None) -> str:
    """
    改进的平滑路径级变形 - 确保输出平滑
    """
    print(f"[SMOOTH_DEFORM] 🎯 开始平滑路径级变形")
    
    if not grid_state or not has_grid_deformation(grid_state):
        return svg_content
    
    try:
        # 使用更高密度的采样和曲线拟合
        result = apply_grid_deformation_to_svg(
            svg_content, grid_state, canvas_dimensions, 
            rasterize=False,  # 不栅格化，保持矢量
            supersample=1,
            final_size=256
        )
        
        # 后处理：将密集折线转换为平滑曲线
        result = smooth_svg_paths(result)
        
        print(f"[SMOOTH_DEFORM] ✅ 平滑路径级变形完成")
        return result
        
    except Exception as e:
        print(f"[SMOOTH_DEFORM] ❌ 平滑变形失败: {e}")
        return svg_content


def smooth_svg_paths(svg_content: str) -> str:
    """
    将SVG中的密集折线转换为平滑曲线
    """
    import re
    
    def smooth_path_data(match):
        path_data = match.group(1)
        
        # 提取所有L命令的坐标点
        points = []
        l_commands = re.findall(r'L([\d.-]+)\s+([\d.-]+)', path_data)
        
        if len(l_commands) < 3:
            return match.group(0)  # 点太少，不处理
        
        # 获取起点
        m_match = re.search(r'M([\d.-]+)\s+([\d.-]+)', path_data)
        if m_match:
            start_x, start_y = float(m_match.group(1)), float(m_match.group(2))
            points.append((start_x, start_y))
        
        # 添加所有L命令的点
        for x_str, y_str in l_commands:
            points.append((float(x_str), float(y_str)))
        
        if len(points) < 4:
            return match.group(0)
        
        # 使用三次贝塞尔曲线拟合
        smooth_path = create_smooth_curve(points)
        
        return f'd="{smooth_path}"'
    
    # 替换所有路径数据
    result = re.sub(r'd="([^"]*)"', smooth_path_data, svg_content)
    return result


def clamp_point(point):
    """
    限制点坐标在安全范围内，防止SVG坐标溢出
    """
    x, y = point
    # 使用更宽松的坐标范围：-500 到 800
    # 允许更大的变形空间，避免截断笔画
    safe_x = max(-500, min(800, x))
    safe_y = max(-500, min(800, y))
    return (safe_x, safe_y)


def create_smooth_curve(points):
    """
    从点列表创建平滑的三次贝塞尔曲线 - 带坐标安全限制的版本
    """
    # 首先对所有输入点进行坐标限制
    clamped_points = [clamp_point(p) for p in points]
    
    if len(clamped_points) < 4:
        # 点太少，返回直线（使用限制后的点）
        path_parts = [f"M{clamped_points[0][0]:.1f},{clamped_points[0][1]:.1f}"]
        for i in range(1, len(clamped_points)):
            path_parts.append(f"L{clamped_points[i][0]:.1f},{clamped_points[i][1]:.1f}")
        return " ".join(path_parts)
    
    # 简化：每隔几个点才创建一个贝塞尔段，减少复杂度
    step = max(1, len(clamped_points) // 15)  # 最多15个贝塞尔段，提高性能
    simplified_points = [clamped_points[i] for i in range(0, len(clamped_points), step)]
    if simplified_points[-1] != clamped_points[-1]:
        simplified_points.append(clamped_points[-1])  # 确保包含终点
    
    if len(simplified_points) < 4:
        # 简化后点太少，返回直线
        path_parts = [f"M{simplified_points[0][0]:.1f},{simplified_points[0][1]:.1f}"]
        for i in range(1, len(simplified_points)):
            path_parts.append(f"L{simplified_points[i][0]:.1f},{simplified_points[i][1]:.1f}")
        return " ".join(path_parts)
    
    path_parts = [f"M{simplified_points[0][0]:.1f},{simplified_points[0][1]:.1f}"]
    
    # 使用简化的三次贝塞尔曲线
    for i in range(len(simplified_points) - 1):
        p1 = simplified_points[i]
        p2 = simplified_points[i + 1]
        
        # 简单的控制点计算：在两点间1/3和2/3处
        cp1_x = p1[0] + (p2[0] - p1[0]) * 0.33
        cp1_y = p1[1] + (p2[1] - p1[1]) * 0.33
        cp2_x = p1[0] + (p2[0] - p1[0]) * 0.67
        cp2_y = p1[1] + (p2[1] - p1[1]) * 0.67
        
        # 确保控制点在合理范围内 - 使用更宽松的范围避免截断
        cp1_x = max(-500, min(800, cp1_x))
        cp1_y = max(-500, min(800, cp1_y))
        cp2_x = max(-500, min(800, cp2_x))
        cp2_y = max(-500, min(800, cp2_y))
        p2_x = max(-500, min(800, p2[0]))
        p2_y = max(-500, min(800, p2[1]))
        
        path_parts.append(f"C{cp1_x:.1f},{cp1_y:.1f} {cp2_x:.1f},{cp2_y:.1f} {p2_x:.1f},{p2_y:.1f}")
    
    return " ".join(path_parts)
