from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import threading

from common import *

import pyHometax.auto_login as auto_login 
import auto_step_1
import dbjob
import ht_file

import config

import sys, os, time
import shutil


'''

실수로 원본파일 삭제로 인해 백업폴더에서 없어진 파일 복구하는 프로그램
'''


fields = [
	'source_file_seq',
	#'target_file_seq',
	#'transfer_file_seq',
	#'hometax_upload_file_seq'

]

	# 'capture1_file_seq',
	# 'capture2_file_seq',
	# 'capture3_file_seq',
	# 'capture4_file_seq',

	# 'result1_file_seq',
	# 'result2_file_seq',
	# 'result3_file_seq',
	# 'result4_file_seq'

root_dir = "D:\\WWW\\JNK\\files\\hometax\\"

def check_ht_tt_file(row) :
    #au1 = row['au1']
    #if au1 is None:
    #    au1 = "대기"
    #else :
    #    au1 = "신고완료"

    re = []
    re.append(row['reg_nm']) 
    re.append(str(row['ht_tt_seq'])) 
    re.append(row['holder_nm']) 
    re.append(row['step_cd']) 
    #re.append(au1) 
    
    for field in fields:
        #print(field)
        
        # 파일키
        ht_tt_file_seq = row[field]

        if ht_tt_file_seq is not None and ht_tt_file_seq>0 :
            # 파일정보
            file_info = dbjob.select_one_HtTtFile(ht_tt_file_seq)
            re.append(file_info['original_file_nm']) 

            if file_info is not None :
                is_exist_file_1 = False
                is_exist_file_2 = False

                # DB에 있는 파일 정보
                filepath1 = root_dir + file_info['path'] + file_info['changed_file_nm'] 
                if not os.path.isfile(filepath1):
                    #result_dic[field] = 'X'
                    re.append("X")  
                    is_exist_file_1 = False
                else :
                    #result_dic[field] = '-'
                    re.append("-")  
                    is_exist_file_1 = True
                
                # 백업 이미지 파일
                filepath2= "C:\\Users\\lm\\Desktop\\삭제백업\\" + row['reg_nm'] +"\\이미지자료\\" + file_info['original_file_nm'] 
                re.append(filepath2) 
                if not os.path.isfile(filepath2):
                    #result_dic[field] = 'X'
                    re.append("X")  
                    is_exist_file_2 = False
                else :
                    #result_dic[field] = '-'
                    re.append("O")  
                    is_exist_file_2 = True

                if (is_exist_file_1 == False) and is_exist_file_2:
                    shutil.copyfile(filepath2, filepath1)

            else:
                #result_dic[field] = 'D'
                re.append("D")

        else:
            re.append("-")  


    return re


dbjob.connect_db()

result = []
rs = dbjob.select_all_HtTt("COMPLETE")
for row in rs:
    re = check_ht_tt_file(row)
    result.append(re)


f = open("결과파일.txt", 'w',encoding='utf8')

for r in result:

    try:
        if r[5] == 'X' and r[7] == 'X':
            data = ",".join(r)
            print(data)
            f.write(data + "\n")
    except :
        print(r)

    
            
f.close()
    
