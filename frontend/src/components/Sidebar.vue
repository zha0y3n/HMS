<script setup lang="ts">
import { BedDouble, ReceiptText, SlidersHorizontal, Sun, Moon, PanelLeftClose, PanelLeftOpen } from 'lucide-vue-next'

export type ActiveTab = 'rooms' | 'orders' | 'settings'

defineProps<{
  activeTab: ActiveTab
  collapsed: boolean
  isDark: boolean
  occupancyRate?: string
}>()

const emit = defineEmits<{
  (e: 'update:activeTab', tab: ActiveTab): void
  (e: 'update:collapsed', val: boolean): void
  (e: 'toggleTheme'): void
}>()
</script>

<template>
  <aside
    class="flex flex-col border-r transition-all duration-300 ease-in-out select-none"
    :class="[
      collapsed ? 'w-16' : 'w-56',
      'border-neutral-200/70 dark:border-neutral-800/80 bg-paper-100/60 dark:bg-obsidian-900/60 backdrop-blur-md'
    ]"
  >
    <!-- Brand Header -->
    <div class="h-14 flex items-center justify-between px-3.5 border-b border-neutral-200/50 dark:border-neutral-800/50">
      <div v-if="!collapsed" class="flex items-center space-x-2.5 overflow-hidden">
        <div class="w-6 h-6 rounded-md bg-neutral-900 dark:bg-neutral-100 flex items-center justify-center text-white dark:text-neutral-900 font-mono text-xs font-semibold shadow-sm">
          H
        </div>
        <div class="flex flex-col min-w-0">
          <span class="text-xs font-semibold tracking-wider text-neutral-900 dark:text-neutral-100 font-mono uppercase truncate">
            HMS Console
          </span>
          <span class="text-[10px] text-neutral-400 dark:text-neutral-500 truncate">
            客房与前台系统
          </span>
        </div>
      </div>
      <div v-else class="mx-auto">
        <div class="w-7 h-7 rounded-md bg-neutral-900 dark:bg-neutral-100 flex items-center justify-center text-white dark:text-neutral-900 font-mono text-xs font-semibold">
          H
        </div>
      </div>

      <button
        v-if="!collapsed"
        class="p-1 rounded text-neutral-400 hover:text-neutral-700 dark:text-neutral-500 dark:hover:text-neutral-200 transition-colors"
        title="收起侧栏"
        @click="emit('update:collapsed', true)"
      >
        <PanelLeftClose class="w-3.5 h-3.5" />
      </button>
    </div>

    <!-- Navigation List -->
    <nav class="flex-1 py-4 px-2 space-y-1">
      <button
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium transition-all group"
        :class="[
          activeTab === 'rooms'
            ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 shadow-sm'
            : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-200',
          collapsed ? 'justify-center' : 'justify-start space-x-2.5'
        ]"
        :title="collapsed ? '客房与房态' : undefined"
        @click="emit('update:activeTab', 'rooms')"
      >
        <BedDouble class="w-4 h-4 flex-shrink-0" />
        <span v-if="!collapsed" class="truncate">客房与房态</span>
        <span
          v-if="!collapsed && occupancyRate"
          class="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded-full"
          :class="activeTab === 'rooms' ? 'bg-neutral-800 text-neutral-300 dark:bg-neutral-200 dark:text-neutral-700' : 'bg-neutral-200/80 dark:bg-neutral-800 text-neutral-500'"
        >
          {{ occupancyRate }}
        </span>
      </button>

      <button
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium transition-all group"
        :class="[
          activeTab === 'orders'
            ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 shadow-sm'
            : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-200',
          collapsed ? 'justify-center' : 'justify-start space-x-2.5'
        ]"
        :title="collapsed ? '订单与客历' : undefined"
        @click="emit('update:activeTab', 'orders')"
      >
        <ReceiptText class="w-4 h-4 flex-shrink-0" />
        <span v-if="!collapsed" class="truncate">订单与客历</span>
      </button>

      <button
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium transition-all group"
        :class="[
          activeTab === 'settings'
            ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 shadow-sm'
            : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-200',
          collapsed ? 'justify-center' : 'justify-start space-x-2.5'
        ]"
        :title="collapsed ? '客房与配置' : undefined"
        @click="emit('update:activeTab', 'settings')"
      >
        <SlidersHorizontal class="w-4 h-4 flex-shrink-0" />
        <span v-if="!collapsed" class="truncate">客房与配置</span>
      </button>
    </nav>

    <!-- Bottom Controls -->
    <div class="p-2 border-t border-neutral-200/50 dark:border-neutral-800/50 space-y-1">
      <button
        v-if="collapsed"
        class="w-full flex items-center justify-center p-2 rounded-md text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors"
        title="展开侧栏"
        @click="emit('update:collapsed', false)"
      >
        <PanelLeftOpen class="w-4 h-4" />
      </button>

      <button
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 transition-colors"
        :class="collapsed ? 'justify-center' : 'justify-start space-x-2.5'"
        :title="isDark ? '切换浅色模式 (Notion Light)' : '切换深色模式 (Linear Dark)'"
        @click="emit('toggleTheme')"
      >
        <Sun v-if="isDark" class="w-4 h-4 text-amber-400 flex-shrink-0" />
        <Moon v-else class="w-4 h-4 text-neutral-500 flex-shrink-0" />
        <span v-if="!collapsed" class="truncate font-mono text-[11px]">
          {{ isDark ? 'Notion Light' : 'Linear Dark' }}
        </span>
      </button>

      <div v-if="!collapsed" class="pt-2 px-2.5 flex items-center justify-between text-[10px] text-neutral-400 dark:text-neutral-500 font-mono">
        <span class="flex items-center space-x-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>ONLINE 8100</span>
        </span>
        <span>v0.1.0</span>
      </div>
    </div>
  </aside>
</template>
