<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from "vue";
import {
  Search,
  ChevronDown,
  UserCheck,
  Receipt,
  LogOut,
  Trash2,
  AlertCircle,
  CheckCircle2,
} from "lucide-vue-next";
import type { RoomWithActiveOrder, RoomStats } from "../types";
import { api, extractErrorMessage } from "../api";

const props = defineProps<{
  rooms: RoomWithActiveOrder[];
  stats?: RoomStats;
  loading: boolean;
}>();

const emit = defineEmits<{
  (e: "refresh"): void;
}>();

// Filter state
const searchKeyword = ref("");
const selectedType = ref("ALL");
const selectedStatus = ref<"ALL" | "available" | "occupied" | "reserved">(
  "ALL",
);

// Expanded row ID
const expandedRoomId = ref<number | null>(null);

// Actions state inside expanded rows
const extraAmount = ref<number | "">("");
const actionLoading = ref(false);
const confirmingDeleteRoomId = ref<number | null>(null);
const rowMessage = ref<{
  roomId: number;
  type: "success" | "error";
  text: string;
} | null>(null);

// Checkout preview state
const checkoutPreview = ref<{
  roomId: number;
  roomFee: number;
  extraFee: number;
  totalAmount: number;
} | null>(null);

// Available room fast check-in form state
const fastForm = ref<{
  guest_name: string;
  phone: string;
  id_card: string;
  days: number;
  mode: "checkin" | "reserved";
}>({
  guest_name: "",
  phone: "",
  id_card: "",
  days: 1,
  mode: "checkin",
});

// Top-level "+ 新建订单" inline panel state
const isCreatingOrder = ref(false);
const newOrderForm = ref<{
  room_type: string;
  guest_name: string;
  phone: string;
  id_card: string;
  days: number;
  mode: "checkin" | "reserved";
}>({
  room_type: "标准间",
  guest_name: "",
  phone: "",
  id_card: "",
  days: 1,
  mode: "checkin",
});
const newOrderMessage = ref<{ type: "success" | "error"; text: string } | null>(
  null,
);

// Unique room types
const roomTypes = computed(() => {
  const set = new Set<string>();
  props.rooms.forEach((r) => set.add(r.type));
  return Array.from(set);
});

watch(
  roomTypes,
  (types) => {
    if (types.length > 0 && !types.includes(newOrderForm.value.room_type)) {
      newOrderForm.value.room_type = types[0];
    }
  },
  { immediate: true },
);

// Occupancy rate calculation for top-right indicator
const occupancyRateText = computed(() => {
  if (props.stats?.occupancy_rate) {
    return props.stats.occupancy_rate;
  }
  const total = props.rooms.length;
  if (!total) return "0%";
  const occupied = props.rooms.filter((r) => r.status === "occupied").length;
  return `${Math.round((occupied / total) * 1000) / 10}%`;
});

const occupancyPercent = computed(() => {
  const numeric = parseFloat(occupancyRateText.value);
  if (isNaN(numeric)) return 0;
  return Math.min(100, Math.max(0, numeric));
});

// Status counts for Segmented Tabs
const statusTabs = computed(() => {
  const total = props.stats?.totals ?? props.rooms.length;
  const available =
    props.stats?.available ??
    props.rooms.filter((r) => r.status === "available").length;
  const occupied =
    props.stats?.occupied ??
    props.rooms.filter((r) => r.status === "occupied").length;
  const reserved =
    props.stats?.reserved ??
    props.rooms.filter((r) => r.status === "reserved").length;

  return [
    { value: "ALL" as const, label: "全部", count: total },
    { value: "available" as const, label: "空闲", count: available },
    { value: "occupied" as const, label: "在住", count: occupied },
    { value: "reserved" as const, label: "预订", count: reserved },
  ];
});

// Sliding pill indicator for Segmented Tabs
const tabElements = new Map<string, HTMLElement>();
const sliderStyle = ref<{
  transform: string;
  width: string;
  opacity: number;
}>({
  transform: "translateX(0px)",
  width: "0px",
  opacity: 0,
});

function setTabRef(val: string, el: unknown) {
  if (el instanceof HTMLElement) {
    tabElements.set(val, el);
  }
}

function updateSliderPosition() {
  const activeEl = tabElements.get(selectedStatus.value);
  if (!activeEl) return;
  sliderStyle.value = {
    transform: `translateX(${activeEl.offsetLeft}px)`,
    width: `${activeEl.offsetWidth}px`,
    opacity: 1,
  };
}

watch(
  [selectedStatus, statusTabs],
  () => {
    nextTick(updateSliderPosition);
  },
  { deep: true },
);

onMounted(() => {
  nextTick(() => {
    updateSliderPosition();
    setTimeout(updateSliderPosition, 60);
  });
});

