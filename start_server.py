#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from web.app import app
    print("✅ Flask应用导入成功")
    print("🚀 启动服务器在 http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
