"""
D2生成API路由

提供统一的D2生成Web接口，集成完整的D2生成封装功能。
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any

# 导入D2生成器
from src.d2_generator import D2Generator
from web.services.grid_state import save_grid_state, load_grid_state

# 创建蓝图
d2_api = Blueprint('d2_api', __name__)
logger = logging.getLogger(__name__)


@d2_api.route('/api/d2/generate', methods=['POST'])
def generate_d2_api():
    """
    D2生成API接口
    
    POST /api/d2/generate
    {
        "char": "的",
        "grid_state": {
            "size": 3,
            "controlPoints": [...],
            "hasDeformation": true
        }
    }
    
    Returns:
    {
        "success": true,
        "filepath": "output/compare/C_processed_centerline/的_20240822_142000_d2.svg",
        "filename": "的_20240822_142000_d2.svg",
        "has_deformation": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        char = data.get('char')
        if not char:
            return jsonify({
                'success': False,
                'error': '缺少字符参数'
            }), 400
        
        # 获取网格状态
        grid_state = data.get('grid_state')
        
        # 如果提供了网格状态，保存到状态管理器
        if grid_state:
            save_grid_state(grid_state)
            logger.info(f"保存网格状态: {grid_state.get('hasDeformation', False)}")
        
        # 创建D2生成器并生成D2
        generator = D2Generator()
        result = generator.generate_d2(char, grid_state)
        
        if result['success']:
            logger.info(f"D2生成成功: {result['filename']}")
            return jsonify(result)
        else:
            logger.error(f"D2生成失败: {result['error']}")
            return jsonify(result), 500
            
    except Exception as e:
        error_msg = f"D2生成API异常: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@d2_api.route('/api/d2/generate/<char>', methods=['GET'])
def generate_d2_simple(char: str):
    """
    简化的D2生成接口（GET方式）
    
    GET /api/d2/generate/的
    
    自动读取保存的网格状态生成D2
    """
    try:
        # 读取保存的网格状态
        grid_state = load_grid_state()
        
        # 创建D2生成器并生成D2
        generator = D2Generator()
        result = generator.generate_d2(char, grid_state)
        
        if result['success']:
            logger.info(f"D2生成成功: {result['filename']}")
            return jsonify(result)
        else:
            logger.error(f"D2生成失败: {result['error']}")
            return jsonify(result), 500
            
    except Exception as e:
        error_msg = f"D2生成API异常: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@d2_api.route('/api/d2/status', methods=['GET'])
def get_d2_status():
    """
    获取D2生成状态信息
    
    GET /api/d2/status
    
    Returns:
    {
        "has_grid_state": true,
        "has_deformation": true,
        "grid_size": 3,
        "last_updated": "2024-08-22T14:20:00"
    }
    """
    try:
        grid_state = load_grid_state()
        
        if grid_state:
            return jsonify({
                'has_grid_state': True,
                'has_deformation': grid_state.get('hasDeformation', False),
                'grid_size': grid_state.get('size', 3),
                'last_updated': grid_state.get('timestamp')
            })
        else:
            return jsonify({
                'has_grid_state': False,
                'has_deformation': False,
                'grid_size': 3,
                'last_updated': None
            })
            
    except Exception as e:
        error_msg = f"获取D2状态异常: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
