from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
import time


#iframe 전환 : 로그인화면은 화면전체가 iframe
def moveIframe(iframeId:str='txppIframe'):
    iframe1 = driver.find_element(By.ID, iframeId)
    driver.switch_to.frame(iframe1)
    time.sleep(1)

def do_page1():
    moveIframe()

    # 세액공제 항목 클릭하기
    for i in range(1,15):
        btnId = 'btnSearch{0:02d}'.format(i)
        print(btnId)
        driver.find_element(By.ID, btnId).click()    
        driver.implicitly_wait(3)

    # 클릭 : '한번에 내려받기'
    driver.find_element(By.ID, 'btnMultiElecDcmDwld_TODO').click()
    driver.implicitly_wait(5)

    # iframe전환
    moveIframe('ysCmShowMultiElecDcmDwld_iframe')

    # 클릭 : 내려받기
    driver.find_element(By.ID, 'btnDwld').click()
    driver.implicitly_wait(5)
    

# 1.크롬접속
driver = webdriver.Chrome('chromedriver.exe')

# 브라우저 위치 조정하기
driver.set_window_position(0,0) 
# 브라우저 화면 크기 변경하기
driver.set_window_size(1300, 1000)

driver.implicitly_wait(20)

# 2. 홈택스 접속
driver.get('https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=3500000000&tm2lIdx=3513010000&tm3lIdx=')

#  1) 홈택스로 이동
cookie1 = {
    'name':'TXPPsessionID', 
    'value':'Y51tx1rSkd1DkdwXY93GPAZwosEMzTBadsf4bdWoHBwtcovDJhVeamTciwAkWTeb.tupiwsp17_servlet_TXPP01',
    'path': '/',
    'domain': 'hometax.go.kr',
    }
cookie2 = {
    'name':'TEYSsessionID', 
    'value':'cX8ARgOCHw4ruP2oYIUJUN8OoBG31eAzdWwkjTjNusCsJeH6JAczQadMCbvhaUKV.tupiwsp03_servlet_TEYS01',
    'path': '/',
    'domain': 'hometax.go.kr',
    }
driver.add_cookie(cookie1);
driver.add_cookie(cookie2);
time.sleep(3)

do_page1()

# 종료대기
time.sleep(5)

# 종료
driver.close()