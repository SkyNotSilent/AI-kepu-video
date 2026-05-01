"""
FastAPI 路由
定义 API 端点
"""

import io
import json
import logging
import zipfile
from pathlib import Path
from typing import Optional, List
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from .models import CreateTaskRequest, CreateTaskResponse, TaskResponse
from .task_manager import task_manager, TaskStatus
from .task_executor import task_executor
from src.config import Config
from src.database import mysql_client
from src.utils.path_fixer import apply_extract_path, generate_fix_bat

router = APIRouter(prefix="/ai/native/video/kepu", tags=["tasks"])
logger = logging.getLogger(__name__)


@router.get("/config")
async def get_config():
    """获取模型配置"""
    return Config.load_model_config()


@router.put("/config")
async def update_config(config: dict = Body(...)):
    """更新模型配置"""
    return Config.save_model_config(config)


@router.get("/voices")
async def get_voices():
    """
    获取可用的 TTS 音色列表

    返回所有启用的豆包 TTS 音色配置（从数据库读取）
    """
    voices = mysql_client.get_enabled_voices()

    if not voices:
        raise HTTPException(status_code=500, detail="音色数据不可用，请检查数据库连接")

    # 统一返回格式
    return [
        {
            "id": v["voice_id"],
            "name": v["name"],
            "gender": v["gender"],
            "description": v.get("description", "")
        }
        for v in voices
    ]


@router.post("/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    """
    创建视频生成任务

    - **theme**: 视频主题或剧本文案（1-2000字；超过 200 字按用户剧本改写）
    - **style**: 文章风格或“文章风格|画面风格”（默认：温暖感人）
    - **length**: 主题模式下的目标脚本字数（50-2000，默认：300）
    - **voice_type**: TTS 音色 ID（可选）
    """
    # 创建任务
    task_id = task_manager.create_task(
        theme=request.theme,
        name=request.name,
        style=request.style,
        length=request.length,
        voice_type=request.voice_type
    )

    # 启动异步执行
    task_executor.execute_task(
        task_id=task_id,
        theme=request.theme,
        style=request.style,
        length=request.length,
        voice_type=request.voice_type
    )

    return CreateTaskResponse(
        task_id=task_id,
        status="pending"
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    查询任务状态

    - **task_id**: 任务ID
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task.to_response()


@router.get("/tasks/{task_id}/download")
async def download_task(
    task_id: str,
    extract_path: str = Query(..., description="用户解压路径，如 D:\\JianyingPro Drafts"),
):
    """
    下载任务生成的草稿压缩包

    - **task_id**: 任务ID
    - **extract_path**: 用户解压目标路径（必填），用于将草稿内素材路径转为绝对路径

    返回草稿 zip 文件供下载，ZIP 内包含以草稿名命名的根文件夹。
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"任务未完成，当前状态: {task.status}")

    if not task.result or not task.result.draft_path:
        raise HTTPException(status_code=404, detail="草稿路径不存在")

    draft_path = Path(task.result.draft_path)
    zip_path = draft_path / f"{draft_path.name}.zip"

    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="草稿压缩包不存在")

    draft_name = draft_path.name

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(zip_path, "r") as src_zip, \
             zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst_zip:

            for item in src_zip.infolist():
                data = src_zip.read(item.filename)

                if item.filename == "draft_content.json":
                    draft_json = json.loads(data.decode("utf-8"))
                    draft_json = apply_extract_path(draft_json, extract_path, draft_name)
                    data = json.dumps(draft_json, ensure_ascii=False, indent=2).encode("utf-8")

                dst_zip.writestr(f"{draft_name}/{item.filename}", data)

            dst_zip.writestr(f"{draft_name}/fix_paths.bat", generate_fix_bat())

        buf.seek(0)
    except Exception as e:
        logger.exception(f"生成下载 ZIP 失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成下载文件失败: {e}")

    task_manager.update_extract_path(task_id, extract_path)

    filename = f"{task.theme[:20]}.zip"
    encoded_filename = quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.get("/tasks/{task_id}/download-mp4")
