"""
API 数据模型
定义请求和响应的数据结构
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    theme: str = Field(..., min_length=1, max_length=2000, description="视频主题或剧本文案")
    name: Optional[str] = Field(None, max_length=100, description="项目名称")
    style: str = Field(default="温暖感人", description="文章风格")
    length: int = Field(default=300, ge=50, le=2000, description="主题模式下的目标脚本字数")
    voice_type: Optional[str] = Field(None, description="TTS 音色 ID")


class StepProgress(BaseModel):
    """步骤进度"""
    name: str = Field(..., description="步骤名称")
    status: StepStatus = Field(..., description="步骤状态")
    progress: Optional[int] = Field(None, description="当前进度")
    total: Optional[int] = Field(None, description="总数")
    duration: Optional[float] = Field(None, description="耗时（秒）")


class TaskProgress(BaseModel):
    """任务进度"""
    current_step: str = Field(..., description="当前步骤")
    steps: List[StepProgress] = Field(..., description="所有步骤")


class TaskResult(BaseModel):
    """任务结果"""
    draft_path: str = Field(..., description="草稿路径")
    draft_url: Optional[str] = Field(None, description="草稿下载链接（COS CDN）")
    video_url: Optional[str] = Field(None, description="视频下载链接（COS CDN）")
    theme: str = Field(..., description="视频主题")
    segments_count: int = Field(..., description="段落数")
    total_duration: Optional[float] = Field(None, description="总时长（秒）")
    created_at: str = Field(..., description="创建时间")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: Optional[TaskProgress] = Field(None, description="任务进度")
    result: Optional[TaskResult] = Field(None, description="任务结果")
    extract_path: Optional[str] = Field(None, description="用户上次使用的解压路径")
    error: Optional[str] = Field(None, description="错误信息")


class CreateTaskResponse(BaseModel):
    """创建任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
