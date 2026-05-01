# AI 科普视频工具 - 前端 H5 设计文档

**日期**：2026-04-16  
**阶段**：阶段一（MVP）+ 阶段二（产品化改进）  
**项目目录**：`E:\yyl\ai-kepu-video-web`

---

## 一、项目概述

### 目标
为 AI 科普视频工具构建移动端优先的 H5 前端应用，支持用户输入主题、实时查看生成进度、下载剪映草稿。

### 核心流程
```
用户输入主题 → 提交任务 → 实时进度展示 → 完成后下载草稿
```

### 技术选型
- **框架**：Vue 3 + Vite
- **UI 组件库**：Vant 4（移动端优先）
- **路由**：Vue Router（Hash 模式）
- **状态管理**：组件内 ref/reactive（无全局状态库）
- **HTTP 客户端**：Axios
- **部署**：通过 Jenkins 构建部署到腾讯云 K8s

---

## 二、整体架构

### 目录结构
```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── views/
│   │   ├── CreateView.vue      # 首页：输入主题、选择参数
│   │   ├── ProcessView.vue     # 生产页：实时进度、轮询状态
│   │   └── ResultView.vue      # 完成页：草稿下载引导
│   ├── components/
│   │   ├── ProgressBar.vue     # 细粒度进度条
│   │   ├── StepCard.vue        # 步骤卡片
│   │   └── ErrorDialog.vue     # 错误弹窗
│   ├── api/
│   │   ├── request.js          # Axios 封装
│   │   └── task.js             # 任务 API
│   ├── composables/
│   │   └── usePolling.js       # 轮询 Hook
│   ├── router/
│   │   └── index.js            # 路由配置
│   ├── utils/
│   │   └── format.js           # 工具函数
│   ├── App.vue
│   └── main.js
├── .env.development
├── .env.production
├── package.json
├── vite.config.js
└── README.md
```

### 路由设计
```
/#/                    → CreateView（首页）
/#/process/:taskId     → ProcessView（生产页，带任务 ID）
/#/result/:taskId      → ResultView（完成页，带任务 ID）
```

**选择 Hash 模式的原因**：
- 无需服务端配置，部署简单
- 支持通过 URL 分享任务进度
- 适合静态资源部署

---

## 三、核心页面设计

### 1. CreateView.vue（首页）

**功能**：
- 输入视频主题（文本框）
- 选择文章风格（下拉选择：温暖感人、励志向上、科普知识、幽默轻松、深度思考）
- 选择脚本字数（数字输入，范围 100-800，默认 300）
- 提交按钮

**交互流程**：
1. 用户填写表单
2. 点击"开始生成"
3. 前端调用 `POST /api/tasks`，传递 `{theme, style, length}`
4. 后端返回 `{taskId, status: 'pending'}`
5. 前端跳转到 `/#/process/:taskId`

**UI 布局**：
- 顶部：标题 + 副标题
- 中部：表单区（主题输入框 + 风格选择器 + 字数输入）
- 底部：大按钮"开始生成"

**Vant 组件使用**：
- `van-field`（输入框）
- `van-picker` + `van-popup`（风格选择）
- `van-stepper`（字数调节）
- `van-button`（提交按钮）

**参数校验**：
- 主题为空 → "请输入视频主题"
- 字数超出范围 → "字数需在 100-800 之间"

---

### 2. ProcessView.vue（生产页）

**功能**：
- 显示当前任务进度（百分比 + 步骤名称）
- 细粒度进度条（4 大步骤，每步内部显示子进度）
- 每步耗时统计
- 失败时显示错误信息 + 重新生成按钮

**交互流程**：
1. 页面加载时从路由获取 `taskId`
2. 启动轮询（每 2 秒调用 `GET /api/tasks/:taskId`）
3. 根据返回的状态更新 UI：
   - `pending` → 显示"排队中"
   - `processing` → 显示进度条 + 当前步骤
   - `completed` → 自动跳转到 `/#/result/:taskId`
   - `failed` → 显示错误弹窗

