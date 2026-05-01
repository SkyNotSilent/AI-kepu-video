/**
 * 进度条组件
 */
<template>
  <div class="progress-bar">
    <div class="progress-ring-wrapper">
      <svg class="progress-ring" width="88" height="88" viewBox="0 0 88 88">
        <circle class="ring-bg" cx="44" cy="44" r="36" />
        <circle class="ring-fill" cx="44" cy="44" r="36" :style="{ strokeDashoffset: dashOffset }" />
      </svg>
      <div class="ring-text">
        <span class="ring-percent">{{ percentage }}</span>
        <span class="ring-unit">%</span>
      </div>
    </div>
    <div class="progress-info">
      <div class="progress-label">{{ currentStepLabel }}</div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: percentage + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { calculateProgress, getStepLabel } from '../utils/format'

const props = defineProps({
  steps: { type: Array, required: true },
  currentStep: { type: String, default: '' }
})

const percentage = computed(() => calculateProgress(props.steps))
const circumference = 2 * Math.PI * 36
const dashOffset = computed(() => circumference - (percentage.value / 100) * circumference)

const currentStepLabel = computed(() => {
  if (!props.currentStep) return '准备中...'
  const step = props.steps.find(s => s.name === props.currentStep)
  if (!step) return '处理中...'
  const label = getStepLabel(props.currentStep)
  if (step.status === 'processing' && step.progress && step.total) return `${label} (${step.progress}/${step.total})`
  return label
})
</script>

<style scoped>
.progress-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: var(--color-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.progress-ring-wrapper { position: relative; flex-shrink: 0; }
.progress-ring { transform: rotate(-90deg); }

.ring-bg { fill: none; stroke: var(--color-divider); stroke-width: 5; }
.ring-fill {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 5;
  stroke-linecap: round;
  stroke-dasharray: 226.19;
  transition: stroke-dashoffset 0.6s ease;
}

.ring-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
}
.ring-percent { font-size: 22px; font-weight: 700; color: var(--color-text); }
.ring-unit { font-size: 11px; font-weight: 600; color: var(--color-text-tertiary); margin-left: 1px; }

.progress-info { flex: 1; min-width: 0; }
.progress-label { font-size: 14px; font-weight: 500; color: var(--color-text-secondary); margin-bottom: 10px; }

.progress-track { height: 4px; background: var(--color-divider); border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-primary); border-radius: 2px; transition: width 0.6s ease; }
</style>
