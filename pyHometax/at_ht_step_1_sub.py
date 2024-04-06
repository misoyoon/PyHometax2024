import time
import os

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
#from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys


import pyautogui
import math

from common import *
import ht_file
import dbjob
import sele_common as sc

# # 메뉴이동 : '신고/납부' 클릭
# def click_메뉴_신고납부(driver: WebDriver):
#     logt("메뉴이동 : '신고/납부' 메뉴 이동")
#     url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index.xml&tmIdx=9&tm2lIdx=&tm3lIdx='
#     driver.get(url)
    
#     dbjob.insert_auHistory("메뉴이동", "신고납부")

#     logt("클릭: [신고/납부] 화면상단 메뉴",2)
#     driver.find_element(By.ID, 'group1314').click()

#     logt("iframe 이동", 2)
#     sc.move_iframe(driver)

#     wait = WebDriverWait(driver, 10)
#     element = wait.until(EC.element_to_be_clickable((By.ID, 'sub_a_0405050000')))
#     logt("클릭: 양도소득세")
#     element.click()

#     try :
#         time.sleep(1)
#         alert = driver.switch_to.alert
#         alert_msg = alert.text
#         if alert_msg.find("로그인 정보가 없습니다.") > -1 :
#             logt("현재는 로그아웃 상태")
#             alert.accept()
#             raise BizException("로그아웃상태")   
#         else :
#             logt("정상 로그인 상태1")
#     except BizException as e:
#         raise e
#     except :
#         pass

