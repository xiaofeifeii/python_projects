#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import random
import time
#播放音乐
def mplayerMusic(fileName):
    os.system('play ' + './musi/' + fileName  + '*' + ' > /dev/null 2>&1 &')
 
 
def closeMplayer():
    isRunStr = str(os.popen("ps -ef | grep play|grep mp3 | grep -v grep | awk '{print $1}' |sed -n '1p'").readline().strip())
    if isRunStr=='yyf':
        os.system("ps -ef | grep play|grep mp3 | grep -v grep | awk '{print $2}' | xargs kill -9")
       
def getMplayerIsRun():
    isRunStr = str(os.popen("ps -ef | grep play |grep mp3| grep -v grep | awk '{print $1}' |sed -n '1p'").readline().strip())
    
    if isRunStr=='yyf':
        return True
    else:
        return False
 
 

def loop():
    closeMplayer()
    
    fileNameList = os.listdir('/home/yyf/Desktop/语音控制/musi')
    print(fileNameList)
    while True:
        time.sleep(2)
        if getMplayerIsRun()==False:
            fileName = fileNameList[random.randint(0,len(fileNameList) - 1)]
            print(fileName)
            mplayerMusic(fileName)
 
loop()

