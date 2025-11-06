# 后端 Dockerfile - Python FastAPI 应用
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (OR-Tools 需要)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p generated_videos

# 暴露端口（Railway 会使用 $PORT 环境变量）
EXPOSE 8000

# 启动命令（使用 PORT 环境变量，默认 8000）
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