// Filtered rooms
const filteredRooms = computed(() => {
  return props.rooms.filter((r) => {
    if (selectedType.value !== "ALL" && r.type !== selectedType.value) {
      return false;
    }
    if (selectedStatus.value !== "ALL" && r.status !== selectedStatus.value) {
      return false;
    }
    if (searchKeyword.value.trim()) {
      const q = searchKeyword.value.trim().toLowerCase();
      const matchNumber = r.number.toLowerCase().includes(q);
      const matchType = r.type.toLowerCase().includes(q);
      const matchGuest = r.activeOrder?.guest_name.toLowerCase().includes(q);
      const matchPhone = r.activeOrder?.phone.includes(q);
      return matchNumber || matchType || matchGuest || matchPhone;
    }
    return true;
  });
});

// Format estimated arrival / departure date from activeOrder
function formatGuestSchedule(room: RoomWithActiveOrder): string {
  const order = room.activeOrder;
  if (!order) return "";

  const days = Number(order.days) || 1;
  const rawDate = order.created_at ? order.created_at.trim().split(" ")[0] : "";
  const parts = rawDate.split("-").map(Number);

  if (parts.length === 3 && !parts.some(isNaN)) {
    const baseDate = new Date(parts[0], parts[1] - 1, parts[2]);
    if (!isNaN(baseDate.getTime())) {
      if (room.status === "occupied") {
        const leaveDate = new Date(baseDate);
        leaveDate.setDate(leaveDate.getDate() + days);
        const mm = String(leaveDate.getMonth() + 1).padStart(2, "0");
        const dd = String(leaveDate.getDate()).padStart(2, "0");
        return `预计 ${mm}-${dd} 14:00 离店`;
      } else if (room.status === "reserved") {
        const mm = String(baseDate.getMonth() + 1).padStart(2, "0");
        const dd = String(baseDate.getDate()).padStart(2, "0");
        return `预计 ${mm}-${dd} 到店 · 订 ${days} 晚`;
      }
    }
  }

  return room.status === "occupied"
    ? `共 ${days} 晚 · 预计 14:00 离店`
    : `预计今日到店 · 订 ${days} 晚`;
}

function getActionLabel(room: RoomWithActiveOrder): string {
  if (room.status === "available") return "办理入住";
  if (room.status === "reserved") return "确认入住";
  return "查看订单";
}

function toggleNewOrderPanel() {
  isCreatingOrder.value = !isCreatingOrder.value;
  newOrderMessage.value = null;
}

function toggleExpand(room: RoomWithActiveOrder) {
  if (expandedRoomId.value === room.id) {
    expandedRoomId.value = null;
  } else {
    expandedRoomId.value = room.id;
    rowMessage.value = null;
    checkoutPreview.value = null;
    confirmingDeleteRoomId.value = null;
    extraAmount.value = "";
    fastForm.value = {
      guest_name: "",
      phone: "",
      id_card: "",
      days: 1,
      mode: "checkin",
    };
  }
}

// 1. Confirm Check-in for reserved room
async function handleConfirmCheckin(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return;
  actionLoading.value = true;
  rowMessage.value = null;
  try {
    const res = await api.confirmCheckin(room.activeOrder.id);
    rowMessage.value = {
      roomId: room.id,
      type: "success",
      text: res.msg || "办理正式入住成功",
    };
    emit("refresh");
  } catch (err) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: extractErrorMessage(err),
    };
  } finally {
    actionLoading.value = false;
  }
}

// Delete active order for occupied or reserved room
async function handleDeleteActiveOrder(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return;
  actionLoading.value = true;
  rowMessage.value = null;
  try {
    await api.deleteOrder(room.activeOrder.id);
    confirmingDeleteRoomId.value = null;
    expandedRoomId.value = null;
    emit("refresh");
  } catch (err) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: extractErrorMessage(err),
    };
  } finally {
    actionLoading.value = false;
  }
}

// 2. Add extra fee for occupied room
async function handleAddExtraFee(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return;
  const amt = Number(extraAmount.value);
  if (!amt || amt <= 0) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: "请输入大于 0 的消费金额",
    };
    return;
  }

  actionLoading.value = true;
  rowMessage.value = null;
  try {
    const res = await api.addExtraFee(room.activeOrder.id, amt);
    rowMessage.value = {
      roomId: room.id,
      type: "success",
      text: `${res.msg}（当前累计杂费：¥${res.cur_extra_fee.toFixed(2)}）`,
    };
    extraAmount.value = "";
    emit("refresh");
  } catch (err) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: extractErrorMessage(err),
    };
  } finally {
    actionLoading.value = false;
  }
}

