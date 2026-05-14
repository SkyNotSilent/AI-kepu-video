# InsightCut Apple 设计改造指南

## 乔布斯设计哲学核心

> "Simplicity is the ultimate sophistication."  
> — Steve Jobs

### 三大原则
1. **极简主义** - 删除一切不必要的元素
2. **功能优先** - 美观服务于功能，不是装饰
3. **细节完美** - 每个像素都有意义

---

## 改造前后对比

### 当前设计问题
❌ 配色过于鲜艳（蓝色 `#2563eb`）  
❌ 边框太多，视觉噪音大  
❌ 阴影太浅，缺乏层次感  
❌ 字体大小不统一  
❌ 留白不足，显得拥挤  

### Apple 风格特征
✅ 黑白灰为主，蓝色仅用于交互  
✅ 极简边框，甚至无边框  
✅ 柔和深阴影，营造浮动感  
✅ 严格的字体层级系统  
✅ 大量留白，呼吸感强  

---

## 实施步骤

### 第 1 步：替换全局样式

**文件**: `ai-kepu-video-web/frontend/src/App.vue`

**当前代码** (第 13-41 行):
```css
:root {
  --color-primary: #2563eb;  /* 太鲜艳 */
  --color-bg: #f2f3f5;       /* 灰色太重 */
  --shadow-sm: 0 4px 12px rgba(29, 33, 41, 0.06);  /* 阴影太浅 */
  --radius-lg: 12px;         /* 圆角太小 */
}
```

**改为 Apple 风格**:
```css
:root {
  /* 主色：纯黑 */
  --color-primary: #000000;
  --color-primary-hover: #1d1d1f;
  
  /* 强调色：Apple 蓝（仅用于链接和按钮） */
  --color-accent: #0071e3;
  --color-accent-hover: #0077ed;
  
  /* 背景：纯白 */
  --color-bg: #ffffff;
  --color-bg-secondary: #f5f5f7;
  --color-card: #ffffff;
  
  /* 文字：层次分明 */
  --color-text: #1d1d1f;
  --color-text-secondary: #6e6e73;
  --color-text-tertiary: #86868b;
  
  /* 边框：几乎不可见 */
  --color-border: #d2d2d7;
  
  /* 阴影：柔和深邃 */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.16);
  --shadow-xl: 0 16px 64px rgba(0, 0, 0, 0.20);
  
  /* 圆角：大而柔和 */
  --radius-lg: 18px;
  --radius-xl: 24px;
  --radius-2xl: 32px;
  
  /* 字体：SF Pro */
  --font-display: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'PingFang SC', sans-serif;
  --font-text: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
}
```

---

### 第 2 步：改造按钮样式

**文件**: `ai-kepu-video-web/frontend/src/views/CreateView.vue`

**当前按钮** (约 1082-1090 行):
```css
.primary-btn {
  background: var(--color-dark);
  border-color: var(--color-dark);
  color: #fff;
}
```

**改为 Apple 风格**:
```css
.primary-btn {
  background: #000000;
  border: none;
  border-radius: 980px;  /* 完全圆角（胶囊形） */
  padding: 14px 28px;
  font-size: 17px;
  font-weight: 400;
  color: #ffffff;
  letter-spacing: -0.022em;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.primary-btn:hover {
  background: #1d1d1f;
  transform: scale(1.02);
}

.primary-btn:active {
  transform: scale(0.98);
}
```

**次要按钮**:
```css
.secondary-btn {
  background: transparent;
  border: 1px solid #000000;
  border-radius: 980px;
  padding: 14px 28px;
  font-size: 17px;
  font-weight: 400;
  color: #000000;
  letter-spacing: -0.022em;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.secondary-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}
```

---

### 第 3 步：改造卡片样式

**文件**: `ai-kepu-video-web/frontend/src/views/PreviewView.vue`

**当前卡片** (约 1123-1127 行):
```css
.preview-panel {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
```

**改为 Apple 风格**:
```css
.preview-panel {
  background: #ffffff;
  border: none;  /* 移除边框 */
  border-radius: 24px;  /* 更大圆角 */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);  /* 更深阴影 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.preview-panel:hover {
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.16);
  transform: translateY(-4px);  /* 悬浮效果 */
}
```

---

### 第 4 步：改造标题排版

**文件**: `ai-kepu-video-web/frontend/src/views/CreateView.vue`

**当前标题** (约 13 行):
```html
<h1>创建认知科普视频</h1>
```

**改为 Apple 风格**:
```html
<div class="hero-eyebrow">全新 InsightCut</div>
<h1 class="hero-title">创作，从未如此简单。</h1>
<p class="hero-subtitle">AI 驱动的认知科普视频生成工具</p>
```

