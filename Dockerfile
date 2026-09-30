# AI for Comm —— 通信领域多智能体科研协作系统
#
# 容器里跑的是"本地编排层"：六步科研流水线、本地工具层（SymPy 符号推演、
# 通信算法库、Python 沙箱真跑、本地知识库检索）、Flask Web 六页与靛蓝瓷报告渲染。
# 智能体本体在 OpenTrek 平台，通过 HTTP/SSE 远程调用，容器内不需要 GPU 与模型权重。
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    PORT=7860

WORKDIR /app

# 先装依赖再拷代码，利用镜像层缓存；fonts-noto-cjk 供 matplotlib 出中文图
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# 运行时产物目录（报告库 / 日志 / 仿真图），compose 里以卷挂载持久化
RUN mkdir -p logs outputs outputs/sim

EXPOSE 7860

# 默认起 Web 服务；要跑 CLI 或离线回归，用 docker compose run --rm ai-for-comm <命令> 覆盖
CMD ["python", "web/app.py"]
