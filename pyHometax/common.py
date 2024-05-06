import time
import os, sys

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver

import config
#from queue import Queue
#import threading



# https://jvvp.tistory.com/1155
# def receiver(q):
#     print('AU_HISTORY_LOG : START')
#     while True:
#         data = q.get()
#         #if data is None:
#         #    break
#         logt(f'#################################################### AU_HISTORY_LOG: {data}')
#         dbjob.insert_auHistory(data['title'], data['message'])
#     print('AU_HISTORY_LOG : DONE')


# # 히스토리 DB 쌓기
# au_history_queue = Queue()
# au_history_thread = threading.Thread(target=receiver, args=(au_history_queue,))
# au_history_thread.start()
# 로깅 설정

import logging
logger = None


def set_logger(log_filename, level=logging.INFO):
    global logger
    
    # 로깅 설정
    logging.basicConfig(level=level,  format='%(asctime)s - %(levelname)s - %(message)s')

    # 파일 핸들러 생성
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # 로거에 핸들러 추가
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 생성
    #console_handler = logging.StreamHandler()
    #console_handler.setLevel(level)
    #console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    #logger.addHandler(console_handler)
    
    return logger

# def log_base(level, msg):
#     now = time.localtime()
#     pattern = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
#     print("%s %5s %15s : %s" % (pattern, level, sys._getframe(2).f_code.co_name, msg))

# DEBUG
def logd(msg):
    cur_level = config.LOG_LEVEL
    logger.debug(msg)


# WARN
def logw(msg):
    logger.warning(msg)


# ERROR
def loge(msg):
    logger.error(msg)


def logt(title, t=0):
    # dbjob.insert_auHistory(title, "");

    if t==0 :
        logger.info(title)
    else :
        wtime = t * config.TIME_WEIGHT
        time.sleep(wtime)
        if config.TIME_WEIGHT > 1:
            logger.info(f"[{str(t)} * {str(config.TIME_WEIGHT)}초 후] {title}")
        else:
            logger.info(f"[{str(t)}초 후] {title}")

def ht_sleep(t=0):
    if t>0:
        time.sleep(t * config.TIME_WEIGHT)

def logqry(sql, data=()):
    # 작업 진행 jobs 쿼리는 출력하기
    #if config.DB_QUERY_PRINT or sys._getframe(1).f_code.co_name.find("select_auto_") >= 0:
    if config.DB_QUERY_PRINT :
        try :
            lpad_str = "        "
            logger.info(lpad_str + rpad("=== " + sys._getframe(1).f_code.co_name + "() ", 50, "="))
            logger.info(lpad_str + sql % data)
            logger.info(lpad_str + rpad("", 50, "="))
        except:
            logger.info("except: logqry(), sql=" + sql)


def logqry_many(sql, many_data):
    if (config.DB_QUERY_PRINT):
        lpad_str = "        "
        logger.info(lpad_str + rpad("=== (Many) " + sys._getframe(1).f_code.co_name + "()", 50, "="))
        
        for data in many_data:
            logger.info(lpad_str + sql % (data))
        
        logger.info(rpad("", 50, "="))

def logrs(rs:list):
    if (config.DB_QUERY_PRINT):
        logger.info("RecordSet : count=%d" % len(rs))


def resource_path(relative_path):
    try: 
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


'''
# 디셔너리를 파일 저장
import numpy as np

my_dict = { 'Apple': 4, 'Banana': 2, 'Orange': 6, 'Grapes': 11}
np.save('file.npy', my_dict)
'''        


def get_login_info(user_info):
    if user_info:
        worker_id = user_info['id']
        
        login_info = config.LOGIN_INFO
        login_info['name']     = user_info['name']
        login_info['login_id'] = user_info['hometax_id']
        login_info['login_pw'] = user_info['hometax_pw']
        
        if user_info['ht_worker_yn'] != 'Y':
            loge(f'user테이블 ht_worker_yn 필드값을 Y로 설정해 주세요. worker_id={worker_id}')
            exit()
    else:
        loge(f'사용자 정보를 얻을 수 없습니다. worker_id={worker_id}')
        exit()   
        
    return login_info 

def all_cookies(driver):
    all_cookies = driver.get_cookies()
    #print(f'all_cookies: {all_cookies}')

    cookies_dict = {}
    for cookie in all_cookies:
        cookies_dict[cookie['name']] = cookie['value']

    string = ''
    for key in cookies_dict:
        string += f'{key}={cookies_dict[key]};'

    print(string)

    with open("all_cookies.txt", 'w') as f:
        f.write(string)

def get_cookie_value(driver, key):
    all_cookies = driver.get_cookies()
    for cookie in all_cookies:
        if key == cookie['name']:
            return cookie['value']

    return None


def lpad(i, width, fillchar='0'):
    return str(i).rjust(width, fillchar)

def rpad(i, width, fillchar='0'):
    return str(i).ljust(width, fillchar)


# Exception 상속받아 재정의
class BizException(Exception):
    # 생성자
    def __init__(self, name, msg=""):
        self.name = name
        self.msg = msg
    
    # toString()
    def __str__(self):
        return "예외처리 : name={}, message={}".format( self.name, self.msg)

class BizNextLoopException(Exception):
    # 생성자
    def __init__(self, name, msg="", aux_result="S"):
        self.name = name
        self.msg = msg
        self.aux_result = aux_result
    
    # toString()
    def __str__(self):
        return "다음 순번 진행(정상동작) AU_X=>{} : name={}, message={}".format(self.aux_result, self.name, self.msg)        
        