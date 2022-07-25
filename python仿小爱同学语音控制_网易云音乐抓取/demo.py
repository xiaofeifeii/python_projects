#!/usr/bin/python
# -*- coding: UTF-8 -*-
import snowboydecoder
import sys
import signal
import yyf
interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

def callbacks():
    global detector
    detector.terminate()
    yyf.yyfMain()
    snowboydecoder.play_audio_file()
    wake()
    

    
def wake():
    global detector
    model='snowboy.pmdl'
# capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.45)
    print('Listening... 我在听')

# main loop
    detector.start(detected_callback=callbacks,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

    detector.terminate()
    
if __name__== '__main__':
    wake()
