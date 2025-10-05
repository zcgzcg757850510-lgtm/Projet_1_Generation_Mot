#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复小写字母提取问题（简化版，无需scipy）
使用轮廓追踪来提取多个笔画
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("=" * 70)
print("修复小写字母提取（多笔画支持）")
print("=" * 70)

FONT_PATH = 'fonts/SourceSansPro-Regular.ttf'


def render_char(char, size=512):
    """渲染字符"""
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


def find_connected_components(binary):
    """
    简单的连通域查找（不用scipy）
    使用flood fill算法
    """
    h, w = binary.shape
    visited = np.zeros_like(binary, dtype=bool)
    components = []
    
    def flood_fill(start_y, start_x):
        """从一个点开始flood fill"""
        component = []
        stack = [(start_y, start_x)]
        
        while stack:
            y, x = stack.pop()
            
            if y < 0 or y >= h or x < 0 or x >= w:
                continue
            if visited[y, x] or binary[y, x] == 0:
                continue
            
            visited[y, x] = True
            component.append((y, x))
            
            # 8-连通
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    stack.append((y + dy, x + dx))
        
        return component
    
    # 查找所有连通域
    for y in range(h):
        for x in range(w):
            if binary[y, x] > 0 and not visited[y, x]:
                component = flood_fill(y, x)
                if len(component) > 10:  # 至少10个像素
                    components.append(component)
    
    return components


def extract_centerline_from_points(points):
    """从像素点集提取中心线"""
    if not points:
        return []
    
    # 将(y,x)转为(x,y)
    points_xy = [(x, y) for y, x in points]
    
    # 按X坐标排序
    points_xy.sort(key=lambda p: p[0])
    
    # 每隔几个像素采样一个点
    centerline = []
    x_min = min(p[0] for p in points_xy)
    x_max = max(p[0] for p in points_xy)
    
    # 对每个X坐标，找Y坐标的中心
    for x in range(x_min, x_max + 1, 4):  # 每隔4像素
        ys = [p[1] for p in points_xy if abs(p[0] - x) <= 2]
        if ys:
            center_y = int(np.mean(ys))
            centerline.append([x, center_y])
    
    # 如果点太少，尝试按Y坐标
    if len(centerline) < 5:
        points_xy.sort(key=lambda p: p[1])
        centerline = []
        y_min = min(p[1] for p in points_xy)
        y_max = max(p[1] for p in points_xy)
        
        for y in range(y_min, y_max + 1, 4):
            xs = [p[0] for p in points_xy if abs(p[1] - y) <= 2]
            if xs:
                center_x = int(np.mean(xs))
                centerline.append([center_x, y])
    
    return centerline


def simplify_points(points, max_points=20):
    """简化点数"""
    if len(points) <= max_points:
        return points
    
    step = len(points) / max_points
    simplified = []
    
    for i in range(max_points):
        index = int(i * step)
        if index < len(points):
            simplified.append(points[index])
    
    if simplified and simplified[-1] != points[-1]:
        simplified.append(points[-1])
    
    return simplified


def to_mmh_coords(strokes, original_size=512):
    """转换为MMH坐标"""
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
    
    # 居中
    all_points = [p for stroke in mmh_strokes for p in stroke]
    if not all_points:
        return []
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    
    offset_x = 512 - center_x
    offset_y = 388 - center_y
    
    centered_strokes = []
    for stroke in mmh_strokes:
        centered = [[int(p[0] + offset_x), int(p[1] + offset_y)] for p in stroke]
        centered_strokes.append(centered)
    
    return centered_strokes


def main():
    print(f"\n📁 字体: {FONT_PATH}")
    print("🎯 修复有圆圈的字母: a b d e g o p q")
    
    # 所有小写字母
    lowercase = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    
    print(f"\n🎨 重新提取小写字母（支持多笔画）")
    print("-" * 70)
    
    data = {}
    success = 0
    problem_chars = ['a', 'b', 'd', 'e', 'g', 'o', 'p', 'q', 'i', 'j']
    
    for char in lowercase:
        try:
            img = render_char(char, size=512)
            img_array = np.array(img)
            binary = (img_array < 128).astype(np.uint8)
            
            if not binary.any():
                print(f"  ⚠️  {char}: 无像素")
                continue
            
            # 查找连通域
            components = find_connected_components(binary)
            
            if not components:
                print(f"  ⚠️  {char}: 无连通域")
                continue
            
            # 按大小排序（大的优先）
            components.sort(key=len, reverse=True)
            
            # 提取每个连通域的中心线
            strokes = []
            for component in components[:3]:  # 最多3个笔画
                centerline = extract_centerline_from_points(component)
                if centerline and len(centerline) >= 2:
                    simplified = simplify_points(centerline, max_points=20)
                    strokes.append(simplified)
            
            if not strokes:
                print(f"  ⚠️  {char}: 无笔画")
                continue
            
            # 转换坐标
            mmh_strokes = to_mmh_coords(strokes, 512)
            
            if not mmh_strokes:
                print(f"  ⚠️  {char}: 坐标失败")
                continue
            
            total_points = sum(len(s) for s in mmh_strokes)
            
            data[char] = {
                "character": char,
                "medians": mmh_strokes,
                "strokes": len(mmh_strokes),
                "type": "lowercase",
                "source": "source_sans_pro_multi_stroke_v2",
                "license": "OFL",
                "coordinate_system": "MMH"
            }
            
            success += 1
            marker = "🔧" if char in problem_chars else "✅"
            print(f"  {marker} {char}: {len(mmh_strokes)}笔画, {total_points}点")
            
        except Exception as e:
            print(f"  ❌ {char}: {e}")
    
    print(f"\n✅ 成功: {success}/{len(lowercase)}")
    
    # 合并大写和数字
    print("\n📦 合并大写和数字")
    print("-" * 70)
    
    try:
        with open('data/alphanumeric_medians_improved.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        for char, char_data in existing.items():
            if char.isupper() or char.isdigit():
                data[char] = char_data
        
        print(f"✅ 合并了大写和数字")
    except:
        print("⚠️  未找到现有数据")
    
    # 保存
    print("\n💾 保存")
    print("-" * 70)
    
    output = 'data/alphanumeric_medians_fixed.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存: {output}")
    print(f"📦 大小: {os.path.getsize(output)/1024:.2f} KB")
    print(f"📊 总字符: {len(data)}个")
    
    if 'a' in data:
        print(f"\n📝 字母a:")
        print(f"  笔画: {data['a']['strokes']}个")
        for i, s in enumerate(data['a']['medians'], 1):
            print(f"  笔画{i}: {len(s)}点")
    
    print("\n" + "=" * 70)
    print("✅ 完成！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  copy data\\alphanumeric_medians_fixed.json data\\alphanumeric_medians.json")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

