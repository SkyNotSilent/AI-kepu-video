"""
Redis 缓存客户端
负责任务实时进度的缓存
"""

import json
import logging
import os
from typing import Optional, Dict, Any

import redis

from src.config import Config

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 缓存客户端"""

    def __init__(self):
        self.client = None
        self._initialized = False

    def _init_client(self):
        """延迟初始化 Redis 客户端"""
        if self._initialized:
            return

        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self.client.ping()
            self._initialized = True
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            logger.warning("Redis 不可用，任务进度将仅保存在内存中")
            self._initialized = False
            self.client = None

    def _task_key(self, task_id: str) -> str:
        """生成任务缓存键"""
        return f"task:{task_id}"

    def _progress_key(self, task_id: str) -> str:
        """生成进度缓存键"""
        return f"task:progress:{task_id}"

    def cache_task(self, task_id: str, task_data: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        缓存任务数据

        Args:
            task_id: 任务ID
            task_data: 任务数据
            ttl: 过期时间（秒），默认 24 小时
        """
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return False

        try:
            key = self._task_key(task_id)
            self.client.setex(key, ttl, json.dumps(task_data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"缓存任务数据失败: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的任务数据"""
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return None

        try:
            key = self._task_key(task_id)
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取缓存任务数据失败: {e}")
            return None

    def delete_task(self, task_id: str) -> bool:
        """删除任务缓存"""
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return False

        try:
            key = self._task_key(task_id)
            progress_key = self._progress_key(task_id)
            self.client.delete(key, progress_key)
            return True
        except Exception as e:
            logger.error(f"删除任务缓存失败: {e}")
            return False

    def update_progress(
        self,
        task_id: str,
        current_step: str,
        steps: Dict[str, Dict[str, Any]],
        ttl: int = 86400,
    ) -> bool:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            current_step: 当前步骤
            steps: 步骤详情
            ttl: 过期时间（秒），默认 24 小时
        """
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return False

        try:
            key = self._progress_key(task_id)
            progress_data = {
                "current_step": current_step,
                "steps": steps,
            }
            self.client.setex(key, ttl, json.dumps(progress_data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            return False

    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return None

        try:
            key = self._progress_key(task_id)
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取任务进度失败: {e}")
            return None

    def set_step_progress(
        self,
        task_id: str,
        step_name: str,
        status: str,
        progress: int = None,
        total: int = None,
        duration: float = None,
    ) -> bool:
        """更新单个步骤的进度"""
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return False

        try:
            # 获取当前进度数据
            progress_data = self.get_progress(task_id)
            if not progress_data:
                progress_data = {"current_step": step_name, "steps": {}}

            # 更新步骤信息
            if step_name not in progress_data["steps"]:
                progress_data["steps"][step_name] = {}

            progress_data["steps"][step_name]["status"] = status
            if progress is not None:
                progress_data["steps"][step_name]["progress"] = progress
            if total is not None:
                progress_data["steps"][step_name]["total"] = total
            if duration is not None:
                progress_data["steps"][step_name]["duration"] = duration

            # 保存更新后的进度
            key = self._progress_key(task_id)
            self.client.setex(key, 86400, json.dumps(progress_data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"更新步骤进度失败: {e}")
            return False

    def extend_ttl(self, task_id: str, ttl: int = 86400) -> bool:
        """延长任务缓存的过期时间"""
        if not self._initialized:
            self._init_client()

        if not self._initialized or not self.client:
            return False

        try:
            key = self._task_key(task_id)
            progress_key = self._progress_key(task_id)
            self.client.expire(key, ttl)
            self.client.expire(progress_key, ttl)
            return True
        except Exception as e:
            logger.error(f"延长缓存过期时间失败: {e}")
            return False


# 全局 Redis 客户端实例
redis_client = RedisClient()
