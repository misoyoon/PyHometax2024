from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from bs4 import BeautifulSoup

from urllib.request import urlopen
from urllib.parse import quote_plus
import time

baseUrl = "https://www.instagram.com/explore/tags/" + quote_plus('아이유')
driver = webdriver.Chrome()


# 브라우저 위치 조정하기
#driver.set_window_position(0,0) 
# 브라우저 화면 크기 변경하기
#driver.set_window_size(1960, 1000)

driver.get(baseUrl)
driver.implicitly_wait(20)

time.sleep(3)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

insta = soup.select('.FFVAD')
#print(insta[0])

for i in insta:
    print(i.img.src)


driver.close()