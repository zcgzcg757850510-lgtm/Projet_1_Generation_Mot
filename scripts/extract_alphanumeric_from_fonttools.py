#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用fontTools从开源字体提取字母数字数据
完全基于字体文件，不手动创建任何数据
参考标点符号提取方法
"""

import os
import json

print("=" * 70)
print("从开源字体提取字母数字（fontTools方法）")
print("=" * 70)

FONT_PATH = 'fonts/SourceSansPro-Regular.ttf'


def extract_glyph_outline(font_path, char):
    """
    从字体文件提取字符轮廓
    返回: (outline_commands, units_per_em)
    """
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.recordingPen import RecordingPen
        
        font = TTFont(font_path)
        
        # 获取字符的glyph名称
        cmap = font.getBestCmap()
        if ord(char) not in cmap:
            return None, None
        
        glyph_name = cmap[ord(char)]
        
        # 获取glyph set
        glyph_set = font.getGlyphSet()
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
    将字体轮廓转换为medians格式
    直接使用轮廓点作为笔画路径（类似标点符号方法）
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
            # 直线到
            current_stroke.append([int(args[0][0] * scale), int(args[0][1] * scale)])
        
        elif command == 'curveTo':
            # 三次贝塞尔曲线 - 采样点
            for point in args:
                current_stroke.append([int(point[0] * scale), int(point[1] * scale)])
        
        elif command == 'qCurveTo':
            # 二次贝塞尔曲线 - 采样点
            for point in args:
                current_stroke.append([int(point[0] * scale), int(point[1] * scale)])
        
        elif command == 'closePath':
            # 闭合路径
            if current_stroke and len(current_stroke) >= 2:
                # 闭合：添加起点作为终点
                if current_stroke[0] != current_stroke[-1]:
                    current_stroke.append(current_stroke[0])
                medians.append(current_stroke)
            current_stroke = []
    
    # 添加最后一笔
    if current_stroke and len(current_stroke) >= 2:
        medians.append(current_stroke)
    
    return medians


def douglas_peucker(points, tolerance=5.0):
    """
    Douglas-Peucker算法简化路径
    """
    if len(points) <= 2:
        return points
    
    def point_line_distance(point, line_start, line_end):
        """点到线段的距离"""
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
    
    # 找最远点
    max_dist = 0
    max_index = 0
    
    for i in range(1, len(points) - 1):
        dist = point_line_distance(points[i], points[0], points[-1])
        if dist > max_dist:
            max_dist = dist
            max_index = i
    
    # 递归简化
    if max_dist > tolerance:
        left = douglas_peucker(points[:max_index + 1], tolerance)
        right = douglas_peucker(points[max_index:], tolerance)
        return left[:-1] + right
    else:
        return [points[0], points[-1]]


def simplify_medians(medians, tolerance=3.0):
    """简化所有笔画"""
    simplified = []
    for stroke in medians:
        if len(stroke) > 2:
            simplified.append(douglas_peucker(stroke, tolerance))
        else:
            simplified.append(stroke)
    return simplified


def normalize_to_mmh(medians):
    """
    归一化到MMH坐标系
    X: 0-1024, Y: 0-900
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
    
    # 计算缩放比例（保持宽高比）
    target_size = 600  # 目标大小
    scale = min(target_size / width, target_size / height) * 0.8
    
    # 计算中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 归一化
    normalized = []
    for stroke in medians:
        normalized_stroke = []
        for point in stroke:
            # 平移到原点，缩放，平移到MMH中心
            x = (point[0] - center_x) * scale + 512
            y = 900 - ((point[1] - center_y) * scale + 388)  # 翻转Y轴
            normalized_stroke.append([int(x), int(y)])
        normalized.append(normalized_stroke)
    
    return normalized


def extract_character(char, font_path):
    """提取单个字符"""
    # 提取轮廓
    outline, units_per_em = extract_glyph_outline(font_path, char)
    
    if not outline or not units_per_em:
        return None
    
    # 计算缩放比例
    scale = 1000.0 / units_per_em
    
    # 转换为medians
    medians = outline_to_medians(outline, scale)
    
    if not medians:
        return None
    
    # 简化点数
    medians = simplify_medians(medians, tolerance=3.0)
    
    # 归一化到MMH
    medians = normalize_to_mmh(medians)
    
    return medians


def main():
    print(f"\n📁 字体: {FONT_PATH}")
    
    if not os.path.exists(FONT_PATH):
        print(f"❌ 字体不存在: {FONT_PATH}")
        return 1
    
    # 检查fontTools
    try:
        from fontTools.ttLib import TTFont
        print("✅ fontTools已安装")
    except:
        print("❌ 需要安装fontTools:")
        print("   pip install fonttools")
        return 1
    
    print("\n🎨 提取字母数字")
    print("-" * 70)
    
    # 所有字符
    chars = (
        [str(i) for i in range(10)] +  # 0-9
        [chr(i) for i in range(ord('A'), ord('Z')+1)] +  # A-Z
        [chr(i) for i in range(ord('a'), ord('z')+1)]  # a-z
    )
    
    data = {}
    success = 0
    
    for char in chars:
        try:
            medians = extract_character(char, FONT_PATH)
            
            if medians and len(medians) > 0:
                # 计算总点数
                total_points = sum(len(s) for s in medians)
                
                char_type = 'digit' if char.isdigit() else ('uppercase' if char.isupper() else 'lowercase')
                
                data[char] = {
                    "character": char,
                    "medians": medians,
                    "strokes": len(medians),
                    "type": char_type,
                    "source": "source_sans_pro_fonttools",
                    "license": "OFL",
                    "coordinate_system": "MMH",
                    "extraction_method": "fonttools_outline"
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
    
    output = 'data/alphanumeric_medians_fonttools.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(output)
    print(f"✅ 已保存: {output}")
    print(f"📦 大小: {size/1024:.2f} KB")
    
    # 显示字母a
    if 'a' in data:
        print(f"\n📝 字母a:")
        print(f"  笔画: {data['a']['strokes']}个")
        print(f"  来源: 100%从字体文件提取")
        for i, s in enumerate(data['a']['medians'], 1):
            print(f"  笔画{i}: {len(s)}点")
    
    print("\n" + "=" * 70)
    print("✅ 完成！所有数据100%来自开源字体文件！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 可视化测试: python test_letter_a_visual.py")
    print("  2. 如果满意，替换:")
    print("     copy data\\alphanumeric_medians_fonttools.json data\\alphanumeric_medians.json")
    print("  3. 重启服务器")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

