/**
 * 错误弹窗组件
 */
<template>
  <van-dialog
    v-model:show="dialogVisible"
    title="生成失败"
    :show-cancel-button="true"
    confirm-button-text="重新生成"
    cancel-button-text="关闭"
    confirm-button-color="var(--color-primary)"
    @confirm="handleRetry"
  >
    <div class="error-content">
      <p class="error-message">{{ errorMessage }}</p>
      <div v-if="errorDetail" class="error-detail">
        <van-collapse v-model="activeNames">
          <van-collapse-item title="查看详细信息" name="1">
            <p class="detail-text">{{ errorDetail }}</p>
          </van-collapse-item>
        </van-collapse>
      </div>
    </div>
  </van-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Dialog as VanDialog, Collapse as VanCollapse, CollapseItem as VanCollapseItem } from 'vant'

const props = defineProps({
  visible: { type: Boolean, default: false },
  errorMessage: { type: String, default: '生成过程中出现错误' },
  errorDetail: { type: String, default: '' }
})
const emit = defineEmits(['update:visible', 'retry'])
const dialogVisible = ref(props.visible)
const activeNames = ref([])

watch(() => props.visible, (val) => { dialogVisible.value = val })
watch(dialogVisible, (val) => { emit('update:visible', val) })
const handleRetry = () => { emit('retry'); dialogVisible.value = false }
</script>

<style scoped>
.error-content { padding: 20px; }
.error-message { font-size: 14px; color: var(--color-text-secondary); line-height: 1.6; margin-bottom: 12px; }
.error-detail { margin-top: 8px; }
.detail-text { font-size: 13px; color: var(--color-text-placeholder); line-height: 1.5; word-break: break-all; white-space: pre-wrap; }
</style>
