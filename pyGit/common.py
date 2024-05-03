import time
import os, sys
import datetime

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver

import dbjob
import config


def log_base(level, msg):
    now = time.localtime()
    pattern = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    print("%s %5s %15s : %s" % (pattern, level, sys._getframe(2).f_code.co_name, msg))

# DEBUG
def logd(msg):
    cur_level = config.LOG_LEVEL

    if cur_level == "DEBUG":
        log_base("DEBUG", msg)

# INFO        
def logt(msg):
    cur_level = config.LOG_LEVEL
    if cur_level == "INFO" or cur_level == "DEBUG":
        log_base("INFO", msg)

# WARN
def logw(msg):
    log_base("WARN", msg)


# ERROR
def loge(msg):
    log_base("ERROR", msg)



def logt(title, t=0):
    #dbjob.insert_auHistory(title, "")

    if t==0 :
        log_base("INFO", title)
    else :
        log_base("INFO", "[" +str(t) + "초 후] " + title)
        time.sleep(t)


def logqry(sql, data=()):
    if (config.DB_QUERY_PRINT):
        try :
            lpad_str = "        "
            print(lpad_str + rpad("=== " + sys._getframe(1).f_code.co_name + "()", 50, "="))
            print(lpad_str + sql % data)
            print(lpad_str + rpad("", 50, "="))
        except:
            print("except: logqry(), sql=" + sql)


def logqry_many(sql, many_data):
    if (config.DB_QUERY_PRINT):
        lpad_str = "        "
        print(lpad_str + rpad("=== (Many) " + sys._getframe(1).f_code.co_name + "()", 50, "="))
        
        for data in many_data:
            print(lpad_str + sql % (data))
        
        print(rpad("", 50, "="))

def logrs(rs:list):
    if (config.DB_QUERY_PRINT):
        print("RecordSet : count=%d" % len(rs))


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

def all_cookies(driver):

    all_cookies = driver.get_cookies()
    print(f'all_cookies: {all_cookies}')

    cookies_dict = {}
    for cookie in all_cookies:
        cookies_dict[cookie['name']] = cookie['value']

    string = ''
    for key in cookies_dict:
        string += f'{key}={cookies_dict[key]};'

    print(string)

    with open("all_cookies.txt", 'w') as f:
        f.write(string)


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
        