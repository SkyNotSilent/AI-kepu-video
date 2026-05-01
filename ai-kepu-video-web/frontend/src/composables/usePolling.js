/**
 * 轮询 Hook
 * 封装轮询逻辑，自动停止、错误重试、组件卸载清理
 */

import { ref, onUnmounted } from 'vue'
import { getTaskStatus } from '../api/task'

/**
 * 使用轮询查询任务状态
 * @param {string} taskId - 任务ID
 * @param {number} interval - 轮询间隔（毫秒），默认 2000
 * @returns {Object} { data, error, isPolling, startPolling, stopPolling }
 */
export function usePolling(taskId, interval = 2000) {
  const data = ref(null)
  const error = ref(null)
  const isPolling = ref(false)

  let timerId = null
  let retryCount = 0
  const maxRetries = 3

  /**
   * 执行一次查询
   */
  const poll = async () => {
    try {
      const result = await getTaskStatus(taskId)
      data.value = result
      error.value = null
      retryCount = 0

      // 任务完成或失败时停止轮询
      if (result.status === 'completed' || result.status === 'failed') {
        stopPolling()
      }
    } catch (err) {
      console.error('[Polling Error]', err)
      retryCount++

      if (retryCount >= maxRetries) {
        error.value = '查询失败，请刷新页面重试'
        stopPolling()
      }
    }
  }

  /**
   * 开始轮询
   */
  const startPolling = () => {
    if (isPolling.value) return

    isPolling.value = true
    retryCount = 0

    // 立即执行一次
    poll()

    // 启动定时器
    timerId = setInterval(poll, interval)
  }

  /**
   * 停止轮询
   */
  const stopPolling = () => {
    if (timerId) {
      clearInterval(timerId)
      timerId = null
    }
    isPolling.value = false
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    stopPolling()
  })

  return {
    data,
    error,
    isPolling,
    startPolling,
    stopPolling
  }
}
