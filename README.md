# 酒店管理系统（Python + SQLite 极简分层课设版）开发指南

本项目摒弃了过度设计的重型中间件与复杂依赖，基于 **Python + Flask + 原生 sqlite3** 构建，采用**轻量级三层架构（Routes → Services → Repositories）**。零外部数据库依赖，自动建表初始化，既保留了课设“即插即用、零环境配置”的极简体验，又具备清晰的工程代码分层，方便答辩展示与后续扩展。

---

## 一、 技术栈与项目结构

### 1.1 核心技术选型
* **后端语言**：Python 3.8+
* **Web 框架**：Flask（使用 `Blueprint` 蓝图模块化路由，无多余样板代码）
* **数据库**：SQLite 3（Python 标准库自带 `sqlite3`，数据直接存在本地 `hotel.db` 文件中，无需安装数据库服务，拷到 U 盘即插即用）
* **前端建议**：单页原生 HTML + Fetch API（或 Bootstrap），直接调用后端 7 个接口展示房态卡片即可

### 1.2 分层目录结构设计
按职责拆分为**入口层、基础设施层、数据访问层（DAO）、业务逻辑层（Service）和路由控制层（Routes）**，各层单向依赖，答辩讲解架构清晰直观：

```text
hotel-management-lite/
├── run.py                      # 项目启动入口
├── hotel.db                    # 运行后自动生成的 SQLite 数据库文件
└── app/
    ├── __init__.py             # 应用工厂：创建 Flask 实例并注册蓝图
    ├── db.py                   # 基础设施：数据库连接上下文管理与自动建表初始化
    ├── routes/                 # 【路由层】接收 HTTP 请求、调用 Service、返回 JSON
    │   ├── rooms.py            # 客房接口（2 个）
    │   └── orders.py           # 订单接口（5 个）
    ├── services/               # 【业务层】房态统计、自动分房、退房算账与事务控制
    │   ├── room_service.py
    │   └── order_service.py
    └── repositories/           # 【数据层】纯粹的 SQLite 增删改查语句封装
        ├── room_repo.py
        └── order_repo.py
```

---

## 二、 极简数据库表设计（2 张核心表）

将原本冗余的 5 张表合并精简为 **2 张核心数据表**，彻底消除多表联查与事务死锁隐患：

1. **砍掉系统用户表**：课设演示无需复杂 RBAC 权限体系，省去密码加密与 Token 鉴权开销。
2. **合并住客与消费明细表**：将主住客信息及额外消费累加字段直接并入 `orders` 表，用单表支撑完整订单生命周期。

```sql
-- 1. 客房表 (rooms)
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT UNIQUE NOT NULL,      -- 房间号，如 "101"
    type TEXT NOT NULL,               -- 房型：标准间 / 大床房 / 豪华套房
    price REAL NOT NULL,              -- 单价（元/晚）
    status TEXT DEFAULT 'available'   -- 状态：available(空闲) / reserved(预订) / occupied(在用)
);

-- 2. 订单与住客账单三合一表 (orders)
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,         -- 关联房间ID
    guest_name TEXT NOT NULL,         -- 住客姓名
    id_card TEXT NOT NULL,            -- 身份证号
    phone TEXT NOT NULL,              -- 联系电话
    days INTEGER DEFAULT 1,           -- 预计/实际入住天数
    deposit REAL DEFAULT 0,           -- 已交押金
    extra_fee REAL DEFAULT 0,         -- 额外消费总额（矿泉水、餐饮等直接累加）
    total_amount REAL DEFAULT 0,      -- 退房结算总金额
    status TEXT DEFAULT 'reserved',   -- 状态：reserved(已预订) / checked_in(已入住) / completed(已退房)
    created_at TEXT NOT NULL,         -- 创建时间
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);
```

---

## 三、 核心业务分层实现

以下各层代码完整实现**自动建表与测试数据初始化、实时房态统计、自动分房预订/直接入住、预订转入住、额外消费记账、一键退房结算及住客模糊查询**全部功能。

### 3.1 入口与基础设施层

#### `run.py`（启动入口）
```python
from app import create_app
from app.db import init_db

app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=True)
```

#### `app/__init__.py`（应用工厂与蓝图注册）
```python
from flask import Flask
from app.routes.rooms import room_bp
from app.routes.orders import order_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(room_bp)
    app.register_blueprint(order_bp)
    return app
```

#### `app/db.py`（连接管理与自动初始化）
```python
import sqlite3
from contextlib import contextmanager

DB_PATH = "hotel.db"


@contextmanager
def get_db():
    """自动管理事务提交/回滚，并在退出时确保关闭数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持通过列名访问字段
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    """启动时自动建表并初始化测试房间"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'available'
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                guest_name TEXT NOT NULL,
                id_card TEXT NOT NULL,
                phone TEXT NOT NULL,
                days INTEGER DEFAULT 1,
                deposit REAL DEFAULT 0,
                extra_fee REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'reserved',
                created_at TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            );
        """)
        # 若房间表为空，自动插入 4 条初始数据方便演示
        count = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
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
```

---

### 3.2 数据访问层（`app/repositories/`）

