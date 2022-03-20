@[TOC](# python下载抖音无水印视频和网易云歌曲)


   **有时候做项目，突然需要一些音频、视频资源，用浏览器下载太麻烦，下载歌曲有些还需要会员什么的，所以想直接用python爬点资源。不用白不用，知识就是用来方便自己的。**

## python下载抖音无水印视频
代码在下面
还有几个重要参数，`sec_uid：` 自己抖音的id也可以是别人的（这个是我随便找的）

![在这里插入图片描述](https://img-blog.csdnimg.cn/a5a179d063154fcd86b865de5e2192c8.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA5bCP6aOe54ix5a2m5LmgMQ==,size_20,color_FFFFFF,t_70,g_se,x_16#pic_center)
一般情况在网络通常的情况，5次尝试内就能成功，这个当时没联网
![在这里插入图片描述](https://img-blog.csdnimg.cn/63a638b8620e4b68941febef38d1ca80.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA5bCP6aOe54ix5a2m5LmgMQ==,size_16,color_FFFFFF,t_70,g_se,x_16#pic_center)

 #这里参数f是下载喜欢，p是下载作品     ，下面代码有注释
        type_flag ='f' 
需要注意的是，“喜欢” 记得在抖音里 **隐私设置 ->点赞->主页喜欢列表**改为**公开可见**

根据自己需要下载
![在这里插入图片描述](https://img-blog.csdnimg.cn/3eb0ccf12e2344ebbe7ffda1d82435f1.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA5bCP6aOe54ix5a2m5LmgMQ==,size_13,color_FFFFFF,t_70,g_se,x_16)

```python
#!/usr/bin/env python
# encoding: utf-8
import os, sys, requests
import json, re, time
from retrying import retry
from contextlib import closing


class DouYin:
    def __init__(self):
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        }
    def get_video_urls(self, sec_uid, type_flag='p'):
        '''
        获取用户的视频链接
        type_flag：视频类型
        返回：昵称，video_list
        '''
        user_url_prefix = 'https://www.iesdouyin.com/web/api/v2/aweme/post' if type_flag == 'p' else 'https://www.iesdouyin.com/web/api/v2/aweme/like'
        print('---解析视频链接中...\r')

        i = 0
        result = []
        while result == []:
            i = i + 1
            print('---正在第 {} 次尝试...\r'.format(str(i)))
            user_url = user_url_prefix + '/?sec_uid=%s&count=2000' % (sec_uid)
            response = self.get_request(user_url)
            html = json.loads(response.content.decode())
            if html['aweme_list'] != []:
                result = html['aweme_list']

        nickname = None
        count=0
        video_list = []
        for item in result:
            count+=1
            if nickname is None:
                nickname = item['author']['nickname'] if re.sub(r'[\/:*?"<>|]', '',
                                                                item['author']['nickname']) else None

            video_list.append({
                'desc': "{}.".format(str(count))+re.sub(r'[\/:*?"<>|\n]', '', item['desc']) if item['desc'] else "{}.".format(str(count))+'无标题' + str(int(time.time())),
                'url': item['video']['play_addr']['url_list'][0]
            })
        return nickname, video_list

    def get_download_url(self, video_url, watermark_flag):
        
        if watermark_flag == True:
            download_url = video_url.replace('api.amemv.com', 'aweme.snssdk.com')
        else:
            download_url = video_url.replace('aweme.snssdk.com', 'api.amemv.com')

        return download_url

    def hello(self):
        print("开始解析")
        return self

    def run(self):
        sec_uid = 'MS4wLjABAAAAuc2-ZhGi1vmVQl-K6IcTm2Rxvk5UG6BEkSbywa-MVMQ'
        watermark_flag = 0
        watermark_flag = bool(int(watermark_flag)) if watermark_flag else 0
         #这里参数f是下载喜欢，p是下载作品     
        type_flag ='f' 
        
         #下载目录
        save_dir = "./Download/"
    
        nickname, video_list = self.get_video_urls(sec_uid, type_flag)
        nickname_dir = os.path.join(save_dir, nickname)

        if not os.path.exists(nickname_dir):
            os.makedirs(nickname_dir)

        if type_flag == 'f':
            if 'favorite' not in os.listdir(nickname_dir):
                os.mkdir(os.path.join(nickname_dir, 'favorite'))

        print('---视频下载中: 共有%d个作品...\r' % len(video_list))
        sum1 = int(input('需要下载几个：'))
        for num in range(sum1):
            print('---正在解析第%d个视频链接 [%s] 中，请稍后...\n' % (num + 1, video_list[num]['desc']))

            video_path = os.path.join(nickname_dir, video_list[num]['desc']) if type_flag != 'f' else os.path.join(
                nickname_dir, 'favorite', video_list[num]['desc'])
            if os.path.isfile(video_path):
                print('---视频已存在...\r')
            else:
                self.video_downloader(video_list[num]['url'], video_path, watermark_flag)
            print('\n')
        print('---下载完成...\r')
    def video_downloader(self, video_url, video_name, watermark_flag=False):
        '''
        下载视频
         video_url：视频的网址
         video_name：视频的名称
         watermark_flag：视频的标志
        返回：无    
            '''
        size = 0
        video_url = self.get_download_url(video_url, watermark_flag=watermark_flag)
        with closing(requests.get(video_url, headers=self.headers, stream=True)) as response:
            chunk_size = 1024
            content_size = int(response.headers['content-length'])
            if response.status_code == 200:
                sys.stdout.write('----[文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))

                with open(video_name + '.mp4', 'wb') as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        size += len(data)
                        file.flush()

                        sys.stdout.write('----[下载进度]:%.2f%%' % float(size / content_size * 100) + '\r')
                        sys.stdout.flush()

    @retry(stop_max_attempt_number=3)
    def get_request(self, url, params=None):
        
        if params is None:
            params = {}
        response = requests.get(url, params=params, headers=self.headers, timeout=10)
        assert response.status_code == 200
        return response

    @retry(stop_max_attempt_number=3)
    def post_request(self, url, data=None):
        if data is None:
            data = {}
        response = requests.post(url, data=data, headers=self.headers, timeout=10)
        assert response.status_code == 200
        return response

    def run(self):
        sec_uid = 'MS4wLjABAAAAuc2-ZhGi1vmVQl-K6IcTm2Rxvk5UG6BEkSbywa-MVMQ'
        watermark_flag = 0
        watermark_flag = bool(int(watermark_flag)) if watermark_flag else 0
         #这里参数f是下载喜欢，p是下载作品     
        type_flag ='f' 
        
         #下载目录
        save_dir = "./Download/"
    
        nickname, video_list = self.get_video_urls(sec_uid, type_flag)
        nickname_dir = os.path.join(save_dir, nickname)

        if not os.path.exists(nickname_dir):
            os.makedirs(nickname_dir)

        if type_flag == 'f':
            if 'favorite' not in os.listdir(nickname_dir):
                os.mkdir(os.path.join(nickname_dir, 'favorite'))

        print('---视频下载中: 共有%d个作品...\r' % len(video_list))
        sum1 = int(input('需要下载几个：'))
        for num in range(sum1):
            print('---正在解析第%d个视频链接 [%s] 中，请稍后...\n' % (num + 1, video_list[num]['desc']))

            video_path = os.path.join(nickname_dir, video_list[num]['desc']) if type_flag != 'f' else os.path.join(
                nickname_dir, 'favorite', video_list[num]['desc'])
            if os.path.isfile(video_path):
                print('---视频已存在...\r')
            else:
                self.video_downloader(video_list[num]['url'], video_path, watermark_flag)
            print('\n')
        print('---下载完成...\r')


if __name__ == "__main__":
    DouYin().hello().run()

```

## python下载网易云歌单
这里稍微有个坑
地址上有#，不能用，还有就是有些不能下载

![在这里插入图片描述](https://img-blog.csdnimg.cn/9e82027ad2d547bdb729712673e34206.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA5bCP6aOe54ix5a2m5LmgMQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
解决办法也很简单，点这个图标，然后刷新一下，真实地址就出来了
![在这里插入图片描述](https://img-blog.csdnimg.cn/a2d147e2f9204899ae7cb0ac8bec046e.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA5bCP6aOe54ix5a2m5LmgMQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
然后把地址粘在代码`response = requests.get处
`![在这里插入图片描述](https://img-blog.csdnimg.cn/1aca6cd6b203431eae429b62a18c334f.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA5bCP6aOe54ix5a2m5LmgMQ==,size_20,color_FFFFFF,t_70,g_se,x_16#pic_center)
贴下代码

```python
import requests
import urllib.request
import os
from bs4 import BeautifulSoup
if __name__=='__main__':
	header = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
}

	response = requests.get("https://y.music.163.com/m/playlist?id=6894168416",headers = header)
	response.encoding = 'utf-8'
	html = response.text
	bf = BeautifulSoup(html,"lxml")
	texts = bf.find('ul', class_="f-hide")
	texts = texts.find_all('a')
	music_name = []
	music_url = []
	server = "http://music.163.com/song/media/outer/url"
	for i in texts:
            music_name.append(i.string)
            url = str(server) + i.get("href")[5:] + ".mp3"
            music_url.append(url)
            print(url)
	num = len(music_name)
	header1 = {
	    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
	}
	for i in range(num):
            res = requests.get(music_url[i],headers = header1)
            with open('./musi/%s.mp3' % music_name[i],"ab")as f:                 
                 f.write(res.content)
	print("下载完成")

    	    
    	

```


## python下载指定歌曲
这个经过测试可以直接拿来用，但有些歌不能放，大部分都可以
```python
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
    first_key = forth_param
    second_key = 16 * 'F'
    h_encText = AES_encrypt(first_param, first_key, iv)
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


def load_song(num, result):
    
    if isinstance(int(num), int):
        num = int(num)
        if num >= 0 and num <= len(result):
            song_id = ressult[num]['id']
            song_down_link = "http://music.163.com/song/media/outer/url?id=" + ressult[num]['id'] + ".mp3"  # 根据歌曲的 ID 号拼接出下载的链接。歌曲直链获取的方法参考文前的注释部分。
            print("歌曲正在下载...")
            response = requests.get(song_down_link, headers=headers).content  # 亲测必须要加 headers 信息，不然获取不了。
            
            os.chdir(pathmusic)
            f = open(ressult[num]['name'] + ".mp3", 'wb')  # 以二进制的形式写入文件中
            f.write(response)
            f.close()
            print("下载完成.\n\r")
        else:
            print("你输入的数字不在歌曲列表范围，请重新输入")
    else:
        print("请输入正确的歌曲序号")



if __name__ == "__main__":

    search_name = input("请输入你想要在网易云音乐中搜索的单曲：")
    headers = {
        'Cookie': 'appver=1.5.0.75771;',
        'Referer': 'http://music.163.com/'
    }
    first_param = r'{"hlpretag":"<span class=\"s-fc7\">","hlposttag":"</span>","s":"' + search_name + r'","type":"1","offset":"0","total":"true","limit":"30","csrf_token":""}'
    second_param = "010001"
    third_param = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
    forth_param = "0CoJUm6Qyw8W8jud"
    url = "https://music.163.com/weapi/cloudsearch/get/web?csrf_token="
    params = get_params()
    encSeckey = get_encSecKey()
    ressult_b = get_json(url, params, encSeckey)
    ressult = handle_json(ressult_b)  # 过滤出需要的数据，存入到result中
    print("%3s %-35s %-20s %-20s " %("序号", "  歌名", "歌手", "专辑") )
    for i in range(len(ressult)):
        print("%3s %-35s %-20s %-20s " %(ressult[i]["num"], ressult[i]["name"], ressult[i]["singer"], ressult[i]["song_sheet"]))
    num = input("请输入你想要下载歌曲的序号/please input the num you want to download：")
    load_song(num, ressult)  # 下载歌曲
```
