from selenium  import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support  import expected_conditions as EC 

driver = webdriver.Chrome('./chromedriver') 

# 무조건 지정된 time만큼 대기 
#time.sleep(10) 

# 10초까지 기다려준다. 10초 안에 웹 화면이 표시되면 바로 다음 작업이 진행됨 
driver.implicitly_wait(10) 
driver.get('https://naver.com') 
# button = driver.find_element(By.CSS_SELECTOR, '#search_btn') 

# 검색 버튼을 찾아서 누를건데, 최대 5초까지만 기다리겠다라는 의미 
button = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#search_btn'))) 
button.click()

