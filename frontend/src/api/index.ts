import axios from 'axios'
import type {
  RoomListResponse,
  Order,
  CreateOrderPayload,
  CreateOrderResult,
  CreateRoomPayload,
  CheckoutResult,
} from '../types'

const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Extract error message from API response
export function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.response?.data?.msg) {
      return String(err.response.data.msg)
    }
    if (err.message) {
      return err.message
    }
  }
  return err instanceof Error ? err.message : '未知异常，请检查网络或服务状态'
}

export const api = {
  // 获取所有房间和实时房态统计
  async getRooms(): Promise<RoomListResponse> {
    const res = await client.get<RoomListResponse>('/rooms')
    return res.data
  },

  // 新增客房
  async addRoom(payload: CreateRoomPayload): Promise<{ msg: string }> {
    const res = await client.post<{ msg: string }>('/rooms', {
      number: String(payload.number).trim(),
      type: String(payload.type).trim(),
      price: String(payload.price).trim(),
    })
    return res.data
  },

  // 查询订单（可模糊搜索）
  async getOrders(keyword = ''): Promise<Order[]> {
    const res = await client.get<Order[]>('/orders', {
      params: { q: keyword },
    })
    return res.data
  },

  // 创建订单（直接入住或预订）
  async createOrder(payload: CreateOrderPayload): Promise<CreateOrderResult> {
    const res = await client.post<CreateOrderResult>('/orders', {
      ...payload,
      days: Number(payload.days),
    })
    return res.data
  },

  // 预订转入住
  async confirmCheckin(orderId: number): Promise<{ msg: string }> {
    const res = await client.post<{ msg: string }>(`/orders/${orderId}/checkin`)
    return res.data
  },

  // 录入额外消费
  async addExtraFee(orderId: number, amount: number): Promise<{ msg: string; cur_extra_fee: number }> {
    const res = await client.post<{ msg: string; cur_extra_fee: number }>(`/orders/${orderId}/extra`, {
      amount,
    })
    return res.data
  },

  // 退房与结算
  async checkout(orderId: number): Promise<CheckoutResult> {
    const res = await client.post<CheckoutResult>(`/orders/${orderId}/checkout`)
    return res.data
  },

  // 删除订单
  async deleteOrder(orderId: number): Promise<{ msg: string }> {
    const res = await client.delete<{ msg: string }>(`/orders/${orderId}`)
    return res.data
  },
}
