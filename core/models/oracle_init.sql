-- ============================================================
-- WeRSS Oracle 数据库初始化脚本
-- 适用于 Oracle 12c 及以上版本
-- 连接串格式: oracle+oracledb://<user>:<password>@<host>:1521/<service_name>
-- ============================================================

-- 1. we_articles 文章表
CREATE TABLE we_articles (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    mp_id           VARCHAR2(255 CHAR),
    title           VARCHAR2(1000 CHAR),
    pic_url         VARCHAR2(500 CHAR),
    url             VARCHAR2(500 CHAR),
    description     CLOB,
    extinfo         CLOB,
    content         CLOB,
    content_html    CLOB,
    content_markdown CLOB,
    status          NUMBER(10)          DEFAULT 1,
    publish_time    NUMBER(10),
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    updated_at_millis NUMBER(19),
    is_export       NUMBER(10),
    is_read         NUMBER(10)          DEFAULT 0,
    CONSTRAINT pk_we_articles PRIMARY KEY (id)
);

CREATE INDEX ix_we_articles_pub_time ON we_articles (publish_time);
CREATE INDEX ix_we_articles_upd_millis ON we_articles (updated_at_millis);

-- 2. we_feeds 公众号信息表
CREATE TABLE we_feeds (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    mp_name         VARCHAR2(255 CHAR),
    mp_cover        VARCHAR2(255 CHAR),
    mp_intro        VARCHAR2(255 CHAR),
    faker_id        VARCHAR2(255 CHAR),
    status          NUMBER(10),
    sync_time       NUMBER(10),
    update_time     NUMBER(10),
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    CONSTRAINT pk_we_feeds PRIMARY KEY (id)
);

-- 3. we_users 用户表
CREATE TABLE we_users (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    username        VARCHAR2(50 CHAR)   NOT NULL,
    password_hash   VARCHAR2(255 CHAR)  NOT NULL,
    is_active       NUMBER(1)           DEFAULT 1,
    role            VARCHAR2(20 CHAR),
    permissions     CLOB,
    nickname        VARCHAR2(50 CHAR)   DEFAULT '',
    avatar          VARCHAR2(255 CHAR)  DEFAULT '/static/default-avatar.png',
    email           VARCHAR2(50 CHAR)   DEFAULT '',
    mp_name         VARCHAR2(255 CHAR),
    mp_cover        VARCHAR2(255 CHAR),
    mp_intro        VARCHAR2(255 CHAR),
    status          NUMBER(10),
    sync_time       TIMESTAMP,
    update_time     TIMESTAMP,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    faker_id        VARCHAR2(255 CHAR),
    CONSTRAINT pk_we_users PRIMARY KEY (id),
    CONSTRAINT uq_we_users_username UNIQUE (username)
);

-- 4. we_access_keys API密钥表
CREATE TABLE we_access_keys (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    user_id         VARCHAR2(255 CHAR)  NOT NULL,
    key             VARCHAR2(64 CHAR)   NOT NULL,
    secret          VARCHAR2(64 CHAR)   NOT NULL,
    name            VARCHAR2(255 CHAR)  NOT NULL,
    description     CLOB                DEFAULT '',
    permissions     CLOB                DEFAULT '',
    is_active       NUMBER(1)           DEFAULT 1,
    last_used_at    TIMESTAMP,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    expires_at      TIMESTAMP,
    CONSTRAINT pk_we_access_keys PRIMARY KEY (id),
    CONSTRAINT uq_we_access_keys_key UNIQUE (key)
);

-- 5. we_message_tasks 消息任务表
CREATE TABLE we_message_tasks (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    message_type    NUMBER(10)          NOT NULL,
    name            VARCHAR2(100 CHAR)  NOT NULL,
    message_template CLOB               NOT NULL,
    web_hook_url    VARCHAR2(500 CHAR)  NOT NULL,
    headers         CLOB,
    cookies         CLOB,
    mps_id          CLOB                NOT NULL,
    cron_exp        VARCHAR2(100 CHAR),
    status          NUMBER(10)          DEFAULT 0,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    CONSTRAINT pk_we_message_tasks PRIMARY KEY (id)
);

-- 6. we_message_tasks_logs 消息任务日志表
CREATE TABLE we_message_tasks_logs (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    task_id         VARCHAR2(255 CHAR)  NOT NULL,
    mps_id          VARCHAR2(255 CHAR)  NOT NULL,
    update_count    NUMBER(10)          DEFAULT 0,
    log             CLOB,
    status          NUMBER(10)          DEFAULT 0,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    CONSTRAINT pk_we_msg_tasks_logs PRIMARY KEY (id)
);

