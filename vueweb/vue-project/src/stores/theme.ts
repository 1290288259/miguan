import { ref, watch } from 'vue'

// 状态
// 默认深色主题，除非明确设置为 light
const isDark = ref(localStorage.getItem('theme') !== 'light')

// 方法
const toggleTheme = () => {
  isDark.value = !isDark.value
}

// 监听主题变化并应用
watch(isDark, (val) => {
  if (val) {
    document.documentElement.classList.remove('light-theme')
    document.documentElement.classList.add('dark-theme')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark-theme')
    document.documentElement.classList.add('light-theme')
    localStorage.setItem('theme', 'light')
  }
}, { immediate: true })

export function useThemeStore() {
  return {
    isDark,
    toggleTheme
  }
}
