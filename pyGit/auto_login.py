import time, os, sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver

import sele_common as sc
from config import *
from common import *


def init_selenium() -> WebDriver:
    '''
    cur_dir = os.getcwd()
    middle_dir = os.path.dirname(sys.argv[0]) + os.sep
    if middle_dir:
        cur_dir += os.sep + middle_dir
    '''
    cur_dir = os.getcwd()
    chromedriver_path =  cur_dir + os.sep + "chromedriver.exe" #resource_path("chromedriver.exe")
    logi("크롬드라이버 위치=%s" % chromedriver_path)

    # 1.크롬접속
    driver = webdriver.Chrome(chromedriver_path)

    # 브라우저 위치 조정하기
    driver.set_window_position(0,0)
    # 브라우저 화면 크기 변경하기
    driver.set_window_size(config.BROWSER_SIZE['width'], config.BROWSER_SIZE['height'])

    # Implicitly wait을 10초로 설정하면 페이지가 로딩되는데 10초까지 기다립니다. 
    # 만약 페이지 로딩이 2초에 완료되었다면 더 기다리지 않고 다음 코드를 수행합니다. 
    # 기본 설정은 0초로 되어있고, 
    # 한번만 설정하면 driver를 사용하는 모든 코드에 적용이 됩니다.
    driver.implicitly_wait(5)

    return driver


def login(driver, login_info, IS_DEBUG):
    
    if IS_DEBUG:
        # 쿠키 로그인
        TXPP = 'MCM1sq391v0UlTS1A2DX1D702bLJd3H52I2W13fnyb2pzv1T7MaHIdAKi2g1Jybp.tupiwsp17_servlet_TXPP01'
        TEHT = 'vvPHR6JdSXhmwNfgA8a84caoMpvWlG1Q2dHne8Y3ISFyn5Yb76H8NxCqBuGkPWpW.tupiwsp06_servlet_TEHT01'
        JSES = ''  # 없어도 되는 값
        login_use_cookie(driver, TXPP, TEHT, JSES)
    else:
        if login_info['login_id'] == "MANAGER_ID":
            # 인증서 로그인
            login_2step(driver, login_info)
        else :
            # 작업자 개별 로그인s
            login_3step(driver, login_info)

    sc.close_other_windows(driver)


