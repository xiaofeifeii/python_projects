# !/usr/bin/python3
# -*- coding: utf-8 -*-

import getopt
import queue
import struct
import sys
import time
import redis

import numpy as np
from opcua import Client
from opcua.common.type_dictionary_buider import get_ua_class
import asyncio

set_param = False
test_case = 'misc'
sample_rate = 1000

redis_ip = "127.0.0.1"
redis_port = 6379
redis_topic = "ch1"  # 123为消息发布主题

mub_flag = True
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

rc = redis.Redis(host=redis_ip, port=redis_port, decode_responses=True)


def redis_send_msg(msag):
    rc.publish(redis_topic, str(msag))
    print(str(msag))


def redis_send_msg(*msag):
    msg = ""
    for txt in msag:
        msg += str(txt)
    rc.publish(redis_topic, msg)
    print(msg)


def sub_handle(info):
    global mub_flag
    mub_flag = False
    time.sleep(1)
    print(info)
    msg = info['data']
    cmd = msg.split("_")
    loop.stop()
    if cmd[0] == "setChannel":
        c1 = cmd[1]
        c2 = cmd[2]
        print('receive success ' + c1 + " " + c2)
        mub_flag = True
        loop.run_until_complete(mud(c1, c2))
    else:
        print("cmd match error")


ps = rc.pubsub()
ps.subscribe(**{"ch2": sub_handle})
ps.run_in_thread(0.03)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'sc:r:')
    for opt, arg in opts:
        if opt == '-s':
            set_param = True
        elif opt == '-c':
            test_case = arg
        elif opt == '-r':
            try:
                sample_rate = int(arg)
            except ValueError:
                pass
except getopt.GetoptError:
    pass

cli = Client('opc.tcp://10.82.99.1:8299/epur/')
# cli = Client('opc.tcp://localhost:8299/epur/')
cli.connect()
cli.load_type_definitions()


