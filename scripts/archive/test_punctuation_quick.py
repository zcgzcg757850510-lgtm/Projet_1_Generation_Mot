#!/usr/bin/env python3
"""快速测试标点符号系统（不需要交互）"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json

def quick_test():
    print("=" * 70)
    print("标点符号快速测试")
    print("=" * 70)
    
    # 测试1: 文件
    filepath = 'data/punctuation_medians.json'
    print(f"\n[1] 文件检查: {filepath}")
    if not os.path.exists(filepath):
        print("  ❌ 文件不存在")
        return False
    
    file_size = os.path.getsize(filepath)
    print(f"  ✅ 文件存在 ({file_size / 1024:.2f} KB)")
    
    # 测试2: 加载数据
    print(f"\n[2] 加载数据")
    try:
        from src.punctuation_loader import load_punctuation_data
        data = load_punctuation_data()
        print(f"  ✅ 加载成功: {len(data)} 个标点符号")
        print(f"  标点: {''.join(sorted(data.keys()))}")
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return False
    
    # 测试3: 数据源
    print(f"\n[3] 数据来源检查")
    sources = {}
    for char, char_data in data.items():
        source = char_data.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    for source, count in sorted(sources.items()):
        print(f"  {source}: {count} 个")
    
    # 测试4: 质量检查
    print(f"\n[4] 质量检查")
    issues = []
    for char, char_data in data.items():
        # 检查尺寸
        all_points = []
        for stroke in char_data.get('medians', []):
            all_points.extend(stroke)
        
        if all_points:
            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            
            if width < 5 or height < 5:
                issues.append(f"{char}: 尺寸过小 ({width}x{height})")
    
    if issues:
        print(f"  ⚠️ 发现 {len(issues)} 个问题:")
        for issue in issues[:10]:
            print(f"    - {issue}")
    else:
        print("  ✅ 所有标点符号质量合格")
    
    # 测试5: 系统集成
    print(f"\n[5] 系统集成测试")
    try:
        from web.services.generation import load_merged_cache, clear_merged_cache
        clear_merged_cache()
        cache = load_merged_cache()
        
        test_chars = ['，', '。', '！', '？']
        found = [c for c in test_chars if c in cache]
        
        print(f"  ✅ {len(found)}/{len(test_chars)} 个标点在缓存中")
        print(f"  总字符数: {len(cache)}")
    except Exception as e:
        print(f"  ❌ 集成失败: {e}")
    
    print("\n" + "=" * 70)
    if issues:
        print(f"测试完成 (有 {len(issues)} 个质量警告)")
    else:
        print("测试完成 ✅ 一切正常")
    print("=" * 70)
    
    return len(issues) == 0

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)