**后端 API 返回格式**（需要后端实现）：
```json
{
  "taskId": "abc123",
  "status": "processing",
  "progress": {
    "current_step": "image_generation",
    "steps": [
      {
        "name": "text_generation",
        "status": "completed",
        "duration": 5.2
      },
      {
        "name": "voiceover_generation",
        "status": "completed",
        "progress": 6,
        "total": 6,
        "duration": 12.3
      },
      {
        "name": "image_generation",
        "status": "processing",
        "progress": 3,
        "total": 6
      },
      {
        "name": "draft_building",
        "status": "pending"
      }
    ]
  }
}
```

**进度计算逻辑**：
- 文本生成：10%
- 配音生成：10% + (完成段数 / 总段数) × 30%
- 图像生成：40% + (完成张数 / 总张数) × 30%
- 草稿构建：70% + 30%

**UI 布局**：
- 顶部：总进度百分比（大字号）
- 中部：4 个步骤卡片（显示状态图标 + 名称 + 耗时）
- 底部：进度条（Vant ProgressBar）

**Vant 组件使用**：
- `van-progress`（进度条）
- `van-steps`（步骤指示器）
- `van-loading`（加载动画）
- `van-dialog`（错误弹窗）

---

### 3. ResultView.vue（完成页）

**功能**：
- 显示任务完成状态
- 提供剪映草稿下载引导（阶段一）
- 显示生成的视频信息（主题、时长、段落数）
- 返回首页按钮

**交互流程**：
1. 页面加载时从路由获取 `taskId`
2. 调用 `GET /api/tasks/:taskId` 获取任务结果
3. 显示成功信息和草稿路径提示
4. 用户点击"返回首页"回到 CreateView

**后端 API 返回格式**：
```json
{
  "taskId": "abc123",
  "status": "completed",
  "result": {
    "draft_path": "D:/edge/JianyingPro Drafts/主题名_auto",
    "theme": "人工智能的未来",
    "segments_count": 6,
    "total_duration": 180,
    "created_at": "2026-04-16T15:30:00Z"
  }
}
```

**UI 布局**：
- 顶部：成功图标 + "生成完成"
- 中部：视频信息卡片（主题、段落数、预计时长）
- 底部：
  - 提示文字："草稿已保存到剪映，请打开剪映查看"
  - 按钮："返回首页" + "再生成一个"

**Vant 组件使用**：
- `van-result`（结果页组件）
- `van-cell-group`（信息展示）
- `van-button`（操作按钮）

---

## 四、核心组件设计

### 1. ProgressBar.vue（细粒度进度条）

**Props**：
```typescript
{
  steps: Array<Step>,      // 步骤数组
  currentStep: string      // 当前步骤名称
}
```

**功能**：
- 根据步骤状态计算总进度百分比
- 显示平滑的进度条动画
- 当前步骤高亮显示

---

### 2. StepCard.vue（步骤卡片）

**Props**：
```typescript
{
  name: string,       // 步骤名称
  status: string,     // pending | processing | completed | failed
  progress: number,   // 当前进度（如 3）
  total: number,      // 总数（如 6）
  duration: number    // 耗时（秒）
}
```

**UI 状态**：
- `pending`：灰色图标 + "等待中"
- `processing`：蓝色加载图标 + "进行中 (3/6)" + 进度条
- `completed`：绿色对勾 + "已完成" + 耗时
- `failed`：红色叉号 + "失败" + 错误信息

---

### 3. ErrorDialog.vue（错误弹窗）

**Props**：
```typescript
{
  visible: boolean,
  errorMessage: string,
  errorDetail: string,
  onRetry: Function
}
```

**功能**：
- 显示友好的错误提示
- 提供详细错误信息（可折叠）
- "重新生成"按钮（回到 CreateView）
- "关闭"按钮

---

## 五、API 层设计

### 1. api/request.js（Axios 封装）

**功能**：
- 统一配置 baseURL（从环境变量读取）
- 请求拦截器（添加 token、请求日志）
- 响应拦截器（统一错误处理、Toast 提示）
- 超时配置（默认 30 秒）

**配置**：
```javascript
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```

---

### 2. api/task.js（任务 API）

**接口定义**：

#### 创建任务
```
POST /api/tasks
Body: { theme: string, style: string, length: number }
Response: { taskId: string, status: string }
```

