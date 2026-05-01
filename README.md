# AI 科普视频生成器

本项目是一套本地优先的 AI 科普视频生成工具，包含前端创作工作台和后端视频生成服务。

## 目录

```text
ai-kepu-video-web/      # Vue 前端
ai-kepu-video-server/   # FastAPI 后端
assets/style-previews/  # 风格预览素材
```

## 本地开发

后端：

```bash
cd ai-kepu-video-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python api_server.py
```

前端：

```bash
cd ai-kepu-video-web/frontend
npm install
cp .env.example .env.development
npm run dev -- --host 127.0.0.1 --port 5173
```

默认前端连接 `http://localhost:8001`。模型和 API Key 可在前端“模型配置”页填写，配置会保存到后端本地 `data/config.json`。

## 安全说明

不要提交 `.env`、`data/config.json`、生成素材、日志或任何真实 API Key。本仓库只保留 `.env.example` 占位示例。
