from selenium import webdriver
import time

login_name = '정율섭'
login_jomin1 = '730605'
login_jomin2 = '1340337'
login_pwd = '!miso34120'

# 1.크롬접속
driver = webdriver.Chrome('chromedriver.exe')

# 브라우저 위치 조정하기
driver.set_window_position(0,0) 
# 브라우저 화면 크기 변경하기
driver.set_window_size(1300, 1000)

driver.implicitly_wait(20)

# 2. 홈택스 접속

#  1) 홈택스로 이동
driver.get('https://www.hometax.go.kr/')
#driver.implicitly_wait(10)
time.sleep(3)
print("0 " + driver.title)

#  2) 로그인화면으로 이동
driver.find_element(By.CSS_SELECTOR, '#textbox81212912').click() 
time.sleep(5)


#  3) iframe 전환 : 로그인화면은 화면전체가 iframe
iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
driver.switch_to.frame(iframe1)
time.sleep(5)

print("1 " + driver.title)
#  4) 공인인증서 로그인 버튼 클릭
driver.find_element(By.CSS_SELECTOR, '#textbox10881922').click() 
time.sleep(5)

#  5) iframe 전환 : 공인인증서 로그인 화면
iframe = driver.find_element(By.CSS_SELECTOR, '#dscert')
driver.switch_to.frame(iframe)
time.sleep(3)

print("2 " + driver.title)

#  6) 공인인증서 선택
#driver.find_element_by_xpath('//*[@title="공인인증서명"]').click()
driver.implicitly_wait(3)


elem = driver.find_element(By.ID, 'input_cert_pw').send_keys(login_pwd)
time.sleep(5)

#  8) 확인버튼 클릭
driver.find_element(By.ID, 'btn_confirm_iframe').click()
time.sleep(5)
