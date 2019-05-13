from django.test import TestCase
# Create your tests here.
# -*- coding: utf-8 -*-
import re, requests, time, random, threading, pymysql
from my_fake_useragent import UserAgent
from threading import Lock
import queue
from threading import Thread
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.shortcuts import render
from django.shortcuts import HttpResponse



class MyCrawler():
    def __init__(self, seeds):
        # 初始化数据库连接信息
        self.db = pymysql.connect('127.0.0.1',
                                  'root',
                                  'root',
                                  charset='utf8',
                                  db='woaidu',
                                  port=3306)
        self.cursors = self.db.cursor()
        # 初始化当前抓取的深度
        self.current_deepth = 1
        # 初始化book列表
        self.books = []
        # 使用种子初始化url队列
        self.linkQuence = linkQuence()
        # 加锁,保护数据
        self.lock = Lock()
        # 线程池
        self.url_queue = queue.Queue()
        if isinstance(seeds, str):
            self.linkQuence.addUnvisitedUrl(seeds)
        if isinstance(seeds, list):
            for i in seeds:
                self.linkQuence.addUnvisitedUrl(i)
        print("Add the seeds url \"%s\" to the unvisited url list" % str(self.linkQuence.unVisited))

    # 抓取过程主函数
    def crawling(self, seeds, crawl_count):
        # 广度搜索
        # 循环条件：待抓取的链接不空且专区的网页不多于crawl_count
        while self.linkQuence.unVisitedUrlsEnmpy() is False and self.current_deepth <= crawl_count:
            # 队头url出队列
            visitUrl = self.linkQuence.unVisitedUrlDeQuence()
            print("队头url出队列： \"%s\"" % visitUrl)
            if visitUrl is None or visitUrl == "":
                continue

            # 获取超链接
            links = self.getHyperLinks(visitUrl)
            # 获取链接为空则跳过
            if links is None:
                continue

            print("获取新链接个数： %d" % len(links))
            # 将url放入已访问的url中
            self.linkQuence.addVisitedUrl(visitUrl)
            print("已访问网站数: " + str(self.linkQuence.getVisitedUrlCount()))

            # 未访问的url入列
            for link in links:
                self.linkQuence.addUnvisitedUrl(link)
            print("未访问的网站数: %d" % len(self.linkQuence.getUnvisitedUrl()))
            self.current_deepth += 1

        print("总的book数: %d" % self.books.__len__())

        # 多线程采集book
        for book in self.books:
            self.url_queue.put(book)
        spider_list = []
        for i in range(20):
            try:
                t1 = Thread(target=self.getPageData, args=())
                t1.start()
                spider_list.append(t1)
            except:
                i += 1
        for spider in spider_list:
            spider.join()

    # 获取源码中得超链接
    def getHyperLinks(self, url):
        try:
            links = []
            # 随机休眠一定时间
            time.sleep(random.random() * 2)
            # request头部信息
            header = {'User-Agent': UserAgent().chrome}
            # 获取源码
            html = requests.get(url, timeout=30, headers=header, verify=False)
            html.encoding = 'utf-8'
            urls = re.findall(r'href="(.*?)"', html.text)
            for ur in urls:
                # print('+'*50,ur)
                # 如果以【/book_】开头则是想要的book网址
                if ur.startswith('/book_'):
                    bookUrl = 'http://www.woaidu.org' + ur

                    # 查重，book列表如果已经存在该链接则不再添加
                    if self.books.__contains__(bookUrl):
                        continue
                    # 添加到book列表
                    self.books.insert(0, bookUrl)
                # 相关性判断，判断是否和所设定的网址有关系
                elif (ur.endswith('.html') and '/book_' not in ur) or 'www.woaidu.org/' in ur:
                    # print('>'*50,ur)
                    if not ur.startswith('http'):
                        ur2 = url + ur
                    else:
                        ur2 = ur
                    # 添加相关的网址链接
                    links.append(ur2)

            return links

        except Exception as e:
            return None

    def getPageData(self):
        while not self.url_queue.empty():
            url_data = self.url_queue.get()
            #print(url_data)
            header = {'User-Agent': UserAgent().chrome}
            html = requests.get(url_data, verify=False, headers=header)
            html.encoding = 'utf-8'
            with self.lock:
                if html.status_code == 200:
                    # 通过正则表达式，抓取跟主题相关的内容
                    #print(html.text)
                    nam = re.findall(r'<title>(.*?) txt电子书下载 - 我爱读电子书 - 我爱读', html.text)
                    author = re.findall(r'作者：(.*?)\n', html.text)
                    #summay = re.findall(r'(.*?)</p>', html.text, re.S)
                    summay = re.findall(r'<p class="listcolor descrition" style="padding: 10px;">(.*?)</p>', html.text, re.S)

                    # print('书名：', nam[0].strip())
                    # print('作者：', author[0].strip())
                    # print('原文网址：', url_data)
                    # print('简介：', summay[0].strip())

                    # 查重，根据book的url判断是否已经在数据库当中
                    select_sql = "SELECT COUNT(id) FROM book WHERE url = '{}'".format(url_data)
                    self.cursors.execute(select_sql)
                    count = self.cursors.fetchone()
                    # 如果存在，则不再添加，不存在则插入book表
                    if count[0] > 0:
                        print("数据库已经存在该书：" + url_data)
                    else:
                        # 插入book表的sql语句
                        book_sql = "insert into book (name, author, url, brief) values (%s,%s,%s,%s)"
                        # 执行插入book的sql语句
                        self.cursors.execute(book_sql, (nam[0].strip(), author[0].strip(), url_data, summay[0].strip()))
                        self.db.commit()
                        # 获取刚插入的book_id
                        select_id = "select id from book where name='{}'".format(nam[0].strip())
                        self.cursors.execute(select_id)
                        book_id = list(self.cursors.fetchall())[0][0]
                        # 获取下载地址
                        down_urls = re.findall(r'<a rel="nofollow" href=(.*) target="_blank">点击下载</a>', html.text)
                        # 获取更新时间
                        up_times = re.findall(r'div class="ziziziz">(\d+-\d+-\d+)</div', html.text)
                        new_sources = []
                        # 获取 来源
                        for old_url in down_urls:
                            # 获取第一个参数
                            one_info = re.findall(r'_([^_]+)', old_url)[0]
                            # 获取第二个参数
                            twq_info = re.findall(r'_([^_]+)', old_url)[1].split()[0][:-1]
                            sources = re.findall(
                                r'a rel="nofollow" href="https://txt.woaidu.org/bookdownload_bookid_{}_snatchid_{}.html" target="_blank">(.*?)</a>'.format(
                                    one_info, twq_info), html.text)[0]
                            new_sources.append(sources)
                        # 插入下载地址
                        book_down = []
                        # 将所有要下载的地址添加到book_down列表
                        for source, up_time, down_url in zip(new_sources, up_times, down_urls):
                            book_down.append((str(book_id), source, up_time, down_url.strip('""')))
                            # 插入下载地址的sql语句
                            down_sql = "insert into down_url(book_id, source, update_time, down_url) values (%s,%s,%s,%s)"
                            # 执行批量插入下载地址
                            self.cursors.executemany(down_sql, book_down)
                            self.db.commit()


