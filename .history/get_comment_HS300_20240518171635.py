# -*- coding: utf-8 -*-
# @Time    : 2024/3/2
# @Author  : hpz
# @File    : get_comment_HS300.py
# @Software: VScode
# @Description: 东方财富股吧股评爬取

import os
import numpy as np
import pandas as pd
import logging
from tqdm import tqdm
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
class CommentDriver(object):
    """
    这是东方财富股吧股评爬取的类
    
    Attributes:
        url: 沪深300的股票代码（来自锐思数据库）评论网址
        code: 当前爬取的股票代码
        page: 当前爬取的股票评论的总页数
        current_page: 当前爬取的页码
        comments: 所有爬取到的评论，一条条存放。

        current_time: 运行程序的时间，与股评中的“今天”及股评页码有关
        outpath: 存放文件的地址

        StartWebdriver(): 进行webdriver的初始化设置，并启动
        RunStart(): 循环爬取每个股票的股评
        GetPage(): 用于获取每个股票评论的最大页数
        GetComment(): 用于获取每个股票每一页的评论
        PreS(): 将爬取下来的表格保存成csv，每个股票一个
    """

    def __init__(self, url, outpath='./'):
        self.url = url
        self.code = self.url[32:38]
        self.comments = []
        self.page = None
        self.current_page = None
        self.current_time = datetime.now()
        self.outpath=outpath
        os.makedirs(self.outpath, exist_ok=True)

    def logger_config(self, log_path, logging_name):
        '''
        配置log
        :param log_path: 输出log路径
        :param logging_name: 记录中name，可随意
        :return:
        '''
        '''
        logger是日志对象，handler是流处理器，console是控制台输出（没有console也可以，将不会在控制台输出，会在日志文件中输出）
        '''
        # 获取logger对象,取名
        logger = logging.getLogger(logging_name)
        # 输出DEBUG及以上级别的信息，针对所有输出的第一层过滤
        logger.setLevel(level=logging.DEBUG)
        
        if not logger.handlers:
            # 获取文件日志句柄并设置日志级别，第二层过滤
            handler = logging.FileHandler(log_path, encoding='UTF-8')
            handler.setLevel(logging.INFO)
            # 生成并设置文件日志格式
            formatter = logging.Formatter('%(message)s - %(levelname)s - %(asctime)s - %(name)s')
            handler.setFormatter(formatter)
            # 为logger对象添加句柄
            logger.addHandler(handler)
            # logger.addHandler(console)
        return logger
    
    def StartWebdriver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        # options.add_argument("start-minimized")

        options.add_argument("--window-size=1920,1080")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')

        driver = webdriver.Chrome(options=options)
       
        return driver

    def OpenWeb(self, url):
        try:
            self.driver = self.StartWebdriver()
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "abs_list "))).click() # 点击切换视图到摘要
            # self.driver.find_element(By.CLASS_NAME, "abs_list").click() # 点击切换视图到摘要
            # self.driver.minimize_window()
            # self.driver.refresh()
            self.logger.info(f"{url}可用！")
            time.sleep(2)
            return True
        except: 
            return False  

    def GetPage(self):
        try:
            page_cl = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "paging")))[-1]
            self.page = int(page_cl.get_attribute('innerText')[5: -6])
            # page_cl = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "paging"))).get_attribute('innerText')
            # self.page = int(page_cl[5: -6])
            self.logger.info(f"{self.code}共{self.page}页")
            time.sleep(2)
            return True
        except: return False  
        
    def GetComment(self):
        try:
            # Wait for the comments table to be present
            comments_tb = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'abstract_list')))
            # Find all the rows in the comments table
            comments_post = comments_tb.find_elements(By.CLASS_NAME, "post_main")

            today = f'{self.current_time.month}-{self.current_time.day}' 
            for post in comments_post:
                username = post.find_elements(By.CLASS_NAME, "username")[0].get_attribute('innerText')
                update_time = post.find_elements(By.CLASS_NAME, "basic_info")[0].get_attribute('innerText')
                title = post.find_elements(By.CLASS_NAME, "title")[0].get_attribute('innerText')
                content = post.find_elements(By.CLASS_NAME, "content")[0].get_attribute('innerText')

                update_time = update_time.replace("更新于 ", "").replace("今天", today)
                
                self.comments.append({
                    'username': username, 
                    'update_time': update_time,
                    'title': title,
                    'content': content,
                })
            return True
        except: return False
    
    def NextPage(self):
        try: 
            npage = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "paging")))[-1]
            # if len(npage) == 2:
            #     npage = npage[1]
            # else:
            #     npage = npage[0]
            WebDriverWait(npage, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "nextp"))).click() # 点击下一页
            self.current_page += 1
            return True
        except: return False
        
    def PreS(self):
        def add_current_year(date_str, datetime_now=self.current_time):
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    return f"{datetime_now.year}-{date_str}"
                return date_str

        try: 
            comment_df = pd.DataFrame(self.comments)
            comment_df = comment_df.drop_duplicates()
            comment_df['update_time'] = comment_df['update_time'].apply(add_current_year)
            comment_df.to_csv(os.path.join(self.outpath, f"{self.code}.csv"), index=False, encoding = "utf-8")
        except: self.logger.error(f"{self.code}保存CSV文件出错！")
        return
    
    def RunStart(self):
        self.logger = self.logger_config(log_path=os.path.join(self.outpath, 'log.txt'), logging_name='hpz')
        self.page = 0
        self.current_page = 1
    
        # error: open web failure
        open_trial = 0
        self.OpenWebf = self.OpenWeb(self.url)

        while self.OpenWebf == False and open_trial < 3:
            open_trial += 1
            self.logger.warning(f"{self.code}打开网页出错！重新尝试第{open_trial}次")
            try:
                self.driver.quit()
            except:
                pass
            self.OpenWebf = self.OpenWeb(self.url)

        if self.OpenWebf == False:
            self.logger.error(f"{self.url}无法进入！")
            try:
                self.driver.quit()
            except:
                pass
            return
        else:
            open_trial = 0
        
        # error: get page number failure
        getp_trial = 0
        self.GetPagef = self.GetPage()

        while self.GetPagef == False and getp_trial < 3:
            self.driver.quit()
            getp_trial += 1
            self.logger.warning(f"{self.code}获取页码出错！重新尝试第{getp_trial}次")
            self.OpenWeb(self.url)
            self.GetPagef = self.GetPage()

        if self.GetPagef == False:
            self.logger.error(f"{self.code}获取页码失败！")
            self.driver.quit()
            return
        else:
            getp_trial = 0
        
        # get comment one page by one
        comment_trial, page_trial = 0, 0
        pres = 0
        while self.current_page <= self.page:
            if self.current_page >= self.page:
                self.logger.info(f"{self.code}已到尾页！")
                pres = 1
                break
            
            # 每100页重启一遍driver
            if self.current_page % 500 == 0:
                self.driver.quit()
                self.OpenWeb(self.url.replace('.html', f'_{self.current_page}.html'))

            # error: get comment failure
            self.GetCommentf = self.GetComment()
            while self.GetCommentf == False and comment_trial < 3:
                self.driver.quit()
                comment_trial += 1
                self.logger.warning(f"{self.code}的{self.current_page}页获取评论出错！重新尝试第{comment_trial}次")
                self.OpenWeb(self.url.replace('.html', f'_{self.current_page}.html'))
                self.GetCommentf = self.GetComment()

            if self.GetCommentf == False:
                self.logger.error(f"{self.code}的{self.current_page}页获取评论出错！")
                ###
                comment_trial = 0
                self.current_page += 1
                self.OpenWeb(self.url.replace('.html', f'_{self.current_page}.html'))
                self.GetCommentf = self.GetComment()
                # break

            else:
                comment_trial = 0

            # error: nextp error 
            self.NextPagef = self.NextPage()
            while self.NextPagef == False and page_trial < 3:
                self.driver.quit()
                page_trial += 1
                self.logger.warning(f"{self.code}的{self.current_page}翻页出错！重新尝试第{page_trial}次")
                self.OpenWeb(self.url.replace('.html', f'_{self.current_page}.html'))
                self.NextPagef = self.NextPage()
 
            if self.NextPagef == False:
                # self.driver.quit()
                self.logger.error(f"{self.code}的{self.current_page}翻页出错！")
                page_trial = 0
                self.current_page += 1
                self.OpenWeb(self.url.replace('.html', f'_{self.current_page}.html'))
                # break

            else:
                page_trial = 0
            
        self.driver.quit()
        if pres == 1:
            self.PreS()
            self.logger.info(f"{self.code}爬取并保存成功！")
        logging.shutdown()
        return  
    
    
