#!/bin/bash
set -e

# we-mp-rss 服务启动脚本

APP_NAME=we-mp-rss
SERVER_PORT=8001

export PYTHONPATH=$PYTHONPATH:$(pwd)

# install.sh 在构建阶段写入；运行时若不 source，Playwright 会默认用 ~/.cache/ms-playwright
if [ -f /app/environment.sh ]; then
    # shellcheck disable=SC1091
    . /app/environment.sh
fi

# 检查 Playwright 浏览器是否已安装
BROWSER_TYPE=${BROWSER_TYPE:-firefox}
if [ -n "$PLAYWRIGHT_BROWSERS_PATH" ]; then
    BROWSER_CHECK=$(find "$PLAYWRIGHT_BROWSERS_PATH" -type d -name "${BROWSER_TYPE}-*" 2>/dev/null | head -1)
    if [ -z "$BROWSER_CHECK" ]; then
        echo "警告: Playwright ${BROWSER_TYPE} 浏览器未找到，请在 Docker 构建时确保 playwright install ${BROWSER_TYPE} 执行成功"
    else
        echo "Playwright ${BROWSER_TYPE} 浏览器已就绪: ${BROWSER_CHECK}"
    fi
fi

# 检查是否已运行（精简镜像可能未安装 procps，无 ps 时跳过）
PID=""
if command -v ps >/dev/null 2>&1; then
    PID=$(ps -ef | grep "python3 main.py" | grep -v grep | awk '{print $2}')
fi
if [ -n "$PID" ]; then
    echo "ERROR: The $APP_NAME server is already running!"
    echo "PID: $PID"
    exit 1
fi

# APP_ENV=dev 时跳过Disconf配置
if [ ! -f "disconf.properties" ]; then
    echo "警告: disconf.properties 文件不存在，跳过Disconf配置"
else
    # 使用cce-template.yaml传入的环境变量修改disconf.properties
    echo "修改disconf.properties配置..."

    if [ ! -z "$DISCONF_ENV" ]; then
        echo "使用环境变量设置 disconf.env=$DISCONF_ENV"
        sed "s/disconf.env=.*/disconf.env=$DISCONF_ENV/" disconf.properties > disconf.properties.tmp
        mv disconf.properties.tmp disconf.properties
    fi

    if [ ! -z "$DISCONF_VERSION" ]; then
        echo "使用环境变量设置 disconf.version=$DISCONF_VERSION"
        sed "s/disconf.version=.*/disconf.version=$DISCONF_VERSION/" disconf.properties > disconf.properties.tmp
        mv disconf.properties.tmp disconf.properties
    fi

    if [ ! -z "$DISCONF_HOST" ]; then
        echo "使用环境变量设置 disconf.conf_server_host=$DISCONF_HOST"
        sed "s/disconf.conf_server_host=.*/disconf.conf_server_host=$DISCONF_HOST/" disconf.properties > disconf.properties.tmp
        mv disconf.properties.tmp disconf.properties
    fi

    # 打印修改后的配置信息
    echo "当前配置信息:"
    grep "disconf.env" disconf.properties
    grep "disconf.version" disconf.properties
    grep "disconf.conf_server_host" disconf.properties
    grep "disconf.debug" disconf.properties

    # 检查是否启用远程配置，启用时清理旧文件以确保 main.py 拉取最新版本
    REMOTE_CONF_ENABLED=$(grep "disconf.enable.remote.conf" disconf.properties | cut -d'=' -f2)
    if [ "$REMOTE_CONF_ENABLED" = "true" ]; then
        echo "清理旧的disconf配置文件..."
        rm -rf disconf/download/*
    else
        echo "使用本地配置模式，保留现有配置文件..."
    fi

    # Disconf 的下载、apply_configs 和 config.yaml 覆盖统一由 main.py 处理，
    # 避免在 shell 子进程中执行（子进程设置的环境变量会丢失）。
fi

# 打印当前目录
echo "当前工作目录: $(pwd)"
echo "当前目录文件列表:"
ls -la

# 启动应用（前台运行，保持容器不退出）
echo "正在启动应用..."
echo "$APP_NAME service starting on port $SERVER_PORT..."

exec python3 main.py -job True -init True
