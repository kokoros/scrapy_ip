# -*- coding: utf-8 -*-
import scrapy
import requests
import random
import time
import re
#连接redis数据库
import redis

#导入多线程
from threading import Thread

#创造item
from ..items import IppoolItem

class IppoolSpider(scrapy.Spider):
    name = 'ippool'
    allowed_domains = ['www.xicidaili.com']
    # start_urls = ['http://www.xicidaili.com/nn/']

    #因为不想要先丢个url再爬取,所以这里要重写方法
    #重写Spider类中的start_requests方法
    def start_requests(self):
        # 变量引用自settings
        # 连接redis数据库 设为存入的是字符串
        pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0, decode_responses=True)
        self.r = redis.Redis(connection_pool=pool)
        #清除集合
        self.r.delete("ip_port")
        print('删除Redis数据库中ip_port集合完毕,准备录入新数据...')

        # 累计可用的IP和端口号
        self.useip_list = []
        prevsn = 1
        while prevsn < 10:
            url = 'http://www.xicidaili.com/nn/{}'.format(str(prevsn))
            #把url地址入队列
            yield scrapy.Request(
                url=url,
                #解析函数
                callback=self.parse_ip
            )
            prevsn += 1

    # 获取首页的天IP
    def parse_ip(self, response):
        #正则 匹配出每个ip
        p = '<tr.*?</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>.*?</td>.*?<td.*?</td>.*?<td>.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td>(.*?)</td>.*?<td.*?</td>.*?</tr>'
        re_obj = re.compile(p, re.S)
        ip_list = re_obj.findall(response.text)
        yield print(ip_list)
        #遍历
        for i in ip_list:
            #如果是包含天的IP
            if '天' in i[2]:
                print('天', i)
                #尝试ip是否可用
                ip_one = i[0]
                port_one = i[1]
                # 建立线程列表
                threads_list = []

                #传入尝试链接的函数
                #返回得到可用的ip和端口号
                #如果列表中元素小于10位
                if len(self.useip_list) < 10:
                    #试用ip
                    print('准备试用ip...')
                    # 开一个线程
                    t = Thread(
                        target=self.try_ipuse,
                        args=(ip_one, port_one)
                    )
                    #添加到线程列表
                    threads_list.append(t)
                    # 启动线程
                    t.start()
                    # self.try_ipuse(ip_one, port_one)
                #如果线程太多了
                elif len(threads_list) > 10:
                    #判断线程是否活动
                    #当线程处于新建、死亡两种状态时，is_alive()方法返回False
                    for t in threads_list:
                        if not t.is_alive():
                            #回收这个线程
                            t.join()
                            #从列表删除
                            threads_list.remove(t)




    #尝试链接的函数
    def try_ipuse(self, ip_one, port_one):
        print('测试ip')
        # 测试网站
        url = 'http://httpbin.org/get'
        # 要尝试的IP
        proxies = {'http': 'http://{}:{}'.format(ip_one, port_one)}
        # 尝试发送请求
        try:
            res = requests.get(
                url=url,
                proxies=proxies,
                headers={'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'}
            )
            res.encoding = 'utf-8'
            if res.text:
                use_one = (ip_one, port_one)
                #ip可用 添加到列表中
                self.useip_list.append(use_one)
                # 添加入redis数据库 添加集合
                self.r.sadd('ip_port', str(use_one))
                print('已添加一个有效数据入redis')


        except Exception as e:
            print('代理IP不可用:', e)