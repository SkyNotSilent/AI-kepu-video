# InsightCut 项目说明

## 项目结构

```
Auto-jianji/
├── ai-kepu-video-server/    # 后端服务（FastAPI）
│   ├── api_server.py         # FastAPI 应用入口
│   ├── main.py               # 命令行工具入口
│   └── src/                  # 源代码
└── ai-kepu-video-web/        # 前端项目
    └── frontend/             # Vue 3 前端应用
```

## 启动服务

### 一键启动前后端

当用户说"启动"、"打开"、"重新启动端口"时，需要同时启动前后端服务：

**1. 停止旧进程（如果存在）**
```bash
# 停止前端（端口 3004）
lsof -ti:3004 | xargs kill -9 2>/dev/null || true

# 停止后端（端口 8848）
lsof -ti:8848 | xargs kill -9 2>/dev/null || true
```

**2. 启动后端服务**
```bash
cd /Users/mima1234/Documents/AI产品经理/Auto-jianji/ai-kepu-video-server && \
source venv/bin/activate && \
python -m uvicorn api_server:app --host 0.0.0.0 --port 8848 --reload
```
- 后端地址：http://localhost:8848
- API 文档：http://localhost:8848/docs
- 健康检查：http://localhost:8848/health

**3. 启动前端服务**
```bash
cd /Users/mima1234/Documents/AI产品经理/Auto-jianji/ai-kepu-video-web/frontend && \
npm run dev
```
- 前端地址：http://localhost:3004

### 前后端配置对齐

- 前端配置文件：`ai-kepu-video-web/frontend/.env.development`
  ```
  VITE_API_BASE_URL=http://localhost:8848
  VITE_POLLING_INTERVAL=2000
  ```
- 后端监听端口：`8848`
- 前端开发端口：`3004`

## 重要说明

1. **后端入口文件**：使用 `api_server.py`（不是 `main.py`）
2. **虚拟环境**：后端需要激活 venv 虚拟环境
3. **后台运行**：两个服务都应该在后台运行（`run_in_background: true`）
4. **启动顺序**：先启动后端，再启动前端（避免前端启动时后端未就绪）

## 开发注意事项

- 前端使用 Vue 3 + Vite
- 后端使用 FastAPI + Python 3.9
- 素材库按 `segment_index` 排序展示（播放顺序）
