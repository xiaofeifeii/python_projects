from opcua import Client
from opcua.common.type_dictionary_buider import get_ua_class
import time
import struct
import getopt
import sys
import redis

status = None


redis_ip = "127.0.0.1"
redis_port = 6379
redis_topic = "123"  # 123为消息发布主题


def redis_send_msg(msag):
    rc = redis.Redis(host=redis_ip, port=redis_port, decode_responses=True)
    rc.publish(redis_topic, str(msag))
    print(msag)


def redis_send_msg(*msag):
    rc = redis.Redis(host=redis_ip, port=redis_port, decode_responses=True)
    msg = ""
    for t in msag:
        msg += str(t)
    rc.publish(redis_topic, msg)
    print(msg)



class SubHandler1(object):
    def datachange_notification(self, node, val, data):
        redis_send_msg(val)


class SubHandler2(object):
    def datachange_notification(self, node, val, data):
        if val is not None:
            redis_send_msg('CMD:', hex(val.CMD), 'Time:', val.Time)


class SubHandler3(object):
    def datachange_notification(self, node, val, data):
        if val is not None:
            global status
            status = val
            redis_send_msg(time.time(), status)


baudrate = 38400
packet_count = 1024
timeout = 1
try:
    opts, args = getopt.getopt(sys.argv[1:], 'r:p:t:')
    for opt, arg in opts:
        if opt == '-r':
            try:
                baudrate = int(arg)
            except ValueError:
                pass
        elif opt == '-p':
            try:
                packet_count = int(arg)
            except ValueError:
                pass
        elif opt == '-t':
            try:
                timeout = int(arg)
            except ValueError:
                pass
except getopt.GetoptError:
    pass

cli = Client('opc.tcp://10.82.99.1:8299/epur/')
cli.connect()
cli.load_type_definitions()
cli.session_timeout = timeout

hsdl_node = cli.nodes.objects.get_child(('2:EPUR', '2:HSDL'))

status_node = hsdl_node.get_child('2:HSDLStatus')
status_handler = SubHandler3()
status_sub = cli.create_subscription(50, status_handler)
status_sub.subscribe_data_change(status_node)

errors_node = hsdl_node.get_child('2:HSDLErrors')
errors_handler = SubHandler1()
errors_sub = cli.create_subscription(50, errors_handler)
errors_sub.subscribe_data_change(errors_node)

packet_node = hsdl_node.get_child('2:HSDLDataPacket')
packet_handler = SubHandler2()
packet_sub = cli.create_subscription(100, packet_handler)
packet_sub.subscribe_data_change(packet_node, queuesize=1024)

redis_send_msg('Setting baudrate...')
if hsdl_node.call_method('2:SetBaudRate', baudrate):
    redis_send_msg('Set baudrate succeeded.')
else:
    redis_send_msg('Set baudrate failed.')

redis_send_msg('Setting timeout...')
if hsdl_node.call_method('2:SetTimeout', timeout):
    redis_send_msg('Set timeout succeeded.')
else:
    redis_send_msg('Set timeout failed.')

out_packet = get_ua_class('HSDLPacketStruct')()

redis_send_msg('Executing one-shot communication...')
out_packet.ID = 0x0002
out_packet.CMD = 0x00E0
out_packet.Content = b'\x00\x55'
in_packet = hsdl_node.call_method('2:OneshotCOMM', out_packet)
redis_send_msg(in_packet)

redis_send_msg('Reading memory address...')
out_packet.ID = 0x0002
out_packet.CMD = 0x00E1
out_packet.Content = b''
in_packet = hsdl_node.call_method('2:OneshotCOMM', out_packet)
redis_send_msg(in_packet)
buff = in_packet.Content
if len(buff) >= 2:
    zone_count, = struct.unpack('>H', buff[:2])
    buff = buff[2:]
    zone_idx = 0
    while len(buff) >= 12:
        redis_send_msg('===== Memory zone %d =====' % zone_idx)
        start, stop, data_size, erase_size = struct.unpack('>IIHH', buff[:12])
        redis_send_msg('Start at:', hex(start).upper())
        redis_send_msg('Stop at:', hex(stop).upper())
        redis_send_msg('Data block size:', data_size)
        redis_send_msg('Erase size:', erase_size)
        buff = buff[12:]
        zone_idx += 1

start_time = time.time()
redis_send_msg('start time:', start_time)
redis_send_msg('Starting continuous memory read...')
if hsdl_node.call_method('2:StartContinuousMemRead', 0x0002, 0x00E2, 0x00000000, 1024, packet_count):
    redis_send_msg('Start continuous memory read succeeded.')
else:
    redis_send_msg('Start continuous memory read failed.')

try:
    while True:
        if status is not None:
            # print(status)
            if not status.InProgress:
                time.sleep(0.1)
                if not status.InProgress:
                    redis_send_msg('Continuous memory read completed.')
                    break
        time.sleep(0.1)
except KeyboardInterrupt:
    redis_send_msg('Keyboard interrupted, exiting...')

speed = packet_count * 1024 / (time.time() - start_time) / 1024
redis_send_msg('Continuous memory read of %.3f kBytes at %.3f kB/s.' % (0x7F0000/1024, speed))

status = status_node.get_value()
redis_send_msg(status)
if status.InProgress:
    redis_send_msg('Continuous memory read still in progress, stopping...')
    if hsdl_node.call_method('2:StopContinuousMemRead'):
        redis_send_msg('Stop continuous memory read succeeded.')
    else:
        redis_send_msg('Stop continuous memory read failed.')
status = status_node.get_value()
redis_send_msg(status)

errors = errors_node.get_value()
redis_send_msg(errors)

cli.disconnect()
