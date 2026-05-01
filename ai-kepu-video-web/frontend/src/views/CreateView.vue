/**
 * 首页 - 创建任务 + 资产库
 */
<template>
  <div class="create-view">
    <div class="top-nav">
      <div class="nav-left">
        <div class="nav-logo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" /></svg>
        </div>
        <span class="nav-brand">InsightCut</span>
      </div>
      <div class="nav-tabs">
        <button class="nav-tab" :class="{ active: activeTab === 'create' }" @click="activeTab = 'create'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          首页
        </button>
        <button class="nav-tab" :class="{ active: activeTab === 'library' }" @click="switchToLibrary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          资产记录
        </button>
        <button class="nav-tab" @click="router.push('/settings')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/></svg>
          模型配置
        </button>
      </div>
      <div class="nav-right"></div>
    </div>

    <div v-if="activeTab === 'create'" class="create-layout">
      <main class="workspace-panel">
        <div class="workspace-header">
          <div>
            <div class="hero-kicker">Cognitive Video Studio</div>
            <h1>创建认知科普视频</h1>
          </div>
          <div class="workflow-strip">
            <span>脚本</span>
            <span>分镜</span>
            <span>配音</span>
            <span>草稿</span>
            <span>MP4</span>
          </div>
          <button class="settings-link" @click="router.push('/settings')">模型配置</button>
        </div>

        <div class="workspace-grid">
          <section class="form-card primary-card">
            <div class="section-head compact-head">
              <label class="editor-label">基础内容</label>
              <span class="hint-text">{{ form.theme.length }}/2000</span>
            </div>

            <div class="title-row">
              <input v-model="form.name" class="name-input" placeholder="项目名称" maxlength="100" />
            </div>

            <div class="theme-area">
              <textarea
                v-model="form.theme"
                class="theme-textarea"
                placeholder="输入视频主题，或直接粘贴您的剧本文案..."
                maxlength="2000"
                rows="7"
              ></textarea>
            </div>

            <div class="section-head style-head">
              <label class="editor-label">创作风格</label>
              <button class="text-link" @click="openCustomTextStyle">添加</button>
            </div>
            <div class="chip-group">
              <button
                v-for="opt in allStyleOptions"
                :key="opt.value"
                type="button"
                class="chip"
                :class="{ active: form.style === opt.value }"
                @click="form.style = opt.value"
              >
                <span>{{ opt.text }}</span>
                <span v-if="opt.custom" class="chip-remove" @click.stop="removeCustomTextStyle(opt.value)">×</span>
              </button>
              <button type="button" class="chip add-chip" @click="openCustomTextStyle">+ 自定义</button>
            </div>
            <div v-if="showCustomTextStyle" class="custom-inline">
              <input v-model.trim="customTextStyleName" class="inline-input" placeholder="例如：学术严谨" @keyup.enter="addCustomTextStyle" />
              <button class="inline-primary" @click="addCustomTextStyle">添加</button>
              <button class="inline-secondary" @click="showCustomTextStyle = false">取消</button>
            </div>
          </section>

          <aside class="form-card config-card">
            <section class="config-block">
              <div class="section-head compact-head">
                <label class="editor-label">画面风格</label>
                <button class="text-link" @click="openCustomVisualStyle">添加</button>
              </div>
              <div class="style-grid">
                <button
                  v-for="opt in allVisualStyleOptions"
                  :key="opt.value"
                  type="button"
                  class="style-card"
                  :class="{ active: form.visual_style === opt.value }"
                  @click="form.visual_style = opt.value"
                >
                  <img v-if="opt.image" :src="opt.image" :alt="opt.text" class="style-img" />
                  <div v-else class="style-placeholder">{{ opt.text.slice(0, 2) }}</div>
                  <span class="style-name">{{ opt.text }}</span>
                  <span v-if="opt.custom" class="style-remove" @click.stop="removeCustomVisualStyle(opt.value)">×</span>
                </button>
                <button type="button" class="style-card add-style-card" @click="openCustomVisualStyle">
                  <span class="add-style-icon">+</span>
                  <span class="style-name">自定义</span>
                </button>
              </div>
              <div v-if="showCustomVisualStyle" class="custom-visual-panel">
                <div class="custom-fields">
                  <input v-model.trim="customVisualForm.name" class="inline-input" placeholder="风格名称，例如：赛博朋克" />
                  <textarea v-model.trim="customVisualForm.prompt" class="prompt-input" placeholder="英文 prompt 后缀，例如：cyberpunk, neon lights, futuristic city"></textarea>
                  <label class="upload-line">
                    <span>预览图</span>
                    <input type="file" accept="image/*" @change="onCustomVisualImageChange" />
                  </label>
                </div>
                <div class="custom-preview">
                  <img v-if="customVisualForm.image" :src="customVisualForm.image" alt="自定义预览" />
                  <span v-else>Preview</span>
                </div>
                <div class="custom-actions">
                  <button class="inline-primary" @click="addCustomVisualStyle">添加</button>
                  <button class="inline-secondary" @click="showCustomVisualStyle = false">取消</button>
                </div>
              </div>
            </section>

            <section class="config-block control-grid">
              <div class="row-item">
                <label class="editor-label">配音音色</label>
                <button class="voice-picker" @click="showVoicePicker = true">
                  <span class="voice-name">{{ form.voice_name || '选择音色' }}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9" /></svg>
                </button>
              </div>
              <div v-if="form.theme.trim().length <= 200" class="row-item">
                <label class="editor-label">脚本字数</label>
                <div class="length-control">
                  <input type="range" v-model.number="form.length" :min="50" :max="2000" :step="50" class="length-slider" />
                  <div class="length-labels">
                    <span>50</span>
                    <span class="length-value">{{ form.length }} 字</span>
                    <span>2000</span>
                  </div>
                </div>
              </div>
            </section>

            <div class="editor-actions">
              <button class="generate-btn" :disabled="loading || !form.theme.trim() || !form.name.trim()" @click="handleSubmit">
                <van-loading v-if="loading" size="18px" color="#fff" />
                <template v-else>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                  生成视频
                </template>
              </button>
            </div>
          </aside>
        </div>
      </main>
    </div>

    <div v-if="activeTab === 'library'" class="library-panel">
      <div class="library-content">
        <div class="library-header">
          <h2 class="library-title">资产记录</h2>
          <button class="create-btn" @click="activeTab = 'create'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            创建新视频
          </button>
        </div>

        <van-loading v-if="libraryLoading" size="24px" vertical style="padding:60px 0;">加载中...</van-loading>

        <div v-else-if="tasks.length === 0" class="empty-library">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-placeholder)" stroke-width="1.5">
            <rect x="2" y="3" width="20" height="18" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="18" x2="12" y2="21"/>
          </svg>
          <p>暂无生成记录</p>
          <button class="empty-btn" @click="activeTab = 'create'">创建第一个视频</button>
        </div>

        <div v-else class="task-grid">
          <div v-for="task in tasks" :key="task.task_id" class="task-card" @click="onTaskClick(task)">
            <div class="task-card-header">
              <span class="task-name">{{ task.name || task.theme }}</span>
              <span class="task-status" :class="'status-' + task.status">{{ statusLabel(task.status) }}</span>
            </div>
            <div class="task-theme">{{ task.theme }}</div>
            <div class="task-meta">
              <span v-if="task.segments_count">{{ task.segments_count }} 段</span>
              <span>{{ formatTimestamp(task.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <van-popup v-model:show="showVoicePicker" position="bottom" round>
      <van-picker :columns="voiceOptions" @confirm="onVoiceConfirm" @cancel="showVoicePicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Popup as VanPopup, Picker as VanPicker, Loading as VanLoading, showToast } from 'vant'
import { createTask, getVoices, listTasks } from '../api/task'
import { formatTimestamp } from '../utils/format'

const router = useRouter()
const route = useRoute()
const activeTab = ref('create')
const form = ref({ name: '', theme: '', style: '温暖感人', length: 300, visual_style: '电影质感', voice_type: '', voice_name: '米仔' })
const loading = ref(false)
const showVoicePicker = ref(false)
const voiceOptions = ref([])
const voiceMap = ref({})
const tasks = ref([])
const libraryLoading = ref(false)
const showCustomTextStyle = ref(false)
const showCustomVisualStyle = ref(false)
const customTextStyleName = ref('')
const customVisualForm = ref({ name: '', prompt: '', image: '' })
const customTextStyles = ref([])
const customVisualStyles = ref([])

const TEXT_STYLE_STORAGE_KEY = 'kepu_custom_text_styles'
const VISUAL_STYLE_STORAGE_KEY = 'kepu_custom_visual_styles'

const defaultStyleOptions = [
  { text: '温暖感人', value: '温暖感人' },
  { text: '励志向上', value: '励志向上' },
  { text: '科普知识', value: '科普知识' },
  { text: '幽默轻松', value: '幽默轻松' },
  { text: '深度思考', value: '深度思考' },
]

const defaultVisualStyleOptions = [
  { text: '电影质感', value: '电影质感', image: '/styles/电影质感.jpg' },
  { text: '吉卜力', value: '吉卜力', image: '/styles/吉卜力.webp' },
  { text: '3D动画', value: '3D动画', image: '/styles/3D动画.webp' },
  { text: '毛毡风', value: '毛毡风', image: '/styles/毛毡风格.webp' },
  { text: '油彩画', value: '油彩画', image: '/styles/油彩画.jpg' },
  { text: '国风', value: '国风', image: '/styles/国风.webp' },
]

const allStyleOptions = computed(() => [...defaultStyleOptions, ...customTextStyles.value])
const allVisualStyleOptions = computed(() => [...defaultVisualStyleOptions, ...customVisualStyles.value])

onMounted(async () => {
  loadCustomOptions()
  if (route.query.tab === 'library') {
    activeTab.value = 'library'
    loadTasks()
  }

  try {
    const voices = await getVoices()
    voiceOptions.value = voices.map(v => ({ text: `${v.name} (${v.gender === 'female' ? '女' : '男'})`, value: v.id, description: v.description }))
    voiceMap.value = voices.reduce((map, v) => { map[v.id] = v.name; return map }, {})
    if (voices.length > 0) {
      const defaultVoice = voices.find(v => v.name === '米仔') || voices[0]
      form.value.voice_type = defaultVoice.id
      form.value.voice_name = defaultVoice.name
    }
  } catch (error) {
    console.error('加载音色列表失败:', error)
    showToast('加载音色列表失败')
  }
})

function loadCustomOptions() {
  try {
    customTextStyles.value = JSON.parse(localStorage.getItem(TEXT_STYLE_STORAGE_KEY) || '[]')
    customVisualStyles.value = JSON.parse(localStorage.getItem(VISUAL_STYLE_STORAGE_KEY) || '[]')
  } catch (error) {
    console.error('读取自定义风格失败:', error)
    customTextStyles.value = []
    customVisualStyles.value = []
  }
}

function saveCustomTextStyles() {
  localStorage.setItem(TEXT_STYLE_STORAGE_KEY, JSON.stringify(customTextStyles.value))
}

function saveCustomVisualStyles() {
  localStorage.setItem(VISUAL_STYLE_STORAGE_KEY, JSON.stringify(customVisualStyles.value))
}

function openCustomTextStyle() {
  customTextStyleName.value = ''
  showCustomTextStyle.value = true
}

function addCustomTextStyle() {
  const name = customTextStyleName.value.trim()
  if (!name) { showToast('请输入创作风格名称'); return }
  if (allStyleOptions.value.some(opt => opt.value === name)) { showToast('该风格已存在'); return }
  customTextStyles.value.push({ text: name, value: name, custom: true })
  saveCustomTextStyles()
  form.value.style = name
  showCustomTextStyle.value = false
}

function removeCustomTextStyle(value) {
  customTextStyles.value = customTextStyles.value.filter(opt => opt.value !== value)
  saveCustomTextStyles()
  if (form.value.style === value) form.value.style = defaultStyleOptions[0].value
}

function openCustomVisualStyle() {
  customVisualForm.value = { name: '', prompt: '', image: '' }
  showCustomVisualStyle.value = true
}

function onCustomVisualImageChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (file.size > 800 * 1024) {
    showToast('预览图请控制在 800KB 内')
    event.target.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => { customVisualForm.value.image = reader.result }
  reader.readAsDataURL(file)
}

function addCustomVisualStyle() {
  const name = customVisualForm.value.name.trim()
  const prompt = customVisualForm.value.prompt.trim()
  if (!name) { showToast('请输入画面风格名称'); return }
  if (!prompt) { showToast('请输入英文 prompt 后缀'); return }
  if (allVisualStyleOptions.value.some(opt => opt.text === name)) { showToast('该画面风格已存在'); return }

  const value = `custom-${Date.now()}`
  customVisualStyles.value.push({
    text: name,
    value,
    image: customVisualForm.value.image,
    prompt,
    custom: true,
  })
  saveCustomVisualStyles()
  form.value.visual_style = value
  showCustomVisualStyle.value = false
}

function removeCustomVisualStyle(value) {
  customVisualStyles.value = customVisualStyles.value.filter(opt => opt.value !== value)
  saveCustomVisualStyles()
  if (form.value.visual_style === value) form.value.visual_style = defaultVisualStyleOptions[0].value
}

const onVoiceConfirm = ({ selectedOptions }) => {
  form.value.voice_type = selectedOptions[0].value
  form.value.voice_name = voiceMap.value[selectedOptions[0].value]
  showVoicePicker.value = false
}

const handleSubmit = async () => {
  if (!form.value.name.trim()) { showToast('请输入项目名称'); return }
  if (!form.value.theme.trim()) { showToast('请输入视频主题'); return }

  const selectedVisual = allVisualStyleOptions.value.find(opt => opt.value === form.value.visual_style) || defaultVisualStyleOptions[0]
  const visualStyleName = selectedVisual.text || selectedVisual.value
  const visualPromptSuffix = selectedVisual.prompt || ''
  const stylePayload = visualPromptSuffix
    ? `${form.value.style}|${visualStyleName}|${visualPromptSuffix}`
    : `${form.value.style}|${visualStyleName}`

  loading.value = true
  try {
    const response = await createTask({
      name: form.value.name.trim(),
      theme: form.value.theme.trim(),
      style: stylePayload,
      length: form.value.length,
      voice_type: form.value.voice_type || undefined,
    })
    showToast({ message: '任务创建成功', duration: 1500 })
    setTimeout(() => { router.push(`/process/${response.task_id}`) }, 1500)
  } catch (error) {
    console.error('创建任务失败:', error)
    showToast('创建任务失败，请重试')
  } finally {
    loading.value = false
  }
}

async function switchToLibrary() {
  activeTab.value = 'library'
  await loadTasks()
}

async function loadTasks() {
  libraryLoading.value = true
  try {
    tasks.value = await listTasks(null, 50, 0)
  } catch (error) {
    console.error('加载资产列表失败:', error)
    showToast('加载资产列表失败')
  } finally {
    libraryLoading.value = false
  }
}

function statusLabel(status) {
  const map = { pending: '排队中', processing: '生成中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

function onTaskClick(task) {
  if (task.status === 'completed') router.push(`/result/${task.task_id}`)
  else if (task.status === 'processing' || task.status === 'pending') router.push(`/process/${task.task_id}`)
  else showToast('该任务已失败，请创建新任务')
}
</script>

<style scoped>
.create-view { height: 100vh; background: var(--color-bg); display: flex; flex-direction: column; overflow: hidden; }
.top-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 52px; background: var(--color-card);
  border-bottom: 1px solid var(--color-border); flex-shrink: 0;
  position: relative; z-index: 10;
}
.nav-left { display: flex; align-items: center; gap: 10px; }
.nav-logo {
  width: 32px; height: 32px; background: var(--color-primary); color: #fff;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
}
.nav-brand { font-size: 15px; font-weight: 700; color: var(--color-text); }
.nav-tabs { display: flex; gap: 4px; }
.nav-tab {
  display: flex; align-items: center; gap: 6px; padding: 7px 16px;
  border-radius: 6px; font-size: 13px; font-weight: 500;
  color: var(--color-text-tertiary); background: none; border: none;
  cursor: pointer; transition: all 0.15s;
}
.nav-tab:hover { color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.nav-tab.active { color: var(--color-primary); background: var(--color-primary-bg); font-weight: 600; }
.nav-right { width: 120px; }

.create-layout { flex: 1; min-height: 0; overflow: hidden; padding: 18px 24px 22px; }
.workspace-panel {
  height: 100%;
  width: min(1280px, 100%);
  margin: 0 auto;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 14px;
}
.workspace-header {
  min-height: 54px;
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto auto;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-xs);
}
.hero-kicker {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-primary);
  font-weight: 800;
  margin-bottom: 3px;
}
.workspace-header h1 { font-size: 20px; line-height: 1.15; color: var(--color-text); }
.workflow-strip { display: flex; gap: 6px; align-items: center; }
.workflow-strip span {
  height: 26px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  border-radius: 6px;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 700;
}
.workspace-grid {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(360px, 0.82fr);
  gap: 14px;
}
.form-card {
  min-height: 0;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-xs);
  padding: 14px;
}
.primary-card { display: grid; grid-template-rows: auto auto minmax(210px, 1fr) auto auto auto; gap: 10px; }
.config-card { display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
.config-block { min-width: 0; }
.config-card .config-block:first-child {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.compact-head { margin-bottom: 8px; }
.style-head { margin-top: 4px; margin-bottom: 8px; }
.hint-text { font-size: 12px; color: var(--color-text-placeholder); font-weight: 600; }
.settings-link, .text-link {
  border: none; background: transparent; color: var(--color-primary);
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.settings-link {
  height: 32px; padding: 0 12px; border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); background: var(--color-card);
}
.form-section { margin-bottom: 18px; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.editor-label {
  display: block; font-size: 13px; font-weight: 600;
  color: var(--color-text-tertiary); margin-bottom: 8px;
}
.section-head .editor-label { margin-bottom: 0; }
.name-input, .inline-input {
  width: 100%; height: 40px; padding: 0 12px; font-size: 14px;
  color: var(--color-text); border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); background: var(--color-card);
  outline: none; font-family: inherit; transition: border-color 0.15s, box-shadow 0.15s;
}
.name-input:focus, .inline-input:focus, .prompt-input:focus {
  border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-bg);
}
.theme-area {
  position: relative; background: var(--color-card); border-radius: var(--radius-sm);
  border: 1px solid var(--color-border); transition: border-color 0.15s, box-shadow 0.15s;
}
.primary-card .theme-area { min-height: 0; }
.theme-area:focus-within { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-bg); }
.theme-textarea {
  width: 100%; height: 100%; padding: 14px 16px 28px; font-size: 15px; line-height: 1.65;
  color: var(--color-text); border: none; background: transparent;
  border-radius: var(--radius-sm); resize: none; outline: none; font-family: inherit;
  min-height: 220px;
}
.char-count { position: absolute; bottom: 8px; right: 14px; font-size: 11px; color: var(--color-text-placeholder); }
.chip-group { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  height: 30px; display: inline-flex; align-items: center; gap: 6px;
  padding: 0 10px; border-radius: 6px; font-size: 13px;
  color: var(--color-text-secondary); background: var(--color-card);
  border: 1px solid var(--color-border); cursor: pointer; transition: all 0.15s;
}
.chip:hover { border-color: var(--color-primary); color: var(--color-primary); }
.chip.active { color: var(--color-primary); background: var(--color-primary-bg); border-color: var(--color-primary); font-weight: 600; }
.add-chip { border-style: dashed; }
.chip-remove, .style-remove {
  width: 18px; height: 18px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.08); color: currentColor; font-size: 14px; line-height: 1;
}
.custom-inline { display: grid; grid-template-columns: 1fr auto auto; gap: 8px; margin-top: 8px; }
.inline-primary, .inline-secondary {
  height: 36px; padding: 0 12px; border-radius: var(--radius-sm); border: none;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.inline-primary { background: var(--color-primary); color: #fff; }
.inline-secondary { background: var(--color-card); color: var(--color-text-secondary); border: 1px solid var(--color-border); }

.style-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-template-rows: repeat(3, minmax(92px, 1fr));
  grid-auto-rows: minmax(92px, 1fr);
  gap: 10px;
}
.style-card {
  position: relative; min-height: 92px; border-radius: 7px; overflow: hidden;
  cursor: pointer; border: 2px solid transparent; background: var(--color-card);
  padding: 0; transition: border-color 0.15s, box-shadow 0.15s;
}
.style-card:hover { box-shadow: var(--shadow-md); }
.style-card.active { border-color: var(--color-primary); box-shadow: 0 0 0 2px var(--color-primary-bg); }
.style-img, .custom-preview img { width: 100%; height: 100%; object-fit: cover; display: block; }
.style-placeholder, .add-style-card {
  background: #dfe7ec; color: var(--color-primary); display: flex;
  align-items: center; justify-content: center; font-size: 22px; font-weight: 800;
}
.style-name {
  position: absolute; bottom: 0; left: 0; right: 0; padding: 16px 4px 6px;
  text-align: center; font-size: 11px; font-weight: 700; color: #fff;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
}
.style-remove { position: absolute; top: 6px; right: 6px; background: rgba(255,255,255,0.86); color: var(--color-text); }
.add-style-icon { font-size: 30px; font-weight: 300; color: var(--color-primary); }
.custom-visual-panel {
  display: grid; grid-template-columns: minmax(0, 1fr) 92px; gap: 8px;
  margin-top: 8px; padding: 10px; border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); background: var(--color-card);
}
.custom-fields { display: grid; gap: 8px; }
.prompt-input {
  width: 100%; min-height: 58px; padding: 8px 10px; resize: vertical;
  border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  font-family: inherit; font-size: 13px; outline: none;
}
.upload-line { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--color-text-tertiary); }
.upload-line input { font-size: 12px; max-width: 220px; }
.custom-preview {
  height: 100px; border-radius: var(--radius-sm); background: var(--color-bg-secondary);
  color: var(--color-text-placeholder); display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.custom-actions { grid-column: 1 / -1; display: flex; justify-content: flex-end; gap: 8px; }

.control-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; align-items: end; }
.voice-picker {
  width: 100%; height: 40px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 14px; border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  background: var(--color-card); cursor: pointer; transition: border-color 0.15s;
}
.voice-picker:hover { border-color: var(--color-primary); }
.voice-name { font-size: 13px; color: var(--color-text-secondary); }
.length-control {
  height: 40px; background: var(--color-card); border-radius: var(--radius-sm);
  padding: 9px 14px 6px; border: 1px solid var(--color-border);
}
.length-slider {
  width: 100%; height: 4px; appearance: none; -webkit-appearance: none;
  background: var(--color-border); border-radius: 2px; outline: none; display: block;
}
.length-slider::-webkit-slider-thumb {
  -webkit-appearance: none; width: 16px; height: 16px; background: var(--color-primary);
  border-radius: 50%; cursor: pointer;
}
.length-labels { display: flex; justify-content: space-between; align-items: center; margin-top: 3px; font-size: 11px; color: var(--color-text-placeholder); }
.length-value { font-size: 12px; font-weight: 700; color: var(--color-primary); }
.editor-actions { margin-top: auto; display: flex; justify-content: flex-end; }
.generate-btn {
  width: 100%; height: 44px; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 0 28px; border-radius: var(--radius-sm); background: var(--color-primary); color: #fff;
  font-size: 14px; font-weight: 700; border: none; cursor: pointer; transition: background 0.15s, transform 0.1s;
}
.generate-btn:hover:not(:disabled) { background: var(--color-primary-hover); }
.generate-btn:active:not(:disabled) { transform: scale(0.98); }
.generate-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.library-panel { flex: 1; padding: 32px 40px; overflow-y: auto; }
.library-content { max-width: 960px; margin: 0 auto; }
.library-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }
.library-title { font-size: 20px; font-weight: 700; color: var(--color-text); }
.create-btn {
  display: flex; align-items: center; gap: 6px; padding: 8px 16px;
  border-radius: var(--radius-sm); background: var(--color-primary); color: #fff;
  font-size: 13px; font-weight: 500; border: none; cursor: pointer;
}
.empty-library { text-align: center; padding: 80px 0; color: var(--color-text-placeholder); }
.empty-library svg { margin-bottom: 16px; }
.empty-library p { font-size: 14px; margin-bottom: 20px; }
.empty-btn {
  padding: 8px 20px; border-radius: var(--radius-sm); border: 1px solid var(--color-border);
  background: var(--color-card); color: var(--color-text-secondary); font-size: 13px; cursor: pointer;
}
.task-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.task-card {
  background: var(--color-card); border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); padding: 16px 18px; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.task-card:hover { border-color: var(--color-primary); box-shadow: var(--shadow-sm); }