// 3. Prepare / Confirm checkout
function prepareCheckout(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return;
  const days = room.activeOrder.days || 1;
  const roomFee = days * room.price;
  const extraFee = room.activeOrder.extra_fee || 0;
  const totalAmount = roomFee + extraFee;
  checkoutPreview.value = {
    roomId: room.id,
    roomFee,
    extraFee,
    totalAmount,
  };
}

async function handleFinalCheckout(room: RoomWithActiveOrder) {
  if (!room.activeOrder) return;
  actionLoading.value = true;
  rowMessage.value = null;
  try {
    const res = await api.checkout(room.activeOrder.id);
    rowMessage.value = {
      roomId: room.id,
      type: "success",
      text: `${res.msg}，应收总额：¥${res.bill.total_amount.toFixed(2)}（房费 ¥${res.bill.room_fee} + 杂费 ¥${res.bill.extra_fee}）`,
    };
    checkoutPreview.value = null;
    emit("refresh");
    setTimeout(() => {
      if (
        expandedRoomId.value === room.id &&
        rowMessage.value?.type === "success"
      ) {
        expandedRoomId.value = null;
      }
    }, 2500);
  } catch (err) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: extractErrorMessage(err),
    };
  } finally {
    actionLoading.value = false;
  }
}

// 4. Fast check-in directly for an available room
async function handleFastCreateOrder(room: RoomWithActiveOrder) {
  if (!fastForm.value.guest_name.trim()) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: "请输入客人姓名",
    };
    return;
  }
  if (!fastForm.value.phone.trim()) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: "请输入联系电话",
    };
    return;
  }
  if (!fastForm.value.id_card.trim()) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: "请输入身份证号",
    };
    return;
  }

  actionLoading.value = true;
  rowMessage.value = null;
  try {
    const res = await api.createOrder({
      room_type: room.type,
      guest_name: fastForm.value.guest_name.trim(),
      phone: fastForm.value.phone.trim(),
      id_card: fastForm.value.id_card.trim(),
      days: Number(fastForm.value.days) || 1,
      mode: fastForm.value.mode,
    });
    rowMessage.value = {
      roomId: room.id,
      type: "success",
      text: `${res.msg}，分配房号：${res.room_number}`,
    };
    emit("refresh");
    setTimeout(() => {
      expandedRoomId.value = null;
    }, 1500);
  } catch (err) {
    rowMessage.value = {
      roomId: room.id,
      type: "error",
      text: extractErrorMessage(err),
    };
  } finally {
    actionLoading.value = false;
  }
}

// 5. Top "+ 新建订单" form submit
async function handleCreateNewOrder() {
  if (!newOrderForm.value.guest_name.trim()) {
    newOrderMessage.value = { type: "error", text: "请输入客人姓名" };
    return;
  }
  if (!newOrderForm.value.phone.trim()) {
    newOrderMessage.value = { type: "error", text: "请输入联系电话" };
    return;
  }
  if (!newOrderForm.value.id_card.trim()) {
    newOrderMessage.value = { type: "error", text: "请输入身份证号" };
    return;
  }

  actionLoading.value = true;
  newOrderMessage.value = null;
  try {
    const res = await api.createOrder({
      room_type: newOrderForm.value.room_type,
      guest_name: newOrderForm.value.guest_name.trim(),
      phone: newOrderForm.value.phone.trim(),
      id_card: newOrderForm.value.id_card.trim(),
      days: Number(newOrderForm.value.days) || 1,
      mode: newOrderForm.value.mode,
    });
    newOrderMessage.value = {
      type: "success",
      text: `${res.msg}，已自动分配房号 ${res.room_number}（订单 #${res.order_id}）`,
    };
    newOrderForm.value.guest_name = "";
    newOrderForm.value.phone = "";
    newOrderForm.value.id_card = "";
    newOrderForm.value.days = 1;
    emit("refresh");
    setTimeout(() => {
      if (newOrderMessage.value?.type === "success") {
        isCreatingOrder.value = false;
        newOrderMessage.value = null;
      }
    }, 1800);
  } catch (err) {
    newOrderMessage.value = { type: "error", text: extractErrorMessage(err) };
  } finally {
    actionLoading.value = false;
  }
}
</script>

