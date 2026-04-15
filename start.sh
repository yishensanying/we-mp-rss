#!/bin/bash
set -e

cd /app/
plantform="$(uname -m)"
PLANT_PATH=${PLANT_PATH:-/app/env}
plant="${PLANT_PATH}_${plantform}"
source /app/environment.sh
source "$plant/bin/activate"


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

# 启动 Xvfb（如果需要非 headless 模式）
if [ "$HEADLESS" != "true" ] || [ "$ENABLE_XVFB" = "true" ]; then
    echo "启动 Xvfb 虚拟 X Server..."
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 -ac &
    XVFB_PID=$!
    echo "Xvfb 已启动 (PID: $XVFB_PID, DISPLAY=$DISPLAY)"
    
    # 等待 Xvfb 启动
    sleep 2
fi

python3 main.py -job True
