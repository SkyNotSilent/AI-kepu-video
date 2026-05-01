/**
 * 生产页 - 实时进度展示
 */
<template>
  <div class="process-view">
    <div v-if="loading" class="loading-container">
      <van-loading size="24px" vertical>加载中...</van-loading>
    </div>

    <div v-else-if="taskData" class="layout">
      <!-- 左侧进度总览 -->
      <div class="progress-side">
        <div class="progress-content">
          <h2 class="side-title">生成中</h2>
          <p class="side-desc">AI 正在生成可编辑的视频项目</p>

          <ProgressBar
            v-if="taskData.progress"
            :steps="taskData.progress.steps"
            :current-step="taskData.progress.current_step"
          />

          <div v-if="taskData.status === 'pending'" class="pending-tip">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-placeholder)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
            </svg>
            <p>任务排队中，请稍候...</p>
          </div>
        </div>
      </div>

      <!-- 右侧步骤详情 -->
      <div class="steps-side">
        <div class="steps-content">
          <h3 class="steps-title">执行步骤</h3>
          <div v-if="taskData.progress" class="steps-list">
            <StepCard
              v-for="(step, idx) in taskData.progress.steps"
              :key="step.name"
              :name="step.name"
              :status="step.status"
              :progress="step.progress"
              :total="step.total"
              :duration="step.duration"
              :is-last="idx === taskData.progress.steps.length - 1"
            />
          </div>
        </div>
      </div>
    </div>

    <ErrorDialog v-model:visible="showError" :error-message="errorMessage" :error-detail="errorDetail" @retry="handleRetry" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading as VanLoading, showDialog } from 'vant'
import { usePolling } from '../composables/usePolling'
import ProgressBar from '../components/ProgressBar.vue'
import StepCard from '../components/StepCard.vue'
import ErrorDialog from '../components/ErrorDialog.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId
const loading = ref(true)
const showError = ref(false)
const { data: taskData, error: pollingError, startPolling } = usePolling(taskId, 2000)

const errorMessage = computed(() => {
  if (taskData.value?.error) return '生成失败，请重试'
  if (pollingError.value) return pollingError.value
  return '未知错误'
})
const errorDetail = computed(() => taskData.value?.error || '')

onMounted(() => {
  if (!taskId) { router.push('/'); return }
  startPolling()
  loading.value = false
})

watch(() => taskData.value?.status, (status) => {
  if (status === 'completed') {
    showDialog({
      title: '生成完成',
      message: '视频已生成完成，您可以进入编辑页面调整内容，或直接导出。',
      confirmButtonText: '去编辑',
      cancelButtonText: '直接导出',
      showCancelButton: true,
      confirmButtonColor: 'var(--color-primary)',
    }).then(() => {
      router.push(`/preview/${taskId}`)
    }).catch(() => {
      router.push(`/result/${taskId}`)
    })
  }
  if (status === 'failed') showError.value = true
})

const handleRetry = () => { router.push('/') }
</script>

<style scoped>
.process-view { min-height: 100vh; background: var(--color-bg); }
.loading-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.layout { display: flex; min-height: 100vh; }

.progress-side {
  width: 400px;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 44px;
}

.progress-content { width: 100%; max-width: 300px; }

.side-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
}

.side-desc {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-bottom: 36px;
}

.pending-tip {
  text-align: center;
  padding: 40px 0;
  color: var(--color-text-placeholder);
  font-size: 14px;
}
.pending-tip svg {
  margin-bottom: 12px;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.04); }
}

.steps-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  overflow-y: auto;
}

.steps-content { width: 100%; max-width: 480px; }

.steps-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 24px;
  letter-spacing: -0.2px;
}

.steps-list { display: flex; flex-direction: column; }
</style>
