import requests
import urllib.request
import os
from bs4 import BeautifulSoup
if __name__=='__main__':
	header = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
}
	response = requests.get("https://music.163.com/song?id=1440742920",headers = header)
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
            with open('./music/%s.mp3' % music_name[i],"ab")as f:                 
                 f.write(res.content)
	print("下载完成")

    	    
    	