def login_guest(driver, login_info):
    logt ("종합소득세 게스트 ID/PWD 로그인 시작 = " + login_info['name'])

    # 1) 홈택스 접속

    logt("홈택스 메인 화면 이동 및 오픈 대기(10초)")
    sc.go_main_page(driver)

    #  2) 화면 상단 "로그인" 클릭
    logt("화면상단 [로그인] 버튼 클릭", 4)
    driver.find_element(By.CSS_SELECTOR, '#textbox81212912').click()
    
    time.sleep(1)

    #  3) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=txppIframe) 전환", 2)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    #  4) "아이디로그인" 버튼 클릭
    logt("[아이디로그인(li)] 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#group91882156').click()

    logt("[아이디] 값입력", 0.5)
    in_login_id = driver.find_element(By.CSS_SELECTOR, '#iptUserId')
    in_login_id.send_keys(login_info['login_id'])
    logt("[비번] 값입력", 0.5)
    in_login_pw = driver.find_element(By.CSS_SELECTOR, '#iptUserPw')
    in_login_pw.send_keys(login_info['login_pw'])

    print("[로그인] 버튼 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#anchor25').click()


# 업무담당자 3단계 로그인
def login_3step(driver, login_info):
    logt ("업무 담당자 로그인 시작 = " + login_info['name'])

    # 1) 홈택스 접속

    logt("홈택스 메인 화면 이동 및 오픈 대기(10초)")
    sc.go_main_page(driver)

    #  2) 화면 상단 "로그인" 클릭
    logt("화면상단 [로그인] 버튼 클릭", 4)
    driver.find_element(By.CSS_SELECTOR, '#textbox81212912').click()

    #  3) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=txppIframe) 전환", 2)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    #  4) "아이디로그인" 버튼 클릭
    logt("[아이디로그인(li)] 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#group91882156').click()

    logt("[아이디] 값입력", 2)
    in_login_id = driver.find_element(By.CSS_SELECTOR, '#iptUserId')
    in_login_id.send_keys(login_info['login_id'])
    logt("[비번] 값입력", 1)
    in_login_pw = driver.find_element(By.CSS_SELECTOR, '#iptUserPw')
    in_login_pw.send_keys(login_info['login_pw'])

    print("[로그인] 버튼 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#anchor25').click()


    #  5) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=dscert) 전환", 4)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#dscert')
    driver.switch_to.frame(iframe1)


    # 6) 인증서 로그인
    logt("[인증서 비밀번호] 값입력", 2)
    in_cert_login_pw = driver.find_element(By.CSS_SELECTOR, '#input_cert_pw')
    in_cert_login_pw.send_keys(login_info['cert_login_pw'])

    logt("[확인]클릭 =>인증서 로그인]", 1)
    driver.find_element(By.CSS_SELECTOR, '#btn_confirm_iframe').click()

    # 7) 세무대리인 확인 Alert 창
    logt("(Alert창) 세무대리인 권한을 가진 사용자 입니다]", 5)
    try:
        # ==> 이코드는 동작 안함 WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        # Alert창 메세지 출력
        print(alert.text)
        # 확인 버튼
        alert.accept()
    except:
        loge("ALERT 창 오류 : 세무대리인 여부 확인")
        
    # 세무대리인 관리번호 로그인(P24XXX)
    logt("IFrame(=txppIframe) 전환", 3)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    logt("[아이디] 값 입력", 0.1)
    driver.find_element(By.ID, 'input1').send_keys(login_info['rep_id'])
    logt("[비번] 값 입력", 0.1)
    driver.find_element(By.ID, 'input2').send_keys(login_info['rep_pw'])
    logt("[로그인] 클릭", 0.5)
    driver.find_element(By.ID, 'trigger41').click()

    # id: input1
    # pw: input2
    # 로그인 : trigger41
    logt("업무담당자 로그인 완료 !!!", 1)


def login_use_cookie(driver, txpp, teht, jses=''):
    # 2. 홈택스 접속
    url = 'https://www.hometax.go.kr/'
    #url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index.xml&tmIdx=9&tm2lIdx=&tm3lIdx='
    driver.get(url)

    #  1) 홈택스로 이동
    cookie1 = {
        'name'  : 'TXPPsessionID', 
        'value' : txpp,
        'path'  : '/',
        'domain': 'hometax.go.kr',
        }
    cookie2 = {
        'name'  : 'TEHTsessionID', 
        'value' : teht,
        'path'  : '/',
        'domain': 'hometax.go.kr',
        }
    cookie3 = {
        'name'  : 'JSESSIONID', 
        'value' : jses,
        'path'  : '/',
        'domain': 'hometax.go.kr',
        }    
    driver.add_cookie(cookie1)
    driver.add_cookie(cookie2)
    
    if jses:
        driver.add_cookie(cookie3)
    

    time.sleep(2)



# 관리자 인증서 로그인 (공인인증 -> 세무대리 로그인)
def login_2step(driver, login_info):
    logt ("관리인증서  로그인 시작")

    # 1) 홈택스 접속

    logt("홈택스 메인 화면 이동 및 오픈 대기(10초)")
    sc.go_main_page(driver)

    #  2) 화면 상단 "로그인" 클릭
    logt("화면상단 [로그인] 버튼 클릭", 4)
    driver.find_element(By.CSS_SELECTOR, '#textbox81212912').click()

    #  3) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=txppIframe) 전환", 4)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    print("[공동,금융인증서] 버튼 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#anchor22').click()


    #  5) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=dscert) 전환", 5)
    #sc.move_iframe("dscert")
    driver.switch_to.frame("dscert")

    # 6) 인증서 로그인
    logt("[인증서 비밀번호] 값입력", 1)
    in_cert_login_pw = driver.find_element(By.CSS_SELECTOR, '#input_cert_pw')
    in_cert_login_pw.send_keys(login_info['cert_login_pw'])

    logt("[확인]클릭 =>인증서 로그인]", 1)
    driver.find_element(By.CSS_SELECTOR, '#btn_confirm_iframe').click()

    # 7) 세무대리인 확인 Alert 창
    logt("(Alert창) 세무대리인로그인 확인]", 2)
    try:
        # ==> 이코드는 동작 안함 WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        # Alert창 메세지 출력
        print(alert.text)
        # 확인 버튼
        alert.accept()
    except:
        loge("주의 할 것!! 이상한게도 한번은 exception이 발생한다!!!!!")
        alert = driver.switch_to.alert
        # Alert창 메세지 출력
        print(alert.text)
        # 확인 버튼
        alert.accept()
        
    # 세무대리인 관리번호 로그인(P24XXX)
    logt("IFrame(=txppIframe) 전환", 3)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    logt("[아이디] 값 입력", 0.1)
    driver.find_element(By.ID, 'input1').send_keys(login_info['rep_id'])
    logt("[비번] 값 입력", 0.1)
    driver.find_element(By.ID, 'input2').send_keys(login_info['rep_pw'])
    logt("[로그인] 클릭", 0.5)
    driver.find_element(By.ID, 'trigger41').click()

    # id: input1
    # pw: input2
    # 로그인 : trigger41
    logt("업무담당자 로그인 완료 !!!", 1)