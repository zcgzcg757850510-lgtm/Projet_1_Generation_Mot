#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看所有可用的字体数字方案
"""

import json
import os
from pathlib import Path

def check_digit_file(file_path):
    """检查数字文件的内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否包含0-9
        digits = [str(i) for i in range(10)]
        available_digits = [d for d in digits if d in data]
        
        # 获取第一个数字的信息
        sample_info = {}
        if available_digits:
            sample_digit = available_digits[0]
            sample = data[sample_digit]
            sample_info = {
                'source': sample.get('source', 'unknown'),
                'strokes': sample.get('strokes', 0),
                'coordinate_system': sample.get('coordinate_system', 'unknown'),
                'license': sample.get('license', 'unknown')
            }
        
        return {
            'available': True,
            'total_digits': len(available_digits),
            'missing_digits': [d for d in digits if d not in data],
            'sample_info': sample_info,
            'file_size': os.path.getsize(file_path)
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("所有可用的字体数字方案")
    print("=" * 80)
    
    # 搜索所有数字文件
    data_dir = Path('data')
    digit_files = sorted(data_dir.glob('digits*.json'))
    
    print(f"\n找到 {len(digit_files)} 个数字数据文件\n")
    
    available_options = []
    
    for file_path in digit_files:
        filename = file_path.name
        print(f"{'='*80}")
        print(f"📄 {filename}")
        print(f"{'='*80}")
        
        info = check_digit_file(file_path)
        
        if info['available']:
            print(f"✅ 可用")
            print(f"  数字数量: {info['total_digits']}/10")
            
            if info['missing_digits']:
                print(f"  ⚠️  缺失数字: {', '.join(info['missing_digits'])}")
            
            sample = info['sample_info']
            print(f"  来源: {sample.get('source', 'unknown')}")
            print(f"  坐标系统: {sample.get('coordinate_system', 'unknown')}")
            print(f"  许可证: {sample.get('license', 'unknown')}")
            print(f"  文件大小: {info['file_size']:,} bytes")
            
            # 判断推荐度
            score = 0
            reasons = []
            
            if info['total_digits'] == 10:
                score += 10
            else:
                reasons.append(f"缺失{10-info['total_digits']}个数字")
            
            # 根据文件名判断
            if 'simple' in filename:
                score += 5
                reasons.append("简单提取版本")
            elif 'auto' in filename:
                score += 3
                reasons.append("自动提取版本")
            elif 'reliable' in filename:
                score += 7
                reasons.append("可靠提取版本")
            elif 'manual' in filename:
                score += 8
                reasons.append("手工优化版本")
            elif 'super_rounded' in filename:
                score += 9
                reasons.append("超级圆润版本")
            
            # 字体名称加分
            if 'comfortaa' in filename.lower():
                score += 2
                font_name = "Comfortaa"
            elif 'varelaround' in filename.lower():
                score += 2
                font_name = "Varela Round"
            elif 'roboto' in filename.lower():
                score += 1
                font_name = "Roboto"
            elif 'sourcesanspro' in filename.lower():
                score += 1
                font_name = "Source Sans Pro"
            else:
                font_name = "未知字体"
            
            print(f"  📊 推荐度: {score}/20")
            print(f"  💭 说明: {', '.join(reasons)}")
            
            available_options.append({
                'filename': filename,
                'filepath': str(file_path),
                'score': score,
                'total_digits': info['total_digits'],
                'font_name': font_name,
                'reasons': reasons,
                'sample_info': sample
            })
        else:
            print(f"❌ 不可用")
            print(f"  错误: {info['error']}")
        
        print()
    
    # 按推荐度排序
    available_options.sort(key=lambda x: x['score'], reverse=True)
    
    # 显示推荐列表
    print("=" * 80)
    print("🏆 推荐方案（按推荐度排序）")
    print("=" * 80)
    
    for i, option in enumerate(available_options[:10], 1):  # 只显示前10个
        print(f"\n{i}. {option['filename']}")
        print(f"   字体: {option['font_name']}")
        print(f"   数字: {option['total_digits']}/10")
        print(f"   推荐度: {option['score']}/20 ⭐" * min(option['score']//4, 5))
        print(f"   特点: {', '.join(option['reasons'])}")
    
    # 生成应用命令
    print("\n" + "=" * 80)
    print("🚀 快速应用命令")
    print("=" * 80)
    
    top_3 = available_options[:3]
    for i, option in enumerate(top_3, 1):
        print(f"\n方案{i}: {option['font_name']}")
        print(f"命令: python merge_rounded_digits.py {option['filepath']}")
    
    print("\n" + "=" * 80)
    print("✅ 分析完成")
    print("=" * 80)
    
    return available_options

if __name__ == '__main__':
    options = main()

