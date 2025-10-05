"""
API路由模块

提供基础的API路由功能
"""

from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return {'status': 'ok', 'message': 'API is running'}
