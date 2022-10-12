import threading
import asyncio
import redis
import time

redis_ip = "127.0.0.1"
redis_port = 6379
redis_topic = "123"  # 123为消息发布主题
rc = redis.Redis(host=redis_ip, port=redis_port, decode_responses=True)

flag = True

th = None


def sub_handle(info):
    global flag
    flag = False
    time.sleep(1)
    print(info)
    msg = info['data']
    cmd = msg.split("_")

    if cmd[0] == "setChannel":
        c1 = cmd[1]
        c2 = cmd[2]
        # print('receive success ' + c1 + " " + c2)
        flag = True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fun1('receive success ' + c1 + " " + c2, 2))
    else:
        print("match error")
    print("sub_handle end")


def my_time(n, num):
    time.sleep(1)
    t = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
    print(t + "now:" + str(n) + "  name:" + str(num))


async def fun1(msg, num):
    print(msg)

    ps.run_in_thread()

    while True:
        if not flag:
            break
        my_time(flag, num)

    print("end")


ps = rc.pubsub()
ps.subscribe(**{"redis_123": sub_handle})
ps.run_in_thread(0.03)

# print("redis start")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(fun1("redis start", 1))
# th = threading.Thread(target=fun1("redis start", 1))
# th.start()
