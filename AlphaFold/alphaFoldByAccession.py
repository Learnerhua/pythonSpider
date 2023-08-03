# -*- coding: utf-8 -*-
'''
@Time    : 2023/08/03 9:47
@Author  : oyjh
@Mail    : oyjh417701@163.com
@File    : alphaFoldByAccession.py
@Software: PyCharm
@Des     : This python script was created to judge if the uniprot ID is
valid in AlphaFold Protein Structure Database (https://alphafold.ebi.ac.uk/) and
extract critical information if possible.
'''
import sys,io,requests,time,os,re,random,json
from threading import Thread,Lock
from queue import Queue
from lxml import etree
from fake_useragent import UserAgent

class GetInfoFromAlphaFold(object):
    #创建一个从alphaFold中批量获取结构信息的类
    def __init__(self):
        #创建初始变量
        self.url = "https://alphafold.ebi.ac.uk/api/prediction/{}?key" \
                   "=AIzaSyCeurAJz7ZGjPQUtEaerUkBZ3TaBkXrY94"
        #创建存放url的队列
        self.q = Queue()
        #创建锁
        self.lock = Lock()
        #创建输入和输出文件
        self.file_in = "sample.txt" #输入文件，存放uniprot accession
        file_prefix = self.file_in.split(".")[0]
        self.file_out = f"{file_prefix}_result.txt" #输出文件，存放有alphaFold结构的信息
        self.file_blank = f"{file_prefix}_blank.txt"#存放没有alphaFold结构的uniprot accession
        self.file_noResponse = f"{file_prefix}_NoResponse.txt" #存放没有收到网站反馈的
        self.Dir_PDB = f"{file_prefix}_PDBfiles"
        self.file_PDBFailure = f"{file_prefix}_PDBfilesDownloadFailure.txt"
        self.threads = 8

    def filesInit(self):
        #创建输出文件更新器，每次运行时都将已存在的同名文件删除
        file_list = [self.file_out,self.file_blank,self.file_noResponse,
                     self.file_PDBFailure]
        for file in file_list:
            if os.path.isfile(file):
                os.remove(file)
        if os.path.exists(self.Dir_PDB):
            # 如果目录存在，就删除目录及其内容
            for root, dirs, files in os.walk(self.Dir_PDB, topdown=True):
                for name in files:
                    file_path = os.path.join(root, name)
                    os.remove(file_path)
                for name in dirs:
                    self.Dir_PDB = os.path.join(root, name)
                    os.rmdir(self.Dir_PDB)
            os.rmdir(self.Dir_PDB)
        os.makedirs(self.Dir_PDB)


    def getUrlQueue(self):
        #获取url队列的函数
        with open(self.file_in,'r',encoding="utf8") as fi:
            lines = fi.readlines()
        for line in lines:
            line = line.strip()
            url = self.url.format(line)
            self.q.put(url)

    def main(self):
        #脚本的主程序，爬取网页内容并写入文件
        while True:
            t = random.random()
            time.sleep(t)
            if not self.q.empty():
                url = self.q.get()
                re_bds = "api/prediction/(.*?)\?key" #用于从url中提取出ID的正则表达式
                pattern = re.compile(re_bds, re.S)
                ID_list = pattern.findall(url)
                uniprot_ID = ID_list[0]
                headers = {"user-agent": UserAgent().random}
                try:
                    response = requests.get(url = url, headers = headers)
                except Exception as e:
                    with self.lock:
                        with open(self.file_noResponse, 'a', encoding = "utf8") as\
                                f_blank:
                            f_blank.write(uniprot_ID + "\n")
                            f_blank.flush()
                    print(f"UniProt accession {uniprot_ID} has no response  "
                          f"and it was recorded to file '{self.file_noResponse}', "
                          f"you need to check them again later.")
                else:
                    result = response.text
                    data_list = json.loads(result)  # 将字符串转成列表
                    if data_list:
                        info_dict = data_list[0] # 从列表中提取字典
                        values_list = [info_dict[key] for key in
                                   ["uniprotAccession", "entryId", "gene",
                                    "taxId", "organismScientificName",
                                    "uniprotDescription",
                                    "modelCreatedDate", "isReviewed",
                                    "isReferenceProteome", "uniprotSequence"
                                    ]]
                        output_string = '\t'.join(str(item) for item in values_list)
                        with self.lock:
                            with open(self.file_out, 'a', encoding = 'utf8') as fo:
                                fo.write(output_string + "\n")
                                fo.flush()
                        print(f"Data related to UniProt accession {uniprot_ID} "
                              f"was recorded to file '{self.file_out}' successfully.")
                        #下载PDB文件
                        pdb_url = info_dict["pdbUrl"]
                        try:
                            response2 = requests.get(url = pdb_url,
                                                    headers = headers)
                        except:
                            with self.lock:
                                with open(self.file_PDBFailure, 'a',
                                          encoding='utf8') as fP:
                                    fP.write(uniprot_ID + "\n")
                                    fP.flush()
                        else:
                            path = f"{self.Dir_PDB}/{uniprot_ID}.pdb"
                            with open(path, 'wb') as f_PDB:
                                f_PDB.write(response2.content)
                                f_PDB.flush()

                    else:
                        with self.lock:
                            with open(self.file_blank, 'a', encoding = 'utf8') as\
                                    fb:
                                fb.write(uniprot_ID + "\n")
                                fb.flush()
                        print(
                            f"UniProt accession {uniprot_ID} has no AlphaFold "
                            f"3D structure data and related information was "
                            f"recorded to file '{self.file_blank}'")

            else:
                break

    def simple_statistic(self):
        #对获得的结果进行简单的统计
        num1 = num2 = num3 = num4 = 0
        if os.path.isfile(self.file_out):
            with open(self.file_out, 'r', encoding = 'utf8') as fo:
                lines = fo.readlines()
                num1 = len(lines)
        if os.path.isfile(self.file_blank):
            with open(self.file_blank, 'r', encoding = 'utf8') as fb:
                lines = fb.readlines()
                num2 = len(lines)
        if os.path.isfile(self.file_noResponse):
            with open(self.file_noResponse, 'r', encoding = 'utf8') as fr:
                lines = fr.readlines()
                num3 = len(lines)
        PDB_files = os.listdir(self.Dir_PDB)
        num4 = len(PDB_files)

        print("\n**********STATISTIC**********\n")
        print(f"The accessions' number WITH AlphaFold data: {num1}\n"
               f"The accessions' number WITHOUT AlphaFold data: {num2}\n"
               f"The accessions' number WITH RESPONSE: {num3}\n"
              f"The number of downloaded PDB files: {num4}")

    def run(self):
        #定义本脚本的运行主函数
        self.filesInit() #清除已存在的文件
        self.getUrlQueue() #获取url队列
        t_list = []
        #创建多线程
        for i in range(self.threads):
            t = Thread(target = self.main)
            t_list.append(t)
            t.start()
        #回收线程
        for t in t_list:
            t.join()
        self.simple_statistic()


if __name__ == "__main__":
    try:
        print("Start running ......\n")
        start = time.time()
        spider = GetInfoFromAlphaFold()
        spider.run()
        end = time.time()
        print("\nProgram finished\nRunning time:%.2fs"%(end - start))
        exit()
    except Exception as e:
        print("Error: ",e)