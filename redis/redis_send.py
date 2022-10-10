import redis
import time
import threading

a = 0
value1=1
value2=2
value3=0x11

s3 = "xxxx {1} xxx{0}  hex{2}".format(value1,value2,hex(value3))
print(s3)  # xxxx [9, 0] xxx(7, 8)


def redis_send_msg(msg):
    rc = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    rc.publish("123", msg)




def run():
    while True:
        t = time.time()
        data = str(t) + "test message"
        zone_idx=100
        redis_send_msg('===== Memory zone %d =====' % zone_idx)
        time.sleep(2)
        redis_send_msg('data')


t1 = threading.Thread(target=run)
t1.start()
