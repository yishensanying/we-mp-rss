# we-mp-rss 离线生产部署手册（Docker + 外部 Oracle）

本文档用于在**完全离线**生产环境部署当前本地仓库代码，采用“有网环境拉取/构建镜像 → `docker save` 导出 → 离线环境 `docker load` 导入”的方式。

## 1. 适用范围

- 使用本地项目代码构建镜像，不从 GitHub/GitLab 在线拉代码
- 生产环境无外网
- 数据库使用外部 Oracle（业务账号/密码）
- 生产库表由 DBA 预建，不依赖 `oracle_init.sql` 执行初始化
- 不使用 sing-box，不使用任何代理

## 2. 最终交付文件

本方案依赖以下文件：

- `compose/docker-compose.oracle-offline.yaml`
- `config.yaml`（由 `config.example.yaml` 派生）
- `.env`（生产环境变量）
- `we-mp-rss-prod-offline.tar`（离线镜像包）

## 3. 目录与配置说明

项目根目录建议至少包含：

```text
we-mp-rss/
├─ compose/
│  └─ docker-compose.oracle-offline.yaml
├─ data/
├─ config.yaml
├─ .env
└─ we-mp-rss-prod-offline.tar
```

说明：

- `data/` 用于运行期数据落盘
- `config.yaml` 在容器中挂载为 `/app/config.yaml`
- `.env` 由 compose 自动加载，用于替换变量

## 4. 有网环境制作离线镜像包

### 4.1 前置条件

- 已安装 Docker（可联网）
- 当前目录是本地仓库根目录

### 4.2 拉取基础镜像

`Dockerfile` 依赖基础镜像 `ghcr.io/rachelos/base-full:latest`，先在有网环境拉取：

```bash
docker pull ghcr.io/rachelos/base-full:latest
```

### 4.3 用本地代码构建生产镜像

```bash
docker build -t we-mp-rss:prod-offline -f Dockerfile .
```

### 4.4 导出镜像文件

```bash
docker save -o we-mp-rss-prod-offline.tar we-mp-rss:prod-offline
```

### 4.5 交付到离线环境的清单

- `we-mp-rss-prod-offline.tar`
- `compose/docker-compose.oracle-offline.yaml`
- `config.yaml`
- `.env`
- `data/`（按需）

## 5. 生产环境配置准备（离线）

### 5.1 准备 `.env`

示例：

```env
TZ=Asia/Shanghai
PORT=8001

USERNAME=admin
PASSWORD=请替换为强密码

ENABLE_JOB=True
AUTO_RELOAD=False

DB=oracle+oracledb://业务账号:业务密码@10.10.10.10:1521/ORCLPDB1
```

建议：

- `PASSWORD` 首次部署就改为强密码
- Oracle 账号密码如含特殊字符，需进行 URL 编码
- `AUTO_RELOAD` 在生产保持 `False`

### 5.2 准备 `config.yaml`

可从 `config.example.yaml` 复制后最小调整：

```yaml
db: ${DB:-oracle+oracledb://user:password@127.0.0.1:1521/ORCL}

port: ${PORT:-8001}

proxy:
  enabled: ${PROXY_ENABLED:-False}
  deno_url: ${PROXY_DENO_URL:-}
  http_url: ${PROXY_HTTP_URL:-}
```

要求：

- `db` 必须是 Oracle 连接串（由 `.env` 中 `DB` 覆盖）
- 代理保持禁用

## 6. 离线生产环境部署步骤

### 6.1 导入镜像

```bash
docker load -i we-mp-rss-prod-offline.tar
```

### 6.2 启动服务

在项目根目录执行：

```bash
docker compose -f compose/docker-compose.oracle-offline.yaml up -d
```

### 6.3 查看状态

```bash
docker compose -f compose/docker-compose.oracle-offline.yaml ps
docker logs -f we-mp-rss
```

### 6.4 停止与重启

```bash
docker compose -f compose/docker-compose.oracle-offline.yaml stop
docker compose -f compose/docker-compose.oracle-offline.yaml start
```

### 6.5 下线

```bash
docker compose -f compose/docker-compose.oracle-offline.yaml down
```

## 7. 首次上线检查清单

- 容器状态为 `Up`
- 日志无 Oracle 连接报错
- 应用端口可访问：`http://<部署机IP>:8001`
- 可使用 `.env` 中 `USERNAME/PASSWORD` 登录
- 核心页面/API 响应正常

说明：

- 项目启动参数包含 `-init True`，会尝试初始化默认管理员账户
- 生产库表需由 DBA 提前建好；本部署流程不执行 `oracle_init.sql`

## 8. 升级与回滚（离线）

### 8.1 升级流程

1. 有网环境重新构建新镜像并导出 tar
2. 离线生产环境执行：

```bash
docker compose -f compose/docker-compose.oracle-offline.yaml down
docker load -i 新版本镜像.tar
docker compose -f compose/docker-compose.oracle-offline.yaml up -d
```

### 8.2 回滚流程

1. 保留上一版本 tar 包（如 `we-mp-rss-prod-offline-v1.tar`）
2. 发生故障时导入旧包并重启：

```bash
docker compose -f compose/docker-compose.oracle-offline.yaml down
docker load -i we-mp-rss-prod-offline-v1.tar
docker compose -f compose/docker-compose.oracle-offline.yaml up -d
```

## 9. 常见问题排查

### 9.1 Oracle 连接失败

- 核查 `DB` 格式是否为 `oracle+oracledb://user:pass@host:port/service_name`
- 核查数据库白名单、防火墙、路由、端口（常见 1521）
- 核查账号权限是否覆盖业务表

### 9.2 容器不断重启

- 查看日志：`docker logs --tail=200 we-mp-rss`
- 核查 `config.yaml` 是否存在 YAML 语法错误
- 核查 `.env` 中是否缺失 `DB`

### 9.3 端口访问不通

- 核查宿主机防火墙是否放行 `PORT`（默认 8001）
- 核查 compose 端口映射与 `.env` 中 `PORT` 一致

## 10. 使用的生产编排文件

当前部署统一使用：

- `compose/docker-compose.oracle-offline.yaml`

该文件已满足以下约束：

- 仅单容器部署 `we-mp-rss`
- 使用本地镜像标签 `we-mp-rss:prod-offline`
- 外部 Oracle（通过 `DB` 注入）
- 明确禁用代理：`PROXY_ENABLED=False`，`PROXY_HTTP_URL=""`
