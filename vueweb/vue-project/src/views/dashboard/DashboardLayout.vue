<template>
  <div class="dashboard-layout">
    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      router
      class="dashboard-menu"
      :ellipsis="false"
    >
      <el-menu-item index="/overview">
        <el-icon><Odometer /></el-icon>
        <span>总览</span>
      </el-menu-item>
      <el-menu-item index="/trend">
        <el-icon><TrendCharts /></el-icon>
        <span>攻击趋势</span>
      </el-menu-item>
      <el-menu-item index="/types">
        <el-icon><PieChart /></el-icon>
        <span>攻击分布</span>
      </el-menu-item>
      <el-menu-item index="/map">
        <el-icon><MapLocation /></el-icon>
        <span>来源排名</span>
      </el-menu-item>
    </el-menu>
    
    <div class="dashboard-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Odometer, TrendCharts, PieChart, MapLocation } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.dashboard-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.dashboard-menu {
  margin-bottom: 20px;
  border-bottom: solid 1px var(--el-menu-border-color);
}
.dashboard-content {
  flex: 1;
  overflow: auto;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
