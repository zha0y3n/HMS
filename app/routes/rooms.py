from flask import Blueprint, request, jsonify
from flask.wrappers import Response
from app.services import room_service

# Blueprint实例可以被挂载到flask.app.Flask实例，实现代码解耦
room_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")


# 获取所有房间和实时房态
@room_bp.route("", methods=["GET"])
def list_room() -> Response:
    return jsonify(room_service.get_room_with_stats())


# 新增客房
@room_bp.route("", methods=["POST"])
def add_room() -> tuple[Response, int]:
    data = request.json
    try:
        room_service.create_room(data["number"], data["type"], data["price"])
        return jsonify({"msg": "房间添加成功"}), 201
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
