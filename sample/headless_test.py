from selenium import webdriver

# 원문 사이트
# https://beomi.github.io/2017/09/28/HowToMakeWebCrawler-Headless-Chrome/

TEST_URL = 'https://intoli.com/blog/making-chrome-headless-undetectable/chrome-headless-test.html'

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
options.add_argument("lang=ko_KR") # 한국어!
driver = webdriver.Chrome('chromedriver', chrome_options=options)

driver.get(TEST_URL)
driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5]}})")
# lanuages 속성을 업데이트해주기
driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")

user_agent = driver.find_element(By.CSS_SELECTOR, '#user-agent').text
plugins_length = driver.find_element(By.CSS_SELECTOR, '#plugins-length').text
languages = driver.find_element(By.CSS_SELECTOR, '#languages').text

print('User-Agent: ', user_agent)
print('Plugin length: ', plugins_length)
print('languages: ', languages)

driver.get_screenshot_as_file('naver_main_headless.png')

driver.quit()