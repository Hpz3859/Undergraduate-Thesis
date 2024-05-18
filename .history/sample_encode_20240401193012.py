# -*- coding: utf-8 -*-
# @Time    : 2024/3/1 10:00
# @Author  : hpz
# @File    : sample_encode.py
# @Software: PyCharm
# @Description: 进行样本文本编码
import os
import numpy as np
import pandas as pd
# pip3 install transformers
from transformers import BertTokenizer
token = BertTokenizer.from_pretrained('bert-base-chinese')
train_text = []
with open('train_text.csv',encoding ="utf-8-sig") as f:
    while True:
        line = f.readline() # 按行读取文件内容
        if line == "":
            break
        line = line.strip('\n')
        train_text.append(line)
f.close
train_text = train_text[1:]
import torch
# 数据整理函数
def collate_fn(data):
    #编码
    datas = token.batch_encode_plus(batch_text_or_text_pairs=data,
                                   truncation=True,
                                   padding='max_length',
                                   max_length=100,
                                   return_tensors='pt',
                                   return_length=True)

    #input_ids:编码之后的数字
    #attention_mask:是补零的位置是0,其他位置是1
    input_ids = datas['input_ids']
    attention_mask = datas['attention_mask']
    token_type_ids = datas['token_type_ids']

    return input_ids, attention_mask, token_type_ids
input_ids, attention_mask, token_type_ids = collate_fn(train_text)
# # 定义计算设备
device = 'cpu'
if torch.cuda.is_available():
    device = 'cuda:0'

from transformers import BertModel
def encode_text(input_ids, attention_mask, token_type_ids, device, num=500):
    for i in range(0, len(input_ids), num):
        # 加载预训练模型
        pretrained = BertModel.from_pretrained('bert-base-chinese')
        # 不训练预训练模型,不需要计算梯度
        for param in pretrained.parameters():
            param.requires_grad_(False)
        pretrained.to(device)
        
        if len(input_ids) - i > num:
            input_ids1 = input_ids[i:i+num].to(device)
            attention_mask1 = attention_mask[i:i+num].to(device)
            token_type_ids1 = token_type_ids[i:i+num].to(device)
        else:
            input_ids1 = input_ids[i:].to(device)
            attention_mask1 = attention_mask[i:].to(device)
            token_type_ids1 = token_type_ids[i:].to(device)
        out = pretrained(input_ids1, attention_mask1, token_type_ids1)
        out = out.last_hidden_state[:, 0].cpu().detach().numpy().tolist()
        
        if i == 0:
            out1 = out
        else:     
            out1.extend(out)
        # input_ids1.cpu() 
        # attention_mask1.cpu() 
        # token_type_ids1.cpu()
        # pretrained.cpu()
        del input_ids1, attention_mask1, token_type_ids1, out, pretrained
        torch.cuda.empty_cache()
        allocated_memory = torch.cuda.memory_allocated()
        cached_memory = torch.cuda.memory_reserved()
        # print(f"已分配的GPU内存：{allocated_memory}, 已缓存的GPU内存：{cached_memory}")
        # print(i, np.shape(out1))

    return out1
out = encode_text(input_ids, attention_mask, token_type_ids,device, num=5000)
# nvidia-smi
np.savetxt("sample_text_encode.csv", out, delimiter=",")