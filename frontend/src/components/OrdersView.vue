<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Search,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Receipt,
  LogOut,
  UserCheck,
  CheckCircle2,
  AlertCircle,
} from 'lucide-vue-next'
import type { Order } from '../types'
import { api, extractErrorMessage } from '../api'

const props = defineProps<{
  orders: Order[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const searchKeyword = ref('')
const selectedStatus = ref<'ALL' | 'reserved' | 'checked_in' | 'completed'>('ALL')
const expandedOrderId = ref<number | null>(null)

// Extra fee & checkout state
const extraAmount = ref<number | ''>('')
const actionLoading = ref(false)
const orderMessage = ref<{ orderId: number; type: 'success' | 'error'; text: string } | null>(null)

// Filtered orders
const filteredOrders = computed(() => {
  return props.orders.filter((o) => {
    if (selectedStatus.value !== 'ALL' && o.status !== selectedStatus.value) {
      return false
    }
    if (searchKeyword.value.trim()) {
      const q = searchKeyword.value.trim().toLowerCase()
      const matchName = o.guest_name.toLowerCase().includes(q)
      const matchPhone = o.phone.includes(q)
      const matchRoom = o.room_number?.toLowerCase().includes(q)
      const matchId = String(o.id).includes(q)
      return matchName || matchPhone || matchRoom || matchId
    }
    return true
  })
})

function toggleExpand(order: Order) {
  if (expandedOrderId.value === order.id) {
    expandedOrderId.value = null
  } else {
    expandedOrderId.value = order.id
    orderMessage.value = null
    extraAmount.value = ''
  }
}

// Confirm check-in
async function handleConfirmCheckin(order: Order) {
  actionLoading.value = true
  orderMessage.value = null
  try {
    const res = await api.confirmCheckin(order.id)
    orderMessage.value = { orderId: order.id, type: 'success', text: res.msg || '办理正式入住成功' }
    emit('refresh')
  } catch (err) {
    orderMessage.value = { orderId: order.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}

// Add extra fee
async function handleAddExtraFee(order: Order) {
  const amt = Number(extraAmount.value)
  if (!amt || amt <= 0) {
    orderMessage.value = { orderId: order.id, type: 'error', text: '请输入大于 0 的消费金额' }
    return
  }

  actionLoading.value = true
  orderMessage.value = null
  try {
    const res = await api.addExtraFee(order.id, amt)
    orderMessage.value = {
      orderId: order.id,
      type: 'success',
      text: `${res.msg}（当前累计额外杂费：¥${res.cur_extra_fee.toFixed(2)}）`,
    }
    extraAmount.value = ''
    emit('refresh')
  } catch (err) {
    orderMessage.value = { orderId: order.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}

async function handleFinalCheckout(order: Order) {
  actionLoading.value = true
  orderMessage.value = null
  try {
    const res = await api.checkout(order.id)
    orderMessage.value = {
      orderId: order.id,
      type: 'success',
      text: `${res.msg}，结算总金额：¥${res.bill.total_amount.toFixed(2)}（房费 ¥${res.bill.room_fee} + 杂费 ¥${res.bill.extra_fee}）`,
    }
    emit('refresh')
  } catch (err) {
    orderMessage.value = { orderId: order.id, type: 'error', text: extractErrorMessage(err) }
  } finally {
    actionLoading.value = false
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <header class="h-14 px-6 border-b border-neutral-200/50 dark:border-neutral-800/50 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center space-x-4">
        <h1 class="text-sm font-semibold tracking-wide text-neutral-900 dark:text-neutral-100 font-mono">
          订单流水与住客客历 (ORDERS & GUEST HISTORY)
        </h1>
        <span class="text-xs text-neutral-400 font-mono">
          记录共 {{ orders.length }} 条
        </span>
      </div>

      <button
        class="inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100 rounded transition-colors"
        :disabled="loading"
        @click="emit('refresh')"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
        <span>刷新</span>
      </button>
    </header>

    <!-- Sub-bar: Filters & Search -->
    <div class="h-10 px-6 border-b border-neutral-200/40 dark:border-neutral-800/40 flex items-center justify-between text-xs flex-shrink-0 bg-paper-100/30 dark:bg-obsidian-900/30">
      <div class="flex items-center space-x-2 text-[11px] font-mono">
        <button
          class="px-2 py-0.5 rounded transition-colors"
          :class="selectedStatus === 'ALL' ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900' : 'text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-200'"
          @click="selectedStatus = 'ALL'"
        >
          全部订单
        </button>
        <button
          class="px-2 py-0.5 rounded transition-colors"
          :class="selectedStatus === 'checked_in' ? 'bg-sky-600 text-white' : 'text-neutral-500 hover:text-sky-500'"
          @click="selectedStatus = 'checked_in'"
        >
          在住中
        </button>
        <button
          class="px-2 py-0.5 rounded transition-colors"
          :class="selectedStatus === 'reserved' ? 'bg-amber-600 text-white' : 'text-neutral-500 hover:text-amber-500'"
          @click="selectedStatus = 'reserved'"
        >
          已预订
        </button>
        <button
          class="px-2 py-0.5 rounded transition-colors"
          :class="selectedStatus === 'completed' ? 'bg-neutral-600 text-white dark:bg-neutral-400 dark:text-neutral-900' : 'text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300'"
          @click="selectedStatus = 'completed'"
        >
          已归档退房
        </button>
      </div>

      <div class="relative w-56 sm:w-72">
        <Search class="w-3.5 h-3.5 absolute left-2.5 top-2 text-neutral-400 pointer-events-none" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索姓名、电话或房号..."
          class="w-full pl-8 pr-3 py-1 text-xs bg-transparent border border-neutral-300/60 dark:border-neutral-700/60 rounded text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-500 font-mono"
        />
      </div>
    </div>

    <!-- Table Container -->
    <div class="flex-1 overflow-auto px-6 py-6">
      <div class="w-full border-t border-b border-neutral-200/60 dark:border-neutral-800/60 text-xs">
        <!-- Table Header Row -->
        <div class="grid grid-cols-12 py-2 px-3 text-[11px] font-mono uppercase tracking-wider text-neutral-400 dark:text-neutral-500 border-b border-neutral-200/40 dark:border-neutral-800/40 select-none">
          <div class="col-span-1">单号</div>
          <div class="col-span-2">房号 / 房型</div>
          <div class="col-span-3">住客姓名 / 电话</div>
          <div class="col-span-2">入住天数 / 杂费</div>
          <div class="col-span-2">状态</div>
          <div class="col-span-2 text-right">下单时间</div>
        </div>

        <!-- Order Rows with Inline Expansion -->
        <template v-for="order in filteredOrders" :key="order.id">
          <div
            class="grid grid-cols-12 py-2.5 px-3 items-center border-b border-neutral-200/30 dark:border-neutral-800/30 hover:bg-neutral-100/50 dark:hover:bg-neutral-900/40 transition-colors cursor-pointer select-none font-mono"
            :class="{ 'bg-neutral-100/70 dark:bg-neutral-900/60': expandedOrderId === order.id }"
            @click="toggleExpand(order)"
          >
            <!-- 订单号 -->
            <div class="col-span-1 text-neutral-400">
              #{{ order.id }}
            </div>

            <!-- 房号 / 房型 -->
            <div class="col-span-2 font-semibold text-neutral-900 dark:text-neutral-100 flex items-center space-x-1.5">
              <span>{{ order.room_number }}</span>
              <span class="font-normal font-sans text-[11px] text-neutral-500">{{ order.room_type }}</span>
            </div>

            <!-- 住客姓名 / 电话 -->
            <div class="col-span-3">
              <span class="font-semibold font-sans text-neutral-800 dark:text-neutral-200 mr-2">{{ order.guest_name }}</span>
              <span class="text-neutral-400 text-[11px]">{{ order.phone }}</span>
            </div>

            <!-- 入住天数 / 杂费 -->
            <div class="col-span-2 text-neutral-600 dark:text-neutral-300">
              <span>{{ order.days }} 天</span>
              <span v-if="order.extra_fee > 0" class="text-sky-600 dark:text-sky-400 ml-1.5 text-[11px]">
                (杂费 ¥{{ order.extra_fee }})
              </span>
            </div>

            <!-- 状态 -->
            <div class="col-span-2">
              <span
                v-if="order.status === 'checked_in'"
                class="inline-flex items-center text-[10px] text-sky-600 dark:text-sky-400 font-medium"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-sky-500 mr-1.5"></span>
                在住中
              </span>
              <span
                v-else-if="order.status === 'reserved'"
                class="inline-flex items-center text-[10px] text-amber-600 dark:text-amber-400 font-medium"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"></span>
                已预订
              </span>
              <span
                v-else
                class="inline-flex items-center text-[10px] text-neutral-400"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 mr-1.5"></span>
                已结账 (¥{{ order.total_amount ? Number(order.total_amount).toFixed(2) : '0' }})
              </span>
            </div>

            <!-- 时间与折叠箭头 -->
            <div class="col-span-2 text-right text-[11px] text-neutral-400 flex items-center justify-end space-x-1.5">
              <span>{{ order.created_at ? order.created_at.split(' ')[0] : '' }}</span>
              <ChevronUp v-if="expandedOrderId === order.id" class="w-3.5 h-3.5 text-neutral-500" />
              <ChevronDown v-else class="w-3.5 h-3.5" />
            </div>
          </div>

          <!-- Inline Expanded Detail & Operations Zone -->
          <div
            v-if="expandedOrderId === order.id"
            class="border-b border-neutral-200/60 dark:border-neutral-800/60 bg-neutral-50/70 dark:bg-neutral-900/70 p-4 transition-all"
          >
            <!-- Details Strip -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono pb-3 border-b border-neutral-200/40 dark:border-neutral-800/40">
              <div>
                <span class="text-neutral-400 block text-[10px] uppercase">住客身份证号</span>
                <span class="text-neutral-800 dark:text-neutral-200">{{ order.id_card || '-' }}</span>
              </div>
              <div>
                <span class="text-neutral-400 block text-[10px] uppercase">联系电话</span>
                <span class="text-neutral-800 dark:text-neutral-200">{{ order.phone }}</span>
              </div>
              <div>
                <span class="text-neutral-400 block text-[10px] uppercase">当前杂费 / 结算总计</span>
                <span class="text-neutral-800 dark:text-neutral-200 font-semibold">
                  {{ order.status === 'completed' ? `总计 ¥${Number(order.total_amount).toFixed(2)}` : `杂费 ¥${Number(order.extra_fee).toFixed(2)}` }}
                </span>
              </div>
              <div>
                <span class="text-neutral-400 block text-[10px] uppercase">创建完整时间</span>
                <span class="text-neutral-400">{{ order.created_at }}</span>
              </div>
            </div>

            <!-- Operations for In-Progress Orders -->
            <div v-if="order.status === 'checked_in'" class="pt-3 grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- 追加记账 -->
              <div class="space-y-2">
                <div class="flex items-center space-x-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300">
                  <Receipt class="w-3.5 h-3.5 text-neutral-500" />
                  <span>在住消费记账</span>
                </div>
                <div class="flex items-center space-x-2">
                  <div class="relative flex-1">
                    <span class="absolute left-2.5 top-1.5 text-neutral-400 font-mono text-xs">¥</span>
                    <input
                      v-model="extraAmount"
                      type="number"
                      min="1"
                      placeholder="金额"
                      class="w-full pl-6 pr-3 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                      @keydown.enter="handleAddExtraFee(order)"
                    />
                  </div>
                  <button
                    class="px-3 py-1.5 text-xs font-mono font-medium rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 disabled:opacity-50"
                    :disabled="actionLoading"
                    @click="handleAddExtraFee(order)"
                  >
                    记账
                  </button>
                </div>
              </div>

              <!-- 退房结算 -->
              <div class="space-y-2">
                <div class="flex items-center space-x-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300">
                  <LogOut class="w-3.5 h-3.5 text-neutral-500" />
                  <span>退房结算</span>
                </div>
                <button
                  class="px-3.5 py-1.5 text-xs font-mono font-medium rounded bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50"
                  :disabled="actionLoading"
                  @click="handleFinalCheckout(order)"
                >
                  办理退房结账并归档
                </button>
              </div>
            </div>

            <!-- Operations for Reserved Orders -->
            <div v-else-if="order.status === 'reserved'" class="pt-3 flex items-center justify-between">
              <span class="text-xs text-neutral-500">
                此订单处于预订锁定状态，客人到店后可直接转为在住。
              </span>
              <button
                class="px-3.5 py-1.5 text-xs font-mono font-medium rounded bg-amber-600 text-white hover:bg-amber-700 transition-colors disabled:opacity-50 flex items-center space-x-1.5"
                :disabled="actionLoading"
                @click="handleConfirmCheckin(order)"
              >
                <UserCheck class="w-3.5 h-3.5" />
                <span>确认转为正式入住</span>
              </button>
            </div>

            <!-- Completed Summary Receipt -->
            <div v-else class="pt-2 text-xs font-mono text-neutral-500 flex items-center space-x-3">
              <span>该订单已于结算后归档</span>
              <span class="text-neutral-300 dark:text-neutral-700">|</span>
              <span>最终核算总金额：¥{{ order.total_amount ? Number(order.total_amount).toFixed(2) : '0.00' }}</span>
            </div>

            <!-- Feedback Message -->
            <div
              v-if="orderMessage && orderMessage.orderId === order.id"
              class="mt-2.5 text-[11px] font-mono flex items-center space-x-1.5"
              :class="orderMessage.type === 'success' ? 'text-emerald-500' : 'text-rose-500'"
            >
              <CheckCircle2 v-if="orderMessage.type === 'success'" class="w-3.5 h-3.5 flex-shrink-0" />
              <AlertCircle v-else class="w-3.5 h-3.5 flex-shrink-0" />
              <span>{{ orderMessage.text }}</span>
            </div>
          </div>
        </template>

        <div v-if="filteredOrders.length === 0" class="py-8 text-center text-xs font-mono text-neutral-400">
          暂无匹配的订单记录
        </div>
      </div>
    </div>
  </div>
</template>
