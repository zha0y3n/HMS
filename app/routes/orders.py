from flask import Blueprint, request, jsonify
from flask.wrappers import Response
from app.services import order_service

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


# 预订或直接办理入住
@order_bp.route("", methods=["POST"])
def create_order() -> tuple[Response, int]:
    try:
        res = order_service.create_order(request.json)
        return jsonify(res), 201
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400


# 客人到店后预订转入住
@order_bp.route("/<int:order_id>/checkin", methods=["POST"])
def confirm_checkin(order_id: int) -> tuple[Response, int]:
    try:
        order_service.confirm_checkin(order_id)
        return jsonify({"msg": "入住办理成功"}), 201
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400


# 录入额外消费
@order_bp.route("/<int:order_id>/extra", methods=["POST"])
def add_extra_fee(order_id: int) -> tuple[Response, int]:
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            raise ValueError

        cur_extra_fee = order_service.add_extra_fee(order_id, amount)
        return (
            jsonify({"msg": f"已记账 {amount} 元", "cur_extra_fee": cur_extra_fee}),
            201,
        )
    except (ValueError, TypeError) as e:
        return jsonify({"msg": str(e)}), 400


# 退房与结算
@order_bp.route("/<int:order_id>/checkout", methods=["POST"])
def checkout(order_id: int) -> tuple[Response, int]:
    try:
        res = order_service.checkout(order_id)
        return jsonify(res), 201
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400


# 模糊搜索：查询订单与住客档案
@order_bp.route("", methods=["GET"])
def search_orders() -> tuple[Response, int]:
    keyword = request.args.get("q", "")
    return jsonify(order_service.search_orders(keyword)), 200
