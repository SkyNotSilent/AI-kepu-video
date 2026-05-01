# InsightCut

认知科普视频工作台：面向科普、心理学、认知、财经解释类内容的批量 AI 视频生产工具。

InsightCut 不是只生成一条成片的玩具项目。它提供从主题/文案到脚本、分镜图、配音、字幕、MP4 和剪映草稿的完整本地工作流，并保留可编辑空间，方便在专业剪辑软件里继续精修。

## 核心能力

- **批量生成解释型视频**：适合科普、心理学、认知、知识解读、财经教育等内容。
- **一站式素材生产**：自动生成脚本、分段旁白、画面 prompt、AI 图片、TTS 配音和字幕。
- **可视化编辑工作台**：前端可预览和调整段落内容、图片与音频，减少返工成本。
- **导出剪映草稿**：生成可移植的剪映/CapCut 草稿包，导入后可继续二次编辑。
- **同步导出 MP4**：可直接输出带字幕和基础动画的成片，便于快速预览或发布。
- **模型接口可配置**：前端“模型配置”页支持配置生文、生图、TTS 等接口参数，适配 OpenAI/Anthropic 兼容协议和主流图像生成接口。
- **本地优先**：开发、配置和生成产物默认都在本机完成，不依赖外部 CI/CD 或云端流水线。

## 目录结构

```text
ai-kepu-video-web/      # Vue 前端工作台
ai-kepu-video-server/   # FastAPI 后端生成服务
assets/style-previews/  # 画面风格预览素材
```

当前目录名保留了早期项目结构，产品名称以 `InsightCut` 为准。

## 本地开发

### 后端

```bash
cd ai-kepu-video-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python api_server.py
```

默认服务地址：`http://localhost:8000`

### 前端

```bash
cd ai-kepu-video-web/frontend
npm install
cp .env.example .env.development
npm run dev -- --host 127.0.0.1 --port 5173
```

默认访问地址：`http://127.0.0.1:5173`

## 配置说明

仓库提供 `.env.example` 作为占位模板。本地运行时复制为 `.env`，再填写自己的模型、TTS 和对象存储配置。

前端也提供“模型配置”页，可填写：

- 生文模型：协议类型、Base URL、API Key、Model
- 生图模型：API URL、API Key、Model、图片尺寸
- TTS：App ID、Token、Cluster、Voice Type

这些配置会保存在后端本地 `data/config.json`，该目录已被 `.gitignore` 忽略。

## 输出产物

- 剪映/CapCut 草稿 ZIP：适合导入专业剪辑软件继续编辑。
- MP4 成片：适合快速预览或直接发布。
- 任务素材：分段图片、配音、字幕和中间文件默认输出到本地 `output/`。

`data/`、`output/`、`logs/`、`.env`、生成素材和真实 API Key 都不会进入版本库。

## 开源仓库

GitHub: https://github.com/SkyNotSilent/AI-kepu-video
