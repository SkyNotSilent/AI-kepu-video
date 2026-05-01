# InsightCut Server

InsightCut 的 FastAPI 后端生成服务，负责把主题或长文案转换为可编辑的视频项目。

## 工作流

```text
主题 / 文案
  -> LLM 生成或改写旁白脚本
  -> 分段并生成每段画面 prompt
  -> 并行生成 TTS 配音和 AI 图片
  -> 构建剪映/CapCut 草稿
  -> 导出 MP4 成片
  -> 可选上传对象存储
```

## 能力边界

- 面向科普、心理学、认知、财经解释类短视频。
- 支持 OpenAI / Anthropic 兼容 LLM 接口。
- 支持常见 `images/generations` 风格的生图接口，兼容 URL 和 `b64_json` 返回。
- 支持豆包 TTS 参数配置。
- 输出剪映/CapCut 草稿 ZIP，保留二次剪辑空间。
- 同步输出 MP4，便于快速预览。

## 本地启动

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python api_server.py
```

默认服务地址：`http://localhost:8000`

API 文档：`http://localhost:8000/docs`

## 关键配置

### `.env`

`.env.example` 是占位模板。复制为 `.env` 后，填写自己的模型、TTS 和对象存储配置。

### 前端模型配置

前端“模型配置”页会把配置写入本地 `data/config.json`。该文件只用于本机运行，不进入版本库。

配置优先级：

1. `data/config.json`
2. `.env` / 环境变量
3. 代码中的公开默认值

## 输出目录

```text
output/
├── drafts/        # 剪映/CapCut 草稿
└── <task_id>/     # 图片、配音、字幕、MP4 等任务产物
```

这些生成产物默认被 `.gitignore` 忽略。

## 常见问题

**草稿不出现在剪映/CapCut**：确认 `config/settings.json` 中的 `draft_path` 与剪映/CapCut 的草稿目录一致。

**FFmpeg 找不到**：安装依赖后会优先使用 `imageio-ffmpeg` 内置二进制；系统 PATH 中有 ffmpeg 时会优先使用系统版本。

**图像接口报错**：检查“模型配置”页或 `.env` 中的图像 API URL、Key、Model 和尺寸参数。

**TTS 失败**：检查 TTS App ID、Token、Cluster 和 Voice Type 是否匹配当前账号套餐。

**对象存储上传失败**：对象存储是可选能力，本地生成不依赖它；需要上传时再配置对应凭证。