#### 查询任务状态
```
GET /api/tasks/:taskId
Response: {
  taskId: string,
  status: string,
  progress: object,
  result: object,
  error: string
}
```

#### 取消任务（预留）
```
DELETE /api/tasks/:taskId
Response: { success: boolean }
```

---

### 3. composables/usePolling.js（轮询 Hook）

**功能**：
- 封装轮询逻辑（每 2 秒查询一次）
- 自动停止条件（任务完成/失败）
- 错误重试机制（失败 3 次后停止）
- 组件卸载时自动清理定时器

**使用示例**：
```javascript
const { data, error, isPolling, startPolling, stopPolling } = usePolling(taskId)
```

---

### 4. utils/format.js（工具函数）

**功能**：

#### 时间格式化
- `formatDuration(seconds)` → "2分30秒"
- `formatTimestamp(iso)` → "2026-04-16 15:30"

#### 进度计算
- `calculateProgress(steps)` → 总进度百分比
- `getStepWeight(stepName)` → 步骤权重

#### 步骤名称映射
- `getStepLabel(stepName)` → 中文名称
- 例如：`text_generation` → "脚本生成"

---

## 六、错误处理策略

### 1. 网络错误
- **场景**：API 请求超时、服务器无响应
- **处理**：Toast 提示 "网络异常，请检查连接"
- **重试**：自动重试 3 次，失败后显示错误弹窗

### 2. 任务失败
- **场景**：后端返回 `status: 'failed'`
- **处理**：
  - 显示 ErrorDialog，展示失败步骤和原因
  - 提供"重新生成"按钮（保留原参数，回到 CreateView）
  - 记录错误日志（console.error）

### 3. 轮询超时
- **场景**：任务超过 10 分钟仍未完成
- **处理**：
  - 停止轮询
  - Toast 提示 "任务超时，请稍后查看"
  - 提供"查看任务"按钮（可手动刷新状态）

### 4. 参数校验
- **场景**：用户输入不合法
- **处理**：
  - 主题为空 → "请输入视频主题"
  - 字数超出范围 → "字数需在 100-800 之间"
  - 使用 Vant 的 `van-field` 内置校验

---

## 七、边界情况处理

### 1. 页面刷新
- **ProcessView**：刷新后继续轮询（从 URL 读取 taskId）
- **ResultView**：刷新后重新获取任务结果

### 2. 直接访问 URL
- **场景**：用户直接访问 `/#/process/invalid-id`
- **处理**：查询任务失败时，Toast 提示 "任务不存在"，跳转回首页

### 3. 任务已完成
- **场景**：用户访问已完成任务的 ProcessView
- **处理**：检测到 `status: 'completed'`，直接跳转到 ResultView

### 4. 并发限制（预留）
- **场景**：后端限制同时生成任务数
- **处理**：返回 429 状态码时，Toast 提示 "服务繁忙，请稍后重试"

---

## 八、性能优化

### 1. 路由懒加载
```javascript
const routes = [
  {
    path: '/',
    component: () => import('@/views/CreateView.vue')
  },
  {
    path: '/process/:taskId',
    component: () => import('@/views/ProcessView.vue')
  },
  {
    path: '/result/:taskId',
    component: () => import('@/views/ResultView.vue')
  }
]
```

### 2. Vant 按需引入
- 只引入使用的组件，减少打包体积
- 使用 `vite-plugin-style-import` 自动按需引入样式

### 3. 轮询优化
- 任务完成后立即停止轮询
- 页面不可见时（`document.hidden`）降低轮询频率（5 秒一次）
- 页面可见时恢复正常频率（2 秒一次）

### 4. 请求缓存
- 任务结果缓存 5 分钟（避免重复请求）
- 使用 `localStorage` 缓存最近的任务 ID

---

## 九、用户体验优化

### 1. 加载状态
- 所有异步操作显示 Loading（Vant `van-loading`）
- 按钮点击后禁用，防止重复提交
- 骨架屏（Skeleton）用于首次加载

### 2. 进度动画
- 进度条使用平滑过渡动画（CSS transition）
- 步骤切换时有淡入淡出效果
- 完成时播放成功动画

### 3. 反馈提示
- 操作成功：Toast 提示（2 秒自动消失）
- 操作失败：Dialog 弹窗（需要用户确认）
- 长时间等待：显示预计剩余时间

