-- InsightCut 数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_video_generator DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_video_generator;

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    task_id VARCHAR(32) NOT NULL UNIQUE COMMENT '任务ID（32位UUID）',
    name VARCHAR(100) COMMENT '项目名称',
    theme TEXT NOT NULL COMMENT '视频主题或剧本文案',
    style VARCHAR(500) NOT NULL DEFAULT '温暖感人' COMMENT '文章风格',
    ratio VARCHAR(10) NOT NULL DEFAULT '16:9' COMMENT '视频比例：16:9/9:16/1:1',
    voice_type VARCHAR(100) COMMENT '任务创建时使用的 TTS 音色 ID',
    length INT NOT NULL DEFAULT 300 COMMENT '主题模式下的目标脚本字数',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/processing/completed/failed',
    current_step VARCHAR(50) DEFAULT 'pending' COMMENT '当前步骤',
    error TEXT COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    completed_at DATETIME COMMENT '完成时间',
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    extract_path VARCHAR(500) COMMENT '用户解压路径',
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';

-- 任务结果表
CREATE TABLE IF NOT EXISTS task_results (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    task_id VARCHAR(32) NOT NULL UNIQUE COMMENT '任务ID',
    draft_path VARCHAR(500) NOT NULL COMMENT '草稿本地路径',
    draft_url VARCHAR(500) COMMENT '草稿下载链接（COS CDN）',
    video_url VARCHAR(500) COMMENT '视频下载链接（COS CDN）',
    segments_count INT NOT NULL DEFAULT 0 COMMENT '段落数',
    total_duration DECIMAL(10, 2) COMMENT '总时长（秒）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务结果表';

-- 任务步骤表（用于统计分析）
CREATE TABLE IF NOT EXISTS task_steps (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    task_id VARCHAR(32) NOT NULL COMMENT '任务ID',
    step_name VARCHAR(50) NOT NULL COMMENT '步骤名称',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '步骤状态：pending/processing/completed/failed',
    progress INT COMMENT '当前进度',
    total INT COMMENT '总数',
    duration DECIMAL(10, 2) COMMENT '耗时（秒）',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_id (task_id),
    INDEX idx_step_name (step_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务步骤表';

-- TTS 音色表
CREATE TABLE IF NOT EXISTS tts_voices (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    voice_id VARCHAR(100) NOT NULL UNIQUE COMMENT '音色ID（豆包TTS音色标识）',
    name VARCHAR(50) NOT NULL COMMENT '音色名称',
    gender ENUM('male', 'female') NOT NULL COMMENT '性别',
    description VARCHAR(200) COMMENT '音色描述',
    is_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1=启用，0=禁用',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序权重（越大越靠前）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_is_enabled (is_enabled),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='TTS音色表';

-- 任务段落表（用于预览/编辑页面）
CREATE TABLE IF NOT EXISTS task_segments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    task_id VARCHAR(32) NOT NULL COMMENT '任务ID',
    segment_index INT NOT NULL COMMENT '段落索引（从0开始）',
    text VARCHAR(1000) NOT NULL COMMENT '段落文案',
    image_prompt TEXT COMMENT 'AI 图片生成提示词',
    image_path VARCHAR(500) COMMENT '图片本地路径',
    image_url VARCHAR(500) COMMENT '图片URL（COS）',
    audio_path VARCHAR(500) COMMENT '音频本地路径',
    audio_url VARCHAR(500) COMMENT '音频URL（COS）',
    duration DECIMAL(10, 2) COMMENT '段落时长（秒）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_task_segment (task_id, segment_index),
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务段落表';

-- 任务资产表（图片/音频/字幕/历史上传）
CREATE TABLE IF NOT EXISTS task_assets (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    asset_id VARCHAR(32) NOT NULL UNIQUE COMMENT '资产ID',
    task_id VARCHAR(32) NOT NULL COMMENT '任务ID',
    segment_index INT COMMENT '关联段落索引',
    asset_type VARCHAR(20) NOT NULL COMMENT '资产类型：image/audio/subtitle',
    source VARCHAR(20) NOT NULL COMMENT '来源：generated/regenerated/upload/selected/legacy',
    path VARCHAR(500) COMMENT '本地路径',
    url VARCHAR(500) COMMENT '访问 URL',
    label VARCHAR(200) COMMENT '展示名称',
    prompt TEXT COMMENT '图片提示词',
    text TEXT COMMENT '字幕/文案文本',
    voice_type VARCHAR(100) COMMENT '音频音色 ID',
    metadata_json TEXT COMMENT '扩展信息 JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_asset (task_id, asset_type),
    INDEX idx_task_segment_asset (task_id, segment_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务资产表';

-- 插入默认音色数据
INSERT INTO tts_voices (voice_id, name, gender, description, is_enabled, sort_order) VALUES
('zh_female_shuangkuaisisi_moon_bigtts', '爽快思思', 'female', '活泼开朗，适合轻松愉快的内容', 1, 100),
('zh_female_wanwanxiaohe_moon_bigtts', '弯弯小鹤', 'female', '温柔甜美，适合温馨治愈的内容', 1, 90),
('zh_female_tianmeibeibei_moon_bigtts', '甜美贝贝', 'female', '甜美可爱，适合少女风格内容', 1, 80),
('zh_female_qingxinruoxi_moon_bigtts', '清新若溪', 'female', '清新自然，适合文艺清新内容', 1, 70),
('zh_female_wenrouxiaoya_moon_bigtts', '温柔小雅', 'female', '温柔知性，适合知识科普内容', 1, 60),
('zh_female_mizai_uranus_bigtts', '米仔', 'female', '自然真实，适合故事讲述', 1, 50),
('zh_male_wennuanahu_moon_bigtts', '温暖阿虎', 'male', '温暖磁性，适合情感类内容', 1, 40),
('zh_male_qingchexiaoxin_moon_bigtts', '清澈小新', 'male', '清澈明朗，适合青春活力内容', 1, 30),
('zh_male_yangguangxiaolei_moon_bigtts', '阳光小磊', 'male', '阳光开朗，适合励志正能量内容', 1, 20),
('zh_male_chenwendongge_moon_bigtts', '沉稳东哥', 'male', '沉稳大气，适合严肃专业内容', 1, 10)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