<template>
  <div class="flex-1 min-w-0 w-full h-full overflow-y-auto overflow-x-hidden">
    <div
      class="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col min-w-0"
    >
      <!-- 1. 顶部 Header 与主操作区（极简扁平化，无斜杠统计文案，无卡片） -->
      <header
        class="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-neutral-200/70 dark:border-neutral-800/70"
      >
        <h1
          class="text-base font-semibold tracking-tight text-neutral-900 dark:text-neutral-100"
        >
          客房与房态
        </h1>

        <div class="flex items-center gap-5 flex-shrink-0">
          <!-- 入住率指示器（文字 + 极细微型进度条） -->
          <div class="flex items-center gap-2.5 text-xs">
            <span class="text-neutral-500 dark:text-neutral-400">入住率</span>
            <span
              class="font-semibold text-neutral-900 dark:text-neutral-100 tabular-nums"
              style="font-variant-numeric: tabular-nums"
            >
              {{ occupancyRateText }}
            </span>
            <div
              class="w-16 sm:w-20 h-1 bg-neutral-200/80 dark:bg-neutral-800 rounded-full overflow-hidden"
            >
              <div
                class="h-full bg-neutral-900 dark:bg-neutral-100 rounded-full transition-[width] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]"
                :style="{ width: `${occupancyPercent}%` }"
              ></div>
            </div>
          </div>

          <!-- + 新建订单 主按钮（黑底白字 Primary Button） -->
          <button
            type="button"
            class="inline-flex items-center justify-center px-3 py-1.5 text-xs font-medium rounded-md bg-neutral-900 text-white hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-200 transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] active:scale-[0.97]"
            @click="toggleNewOrderPanel"
          >
            <span>+ 新建订单</span>
          </button>
        </div>
      </header>

      <!-- 顶部行内新建订单区（仅水平分割线，无卡片外框，丝滑展开收起） -->
      <Transition name="drawer-expand">
        <div
          v-if="isCreatingOrder"
          class="py-4 border-b border-neutral-200/70 dark:border-neutral-800/70 space-y-3"
        >
        <div class="flex items-center justify-between text-xs">
          <span class="font-medium text-neutral-800 dark:text-neutral-200">
            新建入住或预订订单
          </span>
          <button
            type="button"
            class="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors"
            @click="isCreatingOrder = false"
          >
            收起
          </button>
        </div>

        <div
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end"
        >
          <div>
            <label class="block text-[11px] text-neutral-400 mb-1">房型</label>
            <select
              v-model="newOrderForm.room_type"
              class="w-full px-2.5 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300"
            >
              <option
                v-for="t in roomTypes"
                :key="t"
                :value="t"
                class="bg-white dark:bg-obsidian-900"
              >
                {{ t }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-[11px] text-neutral-400 mb-1"
              >住客姓名</label
            >
            <input
              v-model="newOrderForm.guest_name"
              type="text"
              placeholder="输入姓名"
              class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300"
            />
          </div>

          <div>
            <label class="block text-[11px] text-neutral-400 mb-1"
              >联系电话</label
            >
            <input
              v-model="newOrderForm.phone"
              type="text"
              placeholder="手机号码"
              class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
            />
          </div>

          <div>
            <label class="block text-[11px] text-neutral-400 mb-1"
              >身份证号</label
            >
            <input
              v-model="newOrderForm.id_card"
              type="text"
              placeholder="证件号码"
              class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
            />
          </div>

          <div class="flex items-end gap-2">
            <div class="w-16">
              <label class="block text-[11px] text-neutral-400 mb-1"
                >晚数</label
              >
              <input
                v-model="newOrderForm.days"
                type="number"
                min="1"
                class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
              />
            </div>
            <div class="flex-1">
              <label class="block text-[11px] text-neutral-400 mb-1"
                >类型</label
              >
              <select
                v-model="newOrderForm.mode"
                class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300"
              >
                <option value="checkin" class="bg-white dark:bg-obsidian-900">
                  直接入住
                </option>
                <option value="reserved" class="bg-white dark:bg-obsidian-900">
                  提前预订
                </option>
              </select>
            </div>
          </div>

          <div class="flex justify-end">
            <button
              type="button"
              class="w-full sm:w-auto px-4 py-1.5 text-xs font-medium rounded-md bg-neutral-900 text-white hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-200 transition-all duration-150 active:scale-[0.97] disabled:opacity-50"
              :disabled="actionLoading"
              @click="handleCreateNewOrder"
            >
              确认提交
            </button>
          </div>
        </div>

        <Transition name="fade-slide">
          <div
            v-if="newOrderMessage"
            class="text-xs flex items-center gap-1.5 pt-1"
            :class="
              newOrderMessage.type === 'success'
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-rose-600 dark:text-rose-400'
            "
          >
            <CheckCircle2
              v-if="newOrderMessage.type === 'success'"
              class="w-3.5 h-3.5 flex-shrink-0"
            />
            <AlertCircle v-else class="w-3.5 h-3.5 flex-shrink-0" />
            <span>{{ newOrderMessage.text }}</span>
          </div>
        </Transition>
      </div>
      </Transition>

      <!-- 2. 工具与筛选栏（统计与筛选二合一，带左右滑动阴影胶囊动效） -->
      <div
        class="flex flex-wrap items-center justify-between gap-3 py-3.5 border-b border-neutral-200/70 dark:border-neutral-800/70"
      >
        <!-- 左侧：带计数徽标与滑动阴影滑块的分段筛选器（Segmented Tabs） -->
        <div
          class="relative inline-flex items-center p-1 rounded-lg bg-neutral-100/80 dark:bg-neutral-900/80"
          role="tablist"
          aria-label="房态统计与筛选"
        >
          <!-- 滑动阴影背景滑块（从左向右/从右向左丝滑移动） -->
          <div
            class="pointer-events-none absolute top-1 bottom-1 left-0 rounded-md bg-white dark:bg-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.12),0_1px_2px_rgba(0,0,0,0.06)] dark:shadow-[0_1px_4px_rgba(0,0,0,0.45)] transition-[transform,width,opacity] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]"
            :style="sliderStyle"
          ></div>

          <button
            v-for="tab in statusTabs"
            :key="tab.value"
            :ref="(el) => setTabRef(tab.value, el)"
            type="button"
            role="tab"
            :aria-selected="selectedStatus === tab.value"
            class="relative z-10 inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors duration-200"
            :class="
              selectedStatus === tab.value
                ? 'text-neutral-900 dark:text-neutral-100'
                : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200'
            "
            @click="selectedStatus = tab.value"
          >
            <span>{{ tab.label }}</span>
            <span
              class="inline-flex items-center justify-center px-1.5 py-0.5 text-[11px] leading-none rounded-full transition-colors duration-200 tabular-nums"
              :class="
                selectedStatus === tab.value
                  ? 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700/80 dark:text-neutral-200'
                  : 'bg-neutral-200/70 text-neutral-500 dark:bg-neutral-800/80 dark:text-neutral-400'
              "
              style="font-variant-numeric: tabular-nums"
            >
              {{ tab.count }}
            </span>
          </button>
        </div>

        <!-- 右侧：搜索与房型下拉选择器（Select Dropdown，默认“所有房型”） -->
        <div class="flex items-center gap-3 flex-wrap">
          <div class="relative w-36 sm:w-44">
            <Search
              class="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none"
            />
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索房号或住客"
              class="w-full pl-7 pr-2 py-1 text-xs bg-transparent border-b border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-400 dark:focus:border-neutral-600 transition-colors"
            />
          </div>

          <select
            v-model="selectedType"
            aria-label="房型筛选"
            class="px-2.5 py-1 text-xs bg-transparent border-b border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 focus:outline-none focus:border-neutral-400 dark:focus:border-neutral-600 cursor-pointer"
          >
            <option value="ALL" class="bg-white dark:bg-obsidian-900">
              所有房型
            </option>
            <option
              v-for="t in roomTypes"
              :key="t"
              :value="t"
              class="bg-white dark:bg-obsidian-900"
            >
              {{ t }}
            </option>
          </select>
        </div>
      </div>

      <!-- 3. 极简无卡片列表（直接平铺在页面背景上，无外框或阴影容器） -->
      <div class="w-full min-w-0">
        <table class="w-full table-auto border-collapse text-left text-xs">
          <thead>
            <tr
              class="border-b border-neutral-200/70 dark:border-neutral-800/70 text-[11px] font-medium text-neutral-400 dark:text-neutral-500 select-none"
            >
              <th class="py-3 pr-4 font-medium">房号</th>
              <th class="py-3 px-4 font-medium">房型</th>
              <th class="py-3 px-4 font-medium">门市价</th>
              <th class="py-3 px-4 font-medium">房态</th>
              <th class="py-3 px-4 font-medium">当前住客</th>
              <th class="py-3 pl-4 font-medium text-right">操作</th>
            </tr>
          </thead>

          <tbody
            class="divide-y divide-neutral-200/50 dark:divide-neutral-800/50"
          >
            <template v-for="room in filteredRooms" :key="room.id">
              <!-- 主数据行 -->
              <tr
                class="group hover:bg-neutral-100/60 dark:hover:bg-neutral-800/30 transition-colors cursor-pointer"
                :class="{
                  'bg-neutral-100/70 dark:bg-neutral-800/40':
                    expandedRoomId === room.id,
                }"
                @click="toggleExpand(room)"
              >
                <!-- 房号 -->
                <td
                  class="py-3.5 pr-4 font-semibold text-neutral-900 dark:text-neutral-100 tabular-nums whitespace-nowrap"
                  style="font-variant-numeric: tabular-nums"
                >
                  {{ room.number }}
                </td>

                <!-- 房型 -->
                <td
                  class="py-3.5 px-4 text-neutral-700 dark:text-neutral-300 whitespace-nowrap"
                >
                  {{ room.type }}
                </td>

                <!-- 门市价 -->
                <td
                  class="py-3.5 px-4 text-neutral-700 dark:text-neutral-300 tabular-nums whitespace-nowrap"
                  style="font-variant-numeric: tabular-nums"
                >
                  ¥{{ room.price }}
                </td>

                <!-- 房态（柔和浅底圆角胶囊标签，内置小圆点） -->
                <td class="py-3.5 px-4 whitespace-nowrap">
                  <span
                    v-if="room.status === 'available'"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
                  >
                    <span
                      class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"
                    ></span>
                    空闲
                  </span>

                  <span
                    v-else-if="room.status === 'occupied'"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400"
                  >
                    <span
                      class="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5"
                    ></span>
                    在住
                  </span>

                  <span
                    v-else
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400"
                  >
                    <span
                      class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"
                    ></span>
                    预订
                  </span>
                </td>

                <!-- 当前住客（空闲时 — 占位；非空闲展示姓名及预计离店或到店时间） -->
                <td class="py-3.5 px-4 min-w-0">
                  <span
                    v-if="room.status === 'available' || !room.activeOrder"
                    class="text-neutral-300 dark:text-neutral-600 select-none"
                  >
                    —
                  </span>

                  <div
                    v-else
                    class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 min-w-0"
                  >
                    <span
                      class="font-medium text-neutral-900 dark:text-neutral-100 truncate"
                    >
                      {{ room.activeOrder.guest_name }}
                    </span>
                    <span
                      class="text-[11px] text-neutral-400 dark:text-neutral-500 tabular-nums whitespace-nowrap"
                      style="font-variant-numeric: tabular-nums"
                    >
                      {{ formatGuestSchedule(room) }}
                    </span>
                  </div>
                </td>

                <!-- 操作（右对齐，纯文字无底色 + 丝滑旋转指示） -->
                <td
                  class="py-3.5 pl-4 text-right whitespace-nowrap"
                  @click.stop
                >
                  <button
                    type="button"
                    class="inline-flex items-center justify-end gap-1 p-0 border-0 shadow-none bg-transparent hover:bg-transparent focus:bg-transparent active:bg-transparent text-xs font-medium text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 transition-colors duration-150"
                    @click="toggleExpand(room)"
                  >
                    <span>{{ getActionLabel(room) }}</span>
                    <ChevronDown
                      class="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-transform duration-200 ease-[cubic-bezier(0.16,1,0.3,1)]"
                      :class="{
                        'rotate-180 opacity-100': expandedRoomId === room.id,
                      }"
                    />
                  </button>
                </td>
              </tr>

              <!-- 行内展开操作区（扁平无卡片，仅水平细线与留白，丝滑入场动效） -->
              <tr
                v-if="expandedRoomId === room.id"
                class="bg-neutral-50/40 dark:bg-neutral-900/30"
              >
                <td colspan="6" class="py-4 px-3 sm:px-4">
                  <div class="animate-panel-in">
                  <!-- 1. 在住客房操作面板 -->
                  <div
                    v-if="room.status === 'occupied' && room.activeOrder"
                    class="space-y-4"
                  >
                    <div
                      class="grid grid-cols-2 sm:grid-cols-5 gap-4 pb-3 border-b border-neutral-200/50 dark:border-neutral-800/50 text-xs"
                    >
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >住客姓名</span
                        >
                        <span
                          class="font-semibold text-neutral-900 dark:text-neutral-100"
                        >
                          {{ room.activeOrder.guest_name }}
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >联系电话</span
                        >
                        <span
                          class="text-neutral-700 dark:text-neutral-300 tabular-nums"
                        >
                          {{ room.activeOrder.phone }}
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >证件号码</span
                        >
                        <span
                          class="text-neutral-700 dark:text-neutral-300 tabular-nums"
                        >
                          {{ room.activeOrder.id_card }}
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >入住晚数</span
                        >
                        <span
                          class="text-neutral-700 dark:text-neutral-300 tabular-nums"
                        >
                          {{ room.activeOrder.days }} 晚
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >当前累计消费</span
                        >
                        <span
                          class="text-neutral-900 dark:text-neutral-100 font-semibold tabular-nums"
                        >
                          ¥{{
                            (
                              room.activeOrder.days * room.price +
                              room.activeOrder.extra_fee
                            ).toFixed(2)
                          }}
                        </span>
                        <span
                          class="block text-[11px] text-neutral-400 tabular-nums"
                        >
                          房费 ¥{{ room.activeOrder.days * room.price }} · 杂费
                          ¥{{ room.activeOrder.extra_fee }}
                        </span>
                      </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-1">
                      <!-- 追加消费 -->
                      <div class="space-y-2">
                        <div
                          class="flex items-center gap-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300"
                        >
                          <Receipt class="w-3.5 h-3.5 text-neutral-500" />
                          <span>追加消费记账</span>
                        </div>
                        <div class="flex items-center gap-2">
                          <div class="relative flex-1">
                            <span
                              class="absolute left-2 top-1.5 text-neutral-400 text-xs"
                              >¥</span
                            >
                            <input
                              v-model="extraAmount"
                              type="number"
                              min="1"
                              placeholder="输入消费金额"
                              class="w-full pl-5 pr-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
                              @keydown.enter="handleAddExtraFee(room)"
                            />
                          </div>
                          <button
                            type="button"
                            class="px-3 py-1.5 text-xs font-medium rounded-md bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50"
                            :disabled="actionLoading"
                            @click="handleAddExtraFee(room)"
                          >
                            确认记账
                          </button>
                        </div>
                      </div>

                      <!-- 退房结算 -->
                      <div class="space-y-2">
                        <div
                          class="flex items-center gap-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300"
                        >
                          <LogOut class="w-3.5 h-3.5 text-neutral-500" />
                          <span>退房与账单核算</span>
                        </div>

                        <div
                          v-if="
                            !checkoutPreview ||
                            checkoutPreview.roomId !== room.id
                          "
                        >
                          <button
                            type="button"
                            class="px-3 py-1.5 text-xs font-medium text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 underline-offset-4 hover:underline transition-colors"
                            @click="prepareCheckout(room)"
                          >
                            核算账单并办理退房
                          </button>
                        </div>

                        <div
                          v-else
                          class="pt-2 border-t border-neutral-200/60 dark:border-neutral-800/60 space-y-2 text-xs"
                        >
                          <div
                            class="flex justify-between items-center tabular-nums"
                          >
                            <span class="text-neutral-500"
                              >房费（{{ room.activeOrder.days }} 晚 × ¥{{
                                room.price
                              }}）</span
                            >
                            <span
                              >¥{{ checkoutPreview.roomFee.toFixed(2) }}</span
                            >
                          </div>
                          <div
                            class="flex justify-between items-center tabular-nums"
                          >
                            <span class="text-neutral-500">额外杂费</span>
                            <span
                              >¥{{ checkoutPreview.extraFee.toFixed(2) }}</span
                            >
                          </div>
                          <div
                            class="flex justify-between items-center font-semibold text-neutral-900 dark:text-neutral-100 pt-1 border-t border-neutral-200/60 dark:border-neutral-800/60 tabular-nums"
                          >
                            <span>应收总额</span>
                            <span class="text-rose-600 dark:text-rose-400">
                              ¥{{ checkoutPreview.totalAmount.toFixed(2) }}
                            </span>
                          </div>

                          <div class="flex items-center justify-end gap-3 pt-1">
                            <button
                              type="button"
                              class="px-2 py-1 text-xs text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                              @click="checkoutPreview = null"
                            >
                              取消
                            </button>
                            <button
                              type="button"
                              class="px-3 py-1.5 text-xs font-medium rounded-md bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50"
                              :disabled="actionLoading"
                              @click="handleFinalCheckout(room)"
                            >
                              确认结账并释放房间
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 删除当前订单 -->
                    <div
                      class="pt-3 border-t border-neutral-200/50 dark:border-neutral-800/50 flex items-center justify-end text-xs"
                    >
                      <button
                        v-if="confirmingDeleteRoomId !== room.id"
                        type="button"
                        class="inline-flex items-center gap-1 text-neutral-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                        :disabled="actionLoading"
                        @click="confirmingDeleteRoomId = room.id"
                      >
                        <Trash2 class="w-3.5 h-3.5" />
                        <span>删除订单</span>
                      </button>
                      <div v-else class="flex items-center gap-2.5">
                        <span class="text-rose-500"
                          >删除订单将同步释放该客房为空闲，确认删除？</span
                        >
                        <button
                          type="button"
                          class="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                          @click="confirmingDeleteRoomId = null"
                        >
                          取消
                        </button>
                        <button
                          type="button"
                          class="px-2.5 py-1 rounded bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50"
                          :disabled="actionLoading"
                          @click="handleDeleteActiveOrder(room)"
                        >
                          确认删除
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- 2. 预订客房操作面板 -->
                  <div
                    v-else-if="room.status === 'reserved' && room.activeOrder"
                    class="space-y-3"
                  >
                    <div
                      class="grid grid-cols-2 sm:grid-cols-5 gap-4 pb-3 border-b border-neutral-200/50 dark:border-neutral-800/50 text-xs"
                    >
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >预订住客</span
                        >
                        <span
                          class="font-semibold text-neutral-900 dark:text-neutral-100"
                        >
                          {{ room.activeOrder.guest_name }}
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >联系电话</span
                        >
                        <span
                          class="text-neutral-700 dark:text-neutral-300 tabular-nums"
                        >
                          {{ room.activeOrder.phone }}
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >证件号码</span
                        >
                        <span
                          class="text-neutral-700 dark:text-neutral-300 tabular-nums"
                        >
                          {{ room.activeOrder.id_card }}
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >预订晚数</span
                        >
                        <span
                          class="text-neutral-700 dark:text-neutral-300 tabular-nums"
                        >
                          {{ room.activeOrder.days }} 晚
                        </span>
                      </div>
                      <div>
                        <span class="text-neutral-400 block text-[11px]"
                          >预订创建时间</span
                        >
                        <span class="text-neutral-500 tabular-nums">{{
                          room.activeOrder.created_at
                        }}</span>
                      </div>
                    </div>

                    <div class="flex items-center justify-between pt-1">
                      <div>
                        <button
                          v-if="confirmingDeleteRoomId !== room.id"
                          type="button"
                          class="inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                          :disabled="actionLoading"
                          @click="confirmingDeleteRoomId = room.id"
                        >
                          <Trash2 class="w-3.5 h-3.5" />
                          <span>删除订单</span>
                        </button>
                        <div v-else class="flex items-center gap-2.5 text-xs">
                          <span class="text-rose-500"
                            >确认删除预订并释放房间？</span
                          >
                          <button
                            type="button"
                            class="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                            @click="confirmingDeleteRoomId = null"
                          >
                            取消
                          </button>
                          <button
                            type="button"
                            class="px-2.5 py-1 rounded bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50"
                            :disabled="actionLoading"
                            @click="handleDeleteActiveOrder(room)"
                          >
                            确认删除
                          </button>
                        </div>
                      </div>

                      <button
                        type="button"
                        class="px-3.5 py-1.5 text-xs font-medium rounded-md bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50 inline-flex items-center gap-1.5"
                        :disabled="actionLoading"
                        @click="handleConfirmCheckin(room)"
                      >
                        <UserCheck class="w-3.5 h-3.5" />
                        <span>确认为正式入住</span>
                      </button>
                    </div>
                  </div>

                  <!-- 3. 空闲客房快速入住面板 -->
                  <div
                    v-else-if="room.status === 'available'"
                    class="space-y-3"
                  >
                    <div
                      class="text-xs font-medium text-neutral-800 dark:text-neutral-200"
                    >
                      办理入住 · {{ room.number }}（{{ room.type }}）
                    </div>

                    <div
                      class="grid grid-cols-1 sm:grid-cols-5 gap-3 items-end"
                    >
                      <div>
                        <input
                          v-model="fastForm.guest_name"
                          type="text"
                          placeholder="住客姓名"
                          class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300"
                        />
                      </div>
                      <div>
                        <input
                          v-model="fastForm.phone"
                          type="text"
                          placeholder="联系电话"
                          class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
                        />
                      </div>
                      <div>
                        <input
                          v-model="fastForm.id_card"
                          type="text"
                          placeholder="身份证号码"
                          class="w-full px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
                        />
                      </div>
                      <div class="flex items-center gap-2">
                        <input
                          v-model="fastForm.days"
                          type="number"
                          min="1"
                          placeholder="晚数"
                          class="w-16 px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300 tabular-nums"
                        />
                        <span class="text-xs text-neutral-400">晚</span>
                        <select
                          v-model="fastForm.mode"
                          class="flex-1 px-2 py-1.5 text-xs bg-transparent border-b border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-300"
                        >
                          <option
                            value="checkin"
                            class="bg-white dark:bg-obsidian-900"
                          >
                            直接入住
                          </option>
                          <option
                            value="reserved"
                            class="bg-white dark:bg-obsidian-900"
                          >
                            预订保留
                          </option>
                        </select>
                      </div>
                      <div class="flex justify-end">
                        <button
                          type="button"
                          class="w-full sm:w-auto px-4 py-1.5 text-xs font-medium rounded-md bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 hover:opacity-90 transition-opacity disabled:opacity-50"
                          :disabled="actionLoading"
                          @click="handleFastCreateOrder(room)"
                        >
                          {{
                            fastForm.mode === "checkin"
                              ? "确认办理入住"
                              : "保存预订"
                          }}
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- 行内操作反馈提示 -->
                  <Transition name="fade-slide">
                    <div
                      v-if="rowMessage && rowMessage.roomId === room.id"
                      class="mt-2.5 text-xs flex items-center gap-1.5"
                      :class="
                        rowMessage.type === 'success'
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-rose-600 dark:text-rose-400'
                      "
                    >
                      <CheckCircle2
                        v-if="rowMessage.type === 'success'"
                        class="w-3.5 h-3.5 flex-shrink-0"
                      />
                      <AlertCircle v-else class="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{{ rowMessage.text }}</span>
                    </div>
                  </Transition>
                  </div>
                </td>
              </tr>
            </template>

            <tr v-if="filteredRooms.length === 0">
              <td
                colspan="6"
                class="py-10 text-center text-xs text-neutral-400"
              >
                暂无符合筛选条件的客房
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
