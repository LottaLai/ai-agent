# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录到 app 父目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置 PYTHONPATH 包含当前目录，这样 app.xxx 和 ai.xxx 都能找到
ENV PYTHONPATH=/app:/app/app

# 调试信息
RUN echo "=== 容器内文件结构 ===" && \
    ls -la && \
    echo "=== app 目录 ===" && \
    ls -la app/ && \
    echo "=== app/ai 目录 ===" && \
    ls -la app/ai/ || echo "app/ai 不存在" && \
    echo "=== app/services 目录 ===" && \
    ls -la app/services/ || echo "app/services 不存在"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
