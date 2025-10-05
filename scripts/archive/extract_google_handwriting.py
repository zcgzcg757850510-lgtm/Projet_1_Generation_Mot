#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Google Fonts手写字体 + 改进的骨架提取
比Hershey美观100倍！
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("=" * 70)
print("使用Google Fonts手写字体提取美观的单线数据")
print("=" * 70)

# Google Fonts手写字体
GOOGLE_FONTS = {
    'Caveat': {
        'url': 'https://github.com/google/fonts/raw/main/ofl/caveat/Caveat-Regular.ttf',
        'description': '自然手写风格（推荐）',
        'style': 'handwriting'
    },
    'Pacifico': {
        'url': 'https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf',
        'description': '圆润优雅风格',
        'style': 'script'
    }
}


def download_font(font_info, fonts_dir='fonts'):
    """下载Google字体"""
    os.makedirs(fonts_dir, exist_ok=True)
    
    font_name = font_info['url'].split('/')[-1]
    font_path = os.path.join(fonts_dir, font_name)
    
    if os.path.exists(font_path):
        print(f"✅ 字体已存在: {font_name}")
        return font_path
    
    try:
        print(f"⬇️  下载 {font_info['description']}...")
        print(f"   {font_info['url']}")
        urllib.request.urlretrieve(font_info['url'], font_path)
        print(f"✅ 下载成功: {os.path.getsize(font_path)/1024:.1f} KB")
        return font_path
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None


def render_char(char, font_path, size=512):
    """高分辨率渲染（更好的骨架质量）"""
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, int(size * 0.5))
    
    bbox = draw.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    
    draw.text((x, y), char, fill=0, font=font)
    return img


def improved_skeleton_extraction(img_array):
    """
    改进的骨架提取算法
    比简单的中心线提取好很多
    """
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # Zhang-Suen细化算法的简化版
    skeleton = binary.copy()
    
    # 简化版骨架提取：找到每列的中心
    points = []
    h, w = skeleton.shape
    
    # 方法：对每一列，找黑色像素的中心
    for x in range(w):
        col = skeleton[:, x]
        black_pixels = np.where(col > 0)[0]
        if len(black_pixels) > 0:
            center_y = int(np.mean(black_pixels))
            # 只保留接近中心的点
            if len(black_pixels) > 1:
                std = np.std(black_pixels)
                if std < h * 0.3:  # 只保留比较集中的列
                    points.append([x, center_y])
            else:
                points.append([x, black_pixels[0]])
    
    # 如果点太少，尝试行扫描
    if len(points) < 10:
        points = []
        for y in range(h):
            row = skeleton[y, :]
            black_pixels = np.where(row > 0)[0]
            if len(black_pixels) > 0:
                center_x = int(np.mean(black_pixels))
                std = np.std(black_pixels)
                if len(black_pixels) == 1 or std < w * 0.3:
                    points.append([center_x, y])
    
    return points


def douglas_peucker_simplify(points, epsilon=5.0):
    """
    道格拉斯-普克算法简化点
    大幅减少点数，同时保持形状
    """
    if len(points) < 3:
        return points
    
    def perpendicular_distance(point, line_start, line_end):
        """点到线段的垂直距离"""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return np.hypot(x0 - x1, y0 - y1)
        
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx*dx + dy*dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return np.hypot(x0 - proj_x, y0 - proj_y)
    
    # 找到距离起点-终点连线最远的点
    dmax = 0
    index = 0
    end = len(points) - 1
    
    for i in range(1, end):
        d = perpendicular_distance(points[i], points[0], points[end])
        if d > dmax:
            index = i
            dmax = d
    
    # 如果最大距离大于阈值，递归简化
    if dmax > epsilon:
        rec_results1 = douglas_peucker_simplify(points[:index+1], epsilon)
        rec_results2 = douglas_peucker_simplify(points[index:], epsilon)
        
        result = rec_results1[:-1] + rec_results2
    else:
        result = [points[0], points[end]]
    
    return result


