#!/usr/bin/env python3
"""
简化版字体提取器 - 使用更基本的fontTools API
"""

import os
import json
import platform

def find_chinese_font():
    """查找系统中的中文字体"""
    system = platform.system()
    
    candidates = []
    if system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simhei.ttf',
        ]
    elif system == 'Darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"[OK] 找到字体: {path}")
            return path
    
    return None


def extract_glyph_simple(font, char):
    """简化的字形提取"""
    try:
        # 获取字符编码
        cmap = font.getBestCmap()
        if not cmap:
            return None
        
        char_code = ord(char)
        glyph_name = cmap.get(char_code)
        
        if not glyph_name:
            return None
        
        # 获取glyf表（TrueType轮廓）
        if 'glyf' not in font:
            return None
        
        glyf_table = font['glyf']
        glyph = glyf_table[glyph_name]
        
        # 获取坐标
        if not hasattr(glyph, 'coordinates') or glyph.coordinates is None:
            return None
        
        coords = glyph.coordinates
        end_pts = glyph.endPtsOfContours
        
        if not coords or not end_pts:
            return None
        
        # 分离不同的轮廓
        contours = []
        start = 0
        for end in end_pts:
            contour = list(coords[start:end+1])
            if contour:
                contours.append(contour)
            start = end + 1
        
        # 获取字体单位
        units_per_em = font['head'].unitsPerEm
        
        return contours, units_per_em
        
    except Exception as e:
        # print(f"  [DEBUG] {char}: {e}")
        return None


def normalize_contours(contours, units_per_em, char):
    """归一化轮廓到256x256空间"""
    if not contours:
        return []
    
    # 缩放因子
    scale = 256.0 / units_per_em
    
    # 提取所有点并归一化
    normalized_contours = []
    for contour in contours:
        normalized_contour = []
        for x, y in contour:
            # 翻转Y轴并缩放
            x_norm = int(x * scale)
            y_norm = int((units_per_em - y) * scale)
            normalized_contour.append([x_norm, y_norm])
        
        # 简化：只保留关键点
        if len(normalized_contour) > 15:
            # 抽样：保留每隔N个点
            step = len(normalized_contour) // 10
            normalized_contour = [normalized_contour[i] for i in range(0, len(normalized_contour), step)]
        
        if len(normalized_contour) >= 2:
            normalized_contours.append(normalized_contour)
    
    return normalized_contours


def adjust_position(strokes, char):
    """调整标点符号位置"""
    if not strokes:
        return strokes
    
    # 计算边界
    all_points = []
    for stroke in strokes:
        all_points.extend(stroke)
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    # 根据标点类型确定目标位置
    if char in ['，', '。', '、']:
        target_x, target_y, target_size = 220, 220, 25
    elif char in ['！', '？']:
        target_x, target_y, target_size = 128, 140, 90
    elif char in ['；', '：']:
        target_x, target_y, target_size = 220, 150, 50
    elif char in ['"', '"', ''', ''']:
        target_x, target_y, target_size = 110, 90, 35
    elif char in ['（', '）', '《', '》', '【', '】']:
        target_x, target_y, target_size = 128, 128, 90
    else:
        target_x, target_y, target_size = 128, 128, 70
    
    # 计算当前中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 缩放比例
    current_size = max(width, height)
    if current_size == 0:
        return strokes
    
    scale = target_size / current_size
    
    # 应用变换
    adjusted_strokes = []
    for stroke in strokes:
        adjusted_stroke = []
        for x, y in stroke:
            # 移到原点
            x -= center_x
            y -= center_y
            # 缩放
            x *= scale
            y *= scale
            # 移到目标位置
            x += target_x
            y += target_y
            adjusted_stroke.append([int(x), int(y)])
        adjusted_strokes.append(adjusted_stroke)
    
    return adjusted_strokes


def main():
    from fontTools.ttLib import TTFont
    
    print("=" * 60)
    print("简化版标点符号提取器")
    print("=" * 60)
    
    font_path = find_chinese_font()
    if not font_path:
        print("[ERROR] 未找到字体")
        return 1
    
    try:
        font = TTFont(font_path, fontNumber=0)  # TTC文件需要指定字体索引
    except Exception as e:
        print(f"[ERROR] 打开字体失败: {e}")
        return 1
    
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
        result = extract_glyph_simple(font, char)
        if result is None:
            print(f"  [X] {char:2s} - 未找到或无轮廓")
            continue
        
        contours, units_per_em = result
        
        # 归一化
        normalized = normalize_contours(contours, units_per_em, char)
        if not normalized:
            print(f"  [X] {char:2s} - 归一化失败")
            continue
        
        # 调整位置
        adjusted = adjust_position(normalized, char)
        
        results[char] = {
            "character": char,
            "medians": adjusted,
            "strokes": len(adjusted),
            "source": "system_font_simple"
        }
        
        points = sum(len(s) for s in adjusted)
        print(f"  [OK] {char:2s} - {len(adjusted)} strokes, {points} points")
    
    font.close()
    
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

