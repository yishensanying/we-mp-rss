<template>
  <a-layout-header>
    <a-menu
      mode="horizontal"
      :selected-keys="selectedKeys"
      @menu-item-click="handleMenuClick"
    >
      <a-menu-item key="/">
        <template #icon>
          <icon-home />
        </template>
        订阅管理
      </a-menu-item>
      <a-menu-item key="/wechat-status">
        <template #icon>
          <icon-wechat />
        </template>
        授权管理
      </a-menu-item>
      <a-menu-item key="/message-tasks">
        <template #icon>
          <icon-notification />
        </template>
        消息任务
      </a-menu-item>
      <a-menu-item key="/filter-rules">
        <template #icon>
          <icon-filter />
        </template>
        过滤规则
      </a-menu-item>
      <a-menu-item key="/access-keys">
        <template #icon>
          <icon-lock />
        </template>
        Access Key
      </a-menu-item>
    </a-menu>
  </a-layout-header>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const selectedKeys = ref<string[]>(['/'])

watchEffect(() => {
  selectedKeys.value = [route.path]
})

const handleMenuClick = (key: string) => {
  // 避免重复点击当前路由
  if (route.path === key) return
  router.push(key).catch((err) => {
    // 忽略导航到当前路由的错误
    if (!err.message?.includes('Avoided redundant navigation')) {
      console.error('路由导航失败:', err)
    }
  })
}
</script>