async def download_video(task_id: str):
    """
    下载任务生成的视频文件

    - **task_id**: 任务ID

    返回 MP4 视频文件供下载
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"任务未完成，当前状态: {task.status}")

    if not task.result or not task.result.draft_path:
        raise HTTPException(status_code=404, detail="草稿路径不存在")

    # 查找 MP4 文件（在草稿目录内）
    draft_path = Path(task.result.draft_path)
    video_path = draft_path / f"{draft_path.name}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")

    # 返回文件下载
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{task.theme[:20]}.mp4"
    )


@router.get("/tasks", response_model=List[dict])
async def list_tasks(
    status: Optional[str] = Query(None, description="任务状态筛选：pending/processing/completed/failed"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取任务列表

    - **status**: 任务状态筛选（可选）
    - **limit**: 每页数量（默认 20，最大 100）
    - **offset**: 偏移量（默认 0）
    """
    tasks = mysql_client.list_tasks(status=status, limit=limit, offset=offset)
    return tasks


@router.get("/tasks/{task_id}/segments")
async def get_segments(task_id: str):
    """
    获取任务的段落列表

    - **task_id**: 任务ID
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    segments = mysql_client.get_segments(task_id)

    # 只返回 URL 字段，不返回本地路径
    result = []
    for seg in segments:
        result.append({
            'id': seg.get('id'),
            'task_id': seg.get('task_id'),
            'segment_index': seg.get('segment_index'),
            'text': seg.get('text'),
            'image_url': seg.get('image_url'),
            'audio_url': seg.get('audio_url'),
            'duration': seg.get('duration'),
            'created_at': seg.get('created_at'),
            'updated_at': seg.get('updated_at'),
        })

    return result


@router.put("/tasks/{task_id}/segments/{segment_index}")
async def update_segment(
    task_id: str,
    segment_index: int,
    text: Optional[str] = Body(None),
    image_url: Optional[str] = Body(None),
    audio_url: Optional[str] = Body(None)
):
    """
    更新段落内容

    - **task_id**: 任务ID
    - **segment_index**: 段落索引
    - **text**: 新文案（可选）
    - **image_url**: 新图片URL（可选）
    - **audio_url**: 新音频URL（可选）
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    updates = {}
    if text is not None:
        updates['text'] = text
    if image_url is not None:
        updates['image_url'] = image_url
    if audio_url is not None:
        updates['audio_url'] = audio_url

    if not updates:
        raise HTTPException(status_code=400, detail="至少需要提供一个更新字段")

    success = mysql_client.update_segment(task_id, segment_index, updates)
    if not success:
        raise HTTPException(status_code=500, detail="更新段落失败")

    return {"message": "更新成功"}


