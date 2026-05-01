# AI 科普视频生成 - 前端 H5

基于 Vue 3 + Vite + Vant 4 的移动端 H5 应用。

## 功能特性

- 输入视频主题、选择风格和字数
- 实时查看生成进度（4 个步骤细粒度展示）
- 完成后查看剪映草稿路径
- 移动端优先设计，响应式布局

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI 组件库**: Vant 4
- **路由**: Vue Router 4 (Hash 模式)
- **HTTP 客户端**: Axios
- **状态管理**: 组件内 ref/reactive

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 `http://localhost:3000`

### 生产构建

```bash
npm run build
```

构建产物在 `dist/` 目录。

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API 接口
│   │   ├── request.js  # Axios 封装
│   │   └── task.js     # 任务 API
│   ├── components/     # 公共组件
│   │   ├── ErrorDialog.vue
│   │   ├── ProgressBar.vue
│   │   └── StepCard.vue
│   ├── composables/    # 组合式函数
│   │   └── usePolling.js
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── utils/          # 工具函数
│   │   └── format.js
│   ├── views/          # 页面组件
│   │   ├── CreateView.vue
│   │   ├── ProcessView.vue
│   │   └── ResultView.vue
│   ├── App.vue
│   └── main.js
├── .env.development    # 开发环境变量
├── .env.production     # 生产环境变量
├── index.html
├── package.json
└── vite.config.js
```

## 路由

- `/#/` - 首页（创建任务）
- `/#/process/:taskId` - 生产页（实时进度）
- `/#/result/:taskId` - 完成页（结果展示）

## 环境变量

### 开发环境 (`.env.development`)

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_POLLING_INTERVAL=2000
```

### 生产环境 (`.env.production`)

```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_POLLING_INTERVAL=3000
```

## API 接口

### 创建任务

```javascript
POST /api/tasks
{
  "theme": "人工智能的未来",
  "style": "深度思考",
  "length": 500
}
```

### 查询任务状态

```javascript
GET /api/tasks/{taskId}
```

## 部署

通过 Jenkins 构建并部署到腾讯云 K8s。

构建命令：
```bash
npm run build
```

## 开发说明

- 使用 Composition API 编写组件
- 组件内使用 ref/reactive 管理状态
- 使用 Vant 组件库，按需引入
- 遵循移动端设计规范（最小点击区域 44px）

