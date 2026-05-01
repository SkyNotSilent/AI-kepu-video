"""
字幕动画调度器
实现随机但克制的动画 + 独立音效文件配对逻辑

设计原则:
- 大部分段落用轻量动画（滑动、渐显），保持干净
- 每隔5-8段出现一次打字机动画，配真实打字机音效文件
- 每隔9-13段出现一次强调动画（弹入/甩出），配砰声音效
- 连续相同动画不超过2次
- 所有动画时长放慢（打字机3倍，其余1.5倍），让效果看得见
"""

import random
from dataclasses import dataclass, field
from typing import Optional, Tuple

from pyJianYingDraft.metadata.text_intro import TextIntro
from pyJianYingDraft.metadata.text_loop import TextLoopAnim


# 音效文件标识（对应 assets/sfx/ 下的文件名）
SFX_TYPEWRITER = "typewriter"   # 打字机哒哒声（30s 循环）
SFX_SWOOSH     = "swoosh"       # 滑入嗖声
SFX_POP        = "pop"          # 弹出砰声
SFX_NONE       = None


@dataclass
class AnimationPlan:
    """一段字幕的动画方案"""
    intro: Optional[TextIntro]      # 入场动画
    loop: Optional[TextLoopAnim]    # 循环动画（None = 不加）
    sfx: Optional[str]              # 音效文件标识（None = 不加）
    intro_duration: Optional[int]   # 入场时长（微秒），None = 使用默认×倍速


# ── 动画分组 ──────────────────────────────────────────────────────────────────

# 常规轻量动画（大多数段落）
NORMAL_ANIMS = [
    TextIntro.向上滑动,
    TextIntro.向左滑动,
    TextIntro.向右缓入,
    TextIntro.渐显,
    TextIntro.向下滑动,
    TextIntro.轻微放大,
    TextIntro.向右滑动,
    TextIntro.向左露出,
]

# 打字机类（配打字声）— 故障打字机已移除
TYPEWRITER_ANIMS = [
    TextIntro.打字机_I,
    TextIntro.打字机_II,
    TextIntro.打字机_III,
    TextIntro.复古打字机,
    TextIntro.居中打字,
]

# 强调类（配砰声）
EMPHASIS_ANIMS = [
    TextIntro.弹入,
    TextIntro.甩出,
    TextIntro.随机弹跳,
    TextIntro.向上重叠,
    TextIntro.向右集合,
    TextIntro.逐字旋转,
]

# 循环动画（轻微，偶尔附加）— 颤抖已移除
LOOP_SUBTLE = [
    TextLoopAnim.轻微跳动,
    TextLoopAnim.晃动,
]

# ── 速度倍率 ──────────────────────────────────────────────────────────────────
# 打字机慢 3 倍，让字一个个出现的过程看得见
TYPEWRITER_SPEED = 3.0
# 常规动画慢 1.5 倍，不那么闪
NORMAL_SPEED = 1.5
# 强调动画原速（快感强）
EMPHASIS_SPEED = 1.0


class AnimationScheduler:
    """字幕动画调度器，给每个字幕段落分配动画方案"""

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._last_intro: Optional[TextIntro] = None
        self._last_intro_repeat = 0

    def schedule(self, segments: list) -> list:
        n = len(segments)

        typewriter_pos = self._pick_positions(n, interval=(5, 8), max_count=max(1, n // 5))
        emphasis_pos   = self._pick_positions(n, interval=(9, 13), max_count=max(0, n // 10),
                                               exclude=typewriter_pos)

        plans = []
        for i in range(n):
            if i in emphasis_pos:
                plans.append(self._emphasis_plan())
            elif i in typewriter_pos:
                plans.append(self._typewriter_plan())
            else:
                plans.append(self._normal_plan())
        return plans

    # ── 方案生成 ──────────────────────────────────────────────────────────────

    def _normal_plan(self) -> AnimationPlan:
        intro = self._pick_non_repeat(NORMAL_ANIMS)
        # 25% 纯渐显，最克制
        if self.rng.random() < 0.25:
            intro = TextIntro.渐显
        # 普通动画配滑入音效（但仅30%概率，不过度）
        sfx = SFX_SWOOSH if (intro in (TextIntro.向左滑动, TextIntro.向右缓入, TextIntro.向右滑动)
                              and self.rng.random() < 0.30) else SFX_NONE
        duration = self._slow_duration(intro, NORMAL_SPEED)
        return AnimationPlan(intro=intro, loop=None, sfx=sfx, intro_duration=duration)

    def _typewriter_plan(self) -> AnimationPlan:
        intro = self.rng.choice(TYPEWRITER_ANIMS)
        # 循环动画 35% 概率附加
        loop = self.rng.choice(LOOP_SUBTLE) if self.rng.random() < 0.35 else None
        duration = self._slow_duration(intro, TYPEWRITER_SPEED)
        return AnimationPlan(intro=intro, loop=loop, sfx=SFX_TYPEWRITER, intro_duration=duration)

    def _emphasis_plan(self) -> AnimationPlan:
        intro = self.rng.choice(EMPHASIS_ANIMS)
        loop = self.rng.choice(LOOP_SUBTLE) if self.rng.random() < 0.45 else None
        duration = self._slow_duration(intro, EMPHASIS_SPEED)
        return AnimationPlan(intro=intro, loop=loop, sfx=SFX_POP, intro_duration=duration)

    # ── 工具 ──────────────────────────────────────────────────────────────────

    def _slow_duration(self, intro: TextIntro, multiplier: float) -> int:
        """返回放慢后的入场时长（微秒）"""
        return int(intro.value.duration * multiplier)

    def _pick_non_repeat(self, pool: list) -> TextIntro:
        candidates = pool[:]
        if self._last_intro_repeat >= 2 and self._last_intro in candidates:
            candidates = [a for a in candidates if a != self._last_intro]
        chosen = self.rng.choice(candidates)
        if chosen == self._last_intro:
            self._last_intro_repeat += 1
        else:
            self._last_intro = chosen
            self._last_intro_repeat = 1
        return chosen

    def _pick_positions(self, n: int, interval: Tuple[int, int],
                        max_count: int, exclude: set = None) -> set:
        exclude = exclude or set()
        positions = set()
        i = self.rng.randint(*interval)
        while i < n and len(positions) < max_count:
            if i not in exclude:
                positions.add(i)
            i += self.rng.randint(*interval)
        return positions


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    segments = [f"第{i+1}段" for i in range(15)]
    scheduler = AnimationScheduler(seed=42)
    plans = scheduler.schedule(segments)
    for i, p in enumerate(plans):
        print(f"[{i+1:02d}] 入场={p.intro.name if p.intro else '无':<14} "
              f"循环={p.loop.name if p.loop else '无':<8} "
              f"音效={p.sfx or '无':<12} "
              f"时长={p.intro_duration//1000 if p.intro_duration else 0}ms")
