<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Search,
  RefreshCw,
  Plus,
  ChevronDown,
  ChevronUp,
  UserCheck,
  Receipt,
  LogOut,
  AlertCircle,
  CheckCircle2,
} from 'lucide-vue-next'
import type { RoomWithActiveOrder, RoomStats } from '../types'
import { api, extractErrorMessage } from '../api'

const props = defineProps<{
  rooms: RoomWithActiveOrder[]
  stats?: RoomStats
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

// Filters
const searchKeyword = ref('')
const selectedType = ref('ALL')
const selectedStatus = ref<'ALL' | 'available' | 'reserved' | 'occupied'>('ALL')

// Expanded row ID
const expandedRoomId = ref<number | null>(null)

// Actions state inside expanded rows
const extraAmount = ref<number | ''>('')
const actionLoading = ref(false)
const rowMessage = ref<{ roomId: number; type: 'success' | 'error'; text: string } | null>(null)

// Checkout preview state
const checkoutPreview = ref<{
  roomId: number
  roomFee: number
  extraFee: number
  totalAmount: number
} | null>(null)

// Available room fast check-in form state
const fastForm = ref<{
  guest_name: string
  phone: string
  id_card: string
  days: number
  mode: 'checkin' | 'reserved'
}>({
  guest_name: '',
  phone: '',
  id_card: '',
  days: 1,
  mode: 'checkin',
})

// Notion-style inline append row state at table bottom
const isBottomAdding = ref(false)
const bottomForm = ref<{
  room_type: string
  guest_name: string
  phone: string
  id_card: string
  days: number
  mode: 'checkin' | 'reserved'
}>({
  room_type: '标准间',
  guest_name: '',
  phone: '',
  id_card: '',
  days: 1,
  mode: 'checkin',
})
const bottomMessage = ref<{ type: 'success' | 'error'; text: string } | null>(null)

// Unique room types
const roomTypes = computed(() => {
  const set = new Set<string>()
  props.rooms.forEach((r) => set.add(r.type))
  return Array.from(set)
})

// Filtered rooms
const filteredRooms = computed(() => {
  return props.rooms.filter((r) => {
    // Type filter
    if (selectedType.value !== 'ALL' && r.type !== selectedType.value) {
      return false
    }
    // Status filter
    if (selectedStatus.value !== 'ALL' && r.status !== selectedStatus.value) {
      return false
    }
    // Search keyword
    if (searchKeyword.value.trim()) {
      const q = searchKeyword.value.trim().toLowerCase()
      const matchNumber = r.number.toLowerCase().includes(q)
      const matchType = r.type.toLowerCase().includes(q)
      const matchGuest = r.activeOrder?.guest_name.toLowerCase().includes(q)
      const matchPhone = r.activeOrder?.phone.includes(q)
      return matchNumber || matchType || matchGuest || matchPhone
    }
    return true
  })
})

function toggleExpand(room: RoomWithActiveOrder) {
  if (expandedRoomId.value === room.id) {
    expandedRoomId.value = null
  } else {
    expandedRoomId.value = room.id
    rowMessage.value = null
    checkoutPreview.value = null
    extraAmount.value = ''
    fastForm.value = {
      guest_name: '',
      phone: '',
      id_card: '',
      days: 1,
      mode: 'checkin',
    }
  }
}

// 1. Confirm Check-in for reserved room
async function handleConfirmCheckin(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return
  actionLoading.value = true
  rowMessage.value = null
  try {
    const res = await api.confirmCheckin(room.activeOrder.id)
    rowMessage.value = { roomId: room.id, type: 'success', text: res.msg || '办理正式入住成功' }
    emit('refresh')
  } catch (err) {
    rowMessage.value = { roomId: room.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}

// 2. Add extra fee for occupied room
async function handleAddExtraFee(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return
  const amt = Number(extraAmount.value)
  if (!amt || amt <= 0) {
    rowMessage.value = { roomId: room.id, type: 'error', text: '请输入大于 0 的消费金额' }
    return
  }

  actionLoading.value = true
  rowMessage.value = null
  try {
    const res = await api.addExtraFee(room.activeOrder.id, amt)
    rowMessage.value = {
      roomId: room.id,
      type: 'success',
      text: `${res.msg}（当前累计杂费：¥${res.cur_extra_fee.toFixed(2)}）`,
    }
    extraAmount.value = ''
    emit('refresh')
  } catch (err) {
    rowMessage.value = { roomId: room.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}

// 3. Prepare / Confirm checkout
function prepareCheckout(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return
  const days = room.activeOrder.days || 1
  const roomFee = days * room.price
  const extraFee = room.activeOrder.extra_fee || 0
  const totalAmount = roomFee + extraFee
  checkoutPreview.value = {
    roomId: room.id,
    roomFee,
    extraFee,
    totalAmount,
  }
}

async function handleFinalCheckout(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return
  actionLoading.value = true
  rowMessage.value = null
  try {
    const res = await api.checkout(room.activeOrder.id)
    rowMessage.value = {
      roomId: room.id,
      type: 'success',
      text: `${res.msg}，应收总额：¥${res.bill.total_amount.toFixed(2)}（房费 ¥${res.bill.room_fee} + 杂费 ¥${res.bill.extra_fee}）`,
    }
    checkoutPreview.value = null
    emit('refresh')
    setTimeout(() => {
      if (expandedRoomId.value === room.id && rowMessage.value?.type === 'success') {
        expandedRoomId.value = null
      }
    }, 2500)
  } catch (err) {
    rowMessage.value = { roomId: room.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}

// 4. Fast check-in directly for this available room
async function handleFastCreateOrder(room: RoomWithActiveOrder) {
  if (!fastForm.value.guest_name.trim()) {
    rowMessage.value = { roomId: room.id, type: 'error', text: '请输入客人姓名' }
    return
  }
  if (!fastForm.value.phone.trim()) {
    rowMessage.value = { roomId: room.id, type: 'error', text: '请输入联系电话' }
    return
  }
  if (!fastForm.value.id_card.trim()) {
    rowMessage.value = { roomId: room.id, type: 'error', text: '请输入身份证号' }
    return
  }

  actionLoading.value = true
  rowMessage.value = null
  try {
    const res = await api.createOrder({
      room_type: room.type,
      guest_name: fastForm.value.guest_name.trim(),
      phone: fastForm.value.phone.trim(),
      id_card: fastForm.value.id_card.trim(),
      days: Number(fastForm.value.days) || 1,
      mode: fastForm.value.mode,
    })
    rowMessage.value = {
      roomId: room.id,
      type: 'success',
      text: `${res.msg}，分配房号：${res.room_number}`,
    }
    emit('refresh')
    setTimeout(() => {
      expandedRoomId.value = null
    }, 1500)
  } catch (err) {
    rowMessage.value = { roomId: room.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}

// 5. Bottom Notion-style Append Row Submit
async function handleBottomCreateOrder() {
  if (!bottomForm.value.guest_name.trim()) {
    bottomMessage.value = { type: 'error', text: '请输入客人姓名' }
    return
  }
  if (!bottomForm.value.phone.trim()) {
    bottomMessage.value = { type: 'error', text: '请输入联系电话' }
    return
  }
  if (!bottomForm.value.id_card.trim()) {
    bottomMessage.value = { type: 'error', text: '请输入身份证号' }
    return
  }

  actionLoading.value = true
  bottomMessage.value = null
  try {
    const res = await api.createOrder({
      room_type: bottomForm.value.room_type,
      guest_name: bottomForm.value.guest_name.trim(),
      phone: bottomForm.value.phone.trim(),
      id_card: bottomForm.value.id_card.trim(),
      days: Number(bottomForm.value.days) || 1,
      mode: bottomForm.value.mode,
    })
    bottomMessage.value = {
      type: 'success',
      text: `${res.msg}，已自动排入房号 ${res.room_number}（订单号 #${res.order_id}）`,
    }
    // reset form inputs
    bottomForm.value.guest_name = ''
    bottomForm.value.phone = ''
    bottomForm.value.id_card = ''
    bottomForm.value.days = 1
    emit('refresh')
    setTimeout(() => {
      if (bottomMessage.value?.type === 'success') {
        isBottomAdding.value = false
        bottomMessage.value = null
      }
    }, 2000)
  } catch (err) {
    bottomMessage.value = { type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col h-full overflow-hidden">
    <!-- Header: Title & Real-time Stats Pills -->
    <header class="h-14 px-6 border-b border-neutral-200/50 dark:border-neutral-800/50 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center space-x-4">
        <h1 class="text-sm font-semibold tracking-wide text-neutral-900 dark:text-neutral-100 font-mono">
          客房与实时房态 (ROOMS)
        </h1>

        <!-- Notion-style inline minimalist stats strip -->
        <div v-if="stats" class="hidden sm:flex items-center space-x-2 text-[11px] font-mono">
          <span class="text-neutral-400">总计 {{ stats.totals }} 间</span>
          <span class="text-neutral-300 dark:text-neutral-700">/</span>
          <span class="inline-flex items-center text-emerald-600 dark:text-emerald-400">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1"></span>
            空闲 {{ stats.available }}
          </span>
          <span class="text-neutral-300 dark:text-neutral-700">/</span>
          <span class="inline-flex items-center text-amber-600 dark:text-amber-400">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1"></span>
            预订 {{ stats.reserved }}
          </span>
          <span class="text-neutral-300 dark:text-neutral-700">/</span>
          <span class="inline-flex items-center text-sky-600 dark:text-sky-400">
            <span class="w-1.5 h-1.5 rounded-full bg-sky-500 mr-1"></span>
            在住 {{ stats.occupied }}
          </span>
          <span class="text-neutral-300 dark:text-neutral-700">/</span>
          <span class="font-semibold text-neutral-800 dark:text-neutral-200">
            入住率 {{ stats.occupancy_rate }}
          </span>
        </div>
      </div>

      <!-- Header Right: Refresh -->
      <button
        class="inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100 rounded transition-colors"
        :disabled="loading"
        @click="emit('refresh')"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
        <span>刷新</span>
      </button>
    </header>

    <!-- Sub-bar: Filter controls -->
    <div class="h-10 px-6 border-b border-neutral-200/40 dark:border-neutral-800/40 flex items-center justify-between text-xs flex-shrink-0 bg-paper-100/30 dark:bg-obsidian-900/30">
      <div class="flex items-center space-x-4">
        <!-- Status Filter Segment -->
        <div class="flex items-center space-x-1 text-[11px] font-mono">
          <button
            class="px-2 py-0.5 rounded transition-colors"
            :class="selectedStatus === 'ALL' ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900' : 'text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-200'"
            @click="selectedStatus = 'ALL'"
          >
            全部
          </button>
          <button
            class="px-2 py-0.5 rounded transition-colors"
            :class="selectedStatus === 'available' ? 'bg-emerald-600 text-white' : 'text-neutral-500 hover:text-emerald-500'"
            @click="selectedStatus = 'available'"
          >
            空闲
          </button>
          <button
            class="px-2 py-0.5 rounded transition-colors"
            :class="selectedStatus === 'occupied' ? 'bg-sky-600 text-white' : 'text-neutral-500 hover:text-sky-500'"
            @click="selectedStatus = 'occupied'"
          >
            在住
          </button>
          <button
            class="px-2 py-0.5 rounded transition-colors"
            :class="selectedStatus === 'reserved' ? 'bg-amber-600 text-white' : 'text-neutral-500 hover:text-amber-500'"
            @click="selectedStatus = 'reserved'"
          >
            预订
          </button>
        </div>

        <!-- Room Type Filter Dropdown / Pills -->
        <div v-if="roomTypes.length > 1" class="hidden md:flex items-center space-x-1 text-[11px]">
          <span class="text-neutral-400 mr-1 font-mono">房型:</span>
          <button
            class="px-1.5 py-0.5 rounded transition-colors"
            :class="selectedType === 'ALL' ? 'underline font-medium text-neutral-900 dark:text-neutral-100' : 'text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300'"
            @click="selectedType = 'ALL'"
          >
            全部
          </button>
          <button
            v-for="t in roomTypes"
            :key="t"
            class="px-1.5 py-0.5 rounded transition-colors"
            :class="selectedType === t ? 'underline font-medium text-neutral-900 dark:text-neutral-100' : 'text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300'"
            @click="selectedType = t"
          >
            {{ t }}
          </button>
        </div>
      </div>

      <!-- Search Input -->
      <div class="relative w-48 sm:w-64">
        <Search class="w-3.5 h-3.5 absolute left-2.5 top-2 text-neutral-400 pointer-events-none" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="过滤房号、房型或住客..."
          class="w-full pl-8 pr-3 py-1 text-xs bg-transparent border border-neutral-300/60 dark:border-neutral-700/60 rounded text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-500 font-mono"
        />
      </div>
    </div>

    <!-- Table Container -->
    <div class="flex-1 overflow-auto px-6 py-6">
      <div class="w-full border-t border-b border-neutral-200/60 dark:border-neutral-800/60 text-xs">
        <!-- Table Header Row -->
        <div class="grid grid-cols-12 py-2 px-3 text-[11px] font-mono uppercase tracking-wider text-neutral-400 dark:text-neutral-500 border-b border-neutral-200/40 dark:border-neutral-800/40 select-none">
          <div class="col-span-2">房号</div>
          <div class="col-span-3">房型与单价</div>
          <div class="col-span-5">实时房态 / 当前住客与消费</div>
          <div class="col-span-2 text-right">操作流转</div>
        </div>

        <!-- Room Rows with Inline Expansion -->
        <template v-for="room in filteredRooms" :key="room.id">
          <!-- Main Row -->
          <div
            class="grid grid-cols-12 py-2.5 px-3 items-center border-b border-neutral-200/30 dark:border-neutral-800/30 hover:bg-neutral-100/50 dark:hover:bg-neutral-900/40 transition-colors cursor-pointer select-none group"
            :class="{ 'bg-neutral-100/70 dark:bg-neutral-900/60': expandedRoomId === room.id }"
            @click="toggleExpand(room)"
          >
            <!-- 房号 -->
            <div class="col-span-2 flex items-center space-x-2 font-mono font-semibold text-neutral-900 dark:text-neutral-100">
              <span
                class="w-2 h-2 rounded-full flex-shrink-0"
                :class="{
                  'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]': room.status === 'available',
                  'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]': room.status === 'reserved',
                  'bg-sky-500 shadow-[0_0_8px_rgba(14,165,233,0.5)]': room.status === 'occupied',
                }"
              ></span>
              <span class="text-sm">{{ room.number }}</span>
            </div>

            <!-- 房型与单价 -->
            <div class="col-span-3 flex items-baseline space-x-2">
              <span class="text-neutral-700 dark:text-neutral-200 font-medium">{{ room.type }}</span>
              <span class="text-neutral-400 text-[11px] font-mono">¥{{ room.price }}/晚</span>
            </div>

            <!-- 房态与当前住客 -->
            <div class="col-span-5">
              <div v-if="room.status === 'available'" class="text-emerald-600 dark:text-emerald-400 font-mono text-[11px] flex items-center space-x-1">
                <span>空闲可用</span>
                <span class="text-neutral-400">· 可随时办理入住/预订</span>
              </div>

              <div v-else-if="room.status === 'reserved' && room.activeOrder" class="text-amber-600 dark:text-amber-400 text-xs flex items-center space-x-2">
                <span class="font-mono text-[11px] font-medium">已预订:</span>
                <span class="font-semibold text-neutral-800 dark:text-neutral-200">{{ room.activeOrder.guest_name }}</span>
                <span class="text-neutral-400 font-mono text-[11px]">{{ room.activeOrder.phone }}</span>
                <span class="text-neutral-400 font-mono text-[11px]">(预订 {{ room.activeOrder.days }} 晚)</span>
              </div>

              <div v-else-if="room.status === 'occupied' && room.activeOrder" class="text-sky-600 dark:text-sky-400 text-xs flex items-center space-x-2">
                <span class="font-mono text-[11px] font-medium">在住:</span>
                <span class="font-semibold text-neutral-800 dark:text-neutral-200">{{ room.activeOrder.guest_name }}</span>
                <span class="text-neutral-400 font-mono text-[11px]">{{ room.activeOrder.phone }}</span>
                <span class="text-neutral-400 font-mono text-[11px]">· 住 {{ room.activeOrder.days }} 天</span>
                <span
                  v-if="room.activeOrder.extra_fee > 0"
                  class="font-mono text-[10px] px-1 py-0.5 rounded bg-sky-100 dark:bg-sky-950/80 text-sky-700 dark:text-sky-300"
                >
                  杂费 ¥{{ room.activeOrder.extra_fee.toFixed(2) }}
                </span>
              </div>

              <div v-else class="text-neutral-400 font-mono text-[11px]">
                {{ room.status }}
              </div>
            </div>

            <!-- 右侧操作引导与折叠图标 -->
            <div class="col-span-2 text-right flex items-center justify-end space-x-2 text-neutral-400 group-hover:text-neutral-700 dark:group-hover:text-neutral-200">
              <span class="text-[11px] font-mono">
                {{ expandedRoomId === room.id ? '收起' : room.status === 'available' ? '办理开房' : room.status === 'reserved' ? '转入住' : '记账/结账' }}
              </span>
              <ChevronUp v-if="expandedRoomId === room.id" class="w-3.5 h-3.5" />
              <ChevronDown v-else class="w-3.5 h-3.5" />
            </div>
          </div>

          <!-- Inline Expanded Work Zone (Zero modal, Zero popup) -->
          <div
            v-if="expandedRoomId === room.id"
            class="border-b border-neutral-200/60 dark:border-neutral-800/60 bg-neutral-50/70 dark:bg-neutral-900/70 p-4 transition-all"
          >
            <!-- 1. Occupied Room Actions -->
            <div v-if="room.status === 'occupied' && room.activeOrder" class="space-y-4">
              <!-- Guest Metadata Strip -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-3 border-b border-neutral-200/40 dark:border-neutral-800/40 text-xs font-mono">
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">住客姓名</span>
                  <span class="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">{{ room.activeOrder.guest_name }}</span>
                </div>
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">联系电话 / 证件</span>
                  <span class="text-neutral-700 dark:text-neutral-300">{{ room.activeOrder.phone }}</span>
                  <span class="block text-[11px] text-neutral-400">{{ room.activeOrder.id_card }}</span>
                </div>
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">已住天数 / 单价</span>
                  <span class="text-neutral-700 dark:text-neutral-300">{{ room.activeOrder.days }} 天 (¥{{ room.price }}/晚)</span>
                </div>
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">当前累计消费</span>
                  <span class="text-neutral-900 dark:text-neutral-100 font-semibold">
                    ¥{{ (room.activeOrder.days * room.price + room.activeOrder.extra_fee).toFixed(2) }}
                  </span>
                  <span class="block text-[10px] text-neutral-400">
                    (房费 ¥{{ room.activeOrder.days * room.price }} + 杂费 ¥{{ room.activeOrder.extra_fee }})
                  </span>
                </div>
              </div>

              <!-- Dual Inline Action Strip: Add Extra Fee & Checkout -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-1">
                <!-- Action A: 追加消费记账 -->
                <div class="space-y-2">
                  <div class="flex items-center space-x-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300">
                    <Receipt class="w-3.5 h-3.5 text-neutral-500" />
                    <span>追加在住消费记账 (餐饮/迷你吧/干洗)</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <div class="relative flex-1">
                      <span class="absolute left-2.5 top-1.5 text-neutral-400 font-mono text-xs">¥</span>
                      <input
                        v-model="extraAmount"
                        type="number"
                        min="1"
                        placeholder="输入消费金额"
                        class="w-full pl-6 pr-3 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                        @keydown.enter="handleAddExtraFee(room)"
                      />
                    </div>
                    <button
                      class="px-3 py-1.5 text-xs font-mono font-medium rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50"
                      :disabled="actionLoading"
                      @click="handleAddExtraFee(room)"
                    >
                      确认记账
                    </button>
                  </div>
                </div>

                <!-- Action B: 退房核算结算 -->
                <div class="space-y-2">
                  <div class="flex items-center space-x-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300">
                    <LogOut class="w-3.5 h-3.5 text-neutral-500" />
                    <span>退房与核算结算</span>
                  </div>

                  <div v-if="!checkoutPreview || checkoutPreview.roomId !== room.id">
                    <button
                      class="px-3 py-1.5 text-xs font-mono font-medium rounded border border-rose-300 dark:border-rose-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors"
                      @click="prepareCheckout(room)"
                    >
                      核算账单并办理退房
                    </button>
                  </div>

                  <!-- Checkout Confirmation Inline Box -->
                  <div v-else class="p-2.5 rounded border border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/30 space-y-2 text-xs">
                    <div class="flex justify-between items-center font-mono">
                      <span class="text-neutral-600 dark:text-neutral-400">房费 ({{ room.activeOrder.days }}天 × ¥{{ room.price }}):</span>
                      <span>¥{{ checkoutPreview.roomFee.toFixed(2) }}</span>
                    </div>
                    <div class="flex justify-between items-center font-mono">
                      <span class="text-neutral-600 dark:text-neutral-400">额外消费杂费:</span>
                      <span>¥{{ checkoutPreview.extraFee.toFixed(2) }}</span>
                    </div>
                    <div class="flex justify-between items-center font-mono font-bold text-sm text-neutral-900 dark:text-neutral-100 pt-1 border-t border-rose-200 dark:border-rose-900/60">
                      <span>应收总金额:</span>
                      <span class="text-rose-600 dark:text-rose-400">¥{{ checkoutPreview.totalAmount.toFixed(2) }}</span>
                    </div>

                    <div class="flex items-center justify-end space-x-2 pt-1">
                      <button
                        class="px-2.5 py-1 text-xs text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                        @click="checkoutPreview = null"
                      >
                        取消
                      </button>
                      <button
                        class="px-3 py-1 text-xs font-mono font-medium rounded bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50"
                        :disabled="actionLoading"
                        @click="handleFinalCheckout(room)"
                      >
                        确认结账并释放房间
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. Reserved Room Actions -->
            <div v-else-if="room.status === 'reserved' && room.activeOrder" class="space-y-3">
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono pb-2 border-b border-neutral-200/40 dark:border-neutral-800/40">
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">预订客人</span>
                  <span class="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">{{ room.activeOrder.guest_name }}</span>
                </div>
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">联系电话 / 证件</span>
                  <span class="text-neutral-700 dark:text-neutral-300">{{ room.activeOrder.phone }}</span>
                  <span class="block text-[11px] text-neutral-400">{{ room.activeOrder.id_card }}</span>
                </div>
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">预定入住天数</span>
                  <span class="text-neutral-700 dark:text-neutral-300">{{ room.activeOrder.days }} 天 (¥{{ room.price }}/晚)</span>
                </div>
                <div>
                  <span class="text-neutral-400 block text-[10px] uppercase">预订时间</span>
                  <span class="text-neutral-400 text-[11px]">{{ room.activeOrder.created_at }}</span>
                </div>
              </div>

              <div class="flex items-center justify-between pt-1">
                <span class="text-xs text-neutral-500">
                  客人已到店？点击即可直接将其转换为在住状态。
                </span>
                <button
                  class="px-3.5 py-1.5 text-xs font-mono font-medium rounded bg-amber-600 text-white hover:bg-amber-700 transition-colors disabled:opacity-50 flex items-center space-x-1.5"
                  :disabled="actionLoading"
                  @click="handleConfirmCheckin(room)"
                >
                  <UserCheck class="w-3.5 h-3.5" />
                  <span>确认为正式入住</span>
                </button>
              </div>
            </div>

            <!-- 3. Available Room Actions (Direct Fast Check-in for this room) -->
            <div v-else-if="room.status === 'available'" class="space-y-3">
              <div class="text-xs font-medium text-neutral-800 dark:text-neutral-200 flex items-center justify-between">
                <span>为客房 {{ room.number }} ({{ room.type }} · ¥{{ room.price }}/晚) 办理开房</span>
                <span class="text-[11px] text-neutral-400 font-mono">就地录入 · 无遮罩流转</span>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-5 gap-3 items-center">
                <div>
                  <input
                    v-model="fastForm.guest_name"
                    type="text"
                    placeholder="住客姓名"
                    class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500"
                  />
                </div>
                <div>
                  <input
                    v-model="fastForm.phone"
                    type="text"
                    placeholder="联系电话 (手机号)"
                    class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                  />
                </div>
                <div>
                  <input
                    v-model="fastForm.id_card"
                    type="text"
                    placeholder="身份证号码"
                    class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                  />
                </div>
                <div class="flex items-center space-x-1.5">
                  <input
                    v-model="fastForm.days"
                    type="number"
                    min="1"
                    placeholder="天数"
                    class="w-16 px-2 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                  />
                  <span class="text-xs text-neutral-400">天</span>
                  <select
                    v-model="fastForm.mode"
                    class="px-2 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500"
                  >
                    <option value="checkin">直接入住</option>
                    <option value="reserved">预订保留</option>
                  </select>
                </div>
                <div class="flex justify-end">
                  <button
                    class="w-full sm:w-auto px-4 py-1.5 text-xs font-mono font-medium rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50"
                    :disabled="actionLoading"
                    @click="handleFastCreateOrder(room)"
                  >
                    {{ fastForm.mode === 'checkin' ? '立即开房入住' : '保存预订' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Inline Action Feedback Message Strip -->
            <div
              v-if="rowMessage && rowMessage.roomId === room.id"
              class="mt-2.5 text-[11px] font-mono flex items-center space-x-1.5"
              :class="rowMessage.type === 'success' ? 'text-emerald-500' : 'text-rose-500'"
            >
              <CheckCircle2 v-if="rowMessage.type === 'success'" class="w-3.5 h-3.5 flex-shrink-0" />
              <AlertCircle v-else class="w-3.5 h-3.5 flex-shrink-0" />
              <span>{{ rowMessage.text }}</span>
            </div>
          </div>
        </template>

        <!-- Notion-style Inline Append Row at table bottom (+ New Booking / Order) -->
        <div v-if="!isBottomAdding" class="py-2.5 px-3">
          <button
            class="inline-flex items-center space-x-2 text-xs text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors py-1 group"
            @click="isBottomAdding = true"
          >
            <Plus class="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            <span class="font-mono">+ New Booking / Check-in (新建预订或直接开房)</span>
          </button>
        </div>

        <!-- Inline Adding Form at table bottom -->
        <div
          v-else
          class="border-b border-neutral-200/60 dark:border-neutral-800/60 bg-neutral-50/70 dark:bg-neutral-900/60 p-4 space-y-3 transition-all"
        >
          <div class="flex items-center justify-between text-xs font-mono text-neutral-400 pb-1 border-b border-neutral-200/30 dark:border-neutral-800/30">
            <span>新建前台订单 (系统将按房号升序自动分配首个可用房)</span>
            <button
              class="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
              @click="isBottomAdding = false"
            >
              取消
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-6 gap-3 items-center">
            <!-- 房型 -->
            <div>
              <label class="block text-[10px] text-neutral-400 font-mono mb-1">目标房型</label>
              <select
                v-model="bottomForm.room_type"
                class="w-full px-2 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500"
              >
                <option v-for="t in roomTypes" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>

            <!-- 客人姓名 -->
            <div>
              <label class="block text-[10px] text-neutral-400 font-mono mb-1">住客姓名</label>
              <input
                v-model="bottomForm.guest_name"
                type="text"
                placeholder="姓名"
                class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500"
              />
            </div>

            <!-- 手机号 -->
            <div>
              <label class="block text-[10px] text-neutral-400 font-mono mb-1">联系电话</label>
              <input
                v-model="bottomForm.phone"
                type="text"
                placeholder="手机号"
                class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
              />
            </div>

            <!-- 身份证 -->
            <div>
              <label class="block text-[10px] text-neutral-400 font-mono mb-1">身份证号</label>
              <input
                v-model="bottomForm.id_card"
                type="text"
                placeholder="证件号码"
                class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
              />
            </div>

            <!-- 天数与模式 -->
            <div class="flex items-center space-x-1.5">
              <div>
                <label class="block text-[10px] text-neutral-400 font-mono mb-1">天数</label>
                <input
                  v-model="bottomForm.days"
                  type="number"
                  min="1"
                  class="w-14 px-2 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                />
              </div>
              <div class="flex-1">
                <label class="block text-[10px] text-neutral-400 font-mono mb-1">办理模式</label>
                <select
                  v-model="bottomForm.mode"
                  class="w-full px-2 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500"
                >
                  <option value="checkin">直接入住</option>
                  <option value="reserved">提前预订</option>
                </select>
              </div>
            </div>

            <!-- 提交按钮 -->
            <div class="pt-4">
              <button
                class="w-full px-4 py-1.5 text-xs font-mono font-medium rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50"
                :disabled="actionLoading"
                @click="handleBottomCreateOrder"
              >
                确认下单
              </button>
            </div>
          </div>

          <!-- Bottom Inline Feedback Strip -->
          <div
            v-if="bottomMessage"
            class="text-[11px] font-mono flex items-center space-x-1.5 pt-1"
            :class="bottomMessage.type === 'success' ? 'text-emerald-500' : 'text-rose-500'"
          >
            <CheckCircle2 v-if="bottomMessage.type === 'success'" class="w-3.5 h-3.5 flex-shrink-0" />
            <AlertCircle v-else class="w-3.5 h-3.5 flex-shrink-0" />
            <span>{{ bottomMessage.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
