# Generateur_Mot Docker 部署文件
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libgirepository1.0-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs output/compare

# 设置权限
RUN chmod +x start_server_prod.py

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_ENV=production
ENV HOST=0.0.0.0
ENV PORT=5000

# 启动命令
CMD ["python", "start_server_prod.py"]
