# -*- coding: utf-8 -*-
import requests
from fake_useragent import UserAgent
from time import sleep
from random import randint
import urllib.parse
from PIL import Image
from io import BytesIO
import pymongo
import json
import schedule


#获取页面
def get_html(url):
    headers = {
        "User-Agent": UserAgent().random
    }
    #模拟浏览器，每次访问等3-5秒
    sleep(randint(3, 5))
    response = requests.get(url, headers=headers)

    return response.text

#解析列表页面
def parse_index_html(html):
    #对json数据反序列化，通过key获取指定信息
    data = json.loads(html)['data']
    #建立储存容器列表
    imgs = []
    titles = []
    names = []
    follow_counts = []
    source_urls = []
    descriptions = []
    for d in data:
        #判断是否有大图
        if 'image_list' in d:
            imglist = d['image_list']
            title = d['title']
            for img in imglist:
                #对图片地址做匹配处理，转换为大图地址
                imgurl = 'http:' + img['url'].replace('list', 'large')
                imgs.append(imgurl)
                titles.append(title)
        #判断是否存在用户信息
        elif 'merge_user' in d:
            user_title = d['merge_user']

            for user in user_title:
                screen_name = user['screen_name']
                follow_count = user['follow_count']
                source_url = user['source_url']
                description = user['description']
                # 获取粉丝大于一万的头条号作者
                if follow_count > 10000:
                    names.append(screen_name)
                    follow_counts.append(follow_count)
                    source_urls.append(source_url)

                    descriptions.append(description)
        else:
            continue
    return imgs, titles, names, follow_counts, source_urls, descriptions

#保存图片
def save_img(src, i, title):
    response = requests.get(src)
    #开启图片流
    image = Image.open(BytesIO(response.content))
    # 转换图片格式，防止图片格式不同报错
    image = image.convert('RGB')
    intab = "/?:<\n>？|*"
    outtab = "123456789"
    trantab = title.maketrans(intab, outtab)  # 制作翻译表
    title = title.translate(trantab)
    image.save('E:/toutiao4/%s%d.jpg' % (title, i))

#建立数据库连接
def get_collection():
    client = pymongo.MongoClient()
    collection = client.toutiao.user
    return client, collection

#存入数据到数据库
def save_data(item, collection):

    collection.insert(item)

#关闭数据库连接
def close_client(client):
    client.close()

#主函数
def main():
    base_url = "http://www.toutiao.com/search_content/?offset={0}&format=json&keyword={1}&autoload=true&count=20&cur_tab=1"
    #通过改变关键词来爬取相应内容
    search_word = '时尚'
    offset = 0
    while True:
        #解析中文
        url = base_url.format(offset, urllib.parse.quote(search_word))

        index_html = get_html(url)

        imgs, titles, names, follow_counts, source_urls, descriptions = parse_index_html(index_html)

        if len(titles) == 0:
            break
        item = {}

        for name, follow, desc in zip(names, follow_counts, descriptions):
            item['_id'] = int(follow) + randint(1,100)
            item['names'] = name
            item['follow_counts'] = follow
            item['descriptions'] = desc
            save_data(item,collection)
        i = 1
        for img, title in zip(imgs, titles):
            # print(img)
            try:
                save_img(img, i, title)
                i += 1
            except:
                continue
        offset += 20


if __name__ == '__main__':
    #连接数据库
    client, collection = get_collection()
    #每七天运行一次
    # schedule.every(7).days.do(main)
    #每三秒运行一次
    schedule.every(3).seconds.do(main)
    while True:
        schedule.run_pending()
    close_client(client)
