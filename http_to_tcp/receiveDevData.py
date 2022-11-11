import socket
import requests
import configparser
import os
import json
import time

receive_count: int = 0
tcp_ip = "127.0.0.1"
tcp_port = 8899
url = "http://yyfhome.xyz:1880/test1"


def ini():
    cfgpath = os.path.join("./", "config.ini")
    print(cfgpath)  # cfg.ini的路径
    # 创建管理对象
    conf = configparser.ConfigParser()
    # 读ini文件
    conf.read(cfgpath, encoding="utf-8")
    # 获取所有的section
    sections = conf.sections()
    # print(sections)  # 返回list
    items = conf.items('config')
    # print(items)
    global tcp_ip, tcp_port, url
    tcp_ip = items[0][1]
    tcp_port = int(items[1][1])
    url = items[4][1]


def http_post(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    devJs = {
        "inwardList": [
            {
                "equipmentNumber": "231100000000060010",
                "status": msg,
                "equipmentType": "26",
                "equipmentName": "气象采集设备1",
                "equipmentTime": currentTime
            }
        ]
    }
    requests.post(url=url, json=devJs)


def start_tcp_client(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    failed_count = 0
    while True:
        try:
            print("start connect to server ")
            s.connect((ip, port))
            break
        except socket.error:
            failed_count += 1
            print("fail to connect to server %d times" % failed_count)
            if failed_count == 100: return

    while True:
        print("connect success")

        # get the socket send buffer size and receive buffer size
        s_send_buffer_size = s.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        s_receive_buffer_size = s.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        print("client TCP receive buffer size is %d" % s_receive_buffer_size)
        print("client TCP send buffer size is %d" % s_send_buffer_size)

        while True:
            online = 1
            for _ in range(10):
                s.setblocking(False)
                try:
                    print("\nwait:",_)
                    msg = s.recv(1024)
                    if len(msg) > 0:
                        print("recv len is : [%d]" % len(msg))
                        print(msg.decode('utf-8'))
                        online = 0
                        break
                except BlockingIOError as e:
                    msg = None
                time.sleep(1)
            http_post(online)
            print("\n.")



ini()
print(tcp_ip, tcp_port, url)

try:
    start_tcp_client(tcp_ip, tcp_port)
except:
    print("tcp connect fail")
