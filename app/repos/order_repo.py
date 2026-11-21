from sqlite3 import Connection, Row

# 订单属性: id, room_id, guest_name, id_card, phone, days, extra_fee, total_amount, status, created_at


# 插入新订单，返回本次订单id
def insert(
    conn: Connection,
    room_id: int,
    guest_name: str,
    id_card: str,
    phone: str,
    days: int,
    status: str,
    created_at: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO orders (room_id, guest_name, id_card, phone, days, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (room_id, guest_name, id_card, phone, days, status, created_at),
    )
    return cur.lastrowid


# 按订单id查询首条订单
def find_by_id(conn: Connection, order_id: int) -> Row | None:
    return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


# 按订单id查询首条attribute = value的订单
def find_any_by_id(
    conn: Connection, order_id: int, attribute: str, value: str
) -> Row | None:
    # 仅支持白名单，防止SQL注入
    ALLOWED_ATTRIBUTES = ["status", "room_id", "created_at"]
    if attribute not in ALLOWED_ATTRIBUTES:
        raise ValueError("不允许的查询参数")

    return conn.execute(
        f"SELECT * FROM orders WHERE id = ? AND {attribute} = ?", (order_id, value)
    ).fetchone()


# 按订单id查询某条订单的完整信息，并查出该订单关联的房间单价与房间号
def find_with_room_by_id(conn: Connection, order_id: int) -> Row | None:
    return conn.execute(
        """
SELECT o.*, r.price, r.number AS room_number -- 订单的完整信息、关联房间的价格与房号
FROM orders o JOIN rooms r ON o.room_id = r.id -- 将订单表o与房间表r拼接在一起，并连接o.room_id与r.id
WHERE o.id = ?
""",
        (order_id,),
    ).fetchone()


# 按订单id更新某订单状态
def update_status(conn: Connection, order_id: int, status: str):
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


# 客人消费后更新extra_fee金额
def add_extra_fee(conn: Connection, order_id: int, amount: int):
    conn.execute(
        "UPDATE orders SET extra_fee = extra_fee + ? WHERE id = ?", (amount, order_id)
    )


# 订单完成后更新订单状态并结算总金额
def complete_checkout(
    conn: Connection, order_id: int, spend_days: int, total_amount: int
):
    conn.execute(
        "UPDATE orders SET status = 'completed', days = ?, total_amount = ? WHERE id = ?",
        (spend_days, total_amount, order_id),
    )


# 模糊搜索：传入住客姓名 or 手机号 or 房间号，返回最新订单结果
def search(conn: Connection, keyword: str) -> list[Row]:
    # 两边的%是SQL通配符，加上后能够匹配任意位置包含keyword的字符串
    pattern = f"%{keyword}%"
    return conn.execute(
        """
SELECT o.*, r.number AS room_number, r.type AS room_type
FROM orders o JOIN rooms r ON o.room_id = r.id
WHERE o.guest_name LIKE ? OR o.phone LIKE ? OR r.number LIKE ?
ORDER BY o.id DESC
""",
        (pattern, pattern, pattern),
    ).fetchall()
