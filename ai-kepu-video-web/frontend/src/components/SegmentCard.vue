<template>
  <div class="segment-card">
    <div class="media-col">
      <div class="segment-index">{{ index + 1 }}</div>
      <div class="thumbnail" @click="previewImage">
        <img v-if="segment.image_url" :key="segment.image_url" :src="segment.image_url" class="thumbnail-img" alt="图片" />
        <div v-else class="thumbnail-empty">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        </div>
      </div>
      <div class="audio-wrapper">
        <audio v-if="segment.audio_url" :key="segment.audio_url" :src="segment.audio_url" controls class="audio-player"></audio>
        <div v-else class="audio-empty">暂无音频</div>
      </div>
    </div>

    <div class="text-col">
      <textarea :value="localText" class="text-input" rows="4" placeholder="请输入文案" @input="localText = $event.target.value" @blur="onTextBlur"></textarea>
    </div>

    <div class="action-col">
      <button class="action-btn" :disabled="regeneratingImage || !edited" @click="onRegenerateImage">
        <van-loading v-if="regeneratingImage" size="12px" />
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <span>重新生成图片</span>
      </button>
      <button class="action-btn" :disabled="uploadingImage" @click="onUploadImage">
        <van-loading v-if="uploadingImage" size="12px" />
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        <span>更换图片</span>
      </button>
      <button class="action-btn" :disabled="regeneratingAudio || !edited" @click="onRegenerateAudio">
        <van-loading v-if="regeneratingAudio" size="12px" />
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
        <span>重新生成音频</span>
      </button>
    </div>

    <input ref="imageInput" type="file" accept="image/jpeg,image/jpg,image/png,image/webp" style="display: none" @change="onImageSelected" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { showImagePreview, Loading as VanLoading } from 'vant'

const props = defineProps({
  segment: { type: Object, required: true },
  index: { type: Number, required: true }
})
const emit = defineEmits(['edit', 'regenerate-image', 'regenerate-audio', 'upload-image'])

const localText = ref(props.segment.text || '')
const edited = ref(false)
const regeneratingImage = ref(false)
const regeneratingAudio = ref(false)
const uploadingImage = ref(false)
const imageInput = ref(null)

watch(() => props.segment.text, (newVal) => {
  if (newVal !== undefined && newVal !== null && newVal !== localText.value) {
    localText.value = newVal
    edited.value = false
  }
}, { immediate: true })

function onTextBlur() {
  if (localText.value !== props.segment.text) {
    edited.value = true
    emit('edit', props.index, localText.value)
  }
}
function previewImage() { if (props.segment.image_url) showImagePreview({ images: [props.segment.image_url], closeable: true }) }
function onRegenerateImage() { emit('regenerate-image', props.index) }
function onRegenerateAudio() { emit('regenerate-audio', props.index) }
function onUploadImage() { imageInput.value?.click() }
function onImageSelected(event) { const file = event.target.files?.[0]; if (file) { emit('upload-image', props.index, file); event.target.value = '' } }
</script>

<style scoped>
.segment-card {
  display: flex;
  gap: 16px;
  align-items: stretch;
  background: var(--color-card);
  border-radius: var(--radius-sm);
  padding: 16px;
  border: 1px solid var(--color-border);
  transition: box-shadow 0.15s;
}
.segment-card:hover { box-shadow: var(--shadow-sm); }

.media-col { display: flex; flex-direction: column; align-items: center; gap: 8px; flex-shrink: 0; width: 150px; }

.segment-index {
  width: 24px;
  height: 24px;
  background: var(--color-text);
  color: #fff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.thumbnail { width: 150px; height: 94px; cursor: pointer; border-radius: 6px; overflow: hidden; }
.thumbnail:hover { opacity: 0.9; }
.thumbnail-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumbnail-empty {
  width: 100%;
  height: 100%;
  background: var(--color-bg-secondary);
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-placeholder);
}

.audio-wrapper { width: 100%; }
.audio-player { width: 100%; height: 32px; }
.audio-empty {
  height: 32px;
  background: var(--color-bg-secondary);
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-placeholder);
  font-size: 12px;
}

.text-col { flex: 1; min-width: 0; display: flex; }

.text-input {
  width: 100%;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text);
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-radius: 6px;
  border: 1px solid transparent;
  transition: all 0.15s;
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
}
.text-input:focus {
  outline: none;
  background: var(--color-card);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}
.text-input::placeholder { color: var(--color-text-placeholder); }

.action-col { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; width: 140px; justify-content: center; }

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-text-tertiary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.action-btn:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
.action-btn:disabled { opacity: 0.35; cursor: not-allowed; }
</style>
