from datetime import datetime
from app.db import get_db
from app.repos import room_repo, order_repo
from typing import TypedDict, NotRequired


class OrderData(TypedDict):
    room_type: str
    guest_name: str
    id_card: str
    phone: str
    mode: str
    days: NotRequired[int]


# 根据客人意图创建订单，返回提示信息、订单号和房间号
def create_order(data: OrderData) -> dict:
    # 若客人的意图为直接入住(checkin)
    is_direct_checkin = data["mode"] == "checkin"
    # 那么直接占用房间并更改订单状态为已入住(checked_in)；否则视为预订行为，房间和订单状态更改为reserved
    room_status = "occupied" if is_direct_checkin else "reserved"
    order_status = "checked_in" if is_direct_checkin else "reserved"

    with get_db() as conn:
        # 按客人的房型需求查询是否有对应的可用房
        room = room_repo.find_first_available(conn, data["room_type"])
        if not room:
            raise ValueError(f"{data["room_type"]}已满")

        # 校验days
        days = data.get("days", 1)
        if type(days) is not int or days <= 0:
            raise ValueError

        # 查询到可用房后，插入该条订单信息
        order_id = order_repo.insert(
            conn,
            room_id=room["id"],
            guest_name=data["guest_name"],
            id_card=data["id_card"],
            phone=data["phone"],
            days=days,
            status=order_status,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        # 更新房间状态
        room_repo.update_status(conn, room["id"], room_status)

        return {
            "msg": "直接入住办理成功" if is_direct_checkin else "预订成功",
            "order_id": order_id,
            "room_number": room["number"],
        }


# 更改预订状态的订单为实际入住状态
def confirm_checkin(order_id: int):
    with get_db() as conn:
        order = order_repo.find_by_id(conn, order_id)
        if not order or order["status"] != "reserved":
            raise ValueError("订单不存在或非预订状态")
        order_repo.update_status(conn, order_id, "checked_in")
        room_repo.update_status(conn, order["room_id"], "occupied")


# 更新extra_fee并返回新金额
def add_extra_fee(order_id: int, amount: float) -> int:
    if amount <= 0:
        raise ValueError

    with get_db() as conn:
        order = order_repo.find_any_by_id(conn, order_id, "status", "checked_in")
        if not order:
            raise ValueError("只有在住订单才能记账")

        order_repo.add_extra_fee(conn, order_id, amount)
        return order["extra_fee"] + amount


# 业务层结算函数，返回提示和账单信息
def checkout(order_id: int) -> dict:
    with get_db() as conn:
        row = order_repo.find_with_room_by_id(conn, order_id)
        if not row or row["status"] != "checked_in":
            raise ValueError("订单不存在或非入住状态")

        # 总金额 = 住宿天数 * 每晚房费 + 额外消费
        days = row["days"]
        room_fee = days * row["price"]
        total_amount = room_fee + row["extra_fee"]

        # 结算订单总金额并更新房间状态为可用
        order_repo.complete_checkout(conn, order_id, days, total_amount)
        room_repo.update_status(conn, row["room_id"], "available")

        return {
            "msg": f"{row["room_number"]}退房成功",
            "bill": {
                "room_fee": room_fee,
                "extra_fee": row["extra_fee"],
                "total_amount": total_amount,
            },
        }


# 删除订单（若为预订中或在住中订单，同步释放关联房间为空闲状态）
def delete_order(order_id: int):
    with get_db() as conn:
        order = order_repo.find_by_id(conn, order_id)
        if not order:
            raise ValueError("订单不存在")

        if order["status"] in ("reserved", "checked_in"):
            room_repo.update_status(conn, order["room_id"], "available")

        order_repo.delete_by_id(conn, order_id)


# 调用模糊搜索
def search_orders(keyword: str) -> list[dict]:
    with get_db() as conn:
        return [dict(r) for r in order_repo.search(conn, keyword)]