> **职责说明**：纯粹封装原生 SQL 语句，不包含任何业务规则判断，接收连接 `conn` 执行数据存取。

#### `app/repositories/room_repo.py`
```python
def find_all(conn):
    return conn.execute("SELECT * FROM rooms ORDER BY number").fetchall()


def insert(conn, number, room_type, price):
    conn.execute(
        "INSERT INTO rooms (number, type, price) VALUES (?, ?, ?)",
        (number, room_type, price),
    )


def find_first_available(conn, room_type):
    return conn.execute(
        "SELECT * FROM rooms WHERE type = ? AND status = 'available' ORDER BY number LIMIT 1",
        (room_type,),
    ).fetchone()


def update_status(conn, room_id, status):
    conn.execute("UPDATE rooms SET status = ? WHERE id = ?", (status, room_id))
```

#### `app/repositories/order_repo.py`
```python
def insert(conn, room_id, guest_name, id_card, phone, days, deposit, status, created_at):
    cur = conn.execute(
        """INSERT INTO orders (room_id, guest_name, id_card, phone, days, deposit, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (room_id, guest_name, id_card, phone, days, deposit, status, created_at),
    )
    return cur.lastrowid


def find_by_id(conn, order_id):
    return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def find_checked_in_by_id(conn, order_id):
    return conn.execute(
        "SELECT * FROM orders WHERE id = ? AND status = 'checked_in'",
        (order_id,),
    ).fetchone()


def find_with_room_by_id(conn, order_id):
    return conn.execute(
        """SELECT o.*, r.price, r.number AS room_number
           FROM orders o JOIN rooms r ON o.room_id = r.id
           WHERE o.id = ?""",
        (order_id,),
    ).fetchone()


def update_status(conn, order_id, status):
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def add_extra_fee(conn, order_id, amount):
    conn.execute("UPDATE orders SET extra_fee = extra_fee + ? WHERE id = ?", (amount, order_id))


def complete_checkout(conn, order_id, actual_days, total_amount):
    conn.execute(
        "UPDATE orders SET status = 'completed', days = ?, total_amount = ? WHERE id = ?",
        (actual_days, total_amount, order_id),
    )


def search(conn, keyword):
    pattern = f"%{keyword}%"
    return conn.execute(
        """SELECT o.*, r.number AS room_number, r.type AS room_type
           FROM orders o JOIN rooms r ON o.room_id = r.id
           WHERE o.guest_name LIKE ? OR o.phone LIKE ? OR r.number LIKE ?
           ORDER BY o.id DESC""",
        (pattern, pattern, pattern),
    ).fetchall()
```

---

### 3.3 业务逻辑层（`app/services/`）

> **职责说明**：编排核心业务流程、控制数据库事务边界（确保订单状态与房间状态原子更新）及执行账单金额核算。

#### `app/services/room_service.py`
```python
import sqlite3
from app.db import get_db
from app.repositories import room_repo


def get_rooms_with_stats():
    with get_db() as conn:
        rooms = [dict(r) for r in room_repo.find_all(conn)]
        total = len(rooms)
        occupied = sum(1 for r in rooms if r["status"] == "occupied")
        stats = {
            "total": total,
            "available": sum(1 for r in rooms if r["status"] == "available"),
            "reserved": sum(1 for r in rooms if r["status"] == "reserved"),
            "occupied": occupied,
            "occupancy_rate": f"{round(occupied / total * 100, 1)}%" if total else "0%",
        }
        return {"stats": stats, "rooms": rooms}


def create_room(number, room_type, price):
    try:
        with get_db() as conn:
            room_repo.insert(conn, number, room_type, float(price))
    except sqlite3.IntegrityError:
        raise ValueError("房间号已存在")
```

#### `app/services/order_service.py`
```python
from datetime import datetime
from app.db import get_db
from app.repositories import room_repo, order_repo


def create_order(data):
    is_direct_checkin = data.get("mode") == "checkin"
    room_status = "occupied" if is_direct_checkin else "reserved"
    order_status = "checked_in" if is_direct_checkin else "reserved"

    with get_db() as conn:
        room = room_repo.find_first_available(conn, data["room_type"])
        if not room:
            raise ValueError(f"没有空闲的【{data['room_type']}】了")

        order_id = order_repo.insert(
            conn,
            room_id=room["id"],
            guest_name=data["guest_name"],
            id_card=data["id_card"],
            phone=data["phone"],
            days=int(data.get("days", 1)),
            deposit=float(data.get("deposit", 0)),
            status=order_status,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        room_repo.update_status(conn, room["id"], room_status)

        return {
            "msg": "直接入住办理成功" if is_direct_checkin else "预订成功",
            "order_id": order_id,
            "assigned_room": room["number"],
        }


def confirm_checkin(order_id):
    with get_db() as conn:
        order = order_repo.find_by_id(conn, order_id)
        if not order or order["status"] != "reserved":
            raise ValueError("订单不存在或非预订状态")

        order_repo.update_status(conn, order_id, "checked_in")
        room_repo.update_status(conn, order["room_id"], "occupied")


def add_extra_fee(order_id, amount):
    if amount <= 0:
        raise ValueError("消费金额必须大于 0")

    with get_db() as conn:
        order = order_repo.find_checked_in_by_id(conn, order_id)
        if not order:
            raise ValueError("只有在住订单才能记账")

        order_repo.add_extra_fee(conn, order_id, amount)
        return order["extra_fee"] + amount


def checkout(order_id, custom_days=None):
    with get_db() as conn:
        row = order_repo.find_with_room_by_id(conn, order_id)
        if not row or row["status"] != "checked_in":
            raise ValueError("订单不存在或未处于入住状态")

        actual_days = int(custom_days) if custom_days is not None else row["days"]
        room_fee = actual_days * row["price"]
        total_amount = room_fee + row["extra_fee"]
        net_payable = total_amount - row["deposit"]  # 实际需补交（负数表示退还押金）

        # 同一事务内原子执行订单完成与房间释放
        order_repo.complete_checkout(conn, order_id, actual_days, total_amount)
        room_repo.update_status(conn, row["room_id"], "available")

        return {
            "msg": f"{row['room_number']} 房退房成功",
            "bill": {
                "room_fee": room_fee,
                "extra_fee": row["extra_fee"],
                "total_amount": total_amount,
                "deposit_paid": row["deposit"],
                "net_payable": net_payable,
            },
        }


def search_orders(keyword):
    with get_db() as conn:
        rows = order_repo.search(conn, keyword)
        return [dict(r) for r in rows]
```

