<template>
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
</script>

<style>
:root {
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-bg: rgba(37, 99, 235, 0.1);
  --accent-glow: rgba(37, 99, 235, 0.2);
  --color-success: #00b42a;
  --color-success-bg: #ecfdf5;
  --color-danger: #f53f3f;
  --color-danger-bg: #fef2f2;
  --color-bg: #f2f3f5;
  --color-bg-secondary: #f7f8fa;
  --color-card: #ffffff;
  --color-text: #1d2129;
  --color-text-secondary: #4e5969;
  --color-text-tertiary: #86909c;
  --color-text-placeholder: #c9cdd4;
  --color-border: #e5e6eb;
  --color-divider: #f2f3f5;
  --color-dark: #1d2129;
  --shadow-xs: 0 1px 2px rgba(29, 33, 41, 0.04);
  --shadow-sm: 0 4px 12px rgba(29, 33, 41, 0.06);
  --shadow-md: 0 8px 24px rgba(29, 33, 41, 0.08);
  --shadow-lg: 0 16px 48px rgba(29, 33, 41, 0.12);
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --font-main: 'PingFang SC', 'Microsoft YaHei', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', Consolas, monospace;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-main);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--color-text);
  background: var(--color-bg);
}

#app {
  width: 100%;
  min-height: 100vh;
}

button,
input,
textarea,
select {
  font: inherit;
}

button {
  letter-spacing: 0;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #c9cdd4;
  border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a9aeb8;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.van-toast {
  border-radius: 8px;
}
</style>
