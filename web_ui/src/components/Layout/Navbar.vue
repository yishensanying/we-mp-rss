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
      <a-menu-item key="/message-tasks">
        <template #icon>
          <icon-notification />
        </template>
        消息任务
      </a-menu-item>
      <a-menu-item key="/access-keys">
        <template #icon>
          <icon-key />
        </template>
        Access Key
      </a-menu-item>
      <a-menu-item key="/env-exception">
        <template #icon>
          <icon-exclamation-circle />
        </template>
        异常统计
      </a-menu-item>
       <!-- <a-menu-item key="/reader">
        <template #icon>
          <icon-read />
            阅读器
        </template>
      </a-menu-item> -->
    </a-menu>
  </a-layout-header>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import TextIcon from '@/components/TextIcon.vue'
import { translatePage, setCurrentLanguage } from '@/utils/translate';

const router = useRouter()
const route = useRoute()
const selectedKeys = ref<string[]>(['/'])

watchEffect(() => {
  selectedKeys.value = [route.path]
  // translatePage()
})

const handleMenuClick = (key: string) => {
  router.push(key)
}
</script>