### 4. 移动端适配
- 响应式布局（适配 375px - 768px）
- 触摸友好（按钮最小 44px × 44px）
- 防止页面缩放（viewport meta）
- 安全区域适配（iPhone 刘海屏）

### 5. 离线提示
- 监听网络状态（`navigator.onLine`）
- 断网时显示提示条："网络已断开，请检查连接"
- 恢复网络时自动重试

---

## 十、可访问性（基础）

### 1. 语义化 HTML
- 使用正确的标签（`<button>` 而非 `<div onclick>`）
- 表单元素关联 `<label>`

### 2. 键盘导航
- 所有交互元素可通过 Tab 键访问
- 焦点样式清晰可见

### 3. 屏幕阅读器支持
- 重要元素添加 `aria-label`
- 进度条添加 `role="progressbar"` 和 `aria-valuenow`

---

## 十一、环境配置

### .env.development（开发环境）
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_POLLING_INTERVAL=2000
```

### .env.production（生产环境）
```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_POLLING_INTERVAL=3000
```

---

## 十二、阶段二扩展点

### 1. 实时进度优化

**智能轮询间隔**：
- 任务刚开始：1 秒一次（用户焦虑期）
- 进行中：2 秒一次
- 接近完成（>80%）：1 秒一次

**预估剩余时间**：
- 根据历史数据计算平均耗时
- 显示"预计还需 2 分钟"

**步骤耗时对比**：
- 显示"比平均速度快 20%"

### 2. 错误处理增强

**错误分类**：
- 网络错误 → "请检查网络连接"
- API 超时 → "图像生成较慢，请耐心等待"
- 参数错误 → "主题过短，请输入更详细的描述"

**部分重试**：
- 只重试失败的步骤，不重新开始整个任务
- 需要后端支持 `POST /api/tasks/:taskId/retry`

### 3. 用户反馈闭环

**新增组件：FeedbackDialog.vue**
- 任务完成后弹出满意度调查
- 5 星评分 + 文字反馈
- 提交到后端 `POST /api/feedback`
- 数据用于阶段二迭代优化

---

## 十三、代码扩展点预留

### 1. 组件插槽
```vue
<!-- StepCard.vue 预留插槽 -->
<slot name="actions"></slot>  <!-- 阶段三可以加"重新生成"按钮 -->
```

### 2. API 接口预留
```javascript
// api/task.js
export const retryTask = (taskId, step) => { /* 阶段二实现 */ }
export const cancelTask = (taskId) => { /* 阶段三实现 */ }
```

### 3. 路由守卫预留
```javascript
// router/index.js
router.beforeEach((to, from, next) => {
  // 阶段三：权限校验
  // 阶段四：批量任务跳转
  next()
})
```

---

## 十四、部署说明

### 构建命令
```bash
npm run build
```

### 部署方式
- 通过 Jenkins 构建并部署到腾讯云 K8s
- 前端独立部署，与后端服务分离
- 通过环境变量配置后端 API 地址

---

## 十五、后续阶段规划

### 阶段三：节点可控（5/1-5/14）
- 新增 `EditView.vue`（节点编辑页）
- 支持单个步骤重新生成
- 素材库管理（上传 logo、BGM）

### 阶段四：模板 + 批量（5/15-5/31）
- 新增 `TemplateView.vue`（模板中心）
- 新增 `BatchView.vue`（批量生产）
- 支持 Excel 导入主题列表

### 阶段五：生态 + 对外（6/1 起）
- API 文档页面
- 多平台直发配置
- 数据回流看板

---

## 附录：技术债务和已知限制

### 阶段一已知限制
1. **无用户认证**：所有用户共享任务列表
2. **无任务历史**：刷新页面后无法查看历史任务
3. **无取消功能**：任务提交后无法中途取消
4. **无成品视频下载**：只支持剪映草稿导出

### 技术债务
1. **轮询效率**：高并发时轮询请求量大，阶段二考虑 WebSocket
2. **状态管理**：阶段三节点编辑时可能需要引入 Pinia
3. **错误日志**：缺少前端错误监控（Sentry）

---

**文档版本**：v1.0  
**最后更新**：2026-04-16
