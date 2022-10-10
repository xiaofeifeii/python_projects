# !/usr/bin/python3
# -*- coding: utf-8 -*-

import getopt
import queue
import struct
import sys
import time

import numpy as np
from opcua import Client
from opcua.common.type_dictionary_buider import get_ua_class

set_param = False
test_case = 'misc'
sample_rate = 1000

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

if test_case == 'misc':
    print('===========================')
    print('Misc Test')
    print('===========================')

    misc_node = cli.nodes.objects.get_child(('2:EPUR', '2:Misc'))
    ver_node = misc_node.get_child('2:Version')
    ver = ver_node.get_value()
    print(f'Firmware Version: {ver.Major}.{ver.Minor}.{ver.Release}')
    print('Get Usage:', misc_node.call_method('2:GetUsage'))
    print('Get Time:', misc_node.call_method('2:GetTime'))

    if set_param:
        if misc_node.call_method('2:SetSN', b'EPU-R-0009'):
            print('Set SN succeeded.')
        else:
            print('Set SN failed.')
    sn_node = misc_node.get_child('2:SN')
    sn = sn_node.get_value().decode()
    print('Get SN:', sn)

    if set_param:
        ts = get_ua_class('TimeStampStruct')()
        t = time.localtime()
        ts.Year = t.tm_year
        ts.Month = t.tm_mon
        ts.Day = t.tm_mday
        ts.Hour = t.tm_hour
        ts.Minute = t.tm_min
        ts.Second = t.tm_sec
        print('before:', time.time())
        ret = misc_node.call_method('2:SyncTime', ts)
        print('after:', time.time())
        if ret:
            print('Sync time succeeded.')
        else:
            print('Sync time failed.')
        print('Get Time:', misc_node.call_method('2:GetTime'))
    print('---------------------------')

if test_case == 'rit':
    print('===========================')
    print('RIT Test')
    print('===========================')
    rit_node = cli.nodes.objects.get_child(('2:EPUR', '2:RIT'))
    rit_node.call_method('2:Send', b'\xFF\xFF\x06\x03' + b'Hello')
    print('===========================')

if test_case == 'pump':
    print('===========================')
    print('Pump Test')
    print('===========================')

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
        print('Set channels succeeded.')
    else:
        print('Set channels failed.')
    print('---------------------------')

    if pump_node.call_method('2:SetCounts', 128, 32):
        print('Set counts succeeded.')
    else:
        print('Set counts failed.')
    print('Sleep 2 seconds for pump measurements update...')
    time.sleep(2)
    print('Pump measurements:', pump_handler.pump_measurements)
    print('---------------------------')

    if pump_node.call_method('2:ControlMeasurement', True):
        print('Start pump measurement succeeded.')
    else:
        print('Start pump measurement failed.')
    print('---------------------------')

    try:
        while True:
            print('Pump measurements:', pump_handler.pump_measurements)
            time.sleep(1)
    except KeyboardInterrupt:
        print('Keyboard interrupted, exiting...')

    if pump_node.call_method('2:ControlMeasurement', False):
        print('Stop pump measurement succeeded.')
    else:
        print('Stop pump measurement failed.')
    print('---------------------------')

    print('===========================')

if test_case == 'cdl':
    print('===========================')
    print('CDL Test')
    print('===========================')

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
        print('Reset position succeeded.')
    else:
        print('Reset position failed.')
    print('---------------------------')

    if cdl_node.call_method('2:Control', True):
        print('CDL open succeeded.')
    else:
        print('CDL open failed.')
    print('---------------------------')

    input('Press any key to continue...')

    if cdl_node.call_method('2:Control', False):
        print('CDL close succeeded.')
    else:
        print('CDL close failed.')
    print('---------------------------')

    print('CDL sequence: '
          'Open: 1s, Close: 2s, Open: 3s, Close: 4s, Open: 5s.')
    cdl_seq = b'\x01' * 1 + \
              b'\x00' * 2 + \
              b'\x01' * 3 + \
              b'\x00' * 4 + \
              b'\x01' * 5

    if cdl_node.call_method('2:DownloadSeq', cdl_seq):
        print('Download sequence succeeded.')
    else:
        print('Download sequence failed.')
    print('---------------------------')

    if cdl_node.call_method('2:CancelSeq'):
        print('Cancel sequence succeeded.')
    else:
        print('Cancel sequence failed.')
    print('---------------------------')

    input('Press any key to download & start again.')
    print('------------------------')

    if cdl_node.call_method('2:DownloadSeq', cdl_seq):
        print('Download sequence succeeded.')
    else:
        print('Download sequence failed.')
    print('---------------------------')

    try:
        while True:
            print('CDL state:', cdl_handler.cdl_state)
            time.sleep(1)
    except KeyboardInterrupt:
        print('Keyboard interrupted, exiting...')

    if cdl_node.call_method('2:CancelSeq'):
        print('Cancel sequence succeeded.')
    else:
        print('Cancel sequence failed.')
    print('---------------------------')

