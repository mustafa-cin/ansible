import json
import os
from flask import Flask, jsonify, request
import redis

app = Flask(__name__)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_queue = os.getenv("REDIS_QUEUE", "game-events")
scoreboard_key = os.getenv("SCOREBOARD_KEY", "dungeon:scoreboard")

client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "gateway"}), 200


@app.post("/play")
def play():
    payload = request.get_json(silent=True) or {}
    player = payload.get("player")
    action = payload.get("action")

    if not player or not action:
        return jsonify({"error": "'player' ve 'action' zorunludur"}), 400

    event = json.dumps({"player": player, "action": action})
    client.lpush(redis_queue, event)
    return jsonify({"queued": True, "player": player, "action": action}), 202


@app.get("/score/<player>")
def score(player: str):
    points = client.hget(scoreboard_key, player) or "0"
    return jsonify({"player": player, "score": int(points)}), 200


@app.get("/leaderboard")
def leaderboard():
    data = client.hgetall(scoreboard_key)
    ranking = sorted(
        [{"player": name, "score": int(score)} for name, score in data.items()],
        key=lambda x: x["score"],
        reverse=True,
    )
    return jsonify({"leaderboard": ranking[:10]}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
