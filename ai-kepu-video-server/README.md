# AI 自动科普视频生成工具

**技术栈**: Python 3.10+  
**依赖**: pyJianYingDraft, Claude API, 豆包 TTS, 豆包 Seedream, FFmpeg, 阿里云 OSS

---

## 项目简介

输入主题 → AI 生成脚本 → 豆包 TTS 配音 → 豆包 Seedream 生图 → 双通道并行输出：
- **剪映草稿**（pyJianYingDraft，含 Ken Burns 动画、字幕、配音，可导入剪映二次编辑）
- **FFmpeg MP4**（直接可播放成片，附字幕叠加）

两个产物可选择上传到阿里云 OSS。

---

## 工作流程

```
输入主题
  → [1] Claude API 生成脚本 + 图像 prompt
  → [2] 文本分段（≤22字/段，双向短段合并）
  → [3] 并行生成素材
        ├── 豆包 TTS 配音（每段一个 WAV）
        └── 豆包 Seedream 生图（按画布比例选尺寸）
  → [4] 双通道并行输出
        ├── pyJianYingDraft → 剪映草稿文件夹（可移植）
        └── FFmpeg → MP4 成片（段级并行编码 + concat 拼接）
  → [5] 可选：上传阿里云 OSS，返回公网 URL
```

---

## 快速开始

### Windows 本地开发

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. FFmpeg（pip install 时已通过 imageio-ffmpeg 自动安装，无需手动操作）
#    如系统 PATH 中已有 ffmpeg，优先使用系统版本

# 3. 编辑 config/settings.json（通常不需要改，默认 output/drafts）

# 4. 运行
python main.py
```

### Linux 服务器部署

```bash
# 1. 系统依赖
apt install ffmpeg fonts-noto-cjk -y

# 2. Python 依赖
pip install -r requirements.txt

# 3. 编辑 config/settings.json
#    draft_path  → 服务器上任意目录，如 /data/drafts
#    oss.enabled → true（如需自动上传 OSS）

# 4. 设置 OSS 环境变量（或直接填 settings.json）
export OSS_ACCESS_KEY_ID=xxx
export OSS_ACCESS_KEY_SECRET=xxx
export OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
export OSS_BUCKET=your-bucket

# 5. 启动 Web 服务
uvicorn web.server:app --host 0.0.0.0 --port 8000
```

---

## 配置文件 `config/settings.json`

```json
{
  "canvas": {
    "width": 1920,
    "height": 1080,
    "fps": 30
  },
  "draft_path": "output/drafts",
  "ffmpeg": {
    "enabled": true,
    "crf": 20,
    "preset": "fast"
  },
  "oss": {
    "enabled": false,
    "access_key_id": "",
    "access_key_secret": "",
    "endpoint": "https://oss-cn-hangzhou.aliyuncs.com",
    "bucket": "",
    "prefix": "ai-video/"
  }
}
```

| 字段 | 说明 |
|------|------|
| `canvas` | 画布尺寸，16:9 用 1920×1080，9:16 用 1080×1920 |
| `draft_path` | 剪映草稿输出目录，默认 `output/drafts` |
| `ffmpeg.enabled` | 是否同时导出 MP4，默认 true |
| `ffmpeg.crf` | 视频质量，18-28，越小越清晰，默认 20 |
| `ffmpeg.preset` | 编码速度，ultrafast/fast/medium，默认 fast |
| `oss.enabled` | 是否上传 OSS，默认 false |
| `oss.prefix` | OSS 路径前缀，默认 `ai-video/` |

---

## 输出产物

### 剪映草稿文件夹

```
<draft_path>/<主题>_auto/
├── draft_content.json       # 轨道数据（路径指向内部素材）
├── draft_meta_info.json
├── images/                  # 生成的图片
│   ├── img_000.png
│   └── ...
└── voiceovers/              # 生成的配音 WAV
    ├── seg_000.wav
    └── ...
