# -*- coding: utf-8 -*-
# @Time    : 2024/3/15
# @Author  : hpz
# @File    : daily_sentiment.py
# @Software: VScode
# @Description: 计算HS300股评的日度情绪

import numpy as np
import pandas as pd
import os
from multiprocessing import Pool
import time


def get_list(datapath, outpath):
    # 获取待处理的list
    try:
        datalist = os.listdir(datapath)
        donelist = os.listdir(outpath)
        tohandle_list = [x for x in datalist if x not in donelist]
        tohandle_list = [x for x in tohandle_list if x[-4:] == '.csv']
        return tohandle_list
    except:
        return False
    
def get_trade_date():
    # 获取交易日数据
    trade_date = pd.read_csv("./数据/trade_date.csv")
    trade_date["calendar_date"] = trade_date["calendar_date"].apply(lambda x: x + " 15:00:00")
    trade_date = trade_date[trade_date["is_trading_day"] == 1]
    trade_date = trade_date[["calendar_date"]]
    trade_date["calendar_date"] = pd.to_datetime(trade_date["calendar_date"], format='%Y-%m-%d %H:%M:%S')
    # 计算交易日间隔的天数
    trade_date["interval"] = trade_date["calendar_date"].diff().dt.days
    trade_date["interval"] = trade_date["interval"].fillna(1)
    trade_date_l = trade_date["calendar_date"].tolist()
    return trade_date, trade_date_l

# 定义一个处理日度情绪数据的类

class daily_sentiment(object):
    def __init__(self, stock, datapath, timepath, outpath, trade_date, trade_date_l):
        self.datapath = datapath
        self.timepath = timepath
        self.outpath = outpath
        self.stock = stock
        self.trade_date = trade_date
        self.trade_date_l = trade_date_l
    
    def get_time_df(self):
        # 获取股评的时间数据
        time_df = pd.read_csv(os.path.join(timepath, self.stock))
        time_df["time"] = pd.to_datetime(time_df["update_time"], format='%Y-%m-%d %H:%M')
        return time_df

    def get_sentiment_df(self):
        # 获取股评的情绪数据
        sentiment_df = pd.read_csv(os.path.join(datapath, self.stock),  header=None, names=['neg', 'pos'])
        sent_list = sentiment_df['pos'].tolist()
        return sent_list
    
    
    def get_time_inds(self, time_df):
        trade_date_l = self.trade_date_l
        # 获取股评的日期在交易日中的位置
        time_inds = []
        num = []
        for i in range(len(trade_date_l)-1):
            time1 = time_df[(trade_date_l[i] < time_df["time"])]
            time_ind = time1[(time1["time"] < trade_date_l[i+1])].index.tolist()
            time_inds.append(time_ind)
            num.append(len(time_ind))
        return time_inds, num
    
    def stmt_simple_sum(self, time_inds, sent_list):
        # 简单加和
        sentiment_value = []
        for i in range(len(time_inds)):
            ind = time_inds[i]
            if len(ind) == 0:
                sentiment1 = 0
            else:
                sentiment = [sent_list[j] for j in ind]
                sentiment1 = np.sum(sentiment)
            sentiment_value.append(sentiment1)
        return sentiment_value

    def handle_sentiment(self, sentiment_value, num):
        trade_date = self.trade_date
        # 处理情绪数据
        date = trade_date["calendar_date"].tolist()
        date = date[1:]
        interval = trade_date["interval"].tolist()
        interval = interval[1:]
        df = pd.DataFrame({"date": date, "interval": interval, "sentiment": sentiment_value, "num": num})
        df["sentiment_daily"] = df["sentiment"] / df["interval"]
        
        return df
    

    def save_sentiment(self, df):
        # 保存处理后的情绪数据
        df.to_csv(os.path.join(outpath,self.stock), index=False)
    
    def run(self):
        time_df = self.get_time_df()
        sent_list = self.get_sentiment_df()
        time_inds, num = self.get_time_inds(time_df)
        sentiment_value = self.stmt_simple_sum(time_inds, sent_list)
        df = self.handle_sentiment( sentiment_value, num)
        self.save_sentiment(df)
        print(self.stock + " is done!")

datapath = './数据/股评_HS300_sentiment/'
timepath = './数据/股评_HS300_handled/update_time/'
outpath = './数据/股评_HS300_daily_sentiment/'
trade_date, trade_date_l = get_trade_date()

def run(stock, datapath, timepath, outpath, trade_date, trade_date_l):
    try:
        print(f"Processing stock: {stock}")
        hs_sentiment = daily_sentiment(stock, datapath, timepath, outpath, trade_date, trade_date_l)
        hs_sentiment.run()
    except Exception as e:
        print(f"Error processing stock {stock}: {e}")


if __name__ == '__main__':

    tohandle_list = get_list(datapath, outpath)
    start = time.time()
    p = Pool(4)
    for stock in tohandle_list:
        p.apply_async(run, args=(stock, datapath, timepath, outpath, trade_date, trade_date_l))
    p.close()
    p.join()
    end = time.time()
    print('All subprocesses done.Total time:{}'.format(end-start))