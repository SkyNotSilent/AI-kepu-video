/**
 * Vue Router 配置
 * History 模式 + 路由懒加载
 */

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Create',
    component: () => import('../views/CreateView.vue'),
    meta: { title: '创建视频' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '模型配置' }
  },
  {
    path: '/process/:taskId',
    name: 'Process',
    component: () => import('../views/ProcessView.vue'),
    meta: { title: '生成中' }
  },
  {
    path: '/preview/:taskId',
    name: 'Preview',
    component: () => import('../views/PreviewView.vue'),
    meta: { title: '预览与编辑' }
  },
  {
    path: '/export/:taskId',
    name: 'Export',
    component: () => import('../views/ExportView.vue'),
    meta: { title: '导出视频' }
  },
  {
    path: '/result/:taskId',
    name: 'Result',
    component: () => import('../views/ResultView.vue'),
    meta: { title: '生成完成' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - InsightCut`
  }
  next()
})

export default router
