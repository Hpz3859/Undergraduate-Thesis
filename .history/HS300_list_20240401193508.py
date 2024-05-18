# -*- coding: utf-8 -*-
# @Time    : 2024/3/1 10:00
# @Author  : hpz
# @File    : HS300_list.py
# @Software: PyCharm
# @Description: 整理HS300股票列表

import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import time

stocklistpd_HS300 = pd.read_csv("./数据/RESSET_IDXCOMPO_2.csv", encoding="gbk")
stocklistpd_HS300["证券代码_成分_SecuCd_Compo"] = stocklistpd_HS300["证券代码_成分_SecuCd_Compo"].apply(lambda x: str(int(x)).zfill(6))
# 将结束日期为Nan的数据填充为当前日期
stocklistpd_HS300["结束日期_EndDt"] = stocklistpd_HS300["结束日期_EndDt"].fillna("2024-03-01")
# 将日期转换为datetime格式
stocklistpd_HS300["开始日期_BegDt"] = pd.to_datetime(stocklistpd_HS300["开始日期_BegDt"])
stocklistpd_HS300["结束日期_EndDt"] = pd.to_datetime(stocklistpd_HS300["结束日期_EndDt"])
# 按照证券代码排序
stocklistpd_HS300 = stocklistpd_HS300.sort_values(by="证券代码_成分_SecuCd_Compo")

# 读取trade_date
trade_date = pd.read_csv("./数据/trade_date.csv")
trade_date = trade_date[trade_date["is_trading_day"] == 1].copy()
trade_date = trade_date[trade_date["calendar_date"] >= "2013-01-01"]
trade_date["calendar_date"] = pd.to_datetime(trade_date["calendar_date"])
trade_date = trade_date.reset_index(drop=True)

df = trade_date.copy()
is_in_HS300 = [0]  * len(trade_date)

# 将stocklistpd_HS300按照证券代码分组
stocklistpd_HS300_group = stocklistpd_HS300.groupby("证券代码_成分_SecuCd_Compo")
#stocklistpd_HS300_group = dict(list(stocklistpd_HS300_group))
stocklistpd_HS300_group = list(stocklistpd_HS300_group)

# 提取每日个股是否在HS300中
for i in tqdm(range(len(stocklistpd_HS300_group))):
    stock = stocklistpd_HS300_group[i][0]
    start_date = stocklistpd_HS300_group[i][1]["开始日期_BegDt"].tolist()
    end_date = stocklistpd_HS300_group[i][1]["结束日期_EndDt"].tolist()
    df[f"{stock}"] = is_in_HS300
    for j in range(len(start_date)):
        df[f"{stock}"] = df.apply(lambda x: 1 if (x["calendar_date"] >= start_date[j] and x["calendar_date"] <= end_date[j]) else x[f"{stock}"], axis=1)
    df = df.copy() # 防止df被覆盖,防止报碎片化警告

# 删除df全为0的列
df = df.loc[:, (df != 0).any(axis=0)].copy()
# 将df写入文件
df.to_csv("./数据/HS300_with_date.csv", index=False)

# 提取df的行名
df_columns = df.columns.tolist()
df_columns = df_columns[2:]

# 将HS300_list写入文件
with open("./数据/HS300_list.txt", "w") as f:
    for stock in df_columns:
        f.write(stock + "\n")