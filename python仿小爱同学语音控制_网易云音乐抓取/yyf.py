# coding=utf-8
import sys
import json
import os
import requests
import pycurl
import wave
import time
import random
import signal
import wyyone
from pyaudio import PyAudio,paInt16
import urllib.request

#from playsound import playsound
import paho.mqtt.client as mqtt 

pathmusic = "./musi"
text=""
a=0

# coding = utf-8
#from bs4 import BeautifulSoup        # 用于解析网页源代码的模块
from binascii import b2a_hex, a2b_hex
from jsonpath import jsonpath
from Crypto.Cipher import AES
import requests                        # 用于获取网页内容的模块
import base64
import json

import os, sys

pathmusic = "./musi"

def get_params():  # 获取params 参数的函数
    iv = "0102030405060708"
    forth_param = "0CoJUm6Qyw8W8jud"
    first_key = forth_param
    second_key = 16 * 'F'
    h_encText = AES_encrypt("0CoJUm6Qyw8W8jud", first_key, iv)
    h_encText = AES_encrypt(h_encText, second_key, iv)
    return h_encText


def get_encSecKey():
    encSecKey = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c"
    return encSecKey


def AES_encrypt(text, key, iv):
    text = text.encode('utf-8')
    pad = 16 - len(text) % 16
    text = text + ( pad * chr(pad)).encode('utf-8')  # 需要转成二进制，且可以被16整除
    key = key.encode('utf-8')
    iv = iv.encode('utf-8')
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    encrypt_text = encryptor.encrypt(text)  # .encode('utf-8')
    encrypt_text = base64.b64encode(encrypt_text)
    return encrypt_text.decode('utf-8')


def get_json(url, params, encSecKey):
    data = {
        "params": params,
        "encSecKey": encSecKey
    }
    response = requests.post(url, headers=headers, data=data)
    return response.content


def handle_json(ressult_str):
    """通过request返回的json结果，对结果进行处理"""
    ressult_str = ressult_b.decode('utf-8')  # 结果转码为str类型
    json_text = json.loads(ressult_str)  # 加载为json格式
    i = 0
    L = []
    for i in range(len(jsonpath(json_text, '$..songs[*].id'))):  # 根据id获取列表条数
        D = {'num': 'null', 'name': 'null', 'id': 'null', 'singer':'null', 'song_sheet':'null'}  # 初始化字典
        D['num'] = i
        D['name'] = '/'.join(jsonpath(json_text, "$..songs["+str(i)+"].name"))  # 获取名称
        D['id'] = str(jsonpath(json_text, "$..songs["+str(i)+"].id")[0])  # 获取ID且获取第一个ID值并转化为str类型
        D['singer'] = '/'.join(jsonpath(json_text, "$..songs["+str(i)+"].ar[*].name"))  # 获取歌手列表
        al_list = jsonpath(json_text, "$..songs["+str(i)+"].al.name")  # 获取专辑列表
        al = '/'.join(al_list)  # 将获取的专辑列表合并
        D['song_sheet'] = "《" + al + "》"
        L.append(D)
    return L
