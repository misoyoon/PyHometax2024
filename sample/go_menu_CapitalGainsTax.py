from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
import time

# 참고자료
# https://blog.naver.com/PostView.nhn?blogId=o12486vs2&logNo=221917465949


#iframe 전환 : 로그인화면은 화면전체가 iframe
def moveIframe(iframeId:str='txppIframe'):
    iframe1 = driver.find_element(By.ID, iframeId)
    driver.switch_to.frame(iframe1)
    time.sleep(1)

def selectBox(id:str, index:int=-1, value:str=None, text:str=None):
    select_fr = Select(driver.find_element(By.ID, id))
    
    if index > -1:
        select_fr.select_by_index(index)
        return
    
    if value != None:
        select_fr.select_by_value(value)
        return

    if text != None:
        select_fr.select_by_visible_text(text)
        return

def do_page1_capitalGainsTaxType1():
    '''
    일반신고 : 예정 Page1 
    '''
    # 메뉴이동 : 일반신고 > 예정신고작성
    elem = driver.find_element(By.ID, 'anchor22').click()
    time.sleep(1)

    # iframe이동
    moveIframe('UTERNAAV52_iframe')

    # 체크 : '확인하였습니다'
    driver.find_element(By.ID, 'chkYn_input_0').click()
    time.sleep(1)
    # 클릭 : 닫기
    driver.find_element(By.ID, 'btnClose2').click()
    time.sleep(1)

    # iframe이동 : 메인
    moveIframe()

    # SELECT 선택: 양도자산종류 >  예정-국내주식
    driver.find_element(By.CSS_SELECTOR, '#cmbTrnRtnDdtClCd > option:nth-child(3)').click()

    time.sleep(1)
    # SELECT 선택 : 국내주식
    driver.find_element(By.CSS_SELECTOR, '#cmbTrnHt > option:nth-child(2)').click()
    #selectBox('cmbTrnMm', index=7)

    time.sleep(1)
    # 클릭 : 조회
    driver.find_element(By.ID, 'btnTrnYm').click()
    time.sleep(2)

    # 출력 : 윈도우 창 리스트
    print(driver.window_handles)
    time.sleep(1)

    try:
        da = Alert(driver)
        print(da.text)
        da.accept()
    except Exception as e:
        print('예외가 발생했습니다.', e)


    # 전화번호 입력 가능여부 판단
    hand_phone_num = '010-3656-5574'
    hand_phone_num = hand_phone_num.replace('-','').replace('.','')

    #print(driver.find_element(By.CSS_SELECTOR, 'edtMpno0').get_attribute('readonly'))

    try:
        driver.find_element(By.ID, 'edtMpno0').send_keys(hand_phone_num[0:3])
        driver.find_element(By.ID, 'edtMpno1').send_keys(hand_phone_num[3:7])
        driver.find_element(By.ID, 'edtMpno2').send_keys(hand_phone_num[8])
    except Exception as e:
        print('예외가 발생했습니다.', e)

    # 클릭 : 저장 후 다음이동
    driver.find_element(By.ID, 'btnProcess').click()

    time.sleep(2)

    # 팝업창 유무확인 : 작성중인 신고서가 존재합니다.
    try:
        da = Alert(driver)
        print(da.text)
        da.accept()

        # 클릭 : 저장 후 다음이동
        driver.find_element(By.ID, 'btnProcess').click()
        time.sleep(2)
    except Exception as e:
        print('예외가 발생했습니다.', e)


# 1.크롬접속
driver = webdriver.Chrome('chromedriver.exe')

# 브라우저 위치 조정하기
driver.set_window_position(0,0) 
# 브라우저 화면 크기 변경하기
driver.set_window_size(1300, 1000)

driver.implicitly_wait(20)

# 2. 홈택스 접속
driver.get('https://www.hometax.go.kr/')

#  1) 홈택스로 이동
cookie1 = {
    'name':'TXPPsessionID', 
    'value':'LzBmr9Z7JM19Q0tuDtqJouzmkh5zip8qZ1vaOXiZQYEVGBpHJTYhlB5hPTSudn01.tupiwsp27_servlet_TXPP02',
    'path': '/',
    'domain': 'hometax.go.kr',
    }
cookie2 = {
    'name':'TEHTsessionID', 
    'value':'sBpKHTLTuTla1QWVEk9A81H1Jl6NeK5TZr6YaYTvzHvx1kkWJ9uYEJeNgSFNUf2t.tupiwsp02_servlet_TEHT02',
    'path': '/',
    'domain': 'hometax.go.kr',
    }
driver.add_cookie(cookie1);
driver.add_cookie(cookie2);
time.sleep(3)

# 쿠키 출력
#cookies = driver.get_cookies()
#print(cookies)

# 메뉴이동 : '신고/납부' 메뉴 MouseOver -> '양도소득세' 클릭
menu1 = driver.find_element(By.ID, "textbox81212962")
action=ActionChains(driver)
action.move_to_element(menu1).perform()
submenu = wait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "양도소득세")))
submenu.click()
time.sleep(5)

# iframe이동
moveIframe()

# 이동 : Page1
do_page1_capitalGainsTaxType1()

# 종료대기
time.sleep(5)

# 종료
driver.close()