@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%
echo ========================================
echo MMH Server 启动调试信息 (修复版)
echo ========================================
echo 当前目录: %CD%
echo Python路径: %PYTHONPATH%
echo.

echo [1/5] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)

echo [2/5] 检查依赖模块...
python -c "import flask; print('Flask版本:', flask.__version__)"
if errorlevel 1 (
    echo 错误: Flask未安装
    pause
    exit /b 1
)

echo [3/5] 测试web.app模块导入...
python -c "print('测试导入web.app...'); import web.app; print('导入成功')"
if errorlevel 1 (
    echo 错误: web.app模块导入失败
    echo 详细错误信息:
    python -c "import web.app" 2>&1
    pause
    exit /b 1
)

echo [4/5] 启动服务器...
echo 服务器地址: http://127.0.0.1:5000/
echo 启动时间: %date% %time%
echo.
echo 如果看到错误信息，请检查上方的调试输出
echo ========================================

:: 使用项目的start_server.py启动
echo 正在启动服务器...
start "MMH Server" python start_server.py

:: 等待服务器初始化
echo [5/5] 等待服务器启动并打开浏览器...
timeout /t 5 /nobreak >nul

:: 自动打开浏览器 - 使用正确的端口5000
echo 正在打开浏览器...
start "" "http://127.0.0.1:5000/"

echo.
echo ========================================
echo 服务器已启动并在后台运行！
echo 浏览器地址: http://127.0.0.1:5000/
echo 关闭 "MMH Server" 窗口可停止服务器
echo ========================================

pause

echo.
echo ========================================
echo 服务器已停止运行
echo 时间: %date% %time%
echo ========================================
pause