#mqtt初始化
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("test.ranye-iot.net", 1883, 60)
#stt初始化
framerate=8000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME=2
def save_wave_file(filename,data):
    '''save the date to the wavfile'''
    wf=wave.open(filename,'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b"".join(data))
    wf.close()

def my_record():
    pa=PyAudio()
    stream=pa.open(format = paInt16,channels=1,
                   rate=framerate,input=True,
                   frames_per_buffer=NUM_SAMPLES)
    my_buf=[]
    count=0
    while count<TIME*10:#控制录音时间
        string_audio_data = stream.read(NUM_SAMPLES)
        my_buf.append(string_audio_data)
        count+=1
        print('.')
    save_wave_file('01.wav',my_buf)
    stream.close()

def get_token():
    API_KEY = 'ClGl9cP9jHzmcupL62kcRpeu'
    SECRET_KEY = 'XLiOvQQWCr3RRuOaX2RbXlEyNtpBkvEL'

    auth_url="https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id="+API_KEY+"&client_secret="+SECRET_KEY;

    res=urllib.request.urlopen(auth_url)
    json_data=res.read()
    
    return json.loads(json_data)['access_token']

def dump_res(buf):
   # print('buf=',buf)
   
    my_temp=json.loads(buf)
    if(my_temp['err_no']==3301):
        print('识别失败')
        return
    my_list=my_temp['result']
    global text
    text="".join(my_list[0])
 

def use_cloud(token):
    fp=wave.open('01.wav','rb')
    nf = fp.getnframes()  # 获取文件的采样点数量
    f_len = nf * 2  # 文件长度计算，每个采样2个字节
    audio_data = fp.readframes(nf)

    cuid="1"
    srv_url='http://vop.baidu.com/server_api' + '?cuid=' + cuid + '&token=' +token
    http_header=[
        'Content-Type:audio/pcm;rate=8000',
        'Content-Length: %d' % f_len
    ]
    c=pycurl.Curl()
    c.setopt(pycurl.URL,str(srv_url)) #curl doesn't support unicode 传递一个网址
    #c.setopt(c.RETURNTRANSFER,1)
    c.setopt(c.HTTPHEADER,http_header)#传入一个头部，只能是列表，不能是字典
    c.setopt(c.POST,1)#发送
    c.setopt(c.CONNECTTIMEOUT,80)#尝试连接时间
    c.setopt(c.TIMEOUT,80)#下载时间
    c.setopt(c.WRITEFUNCTION,dump_res)
    c.setopt(c.POSTFIELDS,audio_data)
    c.setopt(c.POSTFIELDSIZE,f_len)
    c.perform() # pycurl.perform() has no return val
    


def stt():
    my_record()
    print('ok!')
    use_cloud(get_token())
    
    
    
#tts初始化
IS_PY3 = sys.version_info.major == 3
if IS_PY3:
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import URLError
    from urllib.parse import urlencode
    from urllib.parse import quote_plus
else:
    import urllib2
    from urllib import quote_plus
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import URLError
    from urllib import urlencode

API_KEY = 'ClGl9cP9jHzmcupL62kcRpeu'
SECRET_KEY = 'XLiOvQQWCr3RRuOaX2RbXlEyNtpBkvEL'


# 发音人选择, 基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫，
# 精品音库：5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美 
PER = 3
# 语速，取值0-15，默认5中语速
SPD = 5
# 音调，取值0-15，默认为5中语调
PIT = 5
# 音量，取值0-9，默认为5中音量
VOL = 9
# 下载的文件格式, 3：mp3(default) 4： pcm-16k 5： pcm-8k 6. wav
AUE = 3

FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
FORMAT = FORMATS[AUE]

CUID = "123456PYTHON"
TTS_URL = 'http://tsn.baidu.com/text2audio'


class DemoError(Exception):
    pass


"""  TOKEN start """

TOKEN_URL = 'http://aip.baidubce.com/oauth/2.0/token'
SCOPE = 'audio_tts_post'  # 有此scope表示有tts能力，没有请在网页里勾选


def fetch_token():
    
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    if (IS_PY3):
        post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        #print('token http response http code : ' + str(err.code))
        result_str = err.read()
    if (IS_PY3):
        result_str = result_str.decode()

   # print(result_str)
    result = json.loads(result_str)
    #print(result)
    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not SCOPE in result['scope'].split(' '):
            raise DemoError('scope is not correct')
       # print('SUCCESS WITH TOKEN: %s ; EXPIRES IN SECONDS: %s' % (result['access_token'], result['expires_in']))
        return result['access_token']
    else:
        raise DemoError('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')


"""  TOKEN end """

def tts(word):
    token = fetch_token()
    tex = quote_plus(word)  # 此处TEXT需要两次urlencode
    #print(tex)
    params = {'tok': token, 'tex': tex, 'per': PER, 'spd': SPD, 'pit': PIT, 'vol': VOL, 'aue': AUE, 'cuid': CUID,
              'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数

    data = urlencode(params)
   # print('test on Web Browser' + TTS_URL + '?' + data)

    req = Request(TTS_URL, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()

        headers = dict((name.lower(), value) for name, value in f.headers.items())

        has_error = ('content-type' not in headers.keys() or headers['content-type'].find('audio/') < 0)
    except  URLError as err:
        print('asr http response http code : ' + str(err.code))
        result_str = err.read()
        has_error = True

    save_file = "error.txt" if has_error else 'result.' + FORMAT
    with open(save_file, 'wb') as of:
        of.write(result_str)

    if has_error:
        if (IS_PY3):
            result_str = str(result_str, 'utf-8')
        print("tts api  error:" + result_str)

    #print("result saved as :" + save_file)
    os.system('play '+'result.mp3')
 
    
def getTemp():
    url = 'http://wthrcdn.etouch.cn/weather_mini?city=曲靖'
    response = requests.get(url)
    wearher_json = json.loads(response.text)
    weather_dict = wearher_json['data']
    str = '%s%s%s%s' % (
    '先生',
    '当前温度', weather_dict['wendu'],'℃')
    return str

def getWeather():
    url = 'http://wthrcdn.etouch.cn/weather_mini?city=曲靖'
    response = requests.get(url)
    wearher_json = json.loads(response.text)
    weather_dict = wearher_json['data']
    str = '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % (
    '先生',
    '今天是', weather_dict['forecast'][0]['date'], '，', '\n',
    '天气', weather_dict["forecast"][0]['type'], '，', '\n',
    weather_dict['city'], '最', weather_dict['forecast'][0]['low'], '，', '\n',
    '最', weather_dict['forecast'][0]['high'], '，', '\n',
    '当前温度', weather_dict['wendu'], '℃', '，', '\n',
    weather_dict["forecast"][0]['fengxiang'],
    weather_dict["forecast"][0]['fengli'].split("[CDATA[")[1].split("]")[0])
    return str

def getTWeather():
    url = 'http://wthrcdn.etouch.cn/weather_mini?city=曲靖'
    response = requests.get(url)
    wearher_json = json.loads(response.text)
    weather_dict = wearher_json['data']
    str = '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % (
    '先生',
    '明天是', weather_dict['forecast'][1]['date'], '，', '\n',
    '天气', weather_dict["forecast"][1]['type'], '，', '\n',
    weather_dict['city'], '最', weather_dict['forecast'][1]['low'], '，', '\n',
    '最', weather_dict['forecast'][1]['high'], '，', '\n',
    weather_dict["forecast"][1]['fengxiang'],
    weather_dict["forecast"][1]['fengli'].split("[CDATA[")[1].split("]")[0],
    '。', '\n')
    return str

def DrawingRoomLight():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='keting', qos=0, retain=False)
    return ('客厅灯 已为您打开')