@router.post("/tasks/{task_id}/segments/{segment_index}/regenerate-image")
async def regenerate_image(task_id: str, segment_index: int):
    """
    重新生成段落图片

    - **task_id**: 任务ID
    - **segment_index**: 段落索引
    """
    logger.info(f"[{task_id}] ========== 开始重新生成图片 ==========")
    logger.info(f"[{task_id}] 段落索引: {segment_index}")

    task = task_manager.get_task(task_id)
    if not task:
        logger.error(f"[{task_id}] 任务不存在")
        raise HTTPException(status_code=404, detail="任务不存在")

    logger.info(f"[{task_id}] 任务主题: {task.theme}")
    logger.info(f"[{task_id}] 草稿路径: {task.result.draft_path}")

    segments = mysql_client.get_segments(task_id)
    if segment_index >= len(segments):
        logger.error(f"[{task_id}] 段落索引超出范围: {segment_index} >= {len(segments)}")
        raise HTTPException(status_code=404, detail="段落不存在")

    segment = segments[segment_index]
    logger.info(f"[{task_id}] 段落文本: {segment['text']}")

    # 重新生成图片
    from src.core.pipeline import VideoEditorPipeline
    logger.info(f"[{task_id}] 创建 VideoEditorPipeline...")
    pipeline = VideoEditorPipeline(theme=task.theme, output_dir=task.result.draft_path)

    # 生成图像 prompt
    logger.info(f"[{task_id}] 生成图像描述...")
    parts = (task.style or "").split("|", 2)
    visual_style = parts[1] if len(parts) > 1 and parts[1] else "写实风格"
    visual_style_suffix = parts[2] if len(parts) > 2 and parts[2] else None
    summary = task.theme[:100]
    image_prompt = pipeline.image_prompt_agent.generate_prompt(
        segment['text'],
        summary,
        visual_style_suffix or visual_style,
    )
    logger.info(f"[{task_id}] 图像描述: {image_prompt}")

    # 生成图片
    logger.info(f"[{task_id}] 开始生成图片...")
    import time
    timestamp = int(time.time())
    image_path = pipeline.image_generator.generate(
        image_prompt,
        index=segment_index,
        style=visual_style,
        style_suffix=visual_style_suffix,
        filename=f"seg_{segment_index:03d}_regen_{timestamp}"
    )
    logger.info(f"[{task_id}] 图片生成完成: {image_path}")

    # 上传到 COS
    from src.utils.cos_uploader import COSUploader
    from pathlib import Path

    image_url = None
    if image_path and Path(image_path).exists():
        logger.info(f"[{task_id}] 图片文件存在，开始上传到 COS...")
        try:
            cos_uploader = COSUploader()
            image_filename = Path(image_path).name
            cos_path = f"{task_id}/images/{image_filename}"
            logger.info(f"[{task_id}] COS 路径: {cos_path}")
            image_url = cos_uploader.upload(image_path, cos_path)
            logger.info(f"[{task_id}] 图片上传成功: {image_url}")
        except Exception as e:
            logger.error(f"[{task_id}] 图片上传失败: {e}")
            logger.exception(f"[{task_id}] 上传错误详情:")
    else:
        logger.error(f"[{task_id}] 图片文件不存在: {image_path}")

    # 更新数据库
    logger.info(f"[{task_id}] 更新数据库...")
    mysql_client.update_segment(task_id, segment_index, {
        'image_path': image_path,
        'image_url': image_url
    })
    logger.info(f"[{task_id}] 数据库更新完成")

    logger.info(f"[{task_id}] ========== 图片重新生成完成 ==========")
    return {"message": "图片重新生成成功", "image_path": image_path, "image_url": image_url}


