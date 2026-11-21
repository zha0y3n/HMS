<script setup lang="ts">
import { BedDouble, ReceiptText, SlidersHorizontal, Sun, Moon, PanelLeftClose, PanelLeftOpen } from 'lucide-vue-next'

export type ActiveTab = 'rooms' | 'orders' | 'settings'

defineProps<{
  activeTab: ActiveTab
  collapsed: boolean
  isDark: boolean
  pendingCount?: number
}>()

const emit = defineEmits<{
  (e: 'update:activeTab', tab: ActiveTab): void
  (e: 'update:collapsed', val: boolean): void
  (e: 'toggleTheme'): void
}>()
</script>

<template>
  <aside
    class="h-full flex flex-col flex-shrink-0 border-r transition-[width,background-color,border-color] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] select-none overflow-hidden"
    :class="[
      collapsed ? 'w-16' : 'w-56',
      'border-neutral-200/70 dark:border-neutral-800/80 bg-paper-100/70 dark:bg-obsidian-900/70 backdrop-blur-md'
    ]"
  >
    <!-- Brand Header -->
    <div
      class="h-14 flex-shrink-0 flex items-center border-b border-neutral-200/50 dark:border-neutral-800/50"
      :class="collapsed ? 'justify-center px-2' : 'justify-between px-3.5'"
    >
      <!-- Expanded Brand Logo & Title -->
      <div v-if="!collapsed" class="flex items-center space-x-2.5 overflow-hidden group cursor-pointer">
        <!-- Custom Geometric Architectural Emblem SVG -->
        <div class="relative w-7 h-7 rounded-lg bg-neutral-900 dark:bg-neutral-100 flex items-center justify-center text-white dark:text-neutral-900 flex-shrink-0 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-105">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Outer architectural arch & prism frame -->
            <path
              d="M4 20V9.5C4 6.46243 6.46243 4 9.5 4H14.5C17.5376 4 20 6.46243 20 9.5V20"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
            <!-- Inner boutique portal & geometric keyline -->
            <path
              d="M8.5 20V13C8.5 11.067 10.067 9.5 12 9.5C13.933 9.5 15.5 11.067 15.5 13V20"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-opacity="0.7"
            />
            <!-- Top compass star dot -->
            <circle cx="12" cy="6.75" r="1.15" fill="currentColor" />
            <!-- Horizon base line -->
            <path d="M2.5 20H21.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </div>

        <div class="flex flex-col min-w-0">
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-semibold tracking-wider text-neutral-900 dark:text-neutral-100 uppercase truncate">
              Aurelia
            </span>
            <span class="text-[9px] font-medium px-1 py-0.2 rounded bg-neutral-200/80 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 tracking-tight">
              HMS
            </span>
          </div>
        </div>
      </div>

      <!-- Collapsed Header: Logo + Direct Expand Action -->
      <button
        v-else
        type="button"
        class="group relative w-9 h-9 rounded-lg flex items-center justify-center text-neutral-700 dark:text-neutral-200 hover:bg-neutral-200/70 dark:hover:bg-neutral-800/70 transition-all duration-200 active:scale-95"
        title="展开侧栏"
        @click="emit('update:collapsed', false)"
      >
        <!-- Default shows the emblem; on hover smoothly reveals the expand icon -->
        <div class="w-7 h-7 rounded-lg bg-neutral-900 dark:bg-neutral-100 flex items-center justify-center text-white dark:text-neutral-900 transition-opacity duration-150 group-hover:opacity-0">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M4 20V9.5C4 6.46243 6.46243 4 9.5 4H14.5C17.5376 4 20 6.46243 20 9.5V20"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
            <path
              d="M8.5 20V13C8.5 11.067 10.067 9.5 12 9.5C13.933 9.5 15.5 11.067 15.5 13V20"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-opacity="0.7"
            />
            <circle cx="12" cy="6.75" r="1.15" fill="currentColor" />
            <path d="M2.5 20H21.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </div>
        <PanelLeftOpen class="w-4 h-4 absolute opacity-0 group-hover:opacity-100 transition-opacity duration-150 text-neutral-900 dark:text-neutral-100" />
      </button>

      <!-- Collapse Button (when expanded) -->
      <button
        v-if="!collapsed"
        type="button"
        class="p-1.5 rounded-md text-neutral-400 hover:text-neutral-800 dark:text-neutral-500 dark:hover:text-neutral-200 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 transition-all duration-150 active:scale-95"
        title="收起侧栏"
        @click="emit('update:collapsed', true)"
      >
        <PanelLeftClose class="w-3.5 h-3.5" />
      </button>
    </div>

    <!-- Quick Expand Bar right under header when collapsed -->
    <div v-if="collapsed" class="px-2 pt-2 flex-shrink-0">
      <button
        type="button"
        class="w-full flex items-center justify-center py-1.5 rounded-md text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 transition-all duration-150 active:scale-95"
        title="展开侧栏"
        @click="emit('update:collapsed', false)"
      >
        <PanelLeftOpen class="w-4 h-4" />
      </button>
    </div>

    <!-- Navigation List -->
    <nav class="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
      <button
        type="button"
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] active:scale-[0.98] group"
        :class="[
          activeTab === 'rooms'
            ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900'
            : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-200',
          collapsed ? 'justify-center' : 'justify-start space-x-2.5'
        ]"
        :title="collapsed ? '客房与房态' : undefined"
        @click="emit('update:activeTab', 'rooms')"
      >
        <BedDouble class="w-4 h-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-105" />
        <span v-if="!collapsed" class="truncate">客房与房态</span>
        <span
          v-if="!collapsed && pendingCount && pendingCount > 0"
          class="ml-auto text-[10px] font-mono tabular-nums px-1.5 py-0.5 rounded-full"
          :class="activeTab === 'rooms' ? 'bg-neutral-800 text-neutral-300 dark:bg-neutral-200 dark:text-neutral-700' : 'bg-neutral-200/80 dark:bg-neutral-800 text-neutral-500'"
        >
          {{ pendingCount }}
        </span>
      </button>

      <button
        type="button"
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] active:scale-[0.98] group"
        :class="[
          activeTab === 'orders'
            ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900'
            : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-200',
          collapsed ? 'justify-center' : 'justify-start space-x-2.5'
        ]"
        :title="collapsed ? '订单与客历' : undefined"
        @click="emit('update:activeTab', 'orders')"
      >
        <ReceiptText class="w-4 h-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-105" />
        <span v-if="!collapsed" class="truncate">订单与客历</span>
      </button>

      <button
        type="button"
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] active:scale-[0.98] group"
        :class="[
          activeTab === 'settings'
            ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900'
            : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-200',
          collapsed ? 'justify-center' : 'justify-start space-x-2.5'
        ]"
        :title="collapsed ? '客房与配置' : undefined"
        @click="emit('update:activeTab', 'settings')"
      >
        <SlidersHorizontal class="w-4 h-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-105" />
        <span v-if="!collapsed" class="truncate">客房与配置</span>
      </button>
    </nav>

    <!-- Bottom Controls (Fixed at bottom-left corner, never scrolls with content) -->
    <div class="mt-auto flex-shrink-0 p-2 border-t border-neutral-200/50 dark:border-neutral-800/50 space-y-1 bg-paper-100/80 dark:bg-obsidian-900/80">
      <button
        v-if="collapsed"
        type="button"
        class="w-full flex items-center justify-center p-2 rounded-md text-neutral-500 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-100 transition-all duration-150 active:scale-95"
        title="展开侧栏"
        @click="emit('update:collapsed', false)"
      >
        <PanelLeftOpen class="w-4 h-4" />
      </button>

      <button
        type="button"
        class="w-full flex items-center rounded-md px-2.5 py-2 text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/60 hover:text-neutral-900 dark:hover:text-neutral-100 transition-all duration-150 active:scale-[0.98]"
        :class="collapsed ? 'justify-center' : 'justify-start space-x-2.5'"
        :title="isDark ? '切换浅色模式 (Notion Light)' : '切换深色模式 (Linear Dark)'"
        @click="emit('toggleTheme')"
      >
        <Transition name="icon-pop" mode="out-in">
          <Sun v-if="isDark" key="sun" class="w-4 h-4 text-amber-400 flex-shrink-0" />
          <Moon v-else key="moon" class="w-4 h-4 text-neutral-500 flex-shrink-0" />
        </Transition>
        <span v-if="!collapsed" class="truncate text-[11px]">
          {{ isDark ? '浅色模式' : '深色模式' }}
        </span>
      </button>
    </div>
  </aside>
</template>