.task-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.task-name {
  font-size: 14px; font-weight: 600; color: var(--color-text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 8px;
}
.task-status { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; flex-shrink: 0; }
.status-pending { color: var(--color-text-tertiary); background: var(--color-bg-secondary); }
.status-processing { color: var(--color-primary); background: var(--color-primary-bg); }
.status-completed { color: var(--color-success); background: var(--color-success-bg); }
.status-failed { color: var(--color-danger); background: var(--color-danger-bg); }
.task-theme {
  font-size: 13px; color: var(--color-text-tertiary); margin-bottom: 10px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.task-meta { display: flex; gap: 12px; font-size: 12px; color: var(--color-text-placeholder); }

@media (max-width: 980px) {
  .create-layout { overflow-y: auto; padding: 16px; }
  .workspace-panel { height: auto; min-height: 100%; }
  .workspace-header { grid-template-columns: 1fr auto; }
  .workflow-strip { grid-column: 1 / -1; order: 3; overflow-x: auto; }
  .workspace-grid { grid-template-columns: 1fr; }
  .primary-card { min-height: 520px; }
  .style-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    grid-template-rows: none;
    grid-auto-rows: 92px;
  }
}

@media (max-width: 680px) {
  .top-nav { padding: 0 12px; }
  .nav-brand, .nav-right { display: none; }
  .nav-tabs { margin-left: auto; overflow-x: auto; }
  .nav-tab { padding: 7px 10px; white-space: nowrap; }
  .create-layout { padding: 12px; }
  .workspace-header { grid-template-columns: 1fr; align-items: start; }
  .settings-link { width: 100%; }
  .style-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: 96px;
  }
  .control-grid, .custom-visual-panel { grid-template-columns: 1fr; }
  .custom-preview { height: 96px; }
  .custom-inline { grid-template-columns: 1fr; }
  .primary-card { min-height: 560px; }
}
</style>
