<template>
  <div class="settings-view">
    <div class="top-nav">
      <div class="nav-left">
        <div class="nav-logo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" /></svg>
        </div>
        <span class="nav-brand">AI 科普视频</span>
      </div>
      <div class="nav-tabs">
        <button class="nav-tab" @click="router.push('/')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          首页
        </button>
        <button class="nav-tab" @click="router.push({ path: '/', query: { tab: 'library' } })">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          资产记录
        </button>
        <button class="nav-tab active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/></svg>
          模型配置
        </button>
      </div>
      <div class="nav-right"></div>
    </div>

    <main class="settings-main">
      <div class="settings-header">
        <h1>模型配置</h1>
        <p>统一管理生文模型和生图模型的接口参数。</p>
      </div>

      <van-loading v-if="loading" size="24px" vertical class="loading-state">加载中...</van-loading>

      <div v-else class="settings-grid">
        <section class="settings-card">
          <div class="card-header">
            <h2>生文模型</h2>
            <span class="card-tag">LLM</span>
          </div>

          <label class="field">
            <span>协议类型</span>
            <div class="protocol-group">
              <button
                type="button"
                class="protocol-btn"
                :class="{ active: form.llm.protocol === 'anthropic' }"
                @click="form.llm.protocol = 'anthropic'"
              >Anthropic 兼容</button>
              <button
                type="button"
                class="protocol-btn"
                :class="{ active: form.llm.protocol === 'openai' }"
                @click="form.llm.protocol = 'openai'"
              >OpenAI 兼容</button>
            </div>
          </label>

          <label class="field">
            <span>API Base URL</span>
            <input v-model.trim="form.llm.base_url" class="text-input" placeholder="https://api.example.com" />
          </label>

          <label class="field">
            <span>API Key</span>
            <input v-model="form.llm.api_key" class="text-input" type="password" autocomplete="off" placeholder="sk-..." />
          </label>

          <label class="field">
            <span>Model</span>
            <input v-model.trim="form.llm.model" class="text-input" placeholder="qwen3.6-plus" />
          </label>
        </section>

        <section class="settings-card">
          <div class="card-header">
            <h2>生图模型</h2>
            <span class="card-tag">Image</span>
          </div>

          <label class="field">
            <span>API URL</span>
            <input v-model.trim="form.image.api_url" class="text-input" placeholder="https://api.example.com/v1/images/generations" />
          </label>

          <label class="field">
            <span>API Key</span>
            <input v-model="form.image.api_key" class="text-input" type="password" autocomplete="off" placeholder="sk-..." />
          </label>

          <label class="field">
            <span>Model</span>
            <input v-model.trim="form.image.model" class="text-input" placeholder="doubao-seedream-4-0-250828" />
          </label>
        </section>
      </div>

      <div v-if="!loading" class="settings-actions">
        <button class="secondary-btn" :disabled="saving" @click="loadConfig">重置</button>
        <button class="primary-btn" :disabled="saving" @click="saveConfig">
          <van-loading v-if="saving" size="18px" color="#fff" />
          <span v-else>保存配置</span>
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Loading as VanLoading, showToast } from 'vant'
import { getConfig, updateConfig } from '../api/task'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const form = ref({
  llm: {
    base_url: '',
    api_key: '',
    model: '',
    protocol: 'anthropic',
  },
  image: {
    api_url: '',
    api_key: '',
    model: '',
  },
})

onMounted(loadConfig)

async function loadConfig() {
  loading.value = true
  try {
    const config = await getConfig()
    form.value = {
      llm: {
        base_url: config?.llm?.base_url || '',
        api_key: config?.llm?.api_key || '',
        model: config?.llm?.model || '',
        protocol: config?.llm?.protocol || 'anthropic',
      },
      image: {
        api_url: config?.image?.api_url || '',
        api_key: config?.image?.api_key || '',
        model: config?.image?.model || '',
      },
    }
  } catch (error) {
    console.error('加载模型配置失败:', error)
    showToast('加载模型配置失败')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  if (!form.value.llm.base_url.trim()) { showToast('请输入生文 Base URL'); return }
  if (!form.value.llm.api_key.trim()) { showToast('请输入生文 API Key'); return }
  if (!form.value.llm.model.trim()) { showToast('请输入生文模型'); return }
  if (!form.value.image.api_url.trim()) { showToast('请输入生图 API URL'); return }
  if (!form.value.image.api_key.trim()) { showToast('请输入生图 API Key'); return }
  if (!form.value.image.model.trim()) { showToast('请输入生图模型'); return }

  saving.value = true
  try {
    const saved = await updateConfig(form.value)
    form.value = saved
    showToast('配置已保存')
  } catch (error) {
    console.error('保存模型配置失败:', error)
    showToast('保存模型配置失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-view { min-height: 100vh; background: var(--color-bg); display: flex; flex-direction: column; }
.top-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 52px; background: var(--color-card);
  border-bottom: 1px solid var(--color-border); flex-shrink: 0;
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

.settings-main { flex: 1; width: min(1120px, calc(100% - 48px)); margin: 0 auto; padding: 36px 0 48px; }
.settings-header { margin-bottom: 24px; }
.settings-header h1 { font-size: 28px; line-height: 1.2; margin-bottom: 8px; color: var(--color-text); }
.settings-header p { font-size: 14px; color: var(--color-text-tertiary); }
.loading-state { padding: 80px 0; }
.settings-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.settings-card {
  background: var(--color-card); border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); padding: 22px; box-shadow: var(--shadow-xs);
}
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.card-header h2 { font-size: 18px; color: var(--color-text); }
.card-tag {
  font-size: 12px; color: var(--color-primary); background: var(--color-primary-bg);
  border-radius: 6px; padding: 4px 8px; font-weight: 600;
}
.field { display: block; margin-bottom: 16px; }
.field span { display: block; font-size: 13px; color: var(--color-text-tertiary); margin-bottom: 8px; font-weight: 500; }
.text-input {
  width: 100%; height: 40px; padding: 0 12px; border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); background: var(--color-bg); color: var(--color-text);
  font-size: 14px; outline: none; transition: border-color 0.15s, box-shadow 0.15s;
}
.text-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-bg); background: var(--color-card); }
.protocol-group { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.protocol-btn {
  height: 38px; border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  background: var(--color-bg); color: var(--color-text-secondary);
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.protocol-btn.active { border-color: var(--color-primary); background: var(--color-primary-bg); color: var(--color-primary); }
.settings-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.secondary-btn, .primary-btn {
  height: 40px; padding: 0 22px; border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600; cursor: pointer; border: none;
}
.secondary-btn { background: var(--color-card); color: var(--color-text-secondary); border: 1px solid var(--color-border); }
.primary-btn { min-width: 112px; background: var(--color-primary); color: #fff; display: inline-flex; align-items: center; justify-content: center; }
.primary-btn:disabled, .secondary-btn:disabled { opacity: 0.55; cursor: not-allowed; }

@media (max-width: 820px) {
  .top-nav { padding: 0 14px; }
  .nav-brand, .nav-right { display: none; }
  .nav-tabs { margin-left: auto; }
  .nav-tab { padding: 7px 10px; }
  .settings-main { width: calc(100% - 28px); padding: 24px 0 36px; }
  .settings-grid { grid-template-columns: 1fr; }
}
</style>
