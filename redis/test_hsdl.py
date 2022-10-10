from opcua import Client
from opcua.common.type_dictionary_buider import get_ua_class
import time
import struct
import getopt
import sys
import redis

status = None


def redis_send_msg(msag):
    rc = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    rc.publish("123", msag)


class SubHandler1(object):
    def datachange_notification(self, node, val, data):
        print(val)
        redis_send_msg(val)


class SubHandler2(object):
    def datachange_notification(self, node, val, data):
        if val is not None:
            print('CMD:', hex(val.CMD), 'Time:', val.Time)
            redis_send_msg("CMD:" + str(hex(val.CMD)) + "Time:" + str(val.Time))


class SubHandler3(object):
    def datachange_notification(self, node, val, data):
        if val is not None:
            global status
            status = val
            print(time.time(), status)
            redis_send_msg(str(time.time()) + str(status))


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

print('Setting baudrate...')
redis_send_msg('Setting baudrate...')
if hsdl_node.call_method('2:SetBaudRate', baudrate):
    print('Set baudrate succeeded.')
    redis_send_msg('Setting baudrate...')
else:
    print('Set baudrate failed.')
    redis_send_msg('Set baudrate failed.')
print('Setting timeout...')
redis_send_msg('Setting timeout...')
if hsdl_node.call_method('2:SetTimeout', timeout):
    print('Set timeout succeeded.')
    redis_send_msg('Set timeout succeeded.')
else:
    print('Set timeout failed.')
    redis_send_msg('Set timeout failed.')

out_packet = get_ua_class('HSDLPacketStruct')()

print('Executing one-shot communication...')
redis_send_msg('Executing one-shot communication...')

out_packet.ID = 0x0002
out_packet.CMD = 0x00E0
out_packet.Content = b'\x00\x55'
in_packet = hsdl_node.call_method('2:OneshotCOMM', out_packet)
print(in_packet)
redis_send_msg(in_packet)

print('Reading memory address...')
redis_send_msg('Reading memory address...')

out_packet.ID = 0x0002
out_packet.CMD = 0x00E1
out_packet.Content = b''
in_packet = hsdl_node.call_method('2:OneshotCOMM', out_packet)
print(in_packet)
redis_send_msg(in_packet)
buff = in_packet.Content
if len(buff) >= 2:
    zone_count, = struct.unpack('>H', buff[:2])
    buff = buff[2:]
    zone_idx = 0
    while len(buff) >= 12:
        print('===== Memory zone %d =====' % zone_idx)
        redis_send_msg('===== Memory zone %d =====' % zone_idx)
        start, stop, data_size, erase_size = struct.unpack('>IIHH', buff[:12])
        print('Start at:', hex(start).upper())
        redis_send_msg('Start at:' + str(hex(start).upper()))
        print('Stop at:', hex(stop).upper())
        redis_send_msg('Stop at:' + str(hex(stop).upper()))
        print('Data block size:', data_size)
        redis_send_msg('Data block size:' + str(data_size))
        print('Erase size:', erase_size)
        redis_send_msg('Erase size:' + str(erase_size))
        buff = buff[12:]
        zone_idx += 1

start_time = time.time()
print('start time:', start_time)
redis_send_msg('start time:' + str(start_time))
print('Starting continuous memory read...')
redis_send_msg('Starting continuous memory read...')
if hsdl_node.call_method('2:StartContinuousMemRead', 0x0002, 0x00E2, 0x00000000, 1024, packet_count):
    print('Start continuous memory read succeeded.')
    redis_send_msg('Start continuous memory read succeeded.')
else:
    print('Start continuous memory read failed.')
    redis_send_msg('Start continuous memory read failed.')
try:
    while True:
        if status is not None:
            # print(status)
            if not status.InProgress:
                time.sleep(0.1)
                if not status.InProgress:
                    print('Continuous memory read completed.')
                    break
        time.sleep(0.1)
except KeyboardInterrupt:
    print('Keyboard interrupted, exiting...')
    redis_send_msg('Keyboard interrupted, exiting...')
speed = packet_count * 1024 / (time.time() - start_time) / 1024
print('Continuous memory read of %.3f kBytes at %.3f kB/s.' % (0x7F0000 / 1024, speed))
redis_send_msg('Continuous memory read of %.3f kBytes at %.3f kB/s.' % (0x7F0000 / 1024, speed))
status = status_node.get_value()
print(status)
redis_send_msg(str(status))
if status.InProgress:
    print('Continuous memory read still in progress, stopping...')
    redis_send_msg('Continuous memory read still in progress, stopping...')
    if hsdl_node.call_method('2:StopContinuousMemRead'):
        print('Stop continuous memory read succeeded.')
        redis_send_msg('Stop continuous memory read succeeded.')
    else:
        print('Stop continuous memory read failed.')
        redis_send_msg('Stop continuous memory read failed.')
status = status_node.get_value()
print(status)
redis_send_msg(str(status))


errors = errors_node.get_value()
print(errors)

cli.disconnect()
