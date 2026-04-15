import os
import time
import json
import logging
import requests
import configparser
import yaml
from pathlib import Path

logger = logging.getLogger("disconf")

disconf_client = None


def _load_disconf_properties(conf_file='disconf.properties'):
    """加载disconf.properties配置文件"""
    config = {}
    if not os.path.exists(conf_file):
        logger.error(f"配置文件不存在: {conf_file}")
        return config

    with open(conf_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
            except ValueError:
                logger.warning(f"无效的配置行: {line}")
    return config


def init_disconf():
    """初始化Disconf客户端并获取配置"""
    global disconf_client

    try:
        config = _load_disconf_properties()
        if not config:
            logger.error("无法加载disconf.properties配置")
            return False

        enable_remote_conf = config.get('disconf.enable.remote.conf', 'true').lower() == 'true'
        if not enable_remote_conf:
            logger.info("远程配置已禁用，将使用本地配置文件")
            os.environ["DISCONF_LOCAL_MODE"] = "true"
            return False

        app = config.get('disconf.app', '')
        env = config.get('disconf.env', '')
        version = config.get('disconf.version', '')
        server_host = config.get('disconf.conf_server_host', '')

        if not all([app, env, version, server_host]):
            logger.error(f"缺少必要的Disconf配置: app={app}, env={env}, version={version}, host={server_host}")
            return False

        logger.info(f"Disconf配置: app={app}, env={env}, version={version}, host={server_host}")

        download_dir = config.get('disconf.user_define_download_dir', './disconf/download')
        Path(download_dir).mkdir(parents=True, exist_ok=True)

        retry_times = int(config.get('disconf.conf_server_url_retry_times', '3'))
        retry_sleep = int(config.get('disconf.conf_server_url_retry_sleep_seconds', '5'))

        logger.info("开始从Disconf服务器下载配置...")

        config_list = _get_config_list(server_host, app, env, version, retry_times, retry_sleep)
        if not config_list:
            logger.error("无法获取配置文件列表")
            return False

        success = True
        for config_item in config_list:
            if not _download_config(server_host, config_item, download_dir, config.get('disconf.ignore', '')):
                success = False

        if not success:
            logger.error("部分配置文件下载失败")

        logger.info("开始应用配置...")
        apply_configs(download_dir)

        logger.info("成功从Disconf加载配置并应用")
        return True
    except Exception as e:
        logger.error(f"Disconf初始化失败: {str(e)}")
        return False


def _get_config_list(server_host, app, env, version, retry_times=3, retry_sleep=5):
    """获取配置文件列表"""
    for i in range(retry_times):
        try:
            url = f"http://{server_host}/api/config/list?app={app}&env={env}&version={version}"
            logger.info(f"正在获取配置列表: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"获取到的响应数据: {data}")

                success = False
                if isinstance(data.get('success'), bool):
                    success = data.get('success')
                elif isinstance(data.get('success'), str):
                    success = data.get('success').lower() == 'true'

                if success:
                    page_result = data.get('page', {}).get('result', [])
                    config_list = []

                    for item in page_result:
                        config_item = {
                            'configId': item.get('id'),
                            'name': item.get('name')
                        }

                        if 'value' in item:
                            logger.info(f"配置项 {item.get('name')} 包含直接值")
                            config_item['has_value'] = True
                            config_item['value'] = item.get('value')

                        config_list.append(config_item)

                    logger.info(f"成功获取配置列表，共 {len(config_list)} 项")
                    return config_list
                else:
                    logger.warning("响应success字段不为true")
        except Exception as e:
            logger.warning(f"获取配置列表异常: {str(e)}")

        logger.warning(f"获取配置列表失败，重试 {i+1}/{retry_times}")
        if i < retry_times - 1:
            time.sleep(retry_sleep)

    return []


def _download_config(server_host, config_item, download_dir, ignore_list=''):
    """下载单个配置文件"""
    config_name = config_item.get('name')

    if not config_name:
        logger.warning(f"无效的配置项: {config_item}")
        return False

    if config_name in ignore_list.split(','):
        logger.info(f"忽略配置: {config_name}")
        return True

    try:
        config = _load_disconf_properties()
        if not config:
            logger.error("无法加载disconf.properties配置")
            return False

        app = config.get('disconf.app', '')
        env = config.get('disconf.env', '')
        version = config.get('disconf.version', '')

        if not all([app, env, version]):
            logger.error("缺少必要的Disconf配置信息")
            return False

        url = f"http://{server_host}/api/config/file?app={app}&env={env}&version={version}&key={config_name}"
        logger.info(f"下载配置: {url}")

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            file_path = os.path.join(download_dir, config_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"成功下载配置: {config_name}")
            return True
        else:
            logger.error(f"下载配置失败: {response.status_code} {response.text[:200]}")
    except Exception as e:
        logger.error(f"下载配置异常: {str(e)}")

    return False


def apply_configs(download_dir):
    """应用下载的配置到环境变量"""
    if not os.path.exists(download_dir):
        logger.error(f"配置目录不存在: {download_dir}")
        return False

    config_files = list(Path(download_dir).glob("*")) + list(Path(download_dir).glob(".*"))
    config_files = list(set(config_files))

    if not config_files:
        logger.warning(f"未找到任何配置文件在 {download_dir}")
        return False

    logger.info(f"开始应用 {len(config_files)} 个配置文件")

    for file_path in config_files:
        if not file_path.is_file():
            continue

        file_name = file_path.name
        logger.info(f"配置文件file_path: {file_path}")
        if '.env' in file_name or file_name.endswith('.env'):
            logger.info(f"应用 .env 配置文件: {file_name}")
            _apply_env_file(file_path)
        elif file_path.suffix.lower() == '.properties':
            logger.info(f"应用 .properties 配置文件: {file_name}")
            _apply_properties_file(file_path)
        elif file_path.suffix.lower() == '.json':
            logger.info(f"应用 .json 配置文件: {file_name}")
            _apply_json_file(file_path)
        elif file_path.suffix.lower() in ('.yaml', '.yml'):
            logger.info(f"应用 .yaml 配置文件: {file_name}")
            _apply_yaml_file(file_path)
        else:
            logger.info(f"未知的配置文件类型: {file_name}")

    os.environ["DISCONF_LOADED"] = "true"
    logger.info("所有配置文件应用完成")
    return True


def _apply_properties_file(file_path):
    """应用.properties文件配置"""
    try:
        config = configparser.ConfigParser()
        with open(file_path, 'r', encoding='utf-8') as f:
            content = '[root]\n' + f.read()

        config.read_string(content)
        for key, value in config['root'].items():
            env_key = key.upper()
            os.environ[env_key] = value
            logger.debug(f"设置环境变量: {env_key}={value}")
        return True
    except Exception as e:
        logger.error(f"应用properties配置失败: {str(e)}")
        return False


def _apply_json_file(file_path):
    """应用.json文件配置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        _set_nested_env(config)
        return True
    except Exception as e:
        logger.error(f"应用json配置失败: {str(e)}")
        return False


def _set_nested_env(config, prefix=''):
    """设置嵌套的JSON配置到环境变量"""
    for key, value in config.items():
        env_key = f"{prefix}_{key}" if prefix else key
        env_key = env_key.upper()

        if isinstance(value, dict):
            _set_nested_env(value, env_key)
        else:
            os.environ[env_key] = str(value)
            logger.debug(f"设置环境变量: {env_key}={value}")


def _apply_yaml_file(file_path):
    """应用.yaml文件配置，将叶子节点展平为环境变量。
    值中的 ${VAR:-default} 占位符保持原样，由 cfg.get() 在读取时解析。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            logger.warning(f"YAML文件内容不是字典类型，跳过: {file_path}")
            return False

        _set_nested_env(config)
        return True
    except Exception as e:
        logger.error(f"应用yaml配置失败: {str(e)}")
        return False


def _apply_env_file(file_path):
    """应用.env文件配置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    logger.debug(f"设置环境变量: {key}={value}")
                except ValueError:
                    logger.warning(f"无效的环境变量行: {line}")
        return True
    except Exception as e:
        logger.error(f"应用env配置失败: {str(e)}")
        return False