**CSS**:
```css
.hero-eyebrow {
  font-size: 21px;
  line-height: 1.381;
  font-weight: 600;
  letter-spacing: 0.011em;
  color: #0071e3;  /* Apple 蓝 */
  margin-bottom: 12px;
}

.hero-title {
  font-size: 80px;
  line-height: 1.05;
  font-weight: 700;
  letter-spacing: -0.015em;
  color: #1d1d1f;
  margin-bottom: 24px;
}

.hero-subtitle {
  font-size: 28px;
  line-height: 1.14286;
  font-weight: 400;
  letter-spacing: 0.007em;
  color: #6e6e73;
  margin-bottom: 48px;
}

/* 响应式 */
@media (max-width: 734px) {
  .hero-title {
    font-size: 40px;
  }
  
  .hero-subtitle {
    font-size: 19px;
  }
}
```

---

### 第 5 步：增加留白

**关键改动**:
```css
/* 增加容器内边距 */
.panel-head {
  padding: 48px 32px;  /* 原来可能是 24px 16px */
}

/* 增加元素间距 */
.form-field + .form-field {
  margin-top: 32px;  /* 原来可能是 16px */
}

/* 增加区块间距 */
.section {
  padding: 96px 0;  /* 原来可能是 48px 0 */
}
```

---

### 第 6 步：简化边框

**全局搜索替换**:
```css
/* 删除或淡化边框 */
border: 1px solid var(--color-border);  /* 删除 */

/* 或者改为极淡 */
border: 1px solid rgba(0, 0, 0, 0.06);
```

**用阴影代替边框**:
```css
/* 原来 */
.card {
  border: 1px solid #e5e6eb;
}

/* 改为 */
.card {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
```

---

## 关键设计细节

### 1. 字体层级（严格遵守）

| 用途 | 字号 | 行高 | 字重 | 字间距 |
|------|------|------|------|--------|
| 超大标题 | 80px | 1.05 | 700 | -0.015em |
| 大标题 | 56px | 1.07 | 600 | -0.005em |
| 标题 1 | 48px | 1.08 | 600 | -0.003em |
| 标题 2 | 40px | 1.1 | 600 | 0 |
| 标题 3 | 32px | 1.125 | 600 | 0.004em |
| 正文大 | 21px | 1.381 | 400 | 0.011em |
| 正文 | 17px | 1.47 | 400 | -0.022em |
| 正文小 | 14px | 1.43 | 400 | -0.016em |

### 2. 间距系统（8px 基准）

```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;
--space-3xl: 64px;
--space-4xl: 96px;
```

### 3. 动画曲线

```css
/* Apple 标准缓动 */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);

/* 使用示例 */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

### 4. 悬停效果

```css
/* 轻微放大 + 阴影加深 */
.card:hover {
  transform: translateY(-4px) scale(1.01);
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.16);
}

/* 按钮轻微放大 */
.btn:hover {
  transform: scale(1.02);
}

/* 按下缩小 */
.btn:active {
  transform: scale(0.98);
}
```

---

## 快速实施清单

### 阶段 1：全局样式（30 分钟）
- [ ] 替换 `App.vue` 中的 CSS 变量
- [ ] 修改字体为 `-apple-system`
- [ ] 调整全局背景色为纯白

### 阶段 2：组件改造（2 小时）
- [ ] 改造所有按钮样式（胶囊形 + 黑色）
- [ ] 移除卡片边框，增加阴影
- [ ] 增大圆角（18px → 24px）
- [ ] 增加悬停动画

### 阶段 3：排版优化（1 小时）
- [ ] 调整标题字号（参考字体层级表）
- [ ] 增加行高和字间距
- [ ] 统一颜色（黑/灰/蓝）

### 阶段 4：留白调整（1 小时）
- [ ] 增加容器内边距（24px → 48px）
- [ ] 增加元素间距（16px → 32px）
- [ ] 增加区块间距（48px → 96px）

### 阶段 5：细节打磨（1 小时）
- [ ] 添加微动画
- [ ] 优化响应式断点
- [ ] 测试所有交互状态

---

## 参考资源

### Apple 官方设计资源
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [SF Pro 字体](https://developer.apple.com/fonts/)
- [Apple Design Resources](https://developer.apple.com/design/resources/)

### 灵感来源
- [Apple.com](https://www.apple.com/) - 官网设计
- [Apple Music](https://music.apple.com/) - 卡片设计
- [macOS Big Sur](https://www.apple.com/macos/) - 圆角和阴影

---

## 预期效果

### 改造前
- 🔵 蓝色为主，视觉疲劳
- 📦 边框太多，显得拥挤
- 📏 留白不足，信息密集
- 🎨 风格普通，缺乏辨识度

### 改造后
- ⚫ 黑白灰为主，优雅高级
- ✨ 无边框设计，简洁清爽
- 🌬️ 大量留白，呼吸感强
- 🍎 Apple 风格，辨识度高

---

## 下一步

想要我帮你实施吗？我可以：

1. **一键替换** - 直接修改 `App.vue` 全局样式
2. **逐步改造** - 先改一个页面（如 CreateView）看效果
3. **创建主题切换** - 保留原样式，新增 Apple 主题选项

选一个，我立即开始！🚀
