from selenium import webdriver
import time

driver = webdriver.Chrome()

driver.get('https://google.com')
print(driver.window_handles)

time.sleep(1)
driver.execute_script('window.open("https://naver.com");')
print(driver.window_handles)

time.sleep(1)
driver.execute_script('window.open("https://www.daum.net");')
print(driver.window_handles)

time.sleep(1)
driver.execute_script('window.open("https://www.korea.kr/news/healthView.do?newsId=148843880");')
print(driver.window_handles)


# 최근 열린 탭으로 전환
driver.switch_to.window(driver.window_handles[-1])

time.sleep(1)
driver.switch_to.window(driver.window_handles[0])
time.sleep(1)
driver.switch_to.window(driver.window_handles[1])
time.sleep(1)
driver.switch_to.window(driver.window_handles[2])
time.sleep(1)
driver.switch_to.window(driver.window_handles[3])

time.sleep(1)


time.sleep(5)
driver.close()
