import redis
import time
import threading


def handle(info):
    print(info)


rc = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
ps = rc.pubsub()

ps.subscribe(**{"123": handle})
ps.run_in_thread(0.03)
