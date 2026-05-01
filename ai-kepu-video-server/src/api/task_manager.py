"""
任务管理模块
负责任务的创建、状态跟踪、进度更新
集成 MySQL 持久化和 Redis 缓存
"""

import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Callable
from threading import Thread, Lock
from .models import (
    TaskStatus, StepStatus, TaskProgress,
    StepProgress, TaskResult, TaskResponse
)
from src.database import mysql_client, redis_client

logger = logging.getLogger(__name__)


class Task:
    """任务对象"""

    def __init__(self, task_id: str, theme: str, style: str, length: int, voice_type: Optional[str] = None, name: Optional[str] = None):
        self.task_id = task_id
        self.theme = theme
        self.name = name or theme[:20]
        self.style = style
        self.length = length
        self.voice_type = voice_type
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.error: Optional[str] = None
        self.result: Optional[TaskResult] = None
        self.extract_path: Optional[str] = None

        # 进度跟踪
        self.current_step = "pending"
        self.steps = {
            "text_generation": StepProgress(
                name="text_generation",
                status=StepStatus.PENDING
            ),
            "image_prompt_generation": StepProgress(
                name="image_prompt_generation",
                status=StepStatus.PENDING
            ),
            "voiceover_generation": StepProgress(
                name="voiceover_generation",
                status=StepStatus.PENDING
            ),
            "image_generation": StepProgress(
                name="image_generation",
                status=StepStatus.PENDING
            ),
            "draft_building": StepProgress(
                name="draft_building",
                status=StepStatus.PENDING
            ),
            "video_synthesis": StepProgress(
                name="video_synthesis",
                status=StepStatus.PENDING
            )
        }
        self.step_start_times: Dict[str, float] = {}

    def start_step(self, step_name: str):
        """开始某个步骤"""
        if step_name in self.steps:
            self.current_step = step_name
            self.steps[step_name].status = StepStatus.PROCESSING
            self.step_start_times[step_name] = time.time()
            logger.info(f"[{self.task_id}] 开始步骤: {step_name}")

            # 更新到 MySQL 和 Redis
            mysql_client.update_step(self.task_id, step_name, "processing")
            mysql_client.update_task_status(self.task_id, "processing", step_name)
            self._sync_progress_to_redis()

    def update_step_progress(self, step_name: str, progress: int, total: int):
        """更新步骤进度"""
        if step_name in self.steps:
            self.steps[step_name].progress = progress
            self.steps[step_name].total = total
            logger.info(f"[{self.task_id}] {step_name} 进度: {progress}/{total}")

            # 更新到 MySQL 和 Redis
            mysql_client.update_step(self.task_id, step_name, "processing", progress, total)
            self._sync_progress_to_redis()

    def complete_step(self, step_name: str):
        """完成某个步骤"""
        if step_name in self.steps:
            self.steps[step_name].status = StepStatus.COMPLETED
            if step_name in self.step_start_times:
                duration = time.time() - self.step_start_times[step_name]
                self.steps[step_name].duration = round(duration, 2)
            logger.info(f"[{self.task_id}] 完成步骤: {step_name}")

            # 更新到 MySQL 和 Redis
            mysql_client.update_step(
                self.task_id, step_name, "completed",
                self.steps[step_name].progress,
                self.steps[step_name].total,
                self.steps[step_name].duration
            )
            self._sync_progress_to_redis()

    def fail_step(self, step_name: str, error: str):
        """步骤失败"""
        if step_name in self.steps:
            self.steps[step_name].status = StepStatus.FAILED
            self.error = error
            logger.error(f"[{self.task_id}] 步骤失败 {step_name}: {error}")

            # 更新到 MySQL 和 Redis
            mysql_client.update_step(self.task_id, step_name, "failed")
            self._sync_progress_to_redis()

    def _sync_progress_to_redis(self):
        """同步进度到 Redis"""
        steps_dict = {
            name: {
                "name": step.name,
                "status": step.status,
                "progress": step.progress,
                "total": step.total,
                "duration": step.duration,
            }
            for name, step in self.steps.items()
        }
        redis_client.update_progress(self.task_id, self.current_step, steps_dict)

    def to_response(self) -> TaskResponse:
        """转换为响应对象"""
        progress = TaskProgress(
            current_step=self.current_step,
            steps=list(self.steps.values())
        )

        return TaskResponse(
            task_id=self.task_id,
            status=self.status,
            progress=progress if self.status in [TaskStatus.PENDING, TaskStatus.PROCESSING] else None,
            result=self.result,
            extract_path=self.extract_path,
            error=self.error
        )


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = Lock()

    def create_task(self, theme: str, style: str, length: int, voice_type: Optional[str] = None, name: Optional[str] = None) -> str:
        """创建新任务"""
        task_id = uuid.uuid4().hex
        task = Task(task_id, theme, style, length, voice_type, name)

        with self.lock:
            self.tasks[task_id] = task

        mysql_client.create_task(task_id, theme, style, length, name)

        # 缓存到 Redis
        task_data = {
            "task_id": task_id,
            "theme": theme,
            "style": style,
            "length": length,
            "status": "pending",
            "created_at": task.created_at,
        }
        redis_client.cache_task(task_id, task_data)

        logger.info(f"创建任务: {task_id}, 主题: {theme}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务（优先从内存，然后 Redis，最后 MySQL）"""
        # 1. 从内存获取
        with self.lock:
            if task_id in self.tasks:
                return self.tasks[task_id]

        # 2. 从 Redis 获取
        cached_data = redis_client.get_task(task_id)
        if cached_data:
            # 重建 Task 对象
            task = self._rebuild_task_from_cache(cached_data)
            if task:
                with self.lock:
                    self.tasks[task_id] = task
                return task

        # 3. 从 MySQL 获取
        db_data = mysql_client.get_task(task_id)
        if db_data:
            task = self._rebuild_task_from_db(db_data)
            if task:
                with self.lock:
                    self.tasks[task_id] = task
                # 回写到 Redis
                redis_client.cache_task(task_id, self._task_to_dict(task))
                return task

        return None

    def _rebuild_task_from_cache(self, data: dict) -> Optional[Task]:
        """从缓存数据重建 Task 对象"""
        try:
            task = Task(data["task_id"], data["theme"], data["style"], data["length"])
            task.status = TaskStatus(data["status"])
            task.created_at = data["created_at"]
            if "error" in data:
                task.error = data["error"]
            if "extract_path" in data:
                task.extract_path = data["extract_path"]
            if "result" in data and data["result"]:
                task.result = TaskResult(**data["result"])

            # 获取进度信息
            progress_data = redis_client.get_progress(data["task_id"])
            if progress_data:
                task.current_step = progress_data["current_step"]
                for step_name, step_data in progress_data["steps"].items():
                    if step_name in task.steps:
                        task.steps[step_name].status = StepStatus(step_data["status"])
                        task.steps[step_name].progress = step_data.get("progress")
                        task.steps[step_name].total = step_data.get("total")
                        task.steps[step_name].duration = step_data.get("duration")

            return task
        except Exception as e:
            logger.error(f"从缓存重建任务失败: {e}")
            return None

    def _rebuild_task_from_db(self, data: dict) -> Optional[Task]:
        """从数据库数据重建 Task 对象"""
        try:
            task = Task(data["task_id"], data["theme"], data["style"], data["length"])
            task.status = TaskStatus(data["status"])
            task.created_at = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
            task.current_step = data.get("current_step", "pending")
            task.error = data.get("error")
            task.extract_path = data.get("extract_path")

            # 重建结果
            if data.get("result"):
                result_data = data["result"]
                task.result = TaskResult(
                    draft_path=result_data["draft_path"],
                    draft_url=result_data.get("draft_url"),
                    video_url=result_data.get("video_url"),
                    theme=data["theme"],
                    segments_count=result_data["segments_count"],
                    total_duration=result_data.get("total_duration"),
                    created_at=task.created_at,
                )

            # 重建步骤
            if data.get("steps"):
                for step_data in data["steps"]:
                    step_name = step_data["step_name"]
                    if step_name in task.steps:
                        task.steps[step_name].status = StepStatus(step_data["status"])
                        task.steps[step_name].progress = step_data.get("progress")
                        task.steps[step_name].total = step_data.get("total")
                        task.steps[step_name].duration = step_data.get("duration")

            return task
        except Exception as e:
            logger.error(f"从数据库重建任务失败: {e}")
            return None

    def _task_to_dict(self, task: Task) -> dict:
        """将 Task 对象转换为字典"""
        return {
            "task_id": task.task_id,
            "theme": task.theme,
            "style": task.style,
            "length": task.length,
            "status": task.status,
            "created_at": task.created_at,
            "error": task.error,
            "extract_path": task.extract_path,
            "result": task.result.dict() if task.result else None,
        }

    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            logger.info(f"[{task_id}] 状态更新: {status}")

            # 更新到 MySQL
            mysql_client.update_task_status(task_id, status, task.current_step, task.error)

            # 更新到 Redis
            redis_client.cache_task(task_id, self._task_to_dict(task))

    def set_task_result(self, task_id: str, draft_path: str, segments_count: int, draft_url: str = None, video_url: str = None):
        """设置任务结果"""
        task = self.get_task(task_id)
        if task:
            task.result = TaskResult(
                draft_path=draft_path,
                draft_url=draft_url,
                video_url=video_url,
                theme=task.theme,
                segments_count=segments_count,
                total_duration=None,
                created_at=task.created_at
            )
            logger.info(f"[{task_id}] 设置结果: {draft_path}")
            if draft_url:
                logger.info(f"[{task_id}] 草稿 URL: {draft_url}")
            if video_url:
                logger.info(f"[{task_id}] 视频 URL: {video_url}")

            # 保存到 MySQL
            mysql_client.save_task_result(task_id, draft_path, segments_count, draft_url, video_url)

            # 更新到 Redis
            redis_client.cache_task(task_id, self._task_to_dict(task))

    def set_task_error(self, task_id: str, error: str):
        """设置任务错误"""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            logger.error(f"[{task_id}] 任务失败: {error}")

            # 更新到 MySQL
            mysql_client.update_task_status(task_id, "failed", task.current_step, error)

            # 更新到 Redis
            redis_client.cache_task(task_id, self._task_to_dict(task))

    def update_extract_path(self, task_id: str, extract_path: str):
        """更新任务的解压路径"""
        task = self.get_task(task_id)
        if task:
            task.extract_path = extract_path
            mysql_client.update_extract_path(task_id, extract_path)
            redis_client.cache_task(task_id, self._task_to_dict(task))


# 全局任务管理器实例
task_manager = TaskManager()