async def mud(c1, c2):
    ps.run_in_thread()

    redis_send_msg('===========================')
    redis_send_msg('Mud Test')
    redis_send_msg('===========================')

    class MudSubHandler(object):

        def __init__(self, data_queue: queue.Queue):
            self.__data_queue = data_queue

        def datachange_notification(self, node, val, data):
            if self.__data_queue is not None:
                if self.__data_queue.full():
                    self.__data_queue.get()
                self.__data_queue.put_nowait(val)

    mud_node = cli.nodes.objects.get_child(('2:EPUR', '2:Mud'))
    mud_status_node = mud_node.get_child('2:DAQStatus')

    mud_data_node = mud_node.get_child('2:WaveformData')
    mud_queue = queue.Queue(300)
    mud_handler = MudSubHandler(mud_queue)
    mud_sub = cli.create_subscription(500, mud_handler)
    mud_handle = mud_sub.subscribe_data_change(mud_data_node)

    np.set_printoptions(threshold=10)

    if mud_node.call_method('2:SetChannel', c1, c2, sample_rate):
        redis_send_msg('Set channel setting succeeded.')
    else:
        redis_send_msg('Set channel setting failed.')
    redis_send_msg('---------------------------')

    if mud_node.call_method('2:ControlDAQ', True):
        redis_send_msg('Start DAQ succeeded.')
    else:
        redis_send_msg('Start DAQ failed.')
    redis_send_msg('---------------------------')

    redis_send_msg('DAQ status:', mud_status_node.get_value())
    redis_send_msg('---------------------------')

    try:
        while True:
            if not mub_flag:
                break
            try:
                wv_data = mud_queue.get(timeout=1)
                if len(wv_data) >= 9:
                    tm = struct.unpack('<HBBBBB', wv_data[:7])
                    redis_send_msg('%d-%02d-%02d %02d:%02d:%02d' % tm)
                    length, = struct.unpack('<H', wv_data[7:9])
                    wv_data = wv_data[9:]
                    if length > 0:
                        if len(wv_data) == (9 * length):
                            ai_data = np.frombuffer(wv_data[:8 * length], np.float32)
                            ai_data.resize(ai_data.size // 2, 2)
                            redis_send_msg('Pressure data: %d samples per channel,time:%d channel:%d' % (
                                ai_data.shape[0], int(time.time()), c1))
                            redis_send_msg(ai_data)

                            di_data = np.frombuffer(wv_data[8 * length:], np.uint8)
                            redis_send_msg('DI data: %d samples,time:%d channel:%d' % (
                                di_data.shape[0], int(time.time()), c2))
                            redis_send_msg(di_data)
                        else:
                            redis_send_msg('Waveform data receiving error.')
                    else:
                        redis_send_msg('No waveform data available.')
                else:
                    redis_send_msg('Mud get waveform data failed.')

                redis_send_msg('------------------------')
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        redis_send_msg('Keyboard interrupted, exiting...')

    if mud_node.call_method('2:ControlDAQ', False):
        redis_send_msg('Stop DAQ succeeded.')
    else:
        redis_send_msg('Stop DAQ failed.')
    redis_send_msg('---------------------------')

    redis_send_msg('DAQ status:', mud_status_node.get_value())
    redis_send_msg('---------------------------')


if test_case == 'misc':
    redis_send_msg('===========================')
    redis_send_msg('Misc Test')
    redis_send_msg('===========================')

    misc_node = cli.nodes.objects.get_child(('2:EPUR', '2:Misc'))
    ver_node = misc_node.get_child('2:Version')
    ver = ver_node.get_value()
    redis_send_msg(f'Firmware Version: {ver.Major}.{ver.Minor}.{ver.Release}')
    redis_send_msg('Get Usage:', misc_node.call_method('2:GetUsage'))
    redis_send_msg('Get Time:', misc_node.call_method('2:GetTime'))

    if set_param:
        if misc_node.call_method('2:SetSN', b'EPU-R-0009'):
            redis_send_msg('Set SN succeeded.')
        else:
            redis_send_msg('Set SN failed.')
    sn_node = misc_node.get_child('2:SN')
    sn = sn_node.get_value().decode()
    redis_send_msg('Get SN:', sn)

    if set_param:
        ts = get_ua_class('TimeStampStruct')()
        t = time.localtime()
        ts.Year = t.tm_year
        ts.Month = t.tm_mon
        ts.Day = t.tm_mday
        ts.Hour = t.tm_hour
        ts.Minute = t.tm_min
        ts.Second = t.tm_sec
        redis_send_msg('before:', time.time())
        ret = misc_node.call_method('2:SyncTime', ts)
        redis_send_msg('after:', time.time())
        if ret:
            redis_send_msg('Sync time succeeded.')
        else:
            redis_send_msg('Sync time failed.')
        redis_send_msg('Get Time:', misc_node.call_method('2:GetTime'))
    redis_send_msg('---------------------------')

if test_case == 'rit':
    redis_send_msg('===========================')
    redis_send_msg('RIT Test')
    redis_send_msg('===========================')
    rit_node = cli.nodes.objects.get_child(('2:EPUR', '2:RIT'))
    rit_node.call_method('2:Send', b'\xFF\xFF\x06\x03' + b'Hello')
    redis_send_msg('===========================')

if test_case == 'pump':
    redis_send_msg('===========================')
    redis_send_msg('Pump Test')
    redis_send_msg('===========================')


    class PumpSubHandler(object):

        def __init__(self):
            self.pump_measurements = None

        def datachange_notification(self, node, val, data):
            self.pump_measurements = val


    pump_node = cli.nodes.objects.get_child(('2:EPUR', '2:Pump'))

    pump_measurements_node = pump_node.get_child('2:PumpMeasurements')
    pump_handler = PumpSubHandler()
    pump_sub = cli.create_subscription(500, pump_handler)
    pump_handle = pump_sub.subscribe_data_change(pump_measurements_node)

    chn0 = get_ua_class('PumpChannelStruct')()
    chn1 = get_ua_class('PumpChannelStruct')()
    chn0.Channel = 0
    chn0.Line = 0
    chn1.Channel = 1
    chn1.Line = 0
    if pump_node.call_method('2:SetChannels', chn0, chn1):
        redis_send_msg('Set channels succeeded.')
    else:
        redis_send_msg('Set channels failed.')
    redis_send_msg('---------------------------')

    if pump_node.call_method('2:SetCounts', 128, 32):
        redis_send_msg('Set counts succeeded.')
    else:
        redis_send_msg('Set counts failed.')
    redis_send_msg('Sleep 2 seconds for pump measurements update...')
    time.sleep(2)
    redis_send_msg('Pump measurements:', pump_handler.pump_measurements)
    redis_send_msg('---------------------------')

    if pump_node.call_method('2:ControlMeasurement', True):
        redis_send_msg('Start pump measurement succeeded.')
    else:
        redis_send_msg('Start pump measurement failed.')
    redis_send_msg('---------------------------')

    try:
        while True:
            redis_send_msg('Pump measurements:', pump_handler.pump_measurements)
            time.sleep(1)
    except KeyboardInterrupt:
        redis_send_msg('Keyboard interrupted, exiting...')

    if pump_node.call_method('2:ControlMeasurement', False):
        redis_send_msg('Stop pump measurement succeeded.')
    else:
        redis_send_msg('Stop pump measurement failed.')
    redis_send_msg('---------------------------')

    redis_send_msg('===========================')

if test_case == 'cdl':
    redis_send_msg('===========================')
    redis_send_msg('CDL Test')
    redis_send_msg('===========================')


    class CDLSubHandler(object):

        def __init__(self):
            self.cdl_state = None

        def datachange_notification(self, node, val, data):
            self.cdl_state = val


    cdl_node = cli.nodes.objects.get_child(('2:EPUR', '2:CDL'))

    cdl_state_node = cdl_node.get_child('2:CDLStatus')
    cdl_handler = CDLSubHandler()
    cdl_sub = cli.create_subscription(500, cdl_handler)
    cdl_handle = cdl_sub.subscribe_data_change(cdl_state_node)

    if cdl_node.call_method('2:ResetPos'):
        redis_send_msg('Reset position succeeded.')
    else:
        redis_send_msg('Reset position failed.')
    redis_send_msg('---------------------------')

    if cdl_node.call_method('2:Control', True):
        redis_send_msg('CDL open succeeded.')
    else:
        redis_send_msg('CDL open failed.')
    redis_send_msg('---------------------------')

    input('Press any key to continue...')

    if cdl_node.call_method('2:Control', False):
        redis_send_msg('CDL close succeeded.')
    else:
        redis_send_msg('CDL close failed.')
    redis_send_msg('---------------------------')

    redis_send_msg('CDL sequence: '
                   'Open: 1s, Close: 2s, Open: 3s, Close: 4s, Open: 5s.')
    cdl_seq = b'\x01' * 1 + \
              b'\x00' * 2 + \
              b'\x01' * 3 + \
              b'\x00' * 4 + \
              b'\x01' * 5

    if cdl_node.call_method('2:DownloadSeq', cdl_seq):
        redis_send_msg('Download sequence succeeded.')
    else:
        redis_send_msg('Download sequence failed.')
    redis_send_msg('---------------------------')

    if cdl_node.call_method('2:CancelSeq'):
        redis_send_msg('Cancel sequence succeeded.')
    else:
        redis_send_msg('Cancel sequence failed.')
    redis_send_msg('---------------------------')

    input('Press any key to download & start again.')
    redis_send_msg('------------------------')

    if cdl_node.call_method('2:DownloadSeq', cdl_seq):
        redis_send_msg('Download sequence succeeded.')
    else:
        redis_send_msg('Download sequence failed.')
    redis_send_msg('---------------------------')

    try:
        while True:
            redis_send_msg('CDL state:', cdl_handler.cdl_state)
            time.sleep(1)
    except KeyboardInterrupt:
        redis_send_msg('Keyboard interrupted, exiting...')

    if cdl_node.call_method('2:CancelSeq'):
        redis_send_msg('Cancel sequence succeeded.')
    else:
        redis_send_msg('Cancel sequence failed.')
    redis_send_msg('---------------------------')

if test_case == 'mud':
    loop.run_until_complete(mud(0, 1))
if test_case == 'depth':
    redis_send_msg('===========================')
    redis_send_msg('Depth Test')
    redis_send_msg('===========================')


    class DepthSubHandler(object):

        def __init__(self):
            self.depth_measurements = None

        def datachange_notification(self, node, val, data):
            self.depth_measurements = val


    depth_node = cli.nodes.objects.get_child(('2:EPUR', '2:Depth'))

    depth_measurements_node = depth_node.get_child('2:DepthMeasurements')
    depth_handler = DepthSubHandler()
    depth_sub = cli.create_subscription(500, depth_handler)
    depth_handle = depth_sub.subscribe_data_change(depth_measurements_node)

    if depth_node.call_method('2:SetMainChannel', 0, False):
        redis_send_msg('Set main channel succeeded.')
    else:
        redis_send_msg('Set main channel failed.')
    redis_send_msg('---------------------------')

    if set_param:
        main_table_counts = (0, 200, 888)
        main_table_lengths = (0, 1.2, 3.5)
        if depth_node.call_method('2:SetWireLengthCalibration',
                                  main_table_counts,
                                  main_table_lengths):
            redis_send_msg('Set wire length calibration succeeded.')
        else:
            redis_send_msg('Set wire length calibration failed.')
        redis_send_msg('---------------------------')

    depth_wire_length_cali_node = depth_node.get_child('2:WireLengthCalibration')
    depth_wire_length_cali_counts_node = depth_wire_length_cali_node.get_child('2:WireLengthCalibrationCounts')
    depth_wire_length_cali_lengths_node = depth_wire_length_cali_node.get_child('2:WireLengthCalibrationLengths')
    redis_send_msg('Wire length calibration table:')
    redis_send_msg('Counts:', depth_wire_length_cali_counts_node.get_value())
    redis_send_msg('Lengths:', depth_wire_length_cali_lengths_node.get_value())
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetCompensatorChannel', 0, False):
        redis_send_msg('Set compensator channel succeeded.')
    else:
        redis_send_msg('Set compensator channel failed.')
    redis_send_msg('---------------------------')

    if set_param:
        cmp_table_counts = (0, 400)
        cmp_table_lengths = (0, 1.5)
        if depth_node.call_method('2:SetCompensatorCalibration',
                                  cmp_table_counts,
                                  cmp_table_lengths):
            redis_send_msg('Set compensator calibration succeeded.')
        else:
            redis_send_msg('Set compensator calibration failed.')
        redis_send_msg('---------------------------')

    depth_compensator_cali_node = depth_node.get_child('2:CompensatorCalibration')
    depth_compensator_cali_counts_node = depth_compensator_cali_node.get_child('2:CompensatorCalibrationCounts')
    depth_compensator_cali_lengths_node = depth_compensator_cali_node.get_child('2:CompensatorCalibrationLengths')
    redis_send_msg('Compensator calibration table:')
    redis_send_msg('Counts:', depth_compensator_cali_counts_node.get_value())
    redis_send_msg('Lengths:', depth_compensator_cali_lengths_node.get_value())
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetHookloadChannel', 2):
        redis_send_msg('Set hookload channel succeeded.')
    else:
        redis_send_msg('Set hookload channel failed.')
    redis_send_msg('---------------------------')

    if set_param:
        hl_table_currents = (5.55, 10.35)
        hl_table_loads = (28.2, 125)
        if depth_node.call_method('2:SetHookloadCalibration',
                                  hl_table_currents,
                                  hl_table_loads):
            redis_send_msg('Set hookload calibration succeeded.')
        else:
            redis_send_msg('Set hookload calibration failed.')
        redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetHookloadThreshold', 42):
        redis_send_msg('Set hookload threshold succeeded.')
    else:
        redis_send_msg('Set hookload threshold failed.')
    redis_send_msg('---------------------------')

    depth_hookload_cali_node = depth_node.get_child('2:HookloadCalibration')
    depth_hookload_cali_currents_node = depth_hookload_cali_node.get_child('2:HookloadCalibrationCurrents')
    depth_hookload_cali_loads_node = depth_hookload_cali_node.get_child('2:HookloadCalibrationLoads')
    redis_send_msg('Hookload calibration table:')
    redis_send_msg('Currents:', depth_hookload_cali_currents_node.get_value())
    redis_send_msg('Loads:', depth_hookload_cali_loads_node.get_value())
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetSlipChannel', 2):
        redis_send_msg('Set slip channel succeeded.')
    else:
        redis_send_msg('Set slip channel failed.')
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetInslipSource', 1):
        redis_send_msg('Set in-slip source succeeded.')
    else:
        redis_send_msg('Set in-slip source failed.')
    redis_send_msg('---------------------------')

    if set_param:
        if depth_node.call_method('2:SetL1L2', 3.45, 2.11):
            redis_send_msg('Set L1 & L2 succeeded.')
        else:
            redis_send_msg('Set L1 & L2 failed.')
        redis_send_msg('---------------------------')

    depth_compensation_node = depth_node.get_child('2:DepthCompensation')
    depth_l1_node = depth_compensation_node.get_child('2:DepthCompensationL1')
    depth_l2_node = depth_compensation_node.get_child('2:DepthCompensationL2')
    redis_send_msg('L1:', depth_l1_node.get_value())
    redis_send_msg('L2:', depth_l2_node.get_value())
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:ResetOffset'):
        redis_send_msg('Reset offset succeeded.')
    else:
        redis_send_msg('Reset offset failed.')
    redis_send_msg('---------------------------')

    if set_param:
        if depth_node.call_method('2:SetCompensation', True, 1):
            redis_send_msg('Set compensation succeeded.')
        else:
            redis_send_msg('Set compensation failed.')
        redis_send_msg('---------------------------')

    depth_compensate_node = depth_compensation_node.get_child('2:DepthCompensationCompensate')
    depth_mode_node = depth_compensation_node.get_child('2:DepthCompensationMode')
    redis_send_msg('compensate:', depth_compensate_node.get_value())
    if depth_mode_node.get_value() == 0:
        redis_send_msg('compensation mode: negative.')
    else:
        redis_send_msg('compensation mode: positive.')
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetBitDepth', 999):
        redis_send_msg('Set bit depth succeeded.')
    else:
        redis_send_msg('Set bit depth failed.')
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:SetBlockHeight', 1):
        redis_send_msg('Set block height succeeded.')
    else:
        redis_send_msg('Set block height failed.')
    redis_send_msg('---------------------------')

    time.sleep(1)

    redis_send_msg('block height:', depth_handler.depth_measurements)
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:ZeroBlockHeight'):
        redis_send_msg('Zero block height succeeded.')
    else:
        redis_send_msg('Zero block height failed.')
    redis_send_msg('---------------------------')

    time.sleep(1)

    redis_send_msg('block height:', depth_handler.depth_measurements)
    redis_send_msg('---------------------------')

    if set_param:
        if depth_node.call_method('2:SetTrackingFrequency', 10):
            redis_send_msg('Set tracking frequency succeeded.')
        else:
            redis_send_msg('Set tracking frequency failed.')
        redis_send_msg('---------------------------')

    depth_tracking_freq_node = depth_node.get_child('2:DepthTrackingFrequency')
    redis_send_msg('tracking frequency:', depth_tracking_freq_node.get_value())
    redis_send_msg('---------------------------')

    if depth_node.call_method('2:ControlTracking', True):
        redis_send_msg('Start depth tracking succeeded.')
    else:
        redis_send_msg('Start depth tracking failed.')
    redis_send_msg('---------------------------')

    depth_tracking_status_node = depth_node.get_child('2:DepthTrackingStatus')
    redis_send_msg(depth_tracking_status_node.get_value())
    redis_send_msg('---------------------------')

    try:
        while True:
            redis_send_msg(depth_handler.depth_measurements)
            time.sleep(1)
    except KeyboardInterrupt:
        redis_send_msg('Keyboard interrupted, exiting...')

    if depth_node.call_method('2:ControlTracking', False):
        redis_send_msg('Stop depth tracking succeeded.')
    else:
        redis_send_msg('Stop depth tracking failed.')
    redis_send_msg('---------------------------')

    redis_send_msg(depth_tracking_status_node.get_value())
    redis_send_msg('---------------------------')

redis_send_msg('============================================================')

# embed()
cli.disconnect()
