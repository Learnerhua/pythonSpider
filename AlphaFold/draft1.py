# -*- coding: utf-8 -*-
'''
@Time    : 2023/08/03 1:22
@Author  : oyjh
@Mail    : oyjh417701@163.com
@File    : draft1.py
@Software: PyCharm
@Des     :
'''
import sys,io,requests,time,os,re,random,json
from threading import Thread,Lock
from queue import Queue
from lxml import etree
from fake_useragent import UserAgent

# 使用一个已知有alphaFold结构的ID来进行验证
url = "https://alphafold.ebi.ac.uk/api/prediction/" \
      "A0A0R3WWR3?key=AIzaSyCeurAJz7ZGjPQUtEaerUkBZ3TaBkXrY94"
headers={"user-agent": UserAgent().random}
response = requests.get(url=url,headers=headers)
print(response.status_code)#判断网页状态
result=response.text
data_list = json.loads(result)#将字符串转成列表
data_dic = data_list[0]
# print(type(result))
# print((data_list[0]['entryId']))
values_list = [data_dic[key] for key in ["uniprotAccession","entryId","gene",
                                         "taxId","organismScientificName",
                                         "uniprotDescription",
                                         "modelCreatedDate","isReviewed",
                                         "isReferenceProteome","uniprotSequence"
                                         ]]
print(values_list)
pdb_url = data_dic["pdbUrl"]
response2 = requests.get(url = pdb_url,headers = headers)
print(response2.content)

#使用一个已知没有alphoad预测的蛋白
url = "https://alphafold.ebi.ac.uk/api/prediction/A0A074Z8N4" \
      "?key=AIzaSyCeurAJz7ZGjPQUtEaerUkBZ3TaBkXrY94"
headers={"user-agent": UserAgent().random}
response = requests.get(url=url,headers=headers)
result=response.text
# print(response.status_code)#判断网页状态

'''
根据本脚本的探究，基本得到了alphaFold返回页面的规律：
- 如果accession号存在alphaFold结构预测，则返回的网页的状态码是200，返回的结果是一个字
符串，这个字符串是一个包含一个字典的列表，因此可以先将字符串转换成列表，再根据需求提取字
典中的元素
- 如果accession号不存在alphaFold的结构预测，则返回的状态码为404
'''