@router.post("/tasks/{task_id}/segments/{segment_index}/regenerate-audio")
async def regenerate_audio(
    task_id: str,
    segment_index: int,
    voice_type: Optional[str] = None
):
    """
    重新生成段落音频

    - **task_id**: 任务ID
    - **segment_index**: 段落索引
    - **voice_type**: TTS 音色 ID（可选，如果不提供则使用任务创建时的音色）
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    segments = mysql_client.get_segments(task_id)
    if segment_index >= len(segments):
        raise HTTPException(status_code=404, detail="段落不存在")

    segment = segments[segment_index]

    # 如果没有指定 voice_type，使用任务创建时的音色
    if voice_type is None:
        voice_type = task.voice_type

    logger.info(f"[{task_id}] 使用音色: {voice_type}")

    # 重新生成音频
    from src.core.pipeline import VideoEditorPipeline
    logger.info(f"[{task_id}] 创建 VideoEditorPipeline...")
    pipeline = VideoEditorPipeline(theme=task.theme, output_dir=task.result.draft_path)

    import time
    timestamp = int(time.time())
    logger.info(f"[{task_id}] 开始生成音频...")
    audio_path = pipeline.voiceover_generator.generate(
        segment['text'],
        filename=f"seg_{segment_index:03d}_regen_{timestamp}",
        voice_type=voice_type
    )
    logger.info(f"[{task_id}] 音频生成完成: {audio_path}")

    # 上传到 COS
    from src.utils.cos_uploader import COSUploader
    from pathlib import Path

    audio_url = None
    if audio_path and Path(audio_path).exists():
        try:
            cos_uploader = COSUploader()
            audio_filename = Path(audio_path).name
            cos_path = f"{task_id}/audio/{audio_filename}"
            audio_url = cos_uploader.upload(audio_path, cos_path)
            logger.info(f"[{task_id}] 段落 {segment_index} 音频重新生成并上传成功: {audio_url}")
        except Exception as e:
            logger.warning(f"[{task_id}] 段落 {segment_index} 音频上传失败: {e}")

    # 更新数据库
    mysql_client.update_segment(task_id, segment_index, {
        'audio_path': audio_path,
        'audio_url': audio_url
    })

    return {"message": "音频重新生成成功", "audio_path": audio_path, "audio_url": audio_url}


@router.post("/tasks/{task_id}/segments/{segment_index}/upload-image")
async def upload_image(task_id: str, segment_index: int, file: UploadFile = File(...)):
    """
    上传自定义图片

    - **task_id**: 任务ID
    - **segment_index**: 段落索引
    - **file**: 图片文件
    """
    from src.utils.cos_uploader import COSUploader
    from pathlib import Path
    import shutil

    logger.info(f"[{task_id}] ========== 开始上传自定义图片 ==========")
    logger.info(f"[{task_id}] 段落索引: {segment_index}")
    logger.info(f"[{task_id}] 文件名: {file.filename}")

    task = task_manager.get_task(task_id)
    if not task:
        logger.error(f"[{task_id}] 任务不存在")
        raise HTTPException(status_code=404, detail="任务不存在")

    segments = mysql_client.get_segments(task_id)
    if segment_index >= len(segments):
        logger.error(f"[{task_id}] 段落索引超出范围: {segment_index} >= {len(segments)}")
        raise HTTPException(status_code=404, detail="段落不存在")

    # 验证文件类型
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、WEBP 格式的图片")

    # 保存到本地临时文件
    draft_path = Path(task.result.draft_path)
    images_dir = draft_path / "images"
    images_dir.mkdir(exist_ok=True)

    import time
    timestamp = int(time.time())
    file_ext = Path(file.filename).suffix or ".jpg"
    local_filename = f"seg_{segment_index:03d}_upload_{timestamp}{file_ext}"
    local_path = images_dir / local_filename

    logger.info(f"[{task_id}] 保存到本地: {local_path}")
    with open(local_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 上传到 COS
    image_url = None
    try:
        cos_uploader = COSUploader()
        cos_path = f"{task_id}/images/{local_filename}"
        logger.info(f"[{task_id}] COS 路径: {cos_path}")
        image_url = cos_uploader.upload(str(local_path), cos_path)
        logger.info(f"[{task_id}] 图片上传成功: {image_url}")
    except Exception as e:
        logger.error(f"[{task_id}] 图片上传失败: {e}")
        logger.exception(f"[{task_id}] 上传错误详情:")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {e}")

    # 更新数据库
    logger.info(f"[{task_id}] 更新数据库...")
    mysql_client.update_segment(task_id, segment_index, {
        'image_path': str(local_path),
        'image_url': image_url
    })
    logger.info(f"[{task_id}] 数据库更新完成")

    logger.info(f"[{task_id}] ========== 图片上传完成 ==========")
    return {"message": "图片上传成功", "image_path": str(local_path), "image_url": image_url}


@router.post("/tasks/{task_id}/rebuild")
async def rebuild_draft(task_id: str):
    """
    根据当前段落数据重新构建草稿和视频

    - **task_id**: 任务ID
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    segments = mysql_client.get_segments(task_id)
    if not segments:
        raise HTTPException(status_code=404, detail="段落数据不存在")

    # 重新构建草稿和视频
    from src.core.pipeline import VideoEditorPipeline
    from src.export.ffmpeg_exporter import FFmpegExporter

    pipeline = VideoEditorPipeline(theme=task.theme, output_dir=task.result.draft_path)

    # 准备数据
    segment_texts = [seg['text'] for seg in segments]
    media_paths = [seg['image_path'] for seg in segments]
    voiceover_files = [seg['audio_path'] for seg in segments]

    draft_name = Path(task.result.draft_path).name

    # 重新构建草稿
    draft_path = pipeline.draft_builder.build(
        segments=segment_texts,
        media_paths=media_paths,
        draft_name=draft_name,
        voiceover_files=voiceover_files,
        output_dir=task.result.draft_path,
    )

    # 重新生成视频
    ffmpeg_exporter = FFmpegExporter()
    video_path = Path(task.result.draft_path) / f"{draft_name}.mp4"

    ffmpeg_exporter.export(
        segments=segment_texts,
        media_paths=media_paths,
        voiceover_files=voiceover_files,
        output_path=str(video_path),
    )

    return {"message": "草稿和视频重新构建成功", "draft_path": draft_path, "video_path": str(video_path)}
