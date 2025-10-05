#!/usr/bin/env python3
"""
生产环境服务器启动脚本
Production server startup script
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from web.app import app
    print("✅ Flask应用导入成功")
    print("🚀 启动生产服务器在 http://0.0.0.0:5000")
    print("⚠️  生产模式：debug=False")
    
    # 生产环境配置
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    # 从环境变量获取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host=host, port=port, debug=False)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
