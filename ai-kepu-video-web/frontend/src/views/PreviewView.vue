<template>
  <div class="preview-view">
    <div class="top-bar">
      <button class="back-btn" @click="onBack">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6" /></svg>
        <span>返回</span>
      </button>
      <h2 class="bar-title">预览与编辑</h2>
      <div class="bar-actions">
        <button class="bar-btn solid" :disabled="rebuilding" @click="onRebuild">
          <van-loading v-if="rebuilding" size="14px" color="#fff" />
          <template v-else>导出视频</template>
        </button>
      </div>
    </div>

    <div class="main-content">
      <van-loading v-if="loading" size="24px" vertical>加载中...</van-loading>
      <div v-else-if="segments.length === 0" class="empty-state"><van-empty description="暂无段落数据" /></div>
      <div v-else class="segments-list">
        <segment-card
          v-for="(segment, index) in segments"
          :key="segment.id || index"
          :segment="segment"
          :index="index"
          @edit="onEditSegment"
          @regenerate-image="onRegenerateImage"
          @regenerate-audio="onRegenerateAudio"
          @upload-image="onUploadImage"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showConfirmDialog, Loading as VanLoading, Empty as VanEmpty } from 'vant'
import { getSegments, updateSegment, regenerateImage, regenerateAudio, rebuildDraft, uploadImage } from '../api/task'
import SegmentCard from '../components/SegmentCard.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId
const loading = ref(true)
const rebuilding = ref(false)
const segments = ref([])

onMounted(async () => { await loadSegments() })

async function loadSegments() {
  try { loading.value = true; segments.value = await getSegments(taskId) }
  catch (error) { console.error('[PreviewView] 加载段落失败:', error); showToast('加载段落失败') }
  finally { loading.value = false }
}

function onBack() { router.back() }

function onEditSegment(index, newText) {
  if (!newText || !newText.trim()) { showToast('文案不能为空'); return }
  updateSegment(taskId, index, { text: newText })
    .then(() => { segments.value[index].text = newText; showToast('保存成功') })
    .catch(() => { showToast('保存失败') })
}

async function onRegenerateImage(index) {
  try {
    await showConfirmDialog({ title: '确认重新生成', message: '重新生成图片需要一定时间，确认继续吗？' })
    showLoadingToast({ message: '生成中...', forbidClick: true, duration: 0 })
    const result = await regenerateImage(taskId, index)
    segments.value[index].image_url = result.image_url
    showToast('图片生成成功')
  } catch (error) { if (error !== 'cancel') showToast('图片生成失败') }
  finally { closeToast() }
}

async function onRegenerateAudio(index) {
  try {
    await showConfirmDialog({ title: '确认重新生成', message: '重新生成音频需要一定时间，确认继续吗？' })
    showLoadingToast({ message: '生成中...', forbidClick: true, duration: 0 })
    const result = await regenerateAudio(taskId, index)
    segments.value[index].audio_url = result.audio_url
    showToast('音频生成成功')
  } catch (error) { if (error !== 'cancel') showToast('音频生成失败') }
  finally { closeToast() }
}

async function onUploadImage(index, file) {
  try {
    showLoadingToast({ message: '上传中...', forbidClick: true, duration: 0 })
    const result = await uploadImage(taskId, index, file)
    segments.value[index].image_url = result.image_url
    showToast('图片上传成功')
  } catch (error) { console.error('上传图片失败:', error); showToast('图片上传失败') }
  finally { closeToast() }
}

async function onRebuild() {
  try {
    await showConfirmDialog({ title: '确认导出', message: '将根据当前编辑内容导出视频，确认继续吗？' })
    rebuilding.value = true
    showLoadingToast({ message: '导出中...', forbidClick: true, duration: 0 })
    await rebuildDraft(taskId)
    showToast('视频导出成功')
    router.push(`/result/${taskId}`)
  } catch (error) { if (error !== 'cancel') showToast('视频导出失败') }
  finally { rebuilding.value = false; closeToast() }
}
</script>

<style scoped>
.preview-view { min-height: 100vh; background: var(--color-bg); }

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 28px;
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 14px;
  cursor: pointer;
}
.back-btn:hover { color: var(--color-primary); }

.bar-title { font-size: 15px; font-weight: 600; color: var(--color-text); }

.bar-actions { display: flex; gap: 8px; }

.bar-btn {
  padding: 7px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}
.bar-btn.solid {
  background: var(--color-primary);
  color: #fff;
}
.bar-btn.solid:hover { background: var(--color-primary-hover); }
.bar-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.main-content {
  max-width: 920px;
  margin: 0 auto;
  padding: 24px 28px 40px;
}

.empty-state { padding: 60px 0; }

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