def CookingRoomLight():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='chufang', qos=0, retain=False)
    return ('厨房灯 已为您打开')
def LivingRoomLight():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='zhuwo', qos=0, retain=False)
    return ('主卧灯 已为您打开')
def ciwo():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='ciwo', qos=0, retain=False)
    return ('次卧灯 已为您打开')
def fengshan():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='fengshan', qos=0, retain=False)
    return ('已为您打开风扇')
def yangtai():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='yangtai', qos=0, retain=False)
    return ('阳台灯 已为您打开')

def DrawingRoomLight1():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='keting1', qos=0, retain=False)
    return ('客厅灯 已关闭')
def CookingRoomLight1():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='chufang1', qos=0, retain=False)
    return ('厨房灯 已关闭')
def LivingRoomLight1():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='zhuwo1', qos=0, retain=False)
    return ('主卧灯 已关闭')
def ciwo1():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='ciwo1', qos=0, retain=False)
    return ('次卧灯 已关闭')
def fengshan1():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='fengshan1', qos=0, retain=False)
    return ('已为您关闭风扇')
def yangtai1():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("test.ranye-iot.net", 1883, 60)
    client.publish('yyf1/topic', payload='yangtai1', qos=0, retain=False)
    return ('阳台灯 已关闭')

# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))
 
