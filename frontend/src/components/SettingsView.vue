<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Check, AlertCircle, RefreshCw } from 'lucide-vue-next'
import type { Room } from '../types'
import { api, extractErrorMessage } from '../api'

defineProps<{
  rooms: Room[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

// Inline add room state
const isAdding = ref(false)
const newNumber = ref('')
const newType = ref('标准间')
const newPrice = ref('180')
const submitting = ref(false)
const statusMessage = ref<{ type: 'success' | 'error'; text: string } | null>(null)

const standardTypes = ['标准间', '大床房', '商务双床房', '豪华套房', '行政单人间', '家庭亲子房']

function startAdd() {
  isAdding.value = true
  statusMessage.value = null
  newNumber.value = ''
}

function cancelAdd() {
  isAdding.value = false
  statusMessage.value = null
}

async function handleCreateRoom() {
  if (!newNumber.value.trim()) {
    statusMessage.value = { type: 'error', text: '请输入客房号（如 201）' }
    return
  }
  if (!newPrice.value || isNaN(Number(newPrice.value)) || Number(newPrice.value) <= 0) {
    statusMessage.value = { type: 'error', text: '请输入合法的房间单价' }
    return
  }

  submitting.value = true
  statusMessage.value = null
  try {
    const res = await api.addRoom({
      number: newNumber.value.trim(),
      type: newType.value.trim(),
      price: newPrice.value.trim(),
    })
    statusMessage.value = { type: 'success', text: res.msg || '客房添加成功' }
    newNumber.value = ''
    emit('refresh')
    setTimeout(() => {
      if (statusMessage.value?.type === 'success') {
        isAdding.value = false
        statusMessage.value = null
      }
    }, 1500)
  } catch (err) {
    statusMessage.value = { type: 'error', text: extractErrorMessage(err) }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <header class="h-14 px-6 border-b border-neutral-200/50 dark:border-neutral-800/50 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center space-x-3">
        <h1 class="text-sm font-semibold tracking-wide text-neutral-900 dark:text-neutral-100 font-mono">
          客房设置
        </h1>
        <span class="text-xs text-neutral-400 font-mono">
          共 {{ rooms.length }} 间客房
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

    <!-- Table Container -->
    <div class="flex-1 overflow-auto px-6 py-6">
      <div class="w-full border-t border-b border-neutral-200/60 dark:border-neutral-800/60 text-xs">
        <!-- Table Header Row -->
        <div class="grid grid-cols-12 py-2 px-3 text-[11px] font-mono uppercase tracking-wider text-neutral-400 dark:text-neutral-500 border-b border-neutral-200/40 dark:border-neutral-800/40 select-none">
          <div class="col-span-3">客房号</div>
          <div class="col-span-4">房型</div>
          <div class="col-span-3">每晚挂牌价</div>
          <div class="col-span-2 text-right">当前状态</div>
        </div>

        <!-- Room Rows -->
        <div
          v-for="room in rooms"
          :key="room.id"
          class="grid grid-cols-12 py-2.5 px-3 items-center border-b border-neutral-200/30 dark:border-neutral-800/30 hover:bg-neutral-100/50 dark:hover:bg-neutral-900/40 transition-colors font-mono"
        >
          <div class="col-span-3 font-semibold text-neutral-900 dark:text-neutral-100 flex items-center space-x-2">
            <span>{{ room.number }}</span>
          </div>

          <div class="col-span-4 text-neutral-600 dark:text-neutral-300 font-sans">
            {{ room.type }}
          </div>

          <div class="col-span-3 text-neutral-700 dark:text-neutral-200">
            ¥{{ Number(room.price).toFixed(2) }}
          </div>

          <div class="col-span-2 text-right">
            <span
              v-if="room.status === 'available'"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-sans font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
              空闲
            </span>
            <span
              v-else-if="room.status === 'reserved'"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-sans font-medium bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"></span>
              预订
            </span>
            <span
              v-else
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-sans font-medium bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5"></span>
              在住
            </span>
          </div>
        </div>

        <!-- Inline Append Row (Notion-style + New) -->
        <div v-if="!isAdding" class="py-2.5 px-3">
          <button
            class="inline-flex items-center space-x-2 text-xs text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors py-1 group"
            @click="startAdd"
          >
            <Plus class="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            <span>新增客房</span>
          </button>
        </div>

        <!-- Inline Adding Form Row -->
        <div
          v-else
          class="animate-panel-in border-b border-neutral-200/60 dark:border-neutral-800/60 bg-neutral-50/70 dark:bg-neutral-900/60 p-3 space-y-2.5 transition-all"
        >
          <div class="grid grid-cols-12 gap-3 items-center">
            <div class="col-span-3">
              <input
                v-model="newNumber"
                type="text"
                placeholder="房号 (如 302)"
                class="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                @keydown.enter="handleCreateRoom"
              />
            </div>

            <div class="col-span-4 flex items-center space-x-1.5">
              <select
                v-model="newType"
                class="w-full px-2 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500"
              >
                <option v-for="t in standardTypes" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>

            <div class="col-span-3">
              <div class="relative">
                <span class="absolute left-2.5 top-1.5 text-neutral-400 font-mono text-xs">¥</span>
                <input
                  v-model="newPrice"
                  type="number"
                  step="10"
                  placeholder="单价 (元/晚)"
                  class="w-full pl-6 pr-2.5 py-1.5 text-xs bg-white dark:bg-obsidian-900 border border-neutral-300/70 dark:border-neutral-700 rounded text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-500 font-mono"
                  @keydown.enter="handleCreateRoom"
                />
              </div>
            </div>

            <div class="col-span-2 flex items-center justify-end space-x-2">
              <button
                class="px-2.5 py-1.5 text-xs font-mono font-medium rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center space-x-1"
                :disabled="submitting"
                @click="handleCreateRoom"
              >
                <Check class="w-3 h-3" />
                <span>{{ submitting ? '保存中' : '保存' }}</span>
              </button>
              <button
                class="px-2 py-1.5 text-xs text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors"
                @click="cancelAdd"
              >
                取消
              </button>
            </div>
          </div>

          <!-- Inline Status/Feedback Banner -->
          <div
            v-if="statusMessage"
            class="text-[11px] font-mono flex items-center space-x-1.5 pt-1"
            :class="statusMessage.type === 'success' ? 'text-emerald-500' : 'text-rose-500'"
          >
            <AlertCircle class="w-3.5 h-3.5 flex-shrink-0" />
            <span>{{ statusMessage.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
