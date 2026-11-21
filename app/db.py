import sqlite3
from contextlib import contextmanager

DB_PATH = "hms.db"


# 相比于 with sqlite3.connect(DB_PATH) as conn，这种函数封装能够安全关闭sqlite连接
@contextmanager
# 调用：with get_db() as conn
def get_db():
    conn = sqlite3.connect(DB_PATH)
    # 默认情况下sqlite返回元组，加上这句以返回类似字典的对象
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            # 把conn交给外部with块使用
            yield conn
    finally:
        conn.close()


# 初始化数据库
def init_db():
    with get_db() as conn:
        conn.executescript("""
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT UNIQUE NOT NULL, -- 房间号
    type TEXT NOT NULL, -- 房型
    price REAL NOT NULL, -- 单晚房价
    status TEXT DEFAULT 'available' -- 房间当前状态
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL, -- 关联rooms表的id字段
    guest_name TEXT NOT NULL, -- 客人姓名
    id_card TEXT NOT NULL, -- 身份证号
    phone TEXT NOT NULL, -- 手机号
    days INTEGER DEFAULT 1, -- 入住天数
    extra_fee REAL DEFAULT 0, -- 额外消费
    total_amount REAL DEFAULT 0, -- 订单总金额
    status TEXT DEFAULT 'reserved', -- 订单状态
    created_at TEXT NOT NULL, -- 订单创建时间
    FOREIGN KEY (room_id) REFERENCES rooms(id) -- 外键约束，声明当前表的room_id字段关联rooms表的id字段
);
""")
        # 查询是否为新表，以决定是否插入初始数据
        # execute方法只允许执行一条SQL语句，能够避免SQL注入
        count = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        # 若为新表
        if count == 0:
            conn.executemany(
                "INSERT INTO rooms (number, type, price) VALUES (?, ?, ?)",
                [
                    ("101", "标准间", 180.0),
                    ("102", "标准间", 180.0),
                    ("201", "大床房", 260.0),
                    ("301", "豪华套房", 520.0),
                ],
            )
