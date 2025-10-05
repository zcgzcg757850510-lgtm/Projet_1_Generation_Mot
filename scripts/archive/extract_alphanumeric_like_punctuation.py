#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字母数字提取器（使用标点符号的成功方法）
100%从字体文件提取，使用fontTools
"""

import os
import json

print("=" * 70)
print("使用fontTools提取字母数字（标点符号方法）")
print("=" * 70)

FONT_PATH = 'fonts/SourceSansPro-Regular.ttf'


def extract_glyph_outline(font_path, char):
    """
    从字体文件提取字符轮廓（标点符号的方法）
    """
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.recordingPen import RecordingPen
        
        font = TTFont(font_path)
        glyph_set = font.getGlyphSet()
        
        # 获取字符对应的glyph名称
        cmap = font.getBestCmap()
        if not cmap:
            return None, None
        
        glyph_name = cmap.get(ord(char))
        if not glyph_name:
            return None, None
        
        if glyph_name not in glyph_set:
            return None, None
        
        # 使用RecordingPen记录绘图命令
        pen = RecordingPen()
        glyph_set[glyph_name].draw(pen)
        
        # 获取units_per_em
        units_per_em = font['head'].unitsPerEm
        
        font.close()
        
        return pen.value, units_per_em
        
    except Exception as e:
        print(f"  ❌ 提取失败 {char}: {e}")
        return None, None


def outline_to_medians(outline, scale=1.0):
    """
    将轮廓转换为medians格式（标点符号的方法）
    """
    if not outline:
        return []
    
    medians = []
    current_stroke = []
    
    for command, args in outline:
        if command == 'moveTo':
            # 开始新笔画
            if current_stroke and len(current_stroke) >= 2:
                medians.append(current_stroke)
            current_stroke = [[int(args[0][0] * scale), int(args[0][1] * scale)]]
        
        elif command == 'lineTo':
            current_stroke.append([int(args[0][0] * scale), int(args[0][1] * scale)])
        
        elif command == 'curveTo':
            # 三次贝塞尔曲线
            for point in args:
                current_stroke.append([int(point[0] * scale), int(point[1] * scale)])
        
        elif command == 'qCurveTo':
            # 二次贝塞尔曲线
            for point in args:
                current_stroke.append([int(point[0] * scale), int(point[1] * scale)])
        
        elif command == 'closePath':
            # 闭合路径
            if current_stroke and len(current_stroke) >= 2:
                # 闭合：添加起点
                if current_stroke[0] != current_stroke[-1]:
                    current_stroke.append(current_stroke[0])
                medians.append(current_stroke)
            current_stroke = []
    
    # 添加最后一笔
    if current_stroke and len(current_stroke) >= 2:
        medians.append(current_stroke)
    
    return medians


def simplify_medians(medians, tolerance=3.0):
    """
    简化medians（Douglas-Peucker算法）
    """
    def point_line_distance(point, line_start, line_end):
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return ((x0 - x1)**2 + (y0 - y1)**2)**0.5
        
        num = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1)
        den = (dy**2 + dx**2)**0.5
        
        return num / den
    
    def douglas_peucker(points, tol):
        if len(points) <= 2:
            return points
        
        max_dist = 0
        max_index = 0
        
        for i in range(1, len(points) - 1):
            dist = point_line_distance(points[i], points[0], points[-1])
            if dist > max_dist:
                max_dist = dist
                max_index = i
        
        if max_dist > tol:
            left = douglas_peucker(points[:max_index + 1], tol)
            right = douglas_peucker(points[max_index:], tol)
            return left[:-1] + right
        else:
            return [points[0], points[-1]]
    
    simplified = []
    for stroke in medians:
        if len(stroke) > 2:
            simplified.append(douglas_peucker(stroke, tolerance))
        else:
            simplified.append(stroke)
    
    return simplified


def normalize_to_mmh(medians):
    """
    归一化到MMH坐标系（标点符号的方法）
    """
    if not medians:
        return medians
    
    # 收集所有点
    all_points = []
    for stroke in medians:
        all_points.extend(stroke)
    
    if not all_points:
        return medians
    
    # 计算边界
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return medians
    
    # 缩放到合适大小
    target_size = 600
    scale = min(target_size / width, target_size / height) * 0.8
    
    # 计算中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 归一化
    normalized = []
    for stroke in medians:
        normalized_stroke = []
        for point in stroke:
            x = (point[0] - center_x) * scale + 512
            y = 900 - ((point[1] - center_y) * scale + 388)
            normalized_stroke.append([int(x), int(y)])
        normalized.append(normalized_stroke)
    
    return normalized


def extract_character(char, font_path):
    """提取单个字符（标点符号的方法）"""
    # 提取轮廓
    outline, units_per_em = extract_glyph_outline(font_path, char)
    
    if not outline or not units_per_em:
        return None
    
    # 计算缩放
    scale = 1000.0 / units_per_em
    
    # 转换为medians
    medians = outline_to_medians(outline, scale)
    
    if not medians:
        return None
    
    # 简化
    medians = simplify_medians(medians, tolerance=3.0)
    
    # 归一化
    medians = normalize_to_mmh(medians)
    
    return medians


def main():
    print(f"\n📁 字体: {FONT_PATH}")
    
    if not os.path.exists(FONT_PATH):
        print(f"❌ 字体不存在!")
        return 1
    
    # 检查fontTools
    try:
        from fontTools.ttLib import TTFont
        print("✅ fontTools已安装")
    except:
        print("❌ fontTools未安装，请运行: pip install fonttools")
        return 1
    
    print("\n🎨 提取字母数字")
    print("-" * 70)
    
    chars = (
        [str(i) for i in range(10)] +
        [chr(i) for i in range(ord('A'), ord('Z')+1)] +
        [chr(i) for i in range(ord('a'), ord('z')+1)]
    )
    
    data = {}
    success = 0
    
    for char in chars:
        try:
            medians = extract_character(char, FONT_PATH)
            
            if medians and len(medians) > 0:
                total_points = sum(len(s) for s in medians)
                char_type = 'digit' if char.isdigit() else ('uppercase' if char.isupper() else 'lowercase')
                
                data[char] = {
                    "character": char,
                    "medians": medians,
                    "strokes": len(medians),
                    "type": char_type,
                    "source": "source_sans_pro_fonttools_method",
                    "license": "OFL",
                    "coordinate_system": "MMH",
                    "extraction_method": "fonttools_like_punctuation"
                }
                
                success += 1
                marker = "🔧" if char in ['a', 'b', 'd', 'e', 'g', 'o', 'p', 'q'] else "✅"
                print(f"  {marker} {char}: {len(medians)}笔画, {total_points}点")
            else:
                print(f"  ⚠️  {char}: 提取失败")
                
        except Exception as e:
            print(f"  ❌ {char}: {e}")
    
    print(f"\n✅ 成功: {success}/{len(chars)}")
    
    # 统计
    stats = {
        'digit': sum(1 for v in data.values() if v['type'] == 'digit'),
        'uppercase': sum(1 for v in data.values() if v['type'] == 'uppercase'),
        'lowercase': sum(1 for v in data.values() if v['type'] == 'lowercase')
    }
    
    print(f"\n📊 统计:")
    for t, c in stats.items():
        print(f"  {t}: {c}个")
    
    # 保存
    print("\n💾 保存")
    print("-" * 70)
    
    # 备份
    output = 'data/alphanumeric_medians.json'
    if os.path.exists(output):
        import shutil
        backup = output + '.backup_before_fonttools'
        shutil.copy(output, backup)
        print(f"📦 已备份: {backup}")
    
    # 保存
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(output)
    print(f"✅ 已保存: {output}")
    print(f"📦 大小: {size/1024:.2f} KB")
    
    # 验证字母a
    if 'a' in data:
        print(f"\n📝 字母a:")
        print(f"  笔画: {data['a']['strokes']}个")
        print(f"  总点数: {sum(len(s) for s in data['a']['medians'])}个")
        for i, s in enumerate(data['a']['medians'], 1):
            print(f"  笔画{i}: {len(s)}点")
    
    print("\n" + "=" * 70)
    print("✅ 完成！使用标点符号的成功方法！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 重启服务器")
    print("  2. 测试字母a")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

