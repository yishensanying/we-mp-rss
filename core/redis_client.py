"""Redis客户端工具类，支持 standalone 和 sentinel 两种部署模式"""
import redis
from redis.sentinel import Sentinel
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from core.config import cfg
from core.print import print_error, print_info, print_warning


def _parse_sentinel_hosts(hosts_str: str) -> List[Tuple[str, int]]:
    """解析逗号分隔的 sentinel 地址列表，如 '10.89.185.20:26379,10.89.185.21:26379'"""
    result = []
    for item in hosts_str.split(","):
        item = item.strip()
        if not item:
            continue
        host, port = item.rsplit(":", 1)
        result.append((host.strip(), int(port.strip())))
    return result


class RedisClient:
    """Redis客户端封装类，支持 standalone / sentinel 两种模式。
    采用懒加载：import 时不创建连接，首次实际使用时才读取配置并连接。
    """
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass

    def _ensure_connected(self):
        """懒加载：首次调用时读取 cfg 并建立连接，之后不再重复执行。"""
        if self._initialized:
            return

        self._initialized = True

        deploy_mode = str(cfg.get("redis.deploy_mode", "standalone")).strip().lower()
        db = int(cfg.get("redis.db", 0))
        password = str(cfg.get("redis.password", "")).strip()
        ssl = str(cfg.get("redis.ssl", "False")).strip().lower() in ("true", "1", "yes", "y")
        socket_timeout = int(cfg.get("redis.socket_timeout", 5))
        connect_timeout = int(cfg.get("redis.connect_timeout", 5))

        try:
            if deploy_mode == "sentinel":
                self._init_sentinel(db, password, ssl, socket_timeout, connect_timeout)
            else:
                self._init_standalone(db, password, ssl, socket_timeout, connect_timeout)
        except redis.exceptions.ConnectionError as e:
            print_error(f"Redis连接失败 - 无法连接到Redis服务")
            print_error(f"  错误详情: {e}")
            print_error(f"  请检查:")
            print_error(f"    1. Redis服务是否已启动")
            print_error(f"    2. 配置的地址和端口是否正确")
            print_error(f"    3. 防火墙是否允许连接")
            self._client = None
        except redis.exceptions.AuthenticationError as e:
            print_error(f"Redis连接失败 - 认证错误")
            print_error(f"  错误详情: {e}")
            print_error(f"  请检查Redis密码配置是否正确")
            self._client = None
        except redis.exceptions.TimeoutError as e:
            print_error(f"Redis连接失败 - 连接超时")
            print_error(f"  错误详情: {e}")
            print_error(f"  请检查网络连接和Redis服务状态")
            self._client = None
        except Exception as e:
            print_error(f"Redis连接失败: {type(e).__name__} - {e}")
            self._client = None

    def _init_standalone(self, db, password, ssl, socket_timeout, connect_timeout):
        """standalone 模式：直连单个 Redis 实例"""
        host = str(cfg.get("redis.host", "")).strip()
        port = int(cfg.get("redis.port", 6379))

        if not host:
            print_info("Redis 未配置 host，统计功能将禁用")
            return

        print_info(f"Redis standalone 模式: {host}:{port}")
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password or None,
            ssl=ssl,
            decode_responses=True,
            socket_connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self._client.ping()
        print_info("Redis连接成功 (standalone)")

    def _init_sentinel(self, db, password, ssl, socket_timeout, connect_timeout):
        """sentinel 模式：通过哨兵发现 master 并连接"""
        sentinel_hosts_str = str(cfg.get("redis.sentinel_hosts", "")).strip()
        master_name = str(cfg.get("redis.master_name", "mymaster")).strip()

        if not sentinel_hosts_str:
            print_error("Redis sentinel 模式已启用，但未配置 sentinel_hosts")
            return

        sentinel_hosts = _parse_sentinel_hosts(sentinel_hosts_str)
        print_info(f"Redis sentinel 模式: master={master_name}, sentinels={sentinel_hosts}")

        sentinel = Sentinel(
            sentinel_hosts,
            password=password or None,
            db=db,
            socket_timeout=socket_timeout,
            socket_connect_timeout=connect_timeout,
            decode_responses=True,
        )
        self._client = sentinel.master_for(
            master_name,
            password=password or None,
            db=db,
            socket_timeout=socket_timeout,
            decode_responses=True,
        )
        self._client.ping()
        print_info(f"Redis连接成功 (sentinel, master={master_name})")
    
    def reconnect(self) -> bool:
        """重置并重新连接 Redis（使用当前最新的 cfg 配置）。
        
        Returns:
            是否重新连接成功
        """
        self._client = None
        self._initialized = False
        self._ensure_connected()
        return self.is_connected
    
    @property
    def is_connected(self) -> bool:
        """检查Redis是否已连接"""
        self._ensure_connected()
        return self._client is not None
    
    def record_env_exception(self, url: str, mp_name: str = "", mp_id: str = "") -> bool:
        """记录环境异常统计
        
        Args:
            url: 文章URL
            mp_name: 公众号名称
            mp_id: 公众号ID
            
        Returns:
            是否记录成功
        """
        self._ensure_connected()
        if self._client is None:
            return False
            
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 使用Redis事务确保原子性
            pipe = self._client.pipeline()
            
            # 1. 总计数器 (按日期)
            pipe.incr(f"werss:env_exception:total:{today}")
            pipe.expire(f"werss:env_exception:total:{today}", 86400 * 30)  # 保留30天
            
            # 2. URL维度统计 (按日期)
            url_key = f"werss:env_exception:url:{today}"
            pipe.hset(url_key, url, timestamp)
            pipe.expire(url_key, 86400 * 30)  # 保留30天
            
            # 3. 公众号维度统计 (按日期)
            if mp_id:
                mp_key = f"werss:env_exception:mp:{today}"
                pipe.hincrby(mp_key, mp_id, 1)
                pipe.expire(mp_key, 86400 * 30)  # 保留30天
            
            # 4. 详细日志列表 (最近1000条)
            log_key = f"werss:env_exception:logs"
            log_data = {
                "url": url,
                "mp_name": mp_name,
                "mp_id": mp_id,
                "timestamp": timestamp
            }
            pipe.lpush(log_key, str(log_data))
            pipe.ltrim(log_key, 0, 999)  # 只保留最近1000条
            pipe.expire(log_key, 86400 * 7)  # 保留7天
            
            # 执行事务
            pipe.execute()
            
            return True
            
        except redis.exceptions.ConnectionError as e:
            print_error(f"Redis连接断开，记录失败: {e}")
            self._client = None
            return False
        except Exception as e:
            print_error(f"记录环境异常统计失败: {e}")
            return False
    
    def get_env_exception_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """获取环境异常统计信息
        
        Args:
            date: 日期，格式为 YYYY-MM-DD，默认为今天
            
        Returns:
            统计信息字典
        """
        # 默认返回值
        default_stats = {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "total": 0,
            "urls": {},
            "mp_stats": {},
            "recent_logs": []
        }
        
        self._ensure_connected()
        if self._client is None:
            print_warning("Redis未连接，返回默认统计信息")
            return default_stats
            
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
                
            # 获取总计数
            total = self._client.get(f"werss:env_exception:total:{date}")
            total = int(total) if total else 0
            
            # 获取URL列表
            url_key = f"werss:env_exception:url:{date}"
            urls = self._client.hgetall(url_key) or {}
            
            # 获取公众号统计
            mp_key = f"werss:env_exception:mp:{date}"
            mp_stats = self._client.hgetall(mp_key) or {}
            
            # 获取最近日志
            logs = self._client.lrange("werss:env_exception:logs", 0, 99) or []  # 最近100条
            
            return {
                "date": date,
                "total": total,
                "urls": urls,
                "mp_stats": mp_stats,
                "recent_logs": logs
            }
            
        except redis.exceptions.ConnectionError as e:
            print_error(f"Redis连接错误: {e}")
            return default_stats
        except Exception as e:
            print_error(f"获取环境异常统计失败: {e}")
            return default_stats


# 全局单例实例
redis_client = RedisClient()


def record_env_exception(url: str, mp_name: str = "", mp_id: str = "") -> bool:
    """记录环境异常统计（便捷函数）
    
    Args:
        url: 文章URL
        mp_name: 公众号名称
        mp_id: 公众号ID
        
    Returns:
        是否记录成功
    """
    return redis_client.record_env_exception(url, mp_name, mp_id)


def get_env_exception_stats(date: Optional[str] = None) -> Dict[str, Any]:
    """获取环境异常统计信息（便捷函数）
    
    Args:
        date: 日期，格式为 YYYY-MM-DD，默认为今天
        
    Returns:
        统计信息字典
    """
    return redis_client.get_env_exception_stats(date)
