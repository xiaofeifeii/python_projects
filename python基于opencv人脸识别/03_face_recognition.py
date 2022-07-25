''''
Real Time Face Recogition
	==> Each face stored on dataset/ dir, should have a unique numeric integer ID as 1, 2, 3, etc                       
	==> LBPH computed model (trained faces) should be on trainer/ dir
Based on original code by Anirban Kar: https://github.com/thecodacus/Face-Recognition    

Developed by Marcelo Rovai - MJRoBot.org @ 21Feb18  
实时人脸识别
==> 存储在 dataset/dir 上的每个人脸都应该有一个唯一的数字整数 ID，如 1、2、3 等
==> LBPH 计算模型（经过训练的人脸）应该在 trainer/dir
'''
#encoding=utf-8
import cv2
import numpy as np
import os 
import requests
import RPi.GPIO as GPIO
import time
from bs4 import BeautifulSoup

GPIO.setmode(GPIO.BCM)

a=0
#L298N驱动初始化
ENA = 13                        # 设置GPIO13连接ENA
IN1 = 19                        # 设置GPIO19连接IN1
IN2 = 26                        # 设置GPIO26连接IN2

v1 = 18                        #灯1
v2 = 23                        #灯2

val=0
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)          # 使用BCM编号方式
GPIO.setup(ENA, GPIO.OUT)       # 将连接ENA的GPIO引脚设置为输出模式
GPIO.setup(IN1, GPIO.OUT)       # 将连接IN1的GPIO引脚设置为输出模式
GPIO.setup(IN2, GPIO.OUT)       # 将连接IN2的GPIO引脚设置为输出模式
GPIO.setup(v1, GPIO.OUT)
GPIO.output(v1, GPIO.LOW)
GPIO.setup(v2, GPIO.OUT)
GPIO.output(v2, GPIO.LOW)
def start():
    GPIO.output(IN1, False)     # 将IN1设置为0
    GPIO.output(IN2, True)      # 将IN2设置为1
    GPIO.output(ENA, True)      # 将ENA设置为1，启动A通道电机
    time.sleep(0.5)               # 等待电机转动5秒
    
    GPIO.output(ENA, False)     # 将ENA设置为0
    time.sleep(5)
       
    GPIO.output(IN1, True)      # 将IN1设置为1
    GPIO.output(IN2, False)     # 将IN2设置为0
    GPIO.output(ENA, True)      # 将ENA设置为1，启动A通道电机
    time.sleep(0.5)               # 等待电机转动5秒
    GPIO.output(ENA, False)     # 将ENA设置为0
    
    
    
def stop():
    GPIO.output(ENA, False)     # 将ENA设置为0


recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);

font = cv2.FONT_HERSHEY_SIMPLEX

#iniciate id counter
id = 0

# names related to ids: example ==> Marcelo: id=1,  etc
names = ['None', 'Leonardo DiCaprio', 'Guailin', 'ZJM', 'Z', 'W'] 

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video widht
cam.set(4, 480) # set video height

# Define min window size to be recognized as a face
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)

while True:

    ret, img =cam.read()
    img = cv2.flip(img, 1) # Flip vertically

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

    for(x,y,w,h) in faces:

        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)

        id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
        
        val=confidence
        # Check if confidence is less them 100 ==> "0" is perfect match 
        if (confidence < 100):
            id = names[id]
            confidence = "  {0}%".format(round(100 - confidence))
        else:
            id = "unknown"
            confidence = "  {0}%".format(round(100 - confidence))
        
        cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)
        
    
    cv2.imshow('camera',img)
    if (val < 50 and val >0):
        if(a!=val):
            name = str(id)
            a=val
        else:
            name=''
        if name=='ZJM':     #排除重复 干扰  
            if(v3!=name):
                start()
                v3=name
        else:
            stop()
          
        if name=='Leonardo DiCaprio':    
            GPIO.output(v1, GPIO.HIGH)#把灯点亮
            time.sleep(1)
        else:
            GPIO.output(v1, GPIO.LOW)#把灯熄灭
        if name=='Guailin':
            GPIO.output(v2, GPIO.HIGH)
            time.sleep(1)
        else:
            GPIO.output(v2, GPIO.LOW)
        print(a)
        print(val)
    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break

# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()
GPIO.cleanup()