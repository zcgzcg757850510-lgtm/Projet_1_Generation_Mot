#!/usr/bin/env python3
"""
标点符号系统测试工具
全面测试标点符号的加载、集成和生成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from typing import Dict, Any


def test_file_existence():
    """测试1: 检查文件是否存在"""
    print("=" * 70)
    print("[测试1] 检查标点符号数据文件")
    print("-" * 70)
    
    filepath = 'data/punctuation_medians.json'
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    
    file_size = os.path.getsize(filepath)
    print(f"✅ 文件存在: {filepath}")
    print(f"   大小: {file_size / 1024:.2f} KB")
    return True


def test_data_loading():
    """测试2: 测试数据加载"""
    print("\n" + "=" * 70)
    print("[测试2] 测试标点符号加载")
    print("-" * 70)
    
    try:
        from src.punctuation_loader import load_punctuation_data
        data = load_punctuation_data()
        
        if not data:
            print("❌ 加载的数据为空")
            return False, None
        
        print(f"✅ 成功加载 {len(data)} 个标点符号")
        print(f"   标点列表: {''.join(data.keys())}")
        
        return True, data
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_data_format(data: Dict[str, Any]):
    """测试3: 验证数据格式"""
    print("\n" + "=" * 70)
    print("[测试3] 验证数据格式")
    print("-" * 70)
    
    if not data:
        print("❌ 没有数据可验证")
        return False
    
    issues = []
    
    for char, char_data in data.items():
        # 检查必需字段
        required_fields = ['character', 'medians', 'strokes', 'source']
        for field in required_fields:
            if field not in char_data:
                issues.append(f"{char}: 缺少字段 '{field}'")
        
        # 检查 medians 格式
        if 'medians' in char_data:
            medians = char_data['medians']
            if not isinstance(medians, list):
                issues.append(f"{char}: medians 不是列表")
            else:
                for stroke_idx, stroke in enumerate(medians):
                    if not isinstance(stroke, list):
                        issues.append(f"{char}: 笔画 {stroke_idx} 不是列表")
                    else:
                        for point_idx, point in enumerate(stroke):
                            if not isinstance(point, list) or len(point) != 2:
                                issues.append(f"{char}: 笔画 {stroke_idx} 点 {point_idx} 格式错误")
                            else:
                                x, y = point
                                if not (0 <= x <= 256) or not (0 <= y <= 256):
                                    issues.append(f"{char}: 坐标越界 ({x}, {y})")
    
    if issues:
        print(f"⚠️ 发现 {len(issues)} 个问题:")
        for issue in issues[:5]:
            print(f"   - {issue}")
        if len(issues) > 5:
            print(f"   ... 还有 {len(issues) - 5} 个问题")
        return False
    
    print("✅ 所有标点符号格式正确")
    return True


def test_system_integration():
    """测试4: 测试系统集成"""
    print("\n" + "=" * 70)
    print("[测试4] 测试系统集成")
    print("-" * 70)
    
    try:
        from web.services.generation import load_merged_cache
        
        # 清除缓存以确保重新加载
        from web.services.generation import clear_merged_cache
        clear_merged_cache()
        
        cache = load_merged_cache()
        
        # 检查常用标点是否在缓存中
        test_punctuation = ['，', '。', '！', '？', '：', '；']
        found = []
        missing = []
        
        for punct in test_punctuation:
            if punct in cache:
                found.append(punct)
            else:
                missing.append(punct)
        
        print(f"✅ 找到 {len(found)}/{len(test_punctuation)} 个标点符号")
        print(f"   已加载: {''.join(found)}")
        
        if missing:
            print(f"   ⚠️ 缺失: {''.join(missing)}")
        
        print(f"   总字符数: {len(cache)}")
        
        return len(found) == len(test_punctuation)
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_character_generation():
    """测试5: 测试单个字符生成"""
    print("\n" + "=" * 70)
    print("[测试5] 测试标点符号生成")
    print("-" * 70)
    
    test_chars = ['，', '。', '！']
    success_count = 0
    
    try:
        from web.services.generation import generate_abcd
        
        for char in test_chars:
            try:
                print(f"\n测试生成: {char}")
                result = generate_abcd(char, style_override_path=None)
                
                if result and any(result.values()):
                    print(f"  ✅ 生成成功")
                    print(f"     - D1: {'✓' if result.get('D1') else '✗'}")
                    print(f"     - D2: {'✓' if result.get('D2') else '✗'}")
                    success_count += 1
                else:
                    print(f"  ❌ 生成失败: 结果为空")
            
            except Exception as e:
                print(f"  ❌ 生成失败: {e}")
        
        print(f"\n✅ 成功生成 {success_count}/{len(test_chars)} 个标点符号")
        return success_count == len(test_chars)
        
    except Exception as e:
        print(f"❌ 生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_statistics(data: Dict[str, Any]):
    """测试6: 数据统计"""
    print("\n" + "=" * 70)
    print("[测试6] 标点符号统计")
    print("-" * 70)
    
    if not data:
        print("❌ 没有数据")
        return
    
    print(f"\n{'标点':<6} {'笔画':<6} {'点数':<8} {'来源':<20}")
    print("-" * 70)
    
    total_strokes = 0
    total_points = 0
    
    for char in sorted(data.keys()):
        char_data = data[char]
        strokes = char_data.get('strokes', 0)
        points = sum(len(stroke) for stroke in char_data.get('medians', []))
        source = char_data.get('source', 'unknown')
        
        print(f"{char:<6} {strokes:<6} {points:<8} {source:<20}")
        
        total_strokes += strokes
        total_points += points
    
    print("-" * 70)
    print(f"总计:  {total_strokes:<6} {total_points:<8}")
    print(f"平均:  {total_strokes/len(data):.1f}  {total_points/len(data):.1f}")


def test_quality_check(data: Dict[str, Any]):
    """测试7: 质量检查"""
    print("\n" + "=" * 70)
    print("[测试7] 标点符号质量检查")
    print("-" * 70)
    
    if not data:
        print("❌ 没有数据")
        return False
    
    warnings = []
    
    for char, char_data in data.items():
        medians = char_data.get('medians', [])
        
        # 检查点数是否过少
        for stroke_idx, stroke in enumerate(medians):
            if len(stroke) < 2:
                warnings.append(f"{char}: 笔画 {stroke_idx} 点数过少 ({len(stroke)})")
            elif len(stroke) > 100:
                warnings.append(f"{char}: 笔画 {stroke_idx} 点数过多 ({len(stroke)})")
        
        # 检查坐标分布
        all_points = []
        for stroke in medians:
            all_points.extend(stroke)
        
        if all_points:
            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            width = max_x - min_x
            height = max_y - min_y
            
            # 检查是否太小
            if width < 5 or height < 5:
                warnings.append(f"{char}: 尺寸过小 ({width}x{height})")
    
    if warnings:
        print(f"⚠️ 发现 {len(warnings)} 个质量警告:")
        for warning in warnings[:10]:
            print(f"   - {warning}")
        if len(warnings) > 10:
            print(f"   ... 还有 {len(warnings) - 10} 个警告")
        return False
    else:
        print("✅ 质量检查通过!")
        return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🔍" * 35)
    print("标点符号系统测试")
    print("🔍" * 35 + "\n")
    
    results = {}
    
    # 测试1: 文件存在
    results['file_existence'] = test_file_existence()
    
    if not results['file_existence']:
        print("\n" + "❌" * 35)
        print("关键测试失败: 文件不存在")
        print("请先生成标点符号数据文件")
        print("运行: python scripts/improved_punctuation_manual.py")
        print("❌" * 35)
        return False
    
    # 测试2: 数据加载
    success, data = test_data_loading()
    results['data_loading'] = success
    
    if not success:
        print("\n" + "❌" * 35)
        print("关键测试失败: 数据加载失败")
        print("❌" * 35)
        return False
    
    # 测试3: 数据格式
    results['data_format'] = test_data_format(data)
    
    # 测试4: 系统集成
    results['system_integration'] = test_system_integration()
    
    # 测试5: 字符生成（可选，比较慢）
    print("\n是否运行字符生成测试? (较慢) [y/N]: ", end='')
    try:
        response = input().strip().lower()
        if response == 'y':
            results['character_generation'] = test_character_generation()
        else:
            print("跳过字符生成测试")
            results['character_generation'] = None
    except:
        print("\n跳过字符生成测试")
        results['character_generation'] = None
    
    # 测试6: 数据统计
    test_data_statistics(data)
    
    # 测试7: 质量检查
    results['quality_check'] = test_quality_check(data)
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    for test_name, result in results.items():
        if result is None:
            status = "⏭️  跳过"
        elif result:
            status = "✅ 通过"
        else:
            status = "❌ 失败"
        
        print(f"{status}  {test_name.replace('_', ' ').title()}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print("-" * 70)
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    return all(r in [True, None] for r in results.values())


def main():
    try:
        success = run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