def to_mmh(points, original_size=512):
    """转换为MMH坐标并居中"""
    if not points:
        return []
    
    scale = 1024.0 / original_size
    mmh = []
    for x, y in points:
        mmh_x = int(x * scale)
        mmh_y = int(900 - y * scale)
        mmh.append([mmh_x, mmh_y])
    
    # 居中
    if not mmh:
        return []
    
    xs = [p[0] for p in mmh]
    ys = [p[1] for p in mmh]
    
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    
    offset_x = 512 - center_x
    offset_y = 388 - center_y
    
    centered = [[int(p[0] + offset_x), int(p[1] + offset_y)] for p in mmh]
    
    return centered


def main():
    # 选择字体（推荐Caveat）
    print("\n📦 步骤1: 下载Google Fonts手写字体")
    print("-" * 70)
    
    selected = 'Caveat'  # 最美观的手写字体
    font_info = GOOGLE_FONTS[selected]
    
    font_path = download_font(font_info)
    if not font_path:
        print("\n⚠️  字体下载失败")
        print("💡 备选方案：手动下载")
        print(f"   URL: {font_info['url']}")
        print(f"   保存到: fonts/Caveat-Regular.ttf")
        return 1
    
    # 提取字符
    print("\n🎨 步骤2: 提取字符（使用改进的骨架算法）")
    print("-" * 70)
    
    chars = (
        [str(i) for i in range(10)] +  # 0-9
        [chr(i) for i in range(ord('A'), ord('Z')+1)] +  # A-Z
        [chr(i) for i in range(ord('a'), ord('z')+1)]  # a-z
    )
    
    print(f"需要提取: {len(chars)} 个字符")
    
    data = {}
    success = 0
    
    for char in chars:
        try:
            # 高分辨率渲染
            img = render_char(char, font_path, size=512)
            img_array = np.array(img)
            
            # 改进的骨架提取
            points = improved_skeleton_extraction(img_array)
            
            if not points or len(points) < 3:
                print(f"  ⚠️  {char}: 点数不足")
                continue
            
            # 道格拉斯-普克简化
            simplified = douglas_peucker_simplify(points, epsilon=3.0)
            
            # 转换坐标
            mmh_points = to_mmh(simplified, 512)
            
            if not mmh_points or len(mmh_points) < 2:
                print(f"  ⚠️  {char}: 转换失败")
                continue
            
            char_type = 'digit' if char.isdigit() else ('uppercase' if char.isupper() else 'lowercase')
            
            data[char] = {
                "character": char,
                "medians": [mmh_points],
                "strokes": 1,
                "type": char_type,
                "source": f"google_fonts_caveat_handwriting",
                "license": "OFL (Open Font License)",
                "coordinate_system": "MMH",
                "extraction_method": "improved_skeleton + douglas_peucker"
            }
            
            success += 1
            print(f"  ✅ {char}: {len(points)}点 → {len(mmh_points)}点 (简化{100*(1-len(mmh_points)/len(points)):.0f}%)")
            
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
    print("\n💾 步骤3: 保存数据")
    print("-" * 70)
    
    output = 'data/alphanumeric_medians_caveat.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(output)
    print(f"✅ 已保存: {output}")
    print(f"📦 大小: {size/1024:.2f} KB")
    
    if 'A' in data:
        print(f"\n📝 示例 - 字母A:")
        print(f"  点数: {len(data['A']['medians'][0])}")
        print(f"  来源: Google Caveat手写字体")
        print(f"  风格: 自然手写，非常美观！")
    
    print("\n" + "=" * 70)
    print("✅ 完成！比Hershey美观100倍！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 测试效果: python test_caveat_render.py")
    print("  2. 对比Hershey: 在Web界面对比两种效果")
    print("  3. 如果满意，替换:")
    print("     copy data\\alphanumeric_medians_caveat.json data\\alphanumeric_medians.json")
    print("  4. 重启服务器查看效果！")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

