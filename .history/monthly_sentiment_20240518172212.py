# -*- coding: utf-8 -*-
# @Time    : 2024/3/15
# @Author  : hpz
# @File    : monthly_sentiment.py
# @Software: VScode
# @Description: 计算HS300股评的月度情绪

import numpy as np
import pandas as pd
import os
from tqdm import tqdm

datapath = './数据/股评_HS300_daily_sentiment/'
timepath = './数据/股评_HS300_handled/update_time/'
outpath = './数据/股评_HS300_monthly_sentiment/'

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
    
tohandle_list = get_list(datapath, outpath)

# 读取日度情绪数据
df = pd.read_csv(datapath + tohandle_list[0], index_col=0)

# 计算月度情绪
df.index = pd.to_datetime(df.index)
df_monthly = df.resample('M').sum()

# 重设索引
df_monthly['date'] = df_monthly.index
df_monthly = df_monthly.reset_index(drop=True)

# 批量处理
for filename in tqdm(tohandle_list):
    df = pd.read_csv(datapath + filename, index_col=0)
    df.index = pd.to_datetime(df.index)
    df_monthly = df.resample('M').sum()
    df_monthly['date'] = df_monthly.index
    df_monthly = df_monthly.reset_index(drop=True)
    df_monthly.to_csv(outpath + filename)