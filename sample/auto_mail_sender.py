from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

import time

# 유튜브 동영상 - https://www.youtube.com/watch?v=2EBrICPZVLY

driver = webdriver.Chrome()
url = 'https://google.com'
driver.get(url)
#driver.maximize_window()
action = ActionChains(driver)
driver.find_element(By.CSS_SELECTOR, '.gb_4.gb_5.gb_ae.gb_4c').click()

action.send_keys('rebornmiso').perform()
action.reset_actions()
driver.find_element(By.CSS_SELECTOR, '.VfPpkd-RLmnJb').click()

time.sleep(2)
driver.find_element(By.CSS_SELECTOR, '.whsOnd.zHQkBf').send_keys('#godghr$Skan99')

time.sleep(10)

driver.find_element(By.CSS_SELECTOR, '.CwaK9').click()
time.sleep(2)

driver.get('https://mail.google.com/mail/u/0/?ogbl#inbox')
time.sleep(2)

driver.find_element(By.CSS_SELECTOR, '.T-I.J-J5-Ji.T-I-KE.L3').click()
time.sleep(1)

send_buton = driver.find_element(By.CSS_SELECTOR, '.gU.Up')

(
action.send_keys('보낼메일주소').key_down(Keys.ENTER).pause(2).key_down(Keys.TAB)
.send_keys('제목입니다.').pause(2).key_down(Keys.TAB)
.send_keys('abcde').pause(2).key_down(Keys.ENTER)
.key_down(Keys.SHIFT).send_keys('abcde').key_up(Keys.SHIFT).pause(2)
.move_to_element(send_buton).click()
.perform()
)