```

整个文件夹可独立移植，拷贝到任意电脑的剪映草稿目录即可导入。

### FFmpeg MP4

`output/<task_id>/<主题>_auto.mp4` — 含字幕叠加、Ken Burns 动画的完整成片。

### OSS 上传（可选）

上传后路径格式：
```
<prefix><主题>_auto/<主题>_auto.zip   # 草稿 zip 包
<prefix><主题>_auto/<主题>_auto.mp4   # MP4 成片
```

Web API `GET /api/tasks/{id}` 返回 `oss_urls` 字段：
```json
{
  "status": "completed",
  "oss_urls": {
    "draft_zip_url": "https://bucket.oss-cn-hangzhou.aliyuncs.com/ai-video/...",
    "mp4_url": "https://bucket.oss-cn-hangzhou.aliyuncs.com/ai-video/..."
  }
}
```

---

## 目录结构

```
AI-kepu-video/
├── main.py                        # 命令行入口
├── gui.py                         # GUI 入口
├── 启动.bat                       # Windows 双击启动 GUI
├── requirements.txt
├── config/
│   └── settings.json              # 画布 / 草稿路径 / FFmpeg / OSS 配置
├── src/
│   ├── core/pipeline.py           # 主流水线（调度所有模块）
│   ├── text/
│   │   ├── generator.py           # Claude API 脚本 + 图像 prompt 生成
│   │   └── segmenter.py           # 文本分段（≤22字 + 双向短段合并）
│   ├── media/image_generator.py   # 豆包 Seedream 图像生成
│   ├── draft/
│   │   ├── builder.py             # pyJianYingDraft 草稿构建（核心）
│   │   └── voiceover.py           # 豆包 TTS 配音
│   └── export/
│       ├── ffmpeg_exporter.py     # FFmpeg MP4 导出（Ken Burns + 字幕）
│       └── oss_uploader.py        # 阿里云 OSS 上传
├── web/
│   ├── server.py                  # FastAPI Web 服务
│   ├── task_manager.py            # 任务状态管理
│   ├── log_handler.py             # 日志推送
│   └── static/index.html          # 前端页面
└── output/                        # 产物输出
    ├── drafts/                    # 剪映草稿（按主题分文件夹）
    └── {task_id}/                 # 中间产物（图片、配音）+ MP4 成片
```

---

## API 凭证

不要把真实 key 写入代码或提交到 Git。凭证优先级：

1. 前端“模型配置”页保存到本地 `data/config.json`
2. 环境变量或本地 `.env`
3. 代码中的公开默认值（不包含密钥）

| 环境变量 | 说明 |
|---------|------|
| `LLM_PROTOCOL` | `anthropic` 或 `openai` |
| `ANTHROPIC_API_KEY` | LLM API key |
| `ANTHROPIC_BASE_URL` | LLM API Base URL |
| `ANTHROPIC_MODEL` | 模型名称 |
| `DOUBAO_TTS_APPID` | 豆包 TTS |
| `DOUBAO_TTS_TOKEN` | 豆包 TTS |
| `SEEDREAM_API_URL` | 图像生成 API URL |
| `SEEDREAM_API_KEY` | 图像生成 API key |
| `SEEDREAM_MODEL` | 图像生成模型 |
| `COS_SECRET_ID` | 腾讯云 COS SecretId（可选） |
| `COS_SECRET_KEY` | 腾讯云 COS SecretKey（可选） |
| `COS_BUCKET` | 腾讯云 COS Bucket（可选） |

---

## 常见问题

**草稿不出现在剪映**：`config/settings.json` 里的 `draft_path` 需与剪映设置中的草稿路径完全一致。

**FFmpeg 找不到**：`pip install imageio-ffmpeg` 即可，代码会自动使用其内置的 ffmpeg 二进制。系统 PATH 中有 ffmpeg 则优先使用系统版本。

**Linux 字幕乱码/缺字**：`apt install fonts-noto-cjk -y`，ffmpeg_exporter 会自动识别该字体路径。

**图像 API 403**：图像生成 key 失效，在“模型配置”页或 `.env` 中更新 `SEEDREAM_API_KEY`。

**TTS 失败**：豆包 TTS appid/token 失效，在 `.env` 中更新 `DOUBAO_TTS_APPID` / `DOUBAO_TTS_TOKEN`。

**COS 上传报错"凭证不完整"**：检查 `COS_SECRET_ID` / `COS_SECRET_KEY` / `COS_BUCKET` 是否都已设置。

**Windows 本地不需要 OSS**：`settings.json` 中 `oss.enabled` 保持 `false` 即可，完全不影响本地运行。
