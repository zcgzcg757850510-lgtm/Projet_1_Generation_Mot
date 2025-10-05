#!/usr/bin/env python3
"""
从图像渲染提取标点符号骨架
使用PIL渲染文字，然后提取骨架线
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def find_system_font():
    """查找系统字体"""
    import platform
    system = platform.system()
    
    if system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
        ]
    elif system == 'Darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Songti.ttc',
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
    
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def render_char_to_image(char, font_path, size=200):
    """渲染字符到图像"""
    try:
        # 创建图像
        img = Image.new('L', (size, size), color=255)  # 白色背景
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        try:
            font = ImageFont.truetype(font_path, size - 40, index=0)
        except:
            font = ImageFont.truetype(font_path, size - 40)
        
        # 获取文字边界
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 居中绘制
        x = (size - text_width) // 2 - bbox[0]
        y = (size - text_height) // 2 - bbox[1]
        
        draw.text((x, y), char, fill=0, font=font)  # 黑色文字
        
        return img
    except Exception as e:
        print(f"  [ERROR] 渲染失败 {char}: {e}")
        return None


def simple_skeleton(img_array):
    """
    简化的骨架提取
    使用形态学细化（thinning）的简化版本
    """
    # 二值化
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 找到所有黑色像素的质心路径（简化方法）
    # 这里使用一个更简单的策略：提取轮廓的中心线
    
    # 方法：分层扫描，找到每行/列的中点
    points = []
    
    # 垂直扫描
    for y in range(binary.shape[0]):
        row = binary[y, :]
        if row.any():
            black_pixels = np.where(row > 0)[0]
            if len(black_pixels) > 0:
                center_x = int(np.mean(black_pixels))
                points.append([center_x, y])
    
    # 去重并排序
    if len(points) > 2:
        # 简化点：每隔几个点取一个
        step = max(1, len(points) // 15)
        points = [points[i] for i in range(0, len(points), step)]
    
    return [points] if points else []


def extract_strokes_from_image(char, font_path):
    """从图像提取笔画"""
    img = render_char_to_image(char, font_path, size=256)
    if img is None:
        return None
    
    # 转为numpy数组
    img_array = np.array(img)
    
    # 提取骨架
    strokes = simple_skeleton(img_array)
    
    if not strokes or not strokes[0]:
        return None
    
    return strokes


def adjust_punctuation_position(strokes, char):
    """调整标点符号到标准位置"""
    if not strokes or not strokes[0]:
        return strokes
    
    # 计算边界
    all_points = []
    for stroke in strokes:
        all_points.extend(stroke)
    
    if not all_points:
        return strokes
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return strokes
    
    # 目标位置
    if char in ['，', '。', '、']:
        target_x, target_y, target_size = 220, 220, 20
    elif char in ['！', '？']:
        target_x, target_y, target_size = 128, 140, 80
    elif char in ['；', '：']:
        target_x, target_y, target_size = 220, 150, 40
    elif char in ['"', '"', ''', ''']:
        target_x, target_y, target_size = 110, 90, 30
    elif char in ['（', '）', '《', '》', '【', '】']:
        target_x, target_y, target_size = 128, 128, 80
    else:
        target_x, target_y, target_size = 128, 128, 60
    
    # 当前中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 缩放
    scale = target_size / max(width, height)
    
    # 变换
    adjusted_strokes = []
    for stroke in strokes:
        adjusted_stroke = []
        for x, y in stroke:
            x = (x - center_x) * scale + target_x
            y = (y - center_y) * scale + target_y
            adjusted_stroke.append([int(x), int(y)])
        adjusted_strokes.append(adjusted_stroke)
    
    return adjusted_strokes


def main():
    print("=" * 60)
    print("从图像渲染提取标点符号")
    print("=" * 60)
    
    font_path = find_system_font()
    if not font_path:
        print("[ERROR] 未找到字体")
        return 1
    
    print(f"[OK] 使用字体: {font_path}")
    
    punctuation_list = [
        '，', '。', '、', '；', '：',
        '！', '？',
        '"', '"', ''', ''',
        '（', '）', '《', '》', '【', '】',
        '…', '——',
    ]
    
    results = {}
    print("\n开始提取...")
    print("-" * 60)
    
    for char in punctuation_list:
        try:
            strokes = extract_strokes_from_image(char, font_path)
            if not strokes:
                print(f"  [X] {char:2s} - 提取失败")
                continue
            
            # 调整位置
            adjusted = adjust_punctuation_position(strokes, char)
            
            # 过滤太短的笔画
            valid = [s for s in adjusted if len(s) >= 2]
            
            if not valid:
                print(f"  [X] {char:2s} - 笔画太短")
                continue
            
            results[char] = {
                "character": char,
                "medians": valid,
                "strokes": len(valid),
                "source": "image_skeleton"
            }
            
            points = sum(len(s) for s in valid)
            print(f"  [OK] {char:2s} - {len(valid)} strokes, {points} points")
            
        except Exception as e:
            print(f"  [X] {char:2s} - ERROR: {e}")
    
    print("-" * 60)
    print(f"\n[RESULT] 成功提取 {len(results)}/{len(punctuation_list)} 个标点")
    
    if results:
        output_path = 'data/punctuation_medians.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_path)
        print(f"[FILE] {output_path}")
        print(f"[SIZE] {file_size / 1024:.1f} KB")
        print("\n" + "=" * 60)
        print("请重启服务器以加载新数据：python start_server.py")
        print("=" * 60)
        return 0
    else:
        print("[ERROR] 没有成功提取任何标点")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