class linkQuence():
    def __init__(self):
        # 已访问的url集合
        self.visted = []
        # 待访问的url集合
        self.unVisited = []
        # 获取访问过的url队列

    def getVisitedUrl(self):
        return self.visted
        # 获取未访问的url队列

    def getUnvisitedUrl(self):
        return self.unVisited
        # 添加到访问过得url队列中

    def addVisitedUrl(self, url):
        self.visted.append(url)
        # 移除访问过得url

    def removeVisitedUrl(self, url):
        self.visted.remove(url)
        # 未访问过得url出队列

    def unVisitedUrlDeQuence(self):
        try:
            return self.unVisited.pop()
        except:
            return None
            # 保证每个url只被访问一次

    def addUnvisitedUrl(self, url):
        if url != "" and url not in self.visted and url not in self.unVisited:
            self.unVisited.insert(0, url)
            # 获得已访问的url数目

    def getVisitedUrlCount(self):
        return len(self.visted)
        # 获得未访问的url数目

    def getUnvistedUrlCount(self):
        return len(self.unVisited)
        # 判断未访问的url队列是否为空

    def unVisitedUrlsEnmpy(self):
        return len(self.unVisited) == 0


def main(seeds, crawl_count):
    # 初始化MyCrawler对象
    craw = MyCrawler(seeds)
    # 执行抓取过程主函数
    craw.crawling(seeds, crawl_count)


# 主函数入口
if __name__ == "__main__":
    main(["http://www.woaidu.org/"], 1)