# Return % of CPU used by user as a character string
def getCPUuse():
    return(str(os.popen("top -bn1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip()))
 

def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:6])

def changeVoiceMax(number):
    os.system("pactl set-sink-volume 0 " + str(number)  + "%")

def playmusic(fileName):
    os.system('play ' + './musi/' + fileName+'.mp3' )
    global a
    a=1
 
def closeMplayer():
    isRunStr = str(os.popen("ps -ef | grep music | grep -v grep | awk '{print $1}' |sed -n '1p'").readline().strip())
   
    
    if isRunStr=='pi':
        os.system("ps -ef | grep music |  grep -v grep | awk '{print $2}'| xargs kill -9")
        os.system("ps -ef | grep play | grep mp3 | grep -v grep |awk '{print $2}'| xargs kill -9")
def getMplayerIsRun():
    isRunStr = str(os.popen("ps -ef | grep play | grep mp3| grep -v grep | awk '{print $1}' |sed -n '1p'").readline().strip())
    
    if isRunStr=='pi':
        return True
    else:
        return False 
def face():
    os.system("python3 03_face_recognition.py")
def yyfMain():
    tts("在的先生")
    stt()
    print(text)
    if '明' in text and '天' in text and '气' in text:
        tts(getTWeather())
    elif '今' in text and '天' in text and '气' in text:
        tts(getWeather())  
    elif '现在' in text and '温度' in text :
        tts(getTemp())
    elif '打开' in text and '主卧' in text :
        tts(LivingRoomLight())
    elif '打开' in text and '次卧' in text :
        tts(ciwo())
    elif '打开' in text and '客厅' in text :
        tts(DrawingRoomLight())
    elif '打开' in text and '风扇' in text :
        tts(fengshan())
    elif '打开' in text and '阳台' in text :
        tts(yangtai())
    elif '打开' in text and '厨房' in text :
        tts(CookingRoomLight())   
    elif '关闭' in text and '主卧' in text :
        tts(LivingRoomLight1())
    elif '关闭' in text and '次卧' in text :
        tts(ciwo1())
    elif '关闭' in text and '客厅' in text :
        tts(DrawingRoomLight1())
    elif '关闭' in text and '风扇' in text :
        tts(fengshan1())
    elif '关闭' in text and '阳台' in text :
        tts(yangtai1())
    elif '关闭' in text and '厨房' in text :
        tts(CookingRoomLight1())
    elif '随机' in text  and'放' in text and '音' in text or '歌' in text:
        tts("马上为您播放") 
        os.system('python3 ' + 'music.py' + ' > /dev/null 2>&1 &')
    elif '音量' in text or '声' in text:
        if '低' in text or '小' in text:
            changeVoiceMax(60)
        elif '恢复' in text or '正常' in text:
            changeVoiceMax(90)
        elif '最大' in text:
            changeVoiceMax(100)
        elif '大' in text or '高' in text:
            changeVoiceMax(90)
        tts('先生，已为您调制合适音量')
    elif 'cpu' in text or 'CPU' in text:
        # CPU informatiom
        CPU_temp = getCPUtemperature()
        CPU_usage = getCPUuse()
        tts('当前CPU温度' + str(CPU_temp) + '度' + '，' + 'CPU使用率百分之' + str(CPU_usage))
        
    elif '温度' in text:
        tts(getTemp())  
        time.sleep(1)
    elif '人脸识别' in text:
        tts('正在为您打开人脸识别')
        face()
    elif '内存' in text:
        # Output is in kb, here I convert it in Mb for readability
        RAM_stats = getRAMinfo()
        RAM_perc = round(100 * float(RAM_stats[1]) / float(RAM_stats[0]), 2)
        RAM_realPerc = round(100 * (float(RAM_stats[1]) + float(RAM_stats[4])) / float(RAM_stats[0]), 2)
        tts('内存已使用百分之' + str(RAM_perc) + '，' + '实际已使用百分之' + str(RAM_realPerc))

    elif '防守' in text or '放手' in text or '放首' in text or '播放' in text or '放一首' in text or '唱一首' in text or '听一下' in text or '听一首' in text:
        newStr = text.replace('播放','').replace('放一首','').replace('唱一首','').replace('听一下','').replace('听一首','').replace('放首','').replace('放手','').replace('防守','').replace('。','')
        closeMplayer()
        playmusic(newStr)
        time.sleep(1) 
        global a
           
        if a==0 :
            if getMplayerIsRun()==False :
                tts("本地没有找到你想要播放的歌曲，请从网易云下载")
                time.sleep(3)             
            a=0
        
    elif '停止' in text or '暂停' in text or '闭嘴' in text or '休息' in text or '关闭音乐' in text or '安静' in text:
        tts('正在关闭')
        closeMplayer()      
    else:
        time.sleep(2)   

