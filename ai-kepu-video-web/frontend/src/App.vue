<template>
  <router-view />
</template>

<script setup>
</script>

<style>
:root {
  --color-primary: #1e3a5f;
  --color-primary-hover: #152d4a;
  --color-primary-bg: #eff4f8;
  --color-success: #059669;
  --color-success-bg: #ecfdf5;
  --color-danger: #dc2626;
  --color-danger-bg: #fef2f2;
  --color-bg: #fafaf9;
  --color-bg-secondary: #f5f5f4;
  --color-card: #ffffff;
  --color-text: #1c1917;
  --color-text-secondary: #44403c;
  --color-text-tertiary: #78716c;
  --color-text-placeholder: #a8a29e;
  --color-border: #e7e5e4;
  --color-divider: #f5f5f4;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 2px 4px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 4px 8px rgba(0,0,0,0.04), 0 12px 32px rgba(0,0,0,0.08);
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--color-text);
  background: var(--color-bg);
}

#app {
  width: 100%;
  min-height: 100vh;
}
</style>