---

### 3.4 路由控制层（`app/routes/`）

> **职责说明**：只负责解析 HTTP 请求参数、调用 Service 层并封装 JSON 响应状态码，不直接接触数据库。

#### `app/routes/rooms.py`
```python
from flask import Blueprint, request, jsonify
from app.services import room_service

room_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")


# 1. 获取所有房间及实时房态统计
@room_bp.route("", methods=["GET"])
def list_rooms():
    return jsonify(room_service.get_rooms_with_stats())


# 2. 新增客房
@room_bp.route("", methods=["POST"])
def add_room():
    data = request.json
    try:
        room_service.create_room(data["number"], data["type"], data["price"])
        return jsonify({"msg": "房间添加成功"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
```

#### `app/routes/orders.py`
```python
from flask import Blueprint, request, jsonify
from app.services import order_service

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


# 3. 预订或直接办理入住（自动分配首间匹配空房）
@order_bp.route("", methods=["POST"])
def create_order():
    try:
        result = order_service.create_order(request.json)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# 4. 预订转入住（客人到店确认）
@order_bp.route("/<int:order_id>/checkin", methods=["POST"])
def confirm_checkin(order_id):
    try:
        order_service.confirm_checkin(order_id)
        return jsonify({"msg": "已办理入住"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# 5. 录入额外消费（直接累加至订单 extra_fee）
@order_bp.route("/<int:order_id>/extra", methods=["POST"])
def add_extra_fee(order_id):
    amount = float(request.json.get("amount", 0))
    try:
        current_extra = order_service.add_extra_fee(order_id, amount)
        return jsonify({"msg": f"已记账 {amount} 元", "current_extra_fee": current_extra})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# 6. 退房与一键结算
@order_bp.route("/<int:order_id>/checkout", methods=["POST"])
def checkout(order_id):
    custom_days = (request.json or {}).get("days")
    try:
        result = order_service.checkout(order_id, custom_days)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# 7. 查询订单与住客档案（支持按姓名、手机号、房间号模糊搜索）
@order_bp.route("", methods=["GET"])
def search_orders():
    keyword = request.args.get("q", "")
    return jsonify(order_service.search_orders(keyword))
```

---

## 四、 精简 API 接口清单

| 模块 | 请求方式 | 接口路径 | 功能说明 | 请求参数示例 (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| **客房** | `GET` | `/api/rooms` | 获取所有房间列表及实时入住率统计 | 无 |
| **客房** | `POST` | `/api/rooms` | 新增客房 | `{"number": "302", "type": "大床房", "price": 260}` |
| **订单** | `POST` | `/api/orders` | 自动分房预订或直接办理入住 | `{"mode": "checkin", "room_type": "标准间", "guest_name": "张三", "id_card": "110...", "phone": "138...", "days": 2, "deposit": 200}` |
| **订单** | `POST` | `/api/orders/<id>/checkin` | 预订订单确认到店转入住 | 无 |
| **消费** | `POST` | `/api/orders/<id>/extra` | 为在住订单累加额外消费金额 | `{"amount": 35.5}` |
| **退房** | `POST` | `/api/orders/<id>/checkout` | 核算房费+消费并释放房间 | `{"days": 2}`（可选，默认按原定天数） |
| **查询** | `GET` | `/api/orders?q=张三` | 按姓名/手机号/房间号查询订单与住客 | URL Query 参数 `q` |

---

## 五、 快速启动指南

```bash
# 1. 仅需安装 Flask 一个第三方包
pip install flask

# 2. 在项目根目录下启动服务（自动创建 hotel.db 并写入初始房间）
python run.py
```

启动后访问 `http://127.0.0.1:8080/api/rooms` 即可看到初始化好的房态 JSON 数据。