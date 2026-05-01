"""
异步任务执行器
将 pipeline 包装为异步任务，支持进度回调
"""

import logging
import time
import zipfile
import shutil
import tempfile
from pathlib import Path
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from .task_manager import task_manager, TaskStatus
from src.core.pipeline import VideoEditorPipeline
from src.utils.cos_uploader import COSUploader
from src.export.ffmpeg_exporter import FFmpegExporter

logger = logging.getLogger(__name__)


class TaskExecutor:
    """任务执行器"""

    def __init__(self):
        pass

    def execute_task(self, task_id: str, theme: str, style: str, length: int, voice_type: Optional[str] = None):
        """在后台线程中执行任务"""
        thread = Thread(target=self._run_task, args=(task_id, theme, style, length, voice_type))
        thread.daemon = True
        thread.start()
        logger.info(f"[{task_id}] 启动后台任务线程")

    def _run_task(self, task_id: str, theme: str, style: str, length: int, voice_type: Optional[str] = None):
        """执行任务的实际逻辑"""
        import time
        from src.database import mysql_client
        from src.utils.cos_uploader import COSUploader

        task = task_manager.get_task(task_id)
        if not task:
            logger.error(f"[{task_id}] 任务不存在")
            return

        try:
            # 更新任务状态为处理中
            task_manager.update_task_status(task_id, TaskStatus.PROCESSING)
            logger.info(f"[{task_id}] ========== 开始执行任务 ==========")
            logger.info(f"[{task_id}] 输入长度: {len(theme)}, 风格: {style}, 目标字数: {length}")

            # 解析 style 字段：格式为 "文章风格|画面风格|自定义画面prompt后缀"
            parts = (style or "").split("|", 2)
            text_style = parts[0] if len(parts) > 0 and parts[0] else "温暖感人"
            visual_style = parts[1] if len(parts) > 1 and parts[1] else "写实风格"
            visual_style_suffix = parts[2] if len(parts) > 2 and parts[2] else None
            visual_prompt_style = visual_style_suffix or visual_style
            logger.info(f"[{task_id}] 文章风格: {text_style}, 画面风格: {visual_style}")

            # 创建草稿名称和目录
            draft_base = task.name or theme[:20]
            draft_name = (
                draft_base.replace(" ", "_")
                .replace("\n", "_")
                .replace("/", "_")
                .replace("\\", "_")
            )[:20]
            output_base = Path("output")
            draft_dir = output_base / draft_name
            draft_dir.mkdir(parents=True, exist_ok=True)

            # 创建 pipeline，指定草稿目录
            pipeline = VideoEditorPipeline(
                theme=theme,
                output_dir=str(draft_dir)
            )

            # 步骤 1: 文案改写 / 主题生成
            logger.info(f"[{task_id}] [1/7] 开始生成/改写脚本...")
            task.start_step("text_generation")
            rewrite_result = pipeline.script_rewriter.rewrite(
                theme,
                style=text_style,
                target_length=length,
            )
            pipeline.article = rewrite_result["script"]
            pipeline.summary = rewrite_result["summary"]
            logger.info(f"[{task_id}] [1/7] 脚本生成完成，共 {len(pipeline.article)} 字")
            logger.info(f"[{task_id}] 内容总结: {pipeline.summary}")
            task.complete_step("text_generation")

            # 步骤 2: 长文本分段
            logger.info(f"[{task_id}] [2/7] 开始长文本分段...")
            pipeline.segments = pipeline.long_text_segmenter.split(pipeline.article)
            segments_count = len(pipeline.segments)
            logger.info(f"[{task_id}] [2/7] 分段完成，共 {segments_count} 段")

            # 步骤 3: 逐段生成图像 prompts
            logger.info(f"[{task_id}] [3/7] 开始逐段生成图像描述...")
            task.start_step("image_prompt_generation")
            image_prompts = []
            for i, seg in enumerate(pipeline.segments):
                logger.info(f"[{task_id}] 图像描述进度: {i+1}/{segments_count}")
                prompt = pipeline.image_prompt_agent.generate_prompt(
                    segment_text=seg,
                    summary=pipeline.summary,
                    style=visual_prompt_style,
                )
                image_prompts.append(prompt)
                task.update_step_progress("image_prompt_generation", i + 1, segments_count)
            pipeline.image_prompts = image_prompts
            logger.info(f"[{task_id}] [3/7] 图像描述生成完成")
            task.complete_step("image_prompt_generation")

            # 步骤 4-5: 配音和生图互不依赖，并行执行；各自内部串行，避免 API 限流
            logger.info(f"[{task_id}] [4-5/7] 开始并行生成配音和图像（共 {segments_count} 段）...")
            pipeline.voiceover_files = [None] * segments_count
            pipeline.media_paths = [None] * segments_count

            def generate_voiceovers():
                task.start_step("voiceover_generation")
                for i, seg in enumerate(pipeline.segments):
                    logger.info(f"[{task_id}] 配音进度: {i+1}/{segments_count}")
                    if i > 0:
                        time.sleep(0.5)
                    path = pipeline.voiceover_generator.generate(
                        seg, filename=f"seg_{i:03d}", voice_type=voice_type
                    )
                    pipeline.voiceover_files[i] = path
                    task.update_step_progress("voiceover_generation", i + 1, segments_count)
                task.complete_step("voiceover_generation")

            def generate_images():
                task.start_step("image_generation")
                for i, prompt in enumerate(image_prompts):
                    logger.info(f"[{task_id}] 图像进度: {i+1}/{segments_count}")
                    path = pipeline.image_generator.generate(
                        prompt,
                        index=i,
                        style=visual_style,
                        style_suffix=visual_style_suffix,
                    )
                    pipeline.media_paths[i] = path
                    task.update_step_progress("image_generation", i + 1, segments_count)
                task.complete_step("image_generation")

            with ThreadPoolExecutor(max_workers=2) as executor:
                voice_future = executor.submit(generate_voiceovers)
                image_future = executor.submit(generate_images)
                voice_future.result()
                image_future.result()

            logger.info(f"[{task_id}] [4-5/7] 配音和图像生成完成")

            # 步骤 6: 草稿构建
            logger.info(f"[{task_id}] [6/7] 开始构建剪映草稿...")
            task.start_step("draft_building")
            draft_path = pipeline.draft_builder.build(
                segments=pipeline.segments,
                media_paths=pipeline.media_paths,
                draft_name=draft_name,
                voiceover_files=pipeline.voiceover_files,
                output_dir=str(draft_dir),
            )
            logger.info(f"[{task_id}] [6/7] 草稿构建完成")
            task.complete_step("draft_building")

            # 检查草稿目录内容
            logger.info(f"[{task_id}] 检查草稿目录内容: {draft_dir}")
            logger.info(f"[{task_id}] draft_path 返回值: {draft_path}")
            for item in draft_dir.rglob("*"):
                if item.is_file():
                    logger.info(f"[{task_id}]   文件: {item.relative_to(draft_dir)} ({item.stat().st_size} bytes)")
                elif item.is_dir():
                    logger.info(f"[{task_id}]   目录: {item.relative_to(draft_dir)}/")

            # 步骤 6: 打包并上传到 COS
            logger.info(f"[{task_id}] [6/7] 开始打包并上传到 COS...")
            zip_path = None
            draft_url = None

            try:
                # 创建临时目录用于打包
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_draft = Path(temp_dir) / draft_name
                    temp_draft.mkdir(parents=True, exist_ok=True)

                    logger.info(f"[{task_id}] 创建临时打包目录: {temp_draft}")

                    # 复制所有文件到临时目录
                    logger.info(f"[{task_id}] 复制草稿文件到临时目录...")
                    for item in draft_dir.rglob("*"):
                        if item.is_file():
                            rel_path = item.relative_to(draft_dir)
                            dest = temp_draft / rel_path
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, dest)
                            logger.info(f"[{task_id}]   复制: {rel_path}")

                    # 打包临时目录
                    zip_path = draft_dir / f"{draft_name}.zip"
                    logger.info(f"[{task_id}] 开始打包: {temp_draft} -> {zip_path}")

                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        for file_path in temp_draft.rglob("*"):
                            if file_path.is_file():
                                # 使用相对于临时草稿目录的路径
                                arcname = file_path.relative_to(temp_draft)
                                zf.write(file_path, arcname)
                                logger.info(f"[{task_id}]   添加: {arcname}")

                    zip_size = zip_path.stat().st_size / 1024 / 1024
                    logger.info(f"[{task_id}] 打包完成，大小: {zip_size:.2f} MB")

                # 上传草稿到 COS
                try:
                    cos_uploader = COSUploader()
                    draft_url = cos_uploader.upload(str(zip_path))
                    logger.info(f"[{task_id}] 草稿上传成功: {draft_url}")
                except Exception as e:
                    logger.warning(f"[{task_id}] 草稿上传失败（不影响本地草稿）: {e}")

            except Exception as e:
                logger.warning(f"[{task_id}] 打包失败（不影响草稿）: {e}")
                logger.exception(f"[{task_id}] 打包错误详情:")

            # 步骤 7: 视频合成并上传到 COS
            logger.info(f"[{task_id}] [7/7] 开始视频合成...")
            task.start_step("video_synthesis")
            video_path = None
            video_url = None

            try:
                ffmpeg_exporter = FFmpegExporter()
                video_path = draft_dir / f"{draft_name}.mp4"

                logger.info(f"[{task_id}] 使用 FFmpeg 生成视频...")
                ffmpeg_exporter.export(
                    segments=pipeline.segments,
                    media_paths=pipeline.media_paths,
                    voiceover_files=pipeline.voiceover_files,
                    output_path=str(video_path),
                )

                video_size = video_path.stat().st_size / 1024 / 1024
                logger.info(f"[{task_id}] 视频生成完成，大小: {video_size:.2f} MB")

                # 上传视频到 COS
                try:
                    cos_uploader = COSUploader()
                    video_url = cos_uploader.upload(str(video_path))
                    logger.info(f"[{task_id}] 视频上传成功: {video_url}")
                except Exception as e:
                    logger.warning(f"[{task_id}] 视频上传失败（不影响本地视频）: {e}")

                task.complete_step("video_synthesis")

            except Exception as e:
                logger.warning(f"[{task_id}] 视频合成失败（不影响草稿）: {e}")
                logger.exception(f"[{task_id}] 视频合成错误详情:")
                task.fail_step("video_synthesis", str(e))

            # 保存段落数据到数据库
            logger.info(f"[{task_id}] 保存段落数据到数据库...")

            segments_data = []
            cos_uploader = COSUploader()

            import time
            upload_ts = int(time.time())

            for i, seg_text in enumerate(pipeline.segments):
                image_path = pipeline.media_paths[i] if i < len(pipeline.media_paths) else None
                audio_path = pipeline.voiceover_files[i] if i < len(pipeline.voiceover_files) else None

                # 上传图片到 COS
                image_url = None
                if image_path and Path(image_path).exists():
                    try:
                        image_ext = Path(image_path).suffix
                        cos_path = f"{task_id}/images/seg_{i:03d}_{upload_ts}{image_ext}"
                        image_url = cos_uploader.upload(image_path, cos_path)
                        logger.info(f"[{task_id}] 段落 {i} 图片上传成功: {image_url}")
                    except Exception as e:
                        logger.warning(f"[{task_id}] 段落 {i} 图片上传失败: {e}")

                # 上传音频到 COS
                audio_url = None
                if audio_path and Path(audio_path).exists():
                    try:
                        audio_ext = Path(audio_path).suffix
                        cos_path = f"{task_id}/audio/seg_{i:03d}_{upload_ts}{audio_ext}"
                        audio_url = cos_uploader.upload(audio_path, cos_path)
                        logger.info(f"[{task_id}] 段落 {i} 音频上传成功: {audio_url}")
                    except Exception as e:
                        logger.warning(f"[{task_id}] 段落 {i} 音频上传失败: {e}")

                seg_data = {
                    'segment_index': i,
                    'text': seg_text,
                    'image_path': image_path,
                    'image_url': image_url,
                    'audio_path': audio_path,
                    'audio_url': audio_url,
                }
                segments_data.append(seg_data)

            mysql_client.save_segments(task_id, segments_data)

            # 设置任务结果
            task_manager.set_task_result(task_id, draft_path, segments_count, draft_url, video_url)
            task_manager.update_task_status(task_id, TaskStatus.COMPLETED)

            logger.info(f"[{task_id}] ========== 任务完成 ==========")
            logger.info(f"[{task_id}] 草稿路径: {draft_path}")
            logger.info(f"[{task_id}] 段落数: {segments_count}")

        except Exception as e:
            logger.error(f"[{task_id}] ========== 任务失败 ==========")
            logger.error(f"[{task_id}] 错误类型: {type(e).__name__}")
            logger.error(f"[{task_id}] 错误信息: {str(e)}")
            logger.exception(f"[{task_id}] 详细堆栈:")

            task_manager.set_task_error(task_id, str(e))
            # 标记当前步骤失败
            if task.current_step in task.steps:
                task.fail_step(task.current_step, str(e))


# 全局任务执行器实例
task_executor = TaskExecutor()
