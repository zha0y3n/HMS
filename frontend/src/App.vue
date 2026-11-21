<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NConfigProvider, darkTheme, zhCN, dateZhCN } from 'naive-ui'
import Sidebar, { type ActiveTab } from './components/Sidebar.vue'
import RoomsView from './components/RoomsView.vue'
import OrdersView from './components/OrdersView.vue'
import SettingsView from './components/SettingsView.vue'
import type { Room, RoomStats, Order, RoomWithActiveOrder } from './types'
import { api, extractErrorMessage } from './api'

// Theme state (Linear Dark / Notion Light)
const isDark = ref(true)

function initTheme() {
  const saved = localStorage.getItem('hms_theme')
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    // Default to dark theme for modern Linear aesthetic
    isDark.value = true
  }
  applyTheme()
}

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('hms_theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}

function applyTheme() {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Navigation & Layout state
const activeTab = ref<ActiveTab>('rooms')
const sidebarCollapsed = ref(false)

// Global Data
const rawRooms = ref<Room[]>([])
const stats = ref<RoomStats>()
const orders = ref<Order[]>([])
const loading = ref(false)
const globalError = ref<string | null>(null)

// Smart Fusion: Combine room data with active orders
const roomsWithOrders = computed<RoomWithActiveOrder[]>(() => {
  // Map of room_id to active order
  const activeOrdersMap = new Map<number, Order>()
  for (const o of orders.value) {
    if (o.status === 'checked_in' || o.status === 'reserved') {
      activeOrdersMap.set(o.room_id, o)
    }
  }

  return rawRooms.value.map((room) => {
    return {
      ...room,
      activeOrder: activeOrdersMap.get(room.id),
    }
  })
})

// Fetch all data
async function loadData() {
  loading.value = true
  globalError.value = null
  try {
    const [roomsRes, ordersRes] = await Promise.all([
      api.getRooms(),
      api.getOrders(),
    ])
    rawRooms.value = roomsRes.rooms || []
    stats.value = roomsRes.stats
    orders.value = ordersRes || []
  } catch (err) {
    globalError.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initTheme()
  loadData()
})
</script>

<template>
  <n-config-provider
    :theme="isDark ? darkTheme : null"
    :locale="zhCN"
    :date-locale="dateZhCN"
  >
    <div class="flex h-screen w-screen overflow-hidden bg-paper-50 dark:bg-obsidian-950 text-neutral-800 dark:text-neutral-100 font-sans selection:bg-neutral-800 selection:text-white dark:selection:bg-neutral-200 dark:selection:text-black">
      <!-- Minimalist Linear-style Sidebar -->
      <Sidebar
        v-model:active-tab="activeTab"
        v-model:collapsed="sidebarCollapsed"
        :is-dark="isDark"
        :occupancy-rate="stats?.occupancy_rate"
        @toggle-theme="toggleTheme"
      />

      <!-- Main Content Stage -->
      <main class="flex-1 flex flex-col h-full min-w-0 bg-white/40 dark:bg-obsidian-900/30">
        <!-- Global Error Banner (if backend unreachable) -->
        <div
          v-if="globalError"
          class="px-6 py-2 bg-rose-500/10 border-b border-rose-500/20 text-rose-500 text-xs font-mono flex items-center justify-between"
        >
          <span>后端接口通信异常：{{ globalError }}（请确保后端服务 http://127.0.0.1:8100 处于运行状态）</span>
          <button class="underline hover:text-rose-400" @click="loadData">重试</button>
        </div>

        <!-- Dynamic Views -->
        <RoomsView
          v-if="activeTab === 'rooms'"
          :rooms="roomsWithOrders"
          :stats="stats"
          :loading="loading"
          @refresh="loadData"
        />

        <OrdersView
          v-else-if="activeTab === 'orders'"
          :orders="orders"
          :loading="loading"
          @refresh="loadData"
        />

        <SettingsView
          v-else-if="activeTab === 'settings'"
          :rooms="rawRooms"
          :loading="loading"
          @refresh="loadData"
        />
      </main>
    </div>
  </n-config-provider>
</template>
