## 请别再加前端编译了，前端编译非常占用工作流时间 ,可以 编译后复制到static目录再提交pull request
#FROM --platform=$BUILDPLATFORM ghcr.io/rachelos/base-full:latest AS runtime
#
#ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
#ENV INSTALL=True
#ENV BROWSER_TYPE=webkit
#ENV PLANT_PATH=/app/env
#
#WORKDIR /app
#RUN echo "1.0.$(date +%Y%m%d.%H%M)">>docker_version.txt
#COPY requirements.txt install.sh ./
#RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/* \
#    && chmod +x /app/install.sh && /app/install.sh
#
#COPY . .
#COPY config.example.yaml /app/config.yaml
#RUN chmod +x /app/start.sh
#
#EXPOSE 8001
#CMD ["/app/start.sh"]

# FROM docker-bkrepo.gffunds.com.cn/z9847e/docker-local/uvicorn-gunicorn-fastapi:python3.12-2025-12-09
# CCE 默认 docker build 未注入 BUILDPLATFORM，--platform=$BUILDPLATFORM 会变成空串导致解析失败
FROM docker-bkrepo.gffunds.com.cn/z9847e/docker-local/base-full:latest

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 运行时关键环境变量（driver/playwright_driver.py 会读取）
# 基础镜像已内置 webkit 浏览器；CCE 构建环境不允许执行二进制，无法安装 firefox
ENV BROWSER_TYPE=webkit
# install.sh 会使用该路径
ENV PLANT_PATH=/app/env
ENV INSTALL=False

ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_PROGRESS_BAR=off

RUN mkdir -p ~/.pip

RUN echo '[global]' > ~/.pip/pip.conf && \
    echo 'timeout = 300' >> ~/.pip/pip.conf && \
    echo 'retries = 5' >> ~/.pip/pip.conf && \
    echo 'index-url = http://bkrepo.gffunds.com.cn/pypi/z9847e/pyip/simple' >> ~/.pip/pip.conf && \
    echo 'trusted-host = bkrepo.gffunds.com.cn' >> ~/.pip/pip.conf

COPY requirements.txt install.sh ./

RUN md5sum requirements.txt > /tmp/req_md5

RUN pip install --no-color --no-input --timeout=600 --retries 10 \
    -i http://bkrepo.gffunds.com.cn/pypi/z9847e/pyip/simple \
    --trusted-host bkrepo.gffunds.com.cn -r requirements.txt

RUN chmod +x /app/install.sh && /app/install.sh

RUN find /usr/local -name '*.pyc' -delete && \
    find /usr/local -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf ~/.cache/pip

COPY . .
COPY config.example.yaml /app/config.yaml

RUN mkdir -p /app/disconf/download /app/logs /app/data && \
    chmod +x /app/start.sh

EXPOSE 8001

CMD ["/app/start.sh"]

# 可选：用于镜像追踪（默认不启用，避免频繁变更镜像层）
# RUN echo "1.0.$(date +%Y%m%d.%H%M)" >> /app/docker_version.txt

