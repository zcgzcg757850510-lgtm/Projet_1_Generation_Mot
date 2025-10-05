#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从Roboto字体提取骨架 - 保存原始图案和提取骨架
"""

import json
import os
import sys
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("=" * 80)
print("从Roboto字体提取骨架中心线")
print("=" * 80)

# 检查依赖
try:
    from skimage.morphology import skeletonize, thin
    from scipy.ndimage import distance_transform_edt, maximum_filter
    import cv2
    print("✅ 所有依赖库已就绪")
except ImportError as e:
    print(f"❌ 缺少依赖库: {e}")
    sys.exit(1)

FONT_PATH = 'fonts/Roboto-Regular.ttf'
FONT_NAME = 'Roboto'

def render_digit(digit, size=500):
    """渲染数字 - 返回PIL Image对象"""
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, int(size * 0.7))
    except Exception as e:
        print(f"❌ 无法加载字体: {e}")
        return None
    
    bbox = draw.textbbox((0, 0), digit, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    
    draw.text((x, y), digit, fill=0, font=font)
    return img

def image_to_base64(img):
    """将PIL Image转换为base64字符串"""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def extract_skeleton(img_array):
    """提取骨架 - 使用Medial Axis Transform"""
    binary = (img_array < 128).astype(bool)
    if not binary.any():
        return None, None
    
    distance = distance_transform_edt(binary)
    local_max = maximum_filter(distance, size=3)
    skeleton = (distance == local_max) & (distance > 0)
    
    return binary.astype(np.uint8), skeleton.astype(np.uint8)

def skeleton_to_points(skeleton_img):
    """骨架转路径点"""
    coords = np.column_stack(np.where(skeleton_img > 0))
    if len(coords) == 0:
        return []
    
    coords = coords[coords[:, 1].argsort()]
    path = [[int(y), int(x)] for x, y in coords]
    
    if len(path) > 50:
        step = len(path) // 40
        simplified = [path[i] for i in range(0, len(path), step)]
        if path[-1] not in simplified:
            simplified.append(path[-1])
        return simplified
    return path

def to_mmh(points):
    """转MMH坐标"""
    if not points or len(points) < 2:
        return []
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width, height = max_x - min_x, max_y - min_y
    
    if width == 0 or height == 0:
        return []
    
    scale = min(250 / width, 400 / height)
    
    mmh_points = []
    for x, y in points:
        scaled_x = (x - min_x) * scale
        scaled_y = (y - min_y) * scale
        mmh_x = int(scaled_x + 425)
        mmh_y = int(650 - scaled_y)
        mmh_points.append([mmh_x, mmh_y])
    
    return mmh_points

def main():
    if not os.path.exists(FONT_PATH):
        print(f"❌ 字体文件不存在: {FONT_PATH}")
        return
    
    print(f"\n正在处理: {FONT_NAME}")
    print(f"字体文件: {FONT_PATH}\n")
    
    skeleton_data = {}
    images_data = {}
    
    for digit in '0123456789':
        print(f"处理数字 {digit}...", end=' ')
        
        # 渲染原始图像
        img = render_digit(digit, 500)
        if img is None:
            print("❌ 渲染失败")
            continue
        
        # 保存原始图像为base64
        img_base64 = image_to_base64(img)
        images_data[digit] = {
            'character': digit,
            'image': img_base64,
            'type': 'original_render'
        }
        
        # 转换为numpy数组
        img_array = np.array(img)
        
        # 提取骨架
        binary, skeleton = extract_skeleton(img_array)
        if skeleton is None:
            print("❌ 骨架提取失败")
            continue
        
        # 转路径
        skeleton_path = skeleton_to_points(skeleton)
        
        if not skeleton_path:
            print("❌ 路径转换失败")
            continue
        
        # 转MMH
        skeleton_mmh = to_mmh(skeleton_path)
        
        if not skeleton_mmh:
            print("❌ 坐标转换失败")
            continue
        
        # 保存骨架数据
        skeleton_data[digit] = {
            'character': digit,
            'medians': [skeleton_mmh],
            'strokes': 1,
            'type': 'digit',
            'source': 'roboto_skeleton',
            'license': 'Apache License 2.0',
            'coordinate_system': 'MMH'
        }
        
        print(f"✅ (骨架:{len(skeleton_mmh)}点)")
    
    # 保存文件
    os.makedirs('data/font_skeletons', exist_ok=True)
    
    skeleton_file = 'data/font_skeletons/digits_roboto_skeleton.json'
    images_file = 'data/font_skeletons/digits_roboto_images.json'
    
    with open(skeleton_file, 'w', encoding='utf-8') as f:
        json.dump(skeleton_data, f, ensure_ascii=False, indent=2)
    
    with open(images_file, 'w', encoding='utf-8') as f:
        json.dump(images_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("✅ 提取完成！")
    print(f"{'='*80}")
    print(f"\n已保存:")
    print(f"  原始图案: {images_file}")
    print(f"  提取骨架: {skeleton_file}")
    print(f"\n每个文件包含10个数字 (0-9)")

if __name__ == '__main__':
    main()

