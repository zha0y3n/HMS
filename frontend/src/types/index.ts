export type RoomStatus = 'available' | 'reserved' | 'occupied'
export type OrderStatus = 'reserved' | 'checked_in' | 'completed'

export interface Room {
  id: number
  number: string
  type: string
  price: number
  status: RoomStatus
}

export interface RoomStats {
  totals: number
  available: number
  reserved: number
  occupied: number
  occupancy_rate: string
}

export interface RoomListResponse {
  stats: RoomStats
  rooms: Room[]
}

export interface Order {
  id: number
  room_id: number
  guest_name: string
  id_card: string
  phone: string
  days: number
  extra_fee: number
  total_amount?: number | null
  status: OrderStatus
  created_at: string
  room_number: string
  room_type: string
}

export interface Bill {
  room_fee: number
  extra_fee: number
  total_amount: number
}

export interface CreateOrderPayload {
  room_type: string
  guest_name: string
  id_card: string
  phone: string
  days: number
  mode: 'checkin' | 'reserved'
}

export interface CreateOrderResult {
  msg: string
  order_id: number
  room_number: string
}

export interface CreateRoomPayload {
  number: string
  type: string
  price: number | string
}

export interface CheckoutResult {
  msg: string
  bill: Bill
}

// Composite type for the Smart Room-Order Fusion view
export interface RoomWithActiveOrder extends Room {
  activeOrder?: Order
}
