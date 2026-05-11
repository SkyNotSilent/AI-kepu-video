"""
MySQL 数据库客户端
负责任务数据的持久化存储
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB

from src.config import Config

logger = logging.getLogger(__name__)


class MySQLClient:
    """MySQL 数据库客户端"""

    def __init__(self):
        self.pool = None
        self._initialized = False

    def _init_pool(self):
        """延迟初始化连接池"""
        if self._initialized:
            return

        try:
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=10,
                mincached=2,
                maxcached=5,
                blocking=True,
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                charset="utf8mb4",
                cursorclass=DictCursor,
            )
            self._initialized = True
            self._ensure_schema_updates()
            logger.info("MySQL 连接池初始化成功")
        except Exception as e:
            logger.error(f"MySQL 连接池初始化失败: {e}")
            logger.warning("MySQL 不可用，任务数据将仅保存在内存和 Redis 中")
            self._initialized = False

    def _ensure_schema_updates(self):
        """应用兼容性字段调整，支持 2000 字剧本文案。"""
        try:
            with self.get_connection() as conn:
                if not conn:
                    return
                with conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE tasks MODIFY COLUMN theme TEXT NOT NULL COMMENT '视频主题或剧本文案'")
                    cursor.execute("ALTER TABLE tasks MODIFY COLUMN style VARCHAR(500) NOT NULL DEFAULT '温暖感人' COMMENT '文章风格'")
                    try:
                        cursor.execute("ALTER TABLE tasks ADD COLUMN ratio VARCHAR(10) NOT NULL DEFAULT '16:9' COMMENT '视频比例：16:9/9:16/1:1' AFTER style")
                    except Exception:
                        pass
                    try:
                        cursor.execute("ALTER TABLE tasks ADD COLUMN voice_type VARCHAR(100) COMMENT '任务创建时使用的 TTS 音色 ID' AFTER ratio")
                    except Exception:
                        pass
                    try:
                        cursor.execute("ALTER TABLE task_segments ADD COLUMN image_prompt TEXT COMMENT 'AI 图片生成提示词' AFTER text")
                    except Exception:
                        pass
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS task_assets (
                            id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                            asset_id VARCHAR(32) NOT NULL UNIQUE,
                            task_id VARCHAR(32) NOT NULL,
                            segment_index INT,
                            asset_type VARCHAR(20) NOT NULL,
                            source VARCHAR(20) NOT NULL,
                            path VARCHAR(500),
                            url VARCHAR(500),
                            label VARCHAR(200),
                            prompt TEXT,
                            text TEXT,
                            voice_type VARCHAR(100),
                            metadata_json TEXT,
                            status VARCHAR(20) DEFAULT 'completed',
                            error_message TEXT,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            INDEX idx_task_asset (task_id, asset_type),
                            INDEX idx_task_segment_asset (task_id, segment_index)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """)
                    # 为已存在的 task_assets 表添加新字段
                    try:
                        cursor.execute("ALTER TABLE task_assets ADD COLUMN status VARCHAR(20) DEFAULT 'completed' COMMENT '资源状态：pending/generating/completed/failed' AFTER metadata_json")
                    except Exception:
                        pass
                    try:
                        cursor.execute("ALTER TABLE task_assets ADD COLUMN error_message TEXT COMMENT '失败原因' AFTER status")
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"MySQL schema 更新跳过: {e}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized or not self.pool:
            # 如果连接池初始化失败，返回一个空的上下文
            logger.warning("MySQL 不可用，跳过数据库操作")
            yield None
            return

        conn = self.pool.connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()

    def create_task(self, task_id: str, theme: str, style: str, length: int, name: str = None, ratio: str = "16:9", voice_type: str = None) -> bool:
        """创建任务记录"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO tasks (task_id, name, theme, style, ratio, voice_type, length, status, current_step)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', 'pending')
                    """
                    cursor.execute(sql, (task_id, name or theme[:20], theme, style, ratio, voice_type, length))

                    # 初始化步骤记录
                    steps = [
                        "text_generation",
                        "image_prompt_generation",
                        "voiceover_generation",
                        "image_generation",
                        "draft_building",
                        "video_synthesis",
                    ]
                    step_sql = """
                        INSERT INTO task_steps (task_id, step_name, status)
                        VALUES (%s, %s, 'pending')
                    """
                    for step in steps:
                        cursor.execute(step_sql, (task_id, step))

            logger.info(f"任务记录创建成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"创建任务记录失败: {e}")
            return False

    def update_task_status(self, task_id: str, status: str, current_step: str = None, error: str = None) -> bool:
        """更新任务状态"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    if status == "completed":
                        sql = """
                            UPDATE tasks
                            SET status = %s, current_step = %s, error = %s, completed_at = NOW()
                            WHERE task_id = %s
                        """
                    else:
                        sql = """
                            UPDATE tasks
                            SET status = %s, current_step = %s, error = %s
                            WHERE task_id = %s
                        """
                    cursor.execute(sql, (status, current_step, error, task_id))
            return True
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False

    def save_task_result(
        self,
        task_id: str,
        draft_path: str,
        segments_count: int,
        draft_url: str = None,
        video_url: str = None,
        total_duration: float = None,
    ) -> bool:
        """保存任务结果"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO task_results
                        (task_id, draft_path, draft_url, video_url, segments_count, total_duration)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        draft_path = VALUES(draft_path),
                        draft_url = VALUES(draft_url),
                        video_url = VALUES(video_url),
                        segments_count = VALUES(segments_count),
                        total_duration = VALUES(total_duration)
                    """
                    cursor.execute(sql, (task_id, draft_path, draft_url, video_url, segments_count, total_duration))
            logger.info(f"任务结果保存成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"保存任务结果失败: {e}")
            return False

    def update_step(
        self,
        task_id: str,
        step_name: str,
        status: str,
        progress: int = None,
        total: int = None,
        duration: float = None,
    ) -> bool:
        """更新步骤状态"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    if status == "processing":
                        sql = """
                            UPDATE task_steps
                            SET status = %s, started_at = NOW()
                            WHERE task_id = %s AND step_name = %s
                        """
                        cursor.execute(sql, (status, task_id, step_name))
                    elif status == "completed":
                        sql = """
                            UPDATE task_steps
                            SET status = %s, progress = %s, total = %s, duration = %s, completed_at = NOW()
                            WHERE task_id = %s AND step_name = %s
                        """
                        cursor.execute(sql, (status, progress, total, duration, task_id, step_name))
                    else:
                        sql = """
                            UPDATE task_steps
                            SET status = %s, progress = %s, total = %s
                            WHERE task_id = %s AND step_name = %s
                        """
                        cursor.execute(sql, (status, progress, total, task_id, step_name))
            return True
        except Exception as e:
            logger.error(f"更新步骤状态失败: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return None

        try:
            with self.get_connection() as conn:
                if not conn:
                    return None

                with conn.cursor() as cursor:
                    # 获取任务基本信息
                    sql = "SELECT * FROM tasks WHERE task_id = %s"
                    cursor.execute(sql, (task_id,))
                    task = cursor.fetchone()

                    if not task:
                        return None

                    # 获取任务结果
                    sql = "SELECT * FROM task_results WHERE task_id = %s"
                    cursor.execute(sql, (task_id,))
                    result = cursor.fetchone()

                    # 获取步骤信息
                    sql = "SELECT * FROM task_steps WHERE task_id = %s ORDER BY id"
                    cursor.execute(sql, (task_id,))
                    steps = cursor.fetchall()

                    task["result"] = result
                    task["steps"] = steps
                    return task
        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None

    def get_enabled_voices(self) -> List[Dict]:
        """获取启用的音色列表（按排序权重降序）"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return []

        try:
            with self.get_connection() as conn:
                if not conn:
                    return []

                with conn.cursor() as cursor:
                    sql = """
                        SELECT voice_id, name, gender, description, sort_order
                        FROM tts_voices
                        WHERE is_enabled = 1
                        ORDER BY sort_order DESC, id ASC
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取音色列表失败: {e}")
            return []

    def update_voice_status(self, voice_id: str, is_enabled: bool) -> bool:
        """更新音色启用状态"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    sql = "UPDATE tts_voices SET is_enabled = %s WHERE voice_id = %s"
                    cursor.execute(sql, (1 if is_enabled else 0, voice_id))
            return True
        except Exception as e:
            logger.error(f"更新音色状态失败: {e}")
            return False

    def update_extract_path(self, task_id: str, extract_path: str) -> bool:
        """更新任务的解压路径"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    sql = "UPDATE tasks SET extract_path = %s WHERE task_id = %s"
                    cursor.execute(sql, (extract_path, task_id))
            return True
        except Exception as e:
            logger.error(f"更新解压路径失败: {e}")
            return False

    def list_tasks(self, status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取任务列表"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return []

        try:
            with self.get_connection() as conn:
                if not conn:
                    return []

                with conn.cursor() as cursor:
                    if status:
                        sql = """
                            SELECT t.*, r.draft_url, r.video_url, r.segments_count
                            FROM tasks t
                            LEFT JOIN task_results r ON t.task_id = r.task_id
                            WHERE t.status = %s
                            ORDER BY t.created_at DESC
                            LIMIT %s OFFSET %s
                        """
                        cursor.execute(sql, (status, limit, offset))
                    else:
                        sql = """
                            SELECT t.*, r.draft_url, r.video_url, r.segments_count
                            FROM tasks t
                            LEFT JOIN task_results r ON t.task_id = r.task_id
                            ORDER BY t.created_at DESC
                            LIMIT %s OFFSET %s
                        """
                        cursor.execute(sql, (limit, offset))
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    def save_segments(self, task_id: str, segments: List[Dict]) -> bool:
        """保存任务段落数据"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO task_segments
                        (task_id, segment_index, text, image_prompt, image_path, image_url, audio_path, audio_url, duration)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        text = VALUES(text),
                        image_prompt = VALUES(image_prompt),
                        image_path = VALUES(image_path),
                        image_url = VALUES(image_url),
                        audio_path = VALUES(audio_path),
                        audio_url = VALUES(audio_url),
                        duration = VALUES(duration)
                    """
                    for seg in segments:
                        cursor.execute(sql, (
                            task_id,
                            seg['segment_index'],
                            seg['text'],
                            seg.get('image_prompt'),
                            seg.get('image_path'),
                            seg.get('image_url'),
                            seg.get('audio_path'),
                            seg.get('audio_url'),
                            seg.get('duration')
                        ))
            logger.info(f"任务段落保存成功: {task_id}, 共 {len(segments)} 段")
            return True
        except Exception as e:
            logger.error(f"保存任务段落失败: {e}")
            return False

    def get_segments(self, task_id: str) -> List[Dict]:
        """获取任务段落列表"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return []

        try:
            with self.get_connection() as conn:
                if not conn:
                    return []

                with conn.cursor() as cursor:
                    sql = """
                        SELECT * FROM task_segments
                        WHERE task_id = %s
                        ORDER BY segment_index ASC
                    """
                    cursor.execute(sql, (task_id,))
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取任务段落失败: {e}")
            return []

    def update_segment(self, task_id: str, segment_index: int, updates: Dict) -> bool:
        """更新单个段落"""
        if not self._initialized:
            self._init_pool()

        if not self._initialized:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                with conn.cursor() as cursor:
                    set_parts = []
                    values = []
                    for key, value in updates.items():
                        if key in ['text', 'image_prompt', 'image_path', 'image_url', 'audio_path', 'audio_url', 'duration']:
                            set_parts.append(f"{key} = %s")
                            values.append(value)

                    if not set_parts:
                        return False

                    values.extend([task_id, segment_index])
                    sql = f"""
                        UPDATE task_segments
                        SET {', '.join(set_parts)}
                        WHERE task_id = %s AND segment_index = %s
                    """
                    cursor.execute(sql, values)
            return True
        except Exception as e:
            logger.error(f"更新段落失败: {e}")
            return False

    def save_task_asset(self, task_id: str, asset_type: str, source: str, path: str = None,
                        url: str = None, segment_index: int = None, label: str = None,
                        prompt: str = None, text: str = None, voice_type: str = None,
                        metadata_json: str = None, status: str = "completed", error_message: str = None) -> Dict:
        if not self._initialized:
            self._init_pool()
        if not self._initialized:
            return {}
        try:
            with self.get_connection() as conn:
                if not conn:
                    return {}
                with conn.cursor() as cursor:
                    if path:
                        cursor.execute(
                            """SELECT * FROM task_assets
                               WHERE task_id=%s AND asset_type=%s AND source=%s AND path=%s
                               ORDER BY id DESC LIMIT 1""",
                            (task_id, asset_type, source, path)
                        )
                        existing = cursor.fetchone()
                        if existing:
                            cursor.execute(
                                """UPDATE task_assets SET segment_index=%s, source=%s, url=%s, label=%s,
                                   prompt=%s, text=%s, voice_type=%s, metadata_json=%s, status=%s, error_message=%s
                                   WHERE asset_id=%s""",
                                (segment_index, source, url, label, prompt, text, voice_type, metadata_json, status, error_message, existing["asset_id"])
                            )
                            cursor.execute("SELECT * FROM task_assets WHERE asset_id=%s", (existing["asset_id"],))
                            return cursor.fetchone()

                    asset_id = uuid.uuid4().hex
                    cursor.execute(
                        """INSERT INTO task_assets
                           (asset_id, task_id, segment_index, asset_type, source, path, url, label, prompt, text, voice_type, metadata_json, status, error_message)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (asset_id, task_id, segment_index, asset_type, source, path, url, label, prompt, text, voice_type, metadata_json, status, error_message)
                    )
                    cursor.execute("SELECT * FROM task_assets WHERE asset_id=%s", (asset_id,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"保存任务资产失败: {e}")
            return {}

    def list_task_assets(self, task_id: str, asset_type: str = None, segment_index: int = None) -> List[Dict]:
        if not self._initialized:
            self._init_pool()
        if not self._initialized:
            return []
        try:
            with self.get_connection() as conn:
                if not conn:
                    return []
                with conn.cursor() as cursor:
                    sql = "SELECT * FROM task_assets WHERE task_id=%s"
                    values = [task_id]
                    if asset_type:
                        if asset_type == "upload":
                            sql += " AND source='upload'"
                        else:
                            sql += " AND asset_type=%s"
                            values.append(asset_type)
                    if segment_index is not None:
                        sql += " AND segment_index=%s"
                        values.append(segment_index)
                    sql += " ORDER BY created_at DESC, id DESC"
                    cursor.execute(sql, values)
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取任务资产失败: {e}")
            return []

    def get_task_asset(self, task_id: str, asset_id: str) -> Optional[Dict]:
        if not self._initialized:
            self._init_pool()
        if not self._initialized:
            return None
        try:
            with self.get_connection() as conn:
                if not conn:
                    return None
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM task_assets WHERE task_id=%s AND asset_id=%s", (task_id, asset_id))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"获取任务资产失败: {e}")
            return None


# 全局 MySQL 客户端实例
mysql_client = MySQLClient()
