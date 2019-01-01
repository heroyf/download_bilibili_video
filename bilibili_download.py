# -*- coding:utf-8 -*-
__author__ = 'Heroyf'

''' 原作者地址 https://github.com/Henryhaohao/Bilibili_video_download
由heroyf进行二次开发
'''

import requests
import time
import hashlib
import urllib.request
import re
from xml.dom.minidom import parseString
from moviepy.editor import *
import os
import sys
import threading

# 用户输入av号或者视频链接地址
key_video = {}
print('*'*30 + 'B站视频下载小助手ver2.0' + '*'*30)
start_list = []
start = input('请输入您要下载的B站av号或者视频链接地址(如需下载多个，以","进行分割):')
start_list = start.split(",")
# print(start_list)
start_url = []
for i in start_list:
    if i.isdigit() == True:
        start_url.append('https://www.bilibili.com/video/av'+i)
        key_video.setdefault(i)
        key_video[i] = []
    else:
        pass
# print(start_url)

# 视频质量
# <accept_format ><![CDATA[flv, flv720, flv480, flv360]] ></accept_format >
#<accept_quality ><![CDATA[80, 64, 32, 16]] ></accept_quality >#
# <accept_description><![CDATA[高清 1080P,高清 720P,清晰 480P,流畅 360P]]></accept_description>
quality_key = {"80": "1080P", "64": "720P", "32": "480P", "16": "360P"}
quality = input(
    '请输入您要下载视频的清晰度(1080p:80;720p:64;480p:32;360p:16)(填写80或64或32或16):')

# 获取视频的cid,title
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Referrer': 'www.bilibili.com'
}
download_num = len(start_url)  # 记录一共要下载几个av号
html = ""
cid = []
title = []
aid = []
real_cid = []
real_cid_num = 0  # 记录有几个P，取得的cid值需要-1
for i in range(download_num):

    html = requests.get(start_url[i], headers=headers).text
    rr = re.compile(r'"cid":(\d+)')
    real_cid = rr.findall(html)
    real_cid_num = len(real_cid) - 1  # av视频中的真实cid数量
    title.append(re.search(r'<h1 title="(.*?)">', html).group(1))
    aid.append(re.search(r'aid=(\d+)&', html).group(1))
    for cleaned_title in title:
        # 清洗一下标题名称(不能有\ / : * ? " < > |)
        cleaned_title = re.sub(r'[\/\\:*?"<>|]', '', cleaned_title)
    if real_cid_num == 1:
        print("av:{},一共有1个P".format(aid[i]))
        key_video[aid[i]].append([real_cid[0]])
        cid.append(real_cid[0])
    elif real_cid_num > 1:
        print("av:{},一共有{}个P".format(aid[i], real_cid_num))
        key_video[aid[i]].append([real_cid[i]
                                  for i in range(1, len(real_cid))])
        for i in range(1, len(real_cid)):
            cid.append(real_cid[i])
print('[下载视频的标题]:{}'.format(title))
print('[下载视频的cid]:{}'.format(cid))
# print(key_video)


def get_keys(d, values):
    return [k for k, v in d.items() for i in v[0] if i == values]


# 访问API地址
SEC1 = '94aba54af9065f71de72f5508f1cd42e'
ts = str(int(time.time()))  # 时间戳
# 清晰度:1080P:80 ;720P:64; 480P:32; 流畅:15 ;自动:0
params = []
encrypt = []
url_api = []
video_list = []  # 存放真实视频地址
for i in range(len(cid)):
    params.append('appkey=84956560bc028eb7&cid={}&otype=xml&qn={}&quality={}&type='.format(
        cid[i], quality, quality))  # otype=json也行!!
    encrypt.append(hashlib.md5(
        bytes(params[i]+SEC1, encoding='utf-8')).hexdigest())
    url_api.append('https://interface.bilibili.com/v2/playurl?' +
                   params[i] + '&sign=' + encrypt[i])
# print(url_api)
# ['https://interface.bilibili.com/v2/playurl?appkey=84956560bc028eb7&cid=69047669&otype=xml&qn=15&quality=15&type=&sign=5f6e538dab4eebfdd38f1b7d53e94577',
# 'https://interface.bilibili.com/v2/playurl?appkey=84956560bc028eb7&cid=69032273&otype=xml&qn=15&quality=15&type=&sign=4940bd2f8cbf4abdecf45ab9b662d1b6']
for i in range(len(cid)):
    headers = {
        # 注意加上referer
        'Referer': 'https://www.bilibili.com/video/av'+str(get_keys(key_video, cid[i])),
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    html = requests.get(url_api[i], headers=headers).text
    # print(html)
    doc = parseString(html.encode('utf-8'))
    durl = doc.getElementsByTagName('durl')
    for i in durl:
        video = i.getElementsByTagName('url')[0]
        url_video = video.childNodes[0].data
        # print(url_video)
        video_list.append(url_video)  # 真实地址导入


# 下载视频进度条,下载速度
def Schedule_cmd(blocknum, blocksize, totalsize):
    speed = (blocknum * blocksize) / (time.time() - start_time)
    # speed_str = " Speed: %.2f" % speed
    speed_str = " Speed: %s" % format_size(speed)
    recv_size = blocknum * blocksize

    # 设置下载进度条
    f = sys.stdout
    percent = recv_size / totalsize
    percent_str = "%.2f%%" % (percent * 100)
    n = round(percent * 50)
    s = ('#' * n).ljust(50, '-')
    f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
    f.flush()
    # time.sleep(0.1)
    f.write('\r')


def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.3fG" % (G)
        else:
            return "%.3fM" % (M)
    else:
        return "%.3fK" % (kb)


# 下载函数


def run_download(cid, num, referer, video_list, title, quality):
    print('[正在下载,请稍等...]:' + title +
          "——{}P".format(num) + '    \033[5;31;2mcid号:\033[0m' + '\033[5;31;2m%s\033[0m' % cid)
    opener = urllib.request.build_opener()
    # 请求头
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
        ('Accept', '*/*'),
        ('Accept-Language', 'en-US,en;q=0.5'),
        ('Accept-Encoding', 'gzip, deflate, br'),
        ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
        ('Referer', referer),  # 注意修改referer,必须要加的!
        ('Origin', 'https://www.bilibili.com'),
        ('Connection', 'keep-alive'),
    ]
    urllib.request.install_opener(opener)
    # 多线程下载开始时间
    try:
        urllib.request.urlretrieve(url=video_list, filename=r'./bilibili_video/{}/{}-{}-{}.flv'.format(
            title, title, cid, quality_key[quality]), reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
        print('第 {} P  [下载完成]:'.format(num) + title.ljust(80, ' '))
    except:
        print('下载出错')


flag = 0
thread_list = []  # 多线程
for i in range(download_num):
    num = 1
    if not os.path.exists(r'./bilibili_video/{}'.format(title[i])):
        os.makedirs(r'./bilibili_video/{}'.format(title[i]))
    for j in range(len(key_video[aid[i]][0])):
        referer = 'https://www.bilibili.com/video/av' + \
            str(get_keys(key_video, key_video[aid[i]][0][j]))
        t = threading.Thread(target=run_download, args=(
            key_video[aid[i]][0][j], num, referer, video_list[flag], title[i], quality))
        flag = flag + 1
        num = num + 1
        thread_list.append(t)
for t in thread_list:
    start_time = time.time()
    t.start()
    t.join()  # 阻塞直到子线程完成，结束主线程
print("视频保存在:{}".format(os.getcwd())+"\\bilibili_video\\")
