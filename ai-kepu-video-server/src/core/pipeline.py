"""
流水线编排模块
编排整个视频编辑流程
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.text.generator import ArticleGenerator
from src.text.segmenter import LongTextSegmenter, TextSegmenter
from src.text.agents import ImagePromptAgent, ScriptRewriter
from src.media.image_generator import ImageGenerator
from src.draft.voiceover import VoiceOverGenerator
from src.draft.builder import DraftBuilder
from src.export.ffmpeg_exporter import FFmpegExporter

logger = logging.getLogger(__name__)


class VideoEditorPipeline:
    """视频编辑流水线"""

    def __init__(
        self,
        theme: str,
        config_path: str = "config/settings.json",
        output_dir: str = "output",
    ):
        self.theme = theme
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.article_generator = ArticleGenerator()
        self.script_rewriter = ScriptRewriter(self.article_generator)
        self.image_prompt_agent = ImagePromptAgent(self.article_generator)
        self.text_segmenter = TextSegmenter()
        self.long_text_segmenter = LongTextSegmenter()

        # 读取画布尺寸，传给图片生成器
        import json
        _cfg = {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                _cfg = json.load(f)
            _canvas = _cfg.get("canvas", {})
            self._canvas_width  = _canvas.get("width", 1080)
            self._canvas_height = _canvas.get("height", 1920)
        except Exception:
            self._canvas_width  = 1080
            self._canvas_height = 1920

        self.image_generator = ImageGenerator(output_dir=str(self.output_dir / "images"))
        self.voiceover_generator = VoiceOverGenerator(
            output_dir=str(self.output_dir / "voiceovers")
        )
        self.draft_builder = DraftBuilder(config_path=config_path)

        # FFmpeg 导出通道
        self._ffmpeg_enabled = _cfg.get("ffmpeg", {}).get("enabled", True)
        try:
            self.ffmpeg_exporter = FFmpegExporter(config_path=config_path)
        except Exception as e:
            logger.warning(f"FFmpeg 导出不可用: {e}")
            self.ffmpeg_exporter = None
            self._ffmpeg_enabled = False

        self.article: str = ""
        self.summary: str = ""
        self.segments: list = []
        self.image_prompts: list = []
        self.media_paths: list = []
        self.voiceover_files: list = []
        self.draft_path: str = ""
        self.mp4_path: str = ""
        self._style: str = "写实风格"  # 供 build_from_script 复用
        self._style_suffix: str = ""
        self._text_style: str = "温暖感人"

    def _split_styles(self, style: str) -> tuple:
        parts = (style or "").split("|", 2)
        text_style = parts[0] if len(parts) > 0 and parts[0] else "温暖感人"
        visual_style = parts[1] if len(parts) > 1 and parts[1] else "写实风格"
        visual_style_suffix = parts[2] if len(parts) > 2 and parts[2] else ""
        return text_style, visual_style, visual_style_suffix

    def generate_script(self, style: str = "温暖感人", length: int = 300) -> str:
        """步骤 1-3：改写/生成脚本、长文本分段、逐段生成图像 prompts。"""
        text_style, visual_style, visual_style_suffix = self._split_styles(style)
        self._text_style = text_style
        self._style = visual_style
        self._style_suffix = visual_style_suffix

        logger.info("=" * 60)
        logger.info(f"开始生成脚本: 《{self.theme}》")
        logger.info("=" * 60)

        # 步骤 1：主题生成或文案改写
        logger.info("\n[1/4] 生成/改写脚本...")
        rewrite_result = self.script_rewriter.rewrite(
            self.theme,
            style=text_style,
            target_length=length,
        )
        self.article = rewrite_result["script"]
        self.summary = rewrite_result["summary"]
        logger.info(f"脚本生成完成，共 {len(self.article)} 字")
        logger.info(f"内容总结: {self.summary}")

        # 步骤 2：长文本分段
        logger.info("\n[2/4] 长文本分段...")
        self.segments = self.long_text_segmenter.split(self.article)
        logger.info(f"分段完成，共 {len(self.segments)} 段")
        for i, seg in enumerate(self.segments):
            logger.info(f"  [{i+1}] {seg}")

        # 步骤 3：逐段生成图像 prompts
        logger.info("\n[3/4] 逐段生成图像描述...")
        self.image_prompts = []
        for i, segment in enumerate(self.segments):
            prompt = self.image_prompt_agent.generate_prompt(
                segment,
                self.summary,
                visual_style_suffix or visual_style,
            )
            self.image_prompts.append(prompt)
            logger.info(f"  [{i+1}] {prompt}")

        return self.article

    def build_from_script(self, script: str = None) -> str:
        """步骤 3-4：并行生图+配音，构建草稿，返回草稿路径。
        script 为可选修改稿；若传入则重新分段并重新生成 image_prompts。
        """
        visual_style = self._style
        visual_style_suffix = self._style_suffix

        if script is not None and script.strip() != self.article.strip():
            logger.info("\n检测到脚本修改，重新分段...")
            self.article = script
            self.segments = self.long_text_segmenter.split(self.article)
            logger.info(f"重新分段完成，共 {len(self.segments)} 段")
            if not self.summary:
                self.summary = self.article[:100]
            self.image_prompts = [
                self.image_prompt_agent.generate_prompt(seg, self.summary, visual_style)
                for seg in self.segments
            ]

        # 步骤 3：并行生成图像 + 配音
        logger.info(f"\n[3/4] 并行生成素材（{len(self.segments)} 段）...")
        self.media_paths = [None] * len(self.segments)
        self.voiceover_files = [None] * len(self.segments)

        import threading
        image_prompts = self.image_prompts
        img_sem = threading.Semaphore(3)   # Seedream 限并发 3
        vo_sem  = threading.Semaphore(5)   # 豆包 TTS 限并发 5

        def gen_image(i):
            prompt = image_prompts[i]
            logger.info(f"  [图像 {i+1}/{len(self.segments)}] {prompt[:50]}...")
            with img_sem:
                path = self.image_generator.generate(
                    prompt, index=i, style=visual_style,
                    style_suffix=visual_style_suffix,
                    width=self._canvas_width, height=self._canvas_height,
                )
            return ("image", i, path)

        def gen_voice(i):
            seg = self.segments[i]
            logger.info(f"  [配音 {i+1}/{len(self.segments)}] {seg[:20]}...")
            with vo_sem:
                path = self.voiceover_generator.generate(seg, filename=f"seg_{i:03d}")
            return ("voice", i, path)

        # 配音和图像并行，各自内部限并发 2，互不干扰
        with ThreadPoolExecutor(max_workers=4) as executor:
            voice_futures = {executor.submit(gen_voice, i): i for i in range(len(self.segments))}
            image_futures = {executor.submit(gen_image, i): i for i in range(len(self.segments))}

            for future in as_completed(voice_futures):
                _, idx, path = future.result()
                self.voiceover_files[idx] = path

            for future in as_completed(image_futures):
                _, idx, path = future.result()
                self.media_paths[idx] = path

        # 步骤 4：构建剪映草稿 + FFmpeg MP4（双通道并行）
        logger.info("\n[4/4] 构建剪映草稿 + FFmpeg MP4...")
        draft_name = self.theme.replace(" ", "_")[:20] + "_auto"

        def _build_draft():
            return self.draft_builder.build(
                segments=self.segments,
                media_paths=self.media_paths,
                draft_name=draft_name,
                voiceover_files=self.voiceover_files,
            )

        def _build_mp4():
            if not self._ffmpeg_enabled or not self.ffmpeg_exporter:
                return ""
            mp4_out = str(self.output_dir / f"{draft_name}.mp4")
            try:
                return self.ffmpeg_exporter.export(
                    segments=self.segments,
                    media_paths=self.media_paths,
                    voiceover_files=self.voiceover_files,
                    output_path=mp4_out,
                )
            except Exception as e:
                logger.warning(f"FFmpeg 导出失败（不影响草稿）: {e}")
                return ""

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_draft = executor.submit(_build_draft)
            future_mp4 = executor.submit(_build_mp4)
            self.draft_path = future_draft.result()
            self.mp4_path = future_mp4.result()

        logger.info("\n" + "=" * 60)
        logger.info("生成完成！")
        logger.info(f"草稿路径: {self.draft_path}")
        if self.mp4_path:
            logger.info(f"MP4 路径: {self.mp4_path}")
        logger.info("=" * 60)

        return self.draft_path

    def run(self, style: str = "温暖感人", length: int = 300) -> str:
        """完整流程，向下兼容 main.py 和 gui.py。"""
        self.generate_script(style=style, length=length)
        return self.build_from_script()
