# 数据库集成说明

## 概述

项目已集成 MySQL 和 Redis，用于任务数据的持久化存储和实时缓存。

## 数据存储策略

### MySQL（持久化存储）
- **任务基本信息**：task_id, theme, style, length, status, created_at 等
- **任务结果**：draft_path, draft_url, video_url, segments_count 等
- **任务步骤记录**：用于统计分析和历史查询

### Redis（实时缓存）
- **任务实时进度**：current_step, steps（各步骤的状态、进度）
- **任务临时状态**：TTL 设置为 24 小时，自动过期
- **减轻数据库压力**：高频查询优先从 Redis 获取

## 数据库初始化

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并配置数据库连接信息：

```bash
# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_video_generator

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 3. 初始化 MySQL 数据库

执行 SQL 脚本创建数据库和表：

```bash
mysql -u root -p < sql/init.sql
```

或者手动执行：

```sql
mysql -u root -p
source sql/init.sql;
```

### 4. 启动 Redis

确保 Redis 服务已启动：

```bash
# Linux/Mac
redis-server

# Windows
redis-server.exe
```

## 数据库表结构

### tasks 表（任务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 自增主键 |
| task_id | VARCHAR(32) | 任务ID（32位UUID，无连字符） |
| theme | VARCHAR(200) | 视频主题 |
| style | VARCHAR(50) | 文章风格 |
| length | INT | 脚本字数 |
| status | VARCHAR(20) | 任务状态：pending/processing/completed/failed |
| current_step | VARCHAR(50) | 当前步骤 |
| error | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| completed_at | DATETIME | 完成时间 |

### task_results 表（任务结果表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 自增主键 |
| task_id | VARCHAR(32) | 任务ID |
| draft_path | VARCHAR(500) | 草稿本地路径 |
| draft_url | VARCHAR(500) | 草稿下载链接（COS CDN） |
| video_url | VARCHAR(500) | 视频下载链接（COS CDN） |
| segments_count | INT | 段落数 |
| total_duration | DECIMAL(10,2) | 总时长（秒） |
| created_at | DATETIME | 创建时间 |

### task_steps 表（任务步骤表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 自增主键 |
| task_id | VARCHAR(32) | 任务ID |
| step_name | VARCHAR(50) | 步骤名称 |
| status | VARCHAR(20) | 步骤状态：pending/processing/completed/failed |
| progress | INT | 当前进度 |
| total | INT | 总数 |
| duration | DECIMAL(10,2) | 耗时（秒） |
| started_at | DATETIME | 开始时间 |
| completed_at | DATETIME | 完成时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## API 接口

### 创建任务

```http
POST /api/tasks
Content-Type: application/json

{
  "theme": "空调原理",
  "style": "温暖感人",
  "length": 300
}
```

### 查询任务状态

```http
GET /api/tasks/{task_id}
```

### 获取任务列表

```http
GET /api/tasks?status=completed&limit=20&offset=0
```

参数：
- `status`（可选）：任务状态筛选（pending/processing/completed/failed）
- `limit`（可选）：每页数量（默认 20，最大 100）
- `offset`（可选）：偏移量（默认 0）

### 下载草稿

```http
GET /api/tasks/{task_id}/download
```

## 数据流转

1. **创建任务**：
   - 生成 32 位 task_id（无连字符）
   - 写入 MySQL tasks 表
   - 缓存到 Redis（TTL 24 小时）

2. **任务执行**：
   - 每个步骤开始/完成时更新 MySQL task_steps 表
   - 实时进度更新到 Redis
   - 任务状态变更同步到 MySQL 和 Redis

3. **任务完成**：
   - 保存结果到 MySQL task_results 表
   - 更新 Redis 缓存
   - 设置 completed_at 时间戳

4. **查询任务**：
   - 优先从内存获取（正在执行的任务）
   - 其次从 Redis 获取（最近的任务）
   - 最后从 MySQL 获取（历史任务）

## 性能优化

1. **三级缓存**：内存 → Redis → MySQL
2. **Redis TTL**：24 小时自动过期，减少内存占用
3. **MySQL 索引**：task_id, status, created_at 建立索引
4. **连接池**：MySQL 使用 DBUtils 连接池，避免频繁创建连接

## 故障处理

### MySQL 连接失败

检查配置和服务状态：

```bash
# 检查 MySQL 服务
systemctl status mysql

# 测试连接
mysql -h localhost -u root -p
```

### Redis 连接失败

检查配置和服务状态：

```bash
# 检查 Redis 服务
redis-cli ping

# 查看 Redis 信息
redis-cli info
```

### 数据不一致

如果 Redis 和 MySQL 数据不一致，可以清空 Redis 缓存：

```bash
redis-cli FLUSHDB
```

系统会自动从 MySQL 重建缓存。
