FROM node:20-alpine AS frontend-builder

# 设置阿里云 npm 源
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/ .
RUN DOCKER_BUILD=true npm run build

# 第二阶段：后端运行
FROM python:3.12-slim

# 设置阿里云 apt 源（Debian 12 Bookworm）
# 先删除所有默认源文件（包括 sources.list.d/debian.sources），再写入阿里云源
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*.sources /etc/apt/sources.list.d/*.list && \
    printf "deb https://mirrors.aliyun.com/debian/ bookworm main non-free non-free-firmware contrib\ndeb https://mirrors.aliyun.com/debian/ bookworm-updates main non-free non-free-firmware contrib\ndeb https://mirrors.aliyun.com/debian/ bookworm-backports main non-free non-free-firmware contrib\ndeb https://mirrors.aliyun.com/debian-security/ bookworm-security main non-free non-free-firmware contrib\n" > /etc/apt/sources.list

# 设置阿里云 pip 源
RUN mkdir -p /root/.config/pip && \
    printf "[global]\nindex-url = https://mirrors.aliyun.com/pypi/simple/\ntrusted-host = mirrors.aliyun.com\n" > /root/.config/pip/pip.conf

# 设置时区为 CST (中国标准时间 UTC+8)
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Set data directory to match Docker volume mount
ENV DATA_DIR=/app/data

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/backend/static

# 复制后端代码
COPY backend/ .

# 安装 Python 依赖（不加版本限制）
RUN pip install -r requirements.txt && pip install gunicorn

# 暴露端口
EXPOSE 8000

# 启动后端 - 多进程部署，4个worker提升并发能力
# WebSocket跨worker匹配需Redis，当前每worker独立匹配（AI对战不受影响）
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keep-alive", "5", "--preload"]
