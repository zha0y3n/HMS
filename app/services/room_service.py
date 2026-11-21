import sqlite3
from app.db import get_db
from app.repos import room_repo


# 返回统计信息（房间总数、空闲房间数、预约房间数、占用房间数和占用率）和房间信息
def get_room_with_stats() -> dict:
    with get_db() as conn:
        rooms = [dict(r) for r in room_repo.find_all(conn)]
        total = len(rooms)
        occupied = sum(1 for r in rooms if r["status"] == "occupied")
        stats = {
            "totals": total,
            "available": sum(1 for r in rooms if r["status"] == "available"),
            "reserved": sum(1 for r in rooms if r["status"] == "reserved"),
            "occupied": occupied,
            "occupancy_rate": f"{round(occupied / total * 100, 1)}%" if total else "0%",
        }
        return {"stats": stats, "rooms": rooms}


def create_room(number, room_type, price):
    try:
        with get_db() as conn:
            room_repo.insert(conn, number, room_type, price)
    except:
        raise ValueError("room")
