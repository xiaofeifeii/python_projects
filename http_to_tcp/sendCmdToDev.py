# coding:utf-8
from flask import Flask
from flask import jsonify
from flask import request, json
from gevent import pywsgi
import socket
import configparser
import os

tcp_ip = "127.0.0.1"
tcp_port = 8899
server_ip = '127.0.0.1'
server_port = 5000
app = Flask(__name__)


def ini():
    cfgpath = os.path.join("./", "config.ini")
    print(cfgpath)  # cfg.ini的路径
    # 创建管理对象
    conf = configparser.ConfigParser()
    # 读ini文件
    conf.read(cfgpath, encoding="utf-8")  # python3
    # 获取所有的section
    sections = conf.sections()
    print(sections)  # 返回list
    items = conf.items('config')
    print(items)
    global tcp_ip, tcp_port, server_port, server_ip
    # tcp_ip = items[0]['tcp_ip']
    tcp_ip = items[0][1]
    tcp_port = int(items[1][1])
    server_ip = items[2][1]
    server_port = int(items[3][1])


def tcp_send_msg(send_data):
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_addr = (tcp_ip, int(tcp_port))
        tcp_socket.connect(server_addr)
        tcp_socket.send(send_data.encode("utf-8"))
        tcp_socket.close()
        return 0
    except:
        return -1


@app.route("/warningDeviceCommand", methods=["POST"])
def recv_data():
    # request.form.get：获取post请求的参数，
    data = request.get_data()
    json_data = json.loads(data.decode("UTF-8"))
    warning = json_data.get("warning")
    print(warning[0])
    dev_cmd = {
        "version": warning[0]['version'],
        "cmd": warning[0]['cmd'],
        "param": {
            "mode": int(warning[0]['param']['mode']),
            "freq": int(warning[0]['param']['freq']),
            "lightness": int(warning[0]['param']['lightness']),
        }
    }
    print(dev_cmd)

    if tcp_send_msg(str(dev_cmd)) < 0:
        return jsonify({"code": -1, "message": "tcp send fail", "value": ""})
    else:
        return jsonify({"code": 1, "message": "success", "value": ""})


if __name__ == '__main__':
    ini()
    app.config['JSON_AS_ASCII'] = False
    # test.start_tcp_client()
    print(tcp_ip, tcp_port, server_port, server_ip)
    # app.run(host=server_ip, port=server_port)
    server = pywsgi.WSGIServer((server_ip, server_port), app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("server exit")
