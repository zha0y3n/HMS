# 房间属性: id, number, type, price, status
# db.py已指定conn.row_factory = sqlite3.Row

from sqlite3 import Connection, Row


# 查询rooms表中的所有房间属性，并按房间号升序返回
def find_all(conn: Connection) -> list[Row]:
    return conn.execute("SELECT * FROM rooms ORDER BY number").fetchall()


# 插入一条房间属性
# id自增，status默认为available，故只需传Connection + 3参数
def insert(conn: Connection, number: str, room_type: str, price: float):
    conn.execute(
        "INSERT INTO rooms (number, type, price) VALUES (?, ?, ?)",
        (number, room_type, price),
    )


# 返回首个符合room_type筛选条件的房间属性
def find_first_available(conn: Connection, room_type: str) -> Row | None:
    return conn.execute(
        "SELECT * FROM rooms "
        "WHERE type = ? AND status = 'available' "
        "ORDER BY number "
        "LIMIT 1",
        (room_type,),
    ).fetchone()


# 依照room_id更新该房间的status
def update_status(conn: Connection, room_id: int, status: str):
    conn.execute("UPDATE rooms SET status = ? WHERE id = ?", (status, room_id))
