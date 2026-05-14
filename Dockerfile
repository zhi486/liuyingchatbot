FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# 避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3

WORKDIR /app

# Python 依赖（分层缓存）
COPY localmodel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu124

# 应用代码
COPY localmodel/ .

# 运行时数据目录
RUN mkdir -p histories voices exports

# 环境变量
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860
ENV KMP_DUPLICATE_LIB_OK=TRUE

EXPOSE 7860

CMD ["python", "web_chatbot_voice4.py"]