if test_case == 'mud':
    print('===========================')
    print('Mud Test')
    print('===========================')

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

    if mud_node.call_method('2:SetChannel', 0, 1, sample_rate):
        print('Set channel setting succeeded.')
    else:
        print('Set channel setting failed.')
    print('---------------------------')

    if mud_node.call_method('2:ControlDAQ', True):
        print('Start DAQ succeeded.')
    else:
        print('Start DAQ failed.')
    print('---------------------------')

    print('DAQ status:', mud_status_node.get_value())
    print('---------------------------')

    try:
        while True:
            try:
                wv_data = mud_queue.get(timeout=1)
                if len(wv_data) >= 9:
                    tm = struct.unpack('<HBBBBB', wv_data[:7])
                    print('%d-%02d-%02d %02d:%02d:%02d' % tm)
                    length, = struct.unpack('<H', wv_data[7:9])
                    wv_data = wv_data[9:]
                    if length > 0:
                        if len(wv_data) == (9 * length):
                            ai_data = np.frombuffer(wv_data[:8 * length], np.float32)
                            ai_data.resize(ai_data.size // 2, 2)
                            print('Pressure data: %d samples per channel.' %
                                  ai_data.shape[0])
                            print(ai_data)

                            di_data = np.frombuffer(wv_data[8 * length:], np.uint8)
                            print('DI data: %d samples.' % di_data.shape[0])
                            print(di_data)
                        else:
                            print('Waveform data receiving error.')
                    else:
                        print('No waveform data available.')
                else:
                    print('Mud get waveform data failed.')

                print('------------------------')
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print('Keyboard interrupted, exiting...')

    if mud_node.call_method('2:ControlDAQ', False):
        print('Stop DAQ succeeded.')
    else:
        print('Stop DAQ failed.')
    print('---------------------------')

    print('DAQ status:', mud_status_node.get_value())
    print('---------------------------')

if test_case == 'depth':
    print('===========================')
    print('Depth Test')
    print('===========================')

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
        print('Set main channel succeeded.')
    else:
        print('Set main channel failed.')
    print('---------------------------')

    if set_param:
        main_table_counts = (0, 200, 888)
        main_table_lengths = (0, 1.2, 3.5)
        if depth_node.call_method('2:SetWireLengthCalibration',
                                  main_table_counts,
                                  main_table_lengths):
            print('Set wire length calibration succeeded.')
        else:
            print('Set wire length calibration failed.')
        print('---------------------------')

    depth_wire_length_cali_node = depth_node.get_child('2:WireLengthCalibration')
    depth_wire_length_cali_counts_node = depth_wire_length_cali_node.get_child('2:WireLengthCalibrationCounts')
    depth_wire_length_cali_lengths_node = depth_wire_length_cali_node.get_child('2:WireLengthCalibrationLengths')
    print('Wire length calibration table:')
    print('Counts:', depth_wire_length_cali_counts_node.get_value())
    print('Lengths:', depth_wire_length_cali_lengths_node.get_value())
    print('---------------------------')

    if depth_node.call_method('2:SetCompensatorChannel', 0, False):
        print('Set compensator channel succeeded.')
    else:
        print('Set compensator channel failed.')
    print('---------------------------')

    if set_param:
        cmp_table_counts = (0, 400)
        cmp_table_lengths = (0, 1.5)
        if depth_node.call_method('2:SetCompensatorCalibration',
                                  cmp_table_counts,
                                  cmp_table_lengths):
            print('Set compensator calibration succeeded.')
        else:
            print('Set compensator calibration failed.')
        print('---------------------------')

    depth_compensator_cali_node = depth_node.get_child('2:CompensatorCalibration')
    depth_compensator_cali_counts_node = depth_compensator_cali_node.get_child('2:CompensatorCalibrationCounts')
    depth_compensator_cali_lengths_node = depth_compensator_cali_node.get_child('2:CompensatorCalibrationLengths')
    print('Compensator calibration table:')
    print('Counts:', depth_compensator_cali_counts_node.get_value())
    print('Lengths:', depth_compensator_cali_lengths_node.get_value())
    print('---------------------------')

    if depth_node.call_method('2:SetHookloadChannel', 2):
        print('Set hookload channel succeeded.')
    else:
        print('Set hookload channel failed.')
    print('---------------------------')

    if set_param:
        hl_table_currents = (5.55, 10.35)
        hl_table_loads = (28.2, 125)
        if depth_node.call_method('2:SetHookloadCalibration',
                                  hl_table_currents,
                                  hl_table_loads):
            print('Set hookload calibration succeeded.')
        else:
            print('Set hookload calibration failed.')
        print('---------------------------')

    if depth_node.call_method('2:SetHookloadThreshold', 42):
        print('Set hookload threshold succeeded.')
    else:
        print('Set hookload threshold failed.')
    print('---------------------------')

    depth_hookload_cali_node = depth_node.get_child('2:HookloadCalibration')
    depth_hookload_cali_currents_node = depth_hookload_cali_node.get_child('2:HookloadCalibrationCurrents')
    depth_hookload_cali_loads_node = depth_hookload_cali_node.get_child('2:HookloadCalibrationLoads')
    print('Hookload calibration table:')
    print('Currents:', depth_hookload_cali_currents_node.get_value())
    print('Loads:', depth_hookload_cali_loads_node.get_value())
    print('---------------------------')

    if depth_node.call_method('2:SetSlipChannel', 2):
        print('Set slip channel succeeded.')
    else:
        print('Set slip channel failed.')
    print('---------------------------')

    if depth_node.call_method('2:SetInslipSource', 1):
        print('Set in-slip source succeeded.')
    else:
        print('Set in-slip source failed.')
    print('---------------------------')

    if set_param:
        if depth_node.call_method('2:SetL1L2', 3.45, 2.11):
            print('Set L1 & L2 succeeded.')
        else:
            print('Set L1 & L2 failed.')
        print('---------------------------')

    depth_compensation_node = depth_node.get_child('2:DepthCompensation')
    depth_l1_node = depth_compensation_node.get_child('2:DepthCompensationL1')
    depth_l2_node = depth_compensation_node.get_child('2:DepthCompensationL2')
    print('L1:', depth_l1_node.get_value())
    print('L2:', depth_l2_node.get_value())
    print('---------------------------')

    if depth_node.call_method('2:ResetOffset'):
        print('Reset offset succeeded.')
    else:
        print('Reset offset failed.')
    print('---------------------------')

    if set_param:
        if depth_node.call_method('2:SetCompensation', True, 1):
            print('Set compensation succeeded.')
        else:
            print('Set compensation failed.')
        print('---------------------------')

    depth_compensate_node = depth_compensation_node.get_child('2:DepthCompensationCompensate')
    depth_mode_node = depth_compensation_node.get_child('2:DepthCompensationMode')
    print('compensate:', depth_compensate_node.get_value())
    if depth_mode_node.get_value() == 0:
        print('compensation mode: negative.')
    else:
        print('compensation mode: positive.')
    print('---------------------------')

    if depth_node.call_method('2:SetBitDepth', 999):
        print('Set bit depth succeeded.')
    else:
        print('Set bit depth failed.')
    print('---------------------------')

    if depth_node.call_method('2:SetBlockHeight', 1):
        print('Set block height succeeded.')
    else:
        print('Set block height failed.')
    print('---------------------------')

    time.sleep(1)

    print('block height:', depth_handler.depth_measurements)
    print('---------------------------')

    if depth_node.call_method('2:ZeroBlockHeight'):
        print('Zero block height succeeded.')
    else:
        print('Zero block height failed.')
    print('---------------------------')

    time.sleep(1)

    print('block height:', depth_handler.depth_measurements)
    print('---------------------------')

    if set_param:
        if depth_node.call_method('2:SetTrackingFrequency', 10):
            print('Set tracking frequency succeeded.')
        else:
            print('Set tracking frequency failed.')
        print('---------------------------')

    depth_tracking_freq_node = depth_node.get_child('2:DepthTrackingFrequency')
    print('tracking frequency:', depth_tracking_freq_node.get_value())
    print('---------------------------')

    if depth_node.call_method('2:ControlTracking', True):
        print('Start depth tracking succeeded.')
    else:
        print('Start depth tracking failed.')
    print('---------------------------')

    depth_tracking_status_node = depth_node.get_child('2:DepthTrackingStatus')
    print(depth_tracking_status_node.get_value())
    print('---------------------------')

    try:
        while True:
            print(depth_handler.depth_measurements)
            time.sleep(1)
    except KeyboardInterrupt:
        print('Keyboard interrupted, exiting...')

    if depth_node.call_method('2:ControlTracking', False):
        print('Stop depth tracking succeeded.')
    else:
        print('Stop depth tracking failed.')
    print('---------------------------')

    print(depth_tracking_status_node.get_value())
    print('---------------------------')

print('============================================================')

# embed()
cli.disconnect()