df = pd.read_csv('./数据/RESSET_IDXCOMPO.CSV', encoding='gbk')
df["证券代码_成分_SecuCd_Compo"] = df["证券代码_成分_SecuCd_Compo"].apply(lambda x: str(int(x)).zfill(6))
df["codehtml"] = df["证券代码_成分_SecuCd_Compo"].apply(lambda x:'https://guba.eastmoney.com/list,' + x +'.html')
df["结束日期_EndDt"] = df["结束日期_EndDt"].fillna('2024-03-01')
outpath = './数据/HS300_comment_raw/'
done_list = [_.split('.')[0] for _ in os.listdir(outpath)]
for i in range(len(done_list)):
    done_list[i] = 'https://guba.eastmoney.com/list,' + done_list[i] +'.html'
codelist_HS300 = df[~df["codehtml"].isin(done_list)]["codehtml"].unique().tolist()
print(len(codelist_HS300), len(done_list))
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_url(url, outpath=outpath):
    comment_driver = CommentDriver(url, outpath=outpath)
    comment_driver.RunStart()

# 设置线程池的最大线程数
max_threads = 2

with ThreadPoolExecutor(max_workers=max_threads) as executor:
    # 将每个链接的处理任务提交到线程池
    futures = [executor.submit(process_url, url, outpath) for url in codelist_HS300]
    # 使用tqdm创建进度条
    for _ in tqdm(as_completed(futures), total=len(codelist_HS300), desc='Retrieving comments'):
        pass