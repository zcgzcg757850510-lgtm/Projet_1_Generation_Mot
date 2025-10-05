#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复小写字母的提取问题
特别是有圆圈的字母：a, b, d, e, g, o, p, q
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage

print("=" * 70)
print("修复小写字母提取问题")
print("=" * 70)

FONT_PATH = 'fonts/SourceSansPro-Regular.ttf'


def render_char(char, size=512):
    """高分辨率渲染"""
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, int(size * 0.5))
    
    bbox = draw.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    
    draw.text((x, y), char, fill=0, font=font)
    return img


def extract_multiple_strokes(img_array):
    """
    提取多个笔画
    使用连通域分析，每个独立的连通区域作为一个笔画
    """
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 连通域标记
    labeled, num_features = ndimage.label(binary)
    
    if num_features == 0:
        return []
    
    strokes = []
    
    # 对每个连通域提取中心线
    for i in range(1, num_features + 1):
        component = (labeled == i).astype(np.uint8)
        
        # 提取这个连通域的中心线
        points = extract_centerline_from_component(component)
        
        if points and len(points) >= 2:
            strokes.append(points)
    
    # 按照Y坐标排序笔画（上面的笔画先）
    strokes.sort(key=lambda s: min(p[1] for p in s))
    
    return strokes


def extract_centerline_from_component(component):
    """从单个连通域提取中心线"""
    h, w = component.shape
    points = []
    
    # 方法：列扫描
    for x in range(0, w, 2):
        col = component[:, x]
        black_pixels = np.where(col > 0)[0]
        
        if len(black_pixels) > 0:
            # 如果黑色像素是连续的，取中心
            if len(black_pixels) > 1:
                # 检查连续性
                gaps = np.diff(black_pixels)
                max_gap = np.max(gaps) if len(gaps) > 0 else 0
                
                if max_gap <= 3:  # 连续
                    center_y = int(np.mean(black_pixels))
                    points.append([x, center_y])
                else:
                    # 不连续，取第一段的中心
                    first_segment = []
                    for i, pixel in enumerate(black_pixels):
                        if i == 0 or black_pixels[i] - black_pixels[i-1] <= 3:
                            first_segment.append(pixel)
                        else:
                            break
                    if first_segment:
                        center_y = int(np.mean(first_segment))
                        points.append([x, center_y])
            else:
                points.append([x, black_pixels[0]])
    
    # 如果点太少，尝试行扫描
    if len(points) < 5:
        points = []
        for y in range(0, h, 2):
            row = component[y, :]
            black_pixels = np.where(row > 0)[0]
            
            if len(black_pixels) > 0:
                center_x = int(np.mean(black_pixels))
                points.append([center_x, y])
    
    return points


def simplify_stroke(points, max_points=20):
    """简化单个笔画的点数"""
    if len(points) <= max_points:
        return points
    
    step = len(points) / max_points
    simplified = []
    
    for i in range(max_points):
        index = int(i * step)
        if index < len(points):
            simplified.append(points[index])
    
    if simplified[-1] != points[-1]:
        simplified.append(points[-1])
    
    return simplified


def to_mmh_coords(strokes, original_size=512):
    """转换多个笔画为MMH坐标"""
    if not strokes:
        return []
    
    scale = 1024.0 / original_size
    mmh_strokes = []
    
    for stroke in strokes:
        mmh_stroke = []
        for x, y in stroke:
            mmh_x = int(x * scale)
            mmh_y = int(900 - y * scale)
            mmh_stroke.append([mmh_x, mmh_y])
        mmh_strokes.append(mmh_stroke)
    
    # 计算所有点的中心
    all_points = [p for stroke in mmh_strokes for p in stroke]
    if not all_points:
        return []
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    
    offset_x = 512 - center_x
    offset_y = 388 - center_y
    
    # 居中所有笔画
    centered_strokes = []
    for stroke in mmh_strokes:
        centered = [[int(p[0] + offset_x), int(p[1] + offset_y)] for p in stroke]
        centered_strokes.append(centered)
    
    return centered_strokes


def main():
    print(f"\n📁 使用字体: {FONT_PATH}")
    print("🎯 重点修复: a b d e g o p q (有圆圈的字母)")
    
    # 需要修复的字母（特别是有多个部分的）
    problem_chars = [
        'a', 'b', 'd', 'e', 'g', 'o', 'p', 'q',  # 有圆圈
        'i', 'j',  # 有点
    ]
    
    # 也重新提取所有小写字母
    all_lowercase = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    
    print(f"\n🎨 重新提取小写字母")
    print("-" * 70)
    
    data = {}
    success = 0
    
    for char in all_lowercase:
        try:
            img = render_char(char, size=512)
            img_array = np.array(img)
            
            # 提取多个笔画
            strokes = extract_multiple_strokes(img_array)
            
            if not strokes:
                print(f"  ⚠️  {char}: 提取失败")
                continue
            
            # 简化每个笔画
            simplified_strokes = [simplify_stroke(s, max_points=20) for s in strokes]
            
            # 转换坐标
            mmh_strokes = to_mmh_coords(simplified_strokes, 512)
            
            if not mmh_strokes:
                print(f"  ⚠️  {char}: 坐标转换失败")
                continue
            
            # 计算总点数
            total_points = sum(len(s) for s in mmh_strokes)
            
            data[char] = {
                "character": char,
                "medians": mmh_strokes,
                "strokes": len(mmh_strokes),
                "type": "lowercase",
                "source": "source_sans_pro_multi_stroke",
                "license": "OFL",
                "coordinate_system": "MMH"
            }
            
            success += 1
            
            # 特别标注问题字符
            marker = "🔧" if char in problem_chars else "✅"
            print(f"  {marker} {char}: {len(mmh_strokes)}笔画, {total_points}点")
            
        except Exception as e:
            print(f"  ❌ {char}: {e}")
    
    print(f"\n✅ 成功: {success}/{len(all_lowercase)}")
    
    # 加载现有数据（大写和数字）
    print("\n📦 合并数据")
    print("-" * 70)
    
    try:
        with open('data/alphanumeric_medians_improved.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        # 保留大写和数字
        for char, char_data in existing.items():
            if char.isupper() or char.isdigit():
                data[char] = char_data
        
        print(f"✅ 合并了 {len(existing)} 个现有字符")
    except:
        print("⚠️  没有找到现有数据，只保存小写字母")
    
    # 保存
    print("\n💾 保存数据")
    print("-" * 70)
    
    output = 'data/alphanumeric_medians_fixed.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(output)
    print(f"✅ 已保存: {output}")
    print(f"📦 大小: {size/1024:.2f} KB")
    print(f"📊 总字符: {len(data)}个")
    
    # 显示字母a的详情
    if 'a' in data:
        print(f"\n📝 字母a的详情:")
        print(f"  笔画数: {data['a']['strokes']}")
        for i, stroke in enumerate(data['a']['medians'], 1):
            print(f"  笔画{i}: {len(stroke)}个点")
    
    print("\n" + "=" * 70)
    print("✅ 修复完成！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 测试: python test_fixed_render.py")
    print("  2. 如果满意，替换:")
    print("     copy data\\alphanumeric_medians_fixed.json data\\alphanumeric_medians.json")
    print("  3. 重启服务器")
    
    return 0


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  已取消")
        sys.exit(1)