-- 7. we_config_management 配置管理表
CREATE TABLE we_config_management (
    config_key      VARCHAR2(100 CHAR)  NOT NULL,
    config_value    CLOB                NOT NULL,
    description     VARCHAR2(200 CHAR),
    CONSTRAINT pk_we_config_mgmt PRIMARY KEY (config_key)
);

-- 8. we_tags 标签表
CREATE TABLE we_tags (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    name            VARCHAR2(255 CHAR),
    cover           VARCHAR2(255 CHAR),
    intro           VARCHAR2(255 CHAR),
    status          NUMBER(10),
    mps_id          CLOB                NOT NULL,
    sync_time       NUMBER(10),
    update_time     NUMBER(10),
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    CONSTRAINT pk_we_tags PRIMARY KEY (id)
);

-- 9. we_cascade_nodes 级联节点表
CREATE TABLE we_cascade_nodes (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    node_type       NUMBER(10)          DEFAULT 0 NOT NULL,
    name            VARCHAR2(255 CHAR)  NOT NULL,
    description     CLOB,
    api_url         VARCHAR2(500 CHAR),
    callback_url    VARCHAR2(500 CHAR),
    api_key         VARCHAR2(100 CHAR),
    api_secret_hash VARCHAR2(64 CHAR),
    parent_id       VARCHAR2(255 CHAR),
    status          NUMBER(10)          DEFAULT 0,
    sync_config     CLOB                DEFAULT '{}',
    last_sync_at    TIMESTAMP,
    last_heartbeat_at TIMESTAMP,
    is_active       NUMBER(1)           DEFAULT 1,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    CONSTRAINT pk_we_cascade_nodes PRIMARY KEY (id)
);

-- 10. we_cascade_sync_logs 级联同步日志表
CREATE TABLE we_cascade_sync_logs (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    node_id         VARCHAR2(255 CHAR)  NOT NULL,
    operation       VARCHAR2(50 CHAR)   NOT NULL,
    direction       VARCHAR2(20 CHAR)   NOT NULL,
    status          NUMBER(10)          DEFAULT 0,
    data_count      NUMBER(10)          DEFAULT 0,
    error_message   CLOB,
    extra_data      CLOB                DEFAULT '{}',
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    CONSTRAINT pk_we_cascade_sync_logs PRIMARY KEY (id)
);

-- 11. we_cascade_task_allocations 级联任务分配表
CREATE TABLE we_cascade_task_allocations (
    id              VARCHAR2(255 CHAR)  NOT NULL,
    task_id         VARCHAR2(255 CHAR)  NOT NULL,
    task_name       VARCHAR2(255 CHAR),
    cron_exp        VARCHAR2(100 CHAR),
    node_id         VARCHAR2(255 CHAR),
    feed_ids        CLOB                NOT NULL,
    status          VARCHAR2(20 CHAR)   DEFAULT 'pending',
    result_summary  CLOB,
    error_message   CLOB,
    dispatched_at   TIMESTAMP,
    claimed_at      TIMESTAMP,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    schedule_run_id VARCHAR2(255 CHAR),
    article_count   NUMBER(10)          DEFAULT 0,
    new_article_count NUMBER(10)        DEFAULT 0,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    CONSTRAINT pk_we_cascade_ta PRIMARY KEY (id)
);

CREATE INDEX ix_we_cascade_ta_task_id ON we_cascade_task_allocations (task_id);
CREATE INDEX ix_we_cascade_ta_node_id ON we_cascade_task_allocations (node_id);
CREATE INDEX ix_we_cascade_ta_status ON we_cascade_task_allocations (status);
CREATE INDEX ix_we_cascade_ta_run_id ON we_cascade_task_allocations (schedule_run_id);

-- ============================================================
-- 12. 初始化管理员用户
-- 默认账号: admin  默认密码: admin@123
-- 密码为 bcrypt 哈希，以下哈希对应密码 admin@123
-- ============================================================
INSERT INTO we_users (id, username, password_hash, is_active, role, created_at, updated_at)
VALUES (
    '0',
    'admin',
    '$2b$12$iL9XIBlKiN3s5xtZ7XmCCuUmg2qzwCEcjcpDjHPwfR31h4bnGhZNu',
    1,
    'admin',
    SYSTIMESTAMP,
    SYSTIMESTAMP
);
COMMIT;

-- ============================================================
-- 注意事项:
-- 1. 上方 INSERT 默认密码为 admin@123，请登录后尽快修改
-- 2. 如需自定义初始密码，可通过以下方式生成 bcrypt 哈希后替换:
--       python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
-- 3. 也可跳过上方 INSERT，通过应用初始化用户 (支持环境变量配置):
--       set USERNAME=admin
--       set PASSWORD=your_password
--       python init_sys.py
-- 4. Oracle 将空字符串视为 NULL，应用层已兼容此行为
-- ============================================================
