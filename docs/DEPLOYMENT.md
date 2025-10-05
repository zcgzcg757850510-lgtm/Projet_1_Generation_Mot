# Generateur_Mot 项目部署指南

## 项目概述

Generateur_Mot 是一个基于 Flask 的汉字生成和变形系统，包含前端界面、后端API、文件处理和SVG变形功能。

## 当前项目部署准备情况评估

### ✅ 项目优势
- **结构清晰**：模块化设计，代码组织良好
- **依赖明确**：requirements.txt 包含所有必要依赖
- **功能完整**：前后端功能齐全，API接口完善
- **文档齐全**：有详细的架构文档和使用说明

### ⚠️ 需要注意的问题
- **调试模式**：当前使用 `debug=True`，生产环境需要关闭
- **硬编码路径**：部分路径配置可能需要调整
- **数据文件**：依赖大量本地数据文件（mmh_pipeline/data/）
- **输出目录**：需要确保输出目录的读写权限

## 部署方案

### 1. 本地/内网部署（推荐）

**适用场景**：内部使用、演示、开发测试

**优势**：
- 部署简单，配置要求低
- 数据安全，不涉及外网传输
- 性能稳定，响应快速

**部署步骤**：
```bash
# 1. 克隆项目
git clone <repository-url>
cd Generateur_Mot

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置生产环境
cp start_server.py start_server_prod.py
# 编辑 start_server_prod.py，设置 debug=False

# 5. 启动服务
python start_server_prod.py
```

### 2. 云服务器部署

**适用场景**：远程访问、多用户使用

**推荐平台**：
- **阿里云ECS**
- **腾讯云CVM**
- **AWS EC2**
- **Azure VM**

**配置要求**：
- **CPU**：2核心以上
- **内存**：4GB以上
- **存储**：20GB以上（数据文件较大）
- **系统**：Ubuntu 20.04+ / CentOS 8+

### 3. Docker 容器化部署

**优势**：环境一致性、易于扩展、便于管理

## 部署前准备工作

### 1. 生产环境配置优化

```python
# 创建 web/config_prod.py
import os

class ProductionConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # 数据库配置（如果需要）
    # DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # 文件上传限制
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/generateur_mot/app.log'
```

### 2. 环境变量配置

```bash
# .env 文件
SECRET_KEY=your-very-secret-key-here
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000
```

### 3. 数据文件检查

确保以下关键文件存在：
- `mmh_pipeline/data/hanzi_data_full.json`
- `data/style_profiles.json`
- `data/stroke_types.json`

## 潜在部署问题及解决方案

### 1. 依赖问题

**问题**：某些依赖在不同系统上安装失败
```bash
# 解决方案：使用系统包管理器预安装
# Ubuntu/Debian
sudo apt-get install python3-dev libcairo2-dev libgirepository1.0-dev

# CentOS/RHEL
sudo yum install python3-devel cairo-devel gobject-introspection-devel
```

### 2. 权限问题

**问题**：输出目录无写入权限
```bash
# 解决方案：设置正确权限
sudo chown -R www-data:www-data /path/to/Generateur_Mot/output/
sudo chmod -R 755 /path/to/Generateur_Mot/output/
```

### 3. 内存不足

**问题**：处理大型SVG文件时内存不足
```python
# 解决方案：添加内存监控和限制
import psutil
import gc

def check_memory_usage():
    memory = psutil.virtual_memory()
    if memory.percent > 80:
        gc.collect()
        return False
    return True
```

### 4. 端口冲突

**问题**：5000端口被占用
```bash
# 检查端口占用
netstat -tlnp | grep :5000

# 解决方案：使用其他端口
export PORT=8080
python start_server_prod.py
```

## 生产环境部署最佳实践

### 1. 使用 Gunicorn + Nginx

```bash
# 安装 Gunicorn
pip install gunicorn

# 创建 Gunicorn 配置文件
# gunicorn.conf.py
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

```nginx
# Nginx 配置
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/Generateur_Mot/web/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. 系统服务配置

```ini
# /etc/systemd/system/generateur-mot.service
[Unit]
Description=Generateur Mot Web Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/Generateur_Mot
Environment=PATH=/path/to/Generateur_Mot/venv/bin
ExecStart=/path/to/Generateur_Mot/venv/bin/gunicorn -c gunicorn.conf.py web.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. 日志管理

```python
# 添加到 web/app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/generateur_mot.log', 
        maxBytes=10240000, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### 4. 监控和健康检查

```python
# 添加健康检查端点
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': _preview_version()
    }
```

## 部署检查清单

### 部署前检查
- [ ] 所有依赖已安装
- [ ] 数据文件完整
- [ ] 配置文件正确
- [ ] 权限设置合适
- [ ] 防火墙规则配置

### 部署后验证
- [ ] 服务正常启动
- [ ] 网页可以访问
- [ ] 文字生成功能正常
- [ ] 网格变形功能正常
- [ ] 文章生成功能正常
- [ ] 日志记录正常

## 维护建议

### 1. 定期备份
```bash
# 备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_${DATE}.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    /path/to/Generateur_Mot/
```

### 2. 性能监控
- 使用 `htop` 监控系统资源
- 使用 `nginx` 访问日志分析流量
- 定期检查磁盘空间使用情况

### 3. 安全更新
- 定期更新 Python 依赖包
- 及时应用系统安全补丁
- 配置适当的防火墙规则

## 总结

当前项目**部署准备情况良好**，主要优势：
- 代码结构清晰，模块化程度高
- 依赖关系明确，便于环境搭建
- 功能完整，测试充分

**部署难度评估**：⭐⭐⭐☆☆（中等）

**推荐部署方案**：本地/内网部署，适合大多数使用场景，部署简单，维护方便。

**预期问题**：主要集中在依赖安装和权限配置，按照本指南操作可以避免大部分问题。
