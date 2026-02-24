import json
import os
import time
import redis

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_queue = os.getenv("REDIS_QUEUE", "game-events")
scoreboard_key = os.getenv("SCOREBOARD_KEY", "dungeon:scoreboard")

ACTION_POINTS = {
    "kill_monster": 10,
    "find_treasure": 25,
    "open_chest": 15,
    "take_damage": -5,
    "drink_potion": 5,
}

client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


def run():
    print("processor started: Dungeon Queue mode")
    while True:
        item = client.brpop(redis_queue, timeout=5)
        if not item:
            continue

        _, payload = item
        try:
            data = json.loads(payload)
            player = data.get("player", "unknown")
            action = data.get("action", "take_damage")
        except json.JSONDecodeError:
            print(f"invalid payload dropped: {payload}")
            continue

        delta = ACTION_POINTS.get(action, 1)
        total = client.hincrby(scoreboard_key, player, delta)
        print(f"player={player} action={action} delta={delta} total={total}")
        time.sleep(0.2)


if __name__ == "__main__":
    run()
