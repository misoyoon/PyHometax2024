from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from urllib.request import urlopen

import time

def loginInsta():
    options = webdriver.ChromeOptions()
    #options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
    options.add_argument("lang=ko_KR") # 한국어!
    driver = webdriver.Chrome('chromedriver', chrome_options=options)
    
    # 브라우저 위치 조정하기
    driver.set_window_position(0,0) 
    # 브라우저 화면 크기 변경하기
    driver.set_window_size(1300, 1000)
    driver.get("https://www.instagram.com/")

    # time.sleep(3)
    try:
        username_box_check = WebDriverWait(driver, 10).until(EC.presence_of_element_located\
        ((By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input')))
        print(username_box_check)
    except:
        print("error")

    username_box = driver.find_elements_by_xpath('//*[@id="loginForm"]/div/div[1]/div/label/input')[0]
    username_box.send_keys("misoyool")
    password_box = driver.find_elements_by_xpath('//*[@id="loginForm"]/div/div[2]/div/label/input')[0]
    password_box.send_keys("!Reborn#01")
    login_button = driver.find_elements_by_xpath('//*[@id="loginForm"]/div/div[3]/button')[0]
    login_button.click()
    
    return driver


driver = loginInsta()
time.sleep(3)

baseUrl = "https://www.instagram.com/explore/tags/아이유"
driver.get(baseUrl)
driver.implicitly_wait(3)


html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

insta = soup.select('.FFVAD')
#print(insta[0])

for i in insta:
    print(i.img.src)


time.sleep(10)
driver.close()

