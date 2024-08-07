from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import traceback
from datetime import datetime


from common import *
import dbjob

import config
from common import *
import dbjob
import common_sele as sc

import auto_login

# DB 접속
conn = dbjob.connect_db()

# Logger 설정
CUR_CWD = os.getcwd()
current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")

# 로그 폴더 생성
print("폴더 생성 확인 = " + f"{config.ETC_LOG_DIR}")
os.makedirs(f"{config.AUTO_STEP_LOG_DIR}", exist_ok=True)

log_filename = f"{config.AUTO_STEP_LOG_DIR}/홈택스_전체_신고목록_{now}.log"
print(f"Log File={log_filename}")
logger = set_logger(log_filename)    # common.py 파일에 있음




# 관리자 인증서 로그인 (공인인증 -> 세무대리 로그인)
def login_2step(driver):
    logt ("관리인증서  로그인 시작")

    # 1) 홈택스 접속

    logt("홈택스 메인 화면 이동 및 오픈 대기(10초)")
    driver.get('https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=&tm2lIdx=&tm3lIdx=')
    #driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml")
    driver.implicitly_wait(10)

    #  2) 화면 상단 "로그인" 클릭
    logt("화면상단 [로그인] 버튼 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#textbox915').click()

    #  3) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=txppIframe) 전환", 2)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    print("[공동,금융인증서] 버튼 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#anchor22').click()


    #  5) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=dscert) 전환", 2)
    #sc.move_iframe("dscert")
    driver.switch_to.frame("dscert")

    # 6) 인증서 로그인
    logt("[인증서 비밀번호] 값입력", 1)
    in_cert_login_pw = driver.find_element(By.CSS_SELECTOR, '#input_cert_pw')
    in_cert_login_pw.send_keys('kksjns1203!')

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
    logt("IFrame(=txppIframe) 전환", 2)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    logt("[아이디] 값 입력", 0.1)
    driver.find_element(By.ID, 'input1').send_keys('P24335')
    logt("[비번] 값 입력", 0.1)
    driver.find_element(By.ID, 'input2').send_keys('kksjns1203!')
    logt("[로그인] 클릭", 0.5)
    driver.find_element(By.ID, 'trigger41').click()

    # id: input1
    # pw: input2
    # 로그인 : trigger41
    logt("업무담당자 로그인 완료 !!!", 1)

if __name__ == '__main__':

    # 셀레니움 드라이버
    driver: WebDriver = auto_login.init_selenium()
    

    # 자동로그인 처리
    #auto_login.login_hometax(driver, login_info, config.IS_DEBUG)
    # ------------------------------------------------------------------
    
    try:

        #######################################################################################

        window_handles = driver.window_handles
        main_window_handle = window_handles[0] 
        print(main_window_handle)
        logt("메인윈도우 핸들: %s" % main_window_handle)

        # logt("메뉴이동 : '신고/납부' 메뉴 이동")
        # url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=&tm2lIdx=&tm3lIdx='
        # driver.get(url)
        login_2step(driver)
        logt("세금신고 -> 신고내역 조회 이동 하기", 2)
        # TODO
        # 수동로그인
        url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
        driver.get(url)

        logt("iframe 이동", 2)
        sc.move_iframe(driver)
        
        # logt("클릭: 신고내역조회(접수증,납부서) 메뉴", 1)
        # element = driver.find_element(By.CSS_SELECTOR, '#tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11 > div.w2tabcontrol_tab_center > a')
        # element.click()

        logt("클릭: 신고내역 조회(접수증,납부서)", 2)
        driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11').click()


        time.sleep(0.5)
        logt("조회클릭")
        driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()
        time.sleep(10)
        alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")


        print("Alter Message Return=%s" % alt_msg)
        # 결과가 없을 경우 처리
        if alt_msg.find("사업자등록번호") > -1 :
            logt("조회결과 없음, 주민번호: %s" % ssn)
            raise BizException("조회결과없음", f"주민번호:{ssn}")
        elif alt_msg.find("이중로그인 방지로 통합인증이 종료되었습니다") > -1 :
            logt("이중로그인 방지로 통합인증이 종료되었습니다 => 프로그램 종료")
            sys.exit()
        elif alt_msg.find("조회된 데이터가 없습니다") > -1 :
            logt("조회결과 없음, 주민번호: %s" % ssn)
            raise BizException("조회결과없음", f"주민번호:{ssn}, 실행자={ht_info['reg_id']}")


        # 100건씩
        select = Select(driver.find_element(By.ID, "edtGrdRowNum"))
        select.select_by_visible_text("100건")
        time.sleep(0.2)
        driver.find_element(By.ID, 'trigger6_UTERNAAZ31').click()
        time.sleep(22)
        
        alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")



        조회건수 = driver.find_element(By.CSS_SELECTOR, "#txtTotal887").text   # 총 1/2 등....
        조회건수 = int(조회건수)
        조회_페이지수 = driver.find_element(By.CSS_SELECTOR, "#txtTotalPage887").text
        조회_페이지수 = int(조회_페이지수)
        logt("조회결과수=%d, 페이지수=%d" % (조회건수, 조회_페이지수))
        
        trs = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_body_tbody > tr")
        현재페이지_ROW_수 = len(trs)

        시작페이지_index = 1   # 1 베이스 시작페이지 지정 (오류 후 재시작용)
        추가row수 = 0
        for i in range(시작페이지_index, 조회_페이지수+1):  # 시작은 1부터 ~
            p_start = time.time()
            logt(f"조회페이지 = {i} page -------------------------")


            # 조회 페이지 클릭        
            if i>10 and i%10 == 1:
                driver.find_element(By.ID, f'pglNavi887_next_btn').click()
            else:
                driver.find_element(By.ID, f'pglNavi887_page_{i}').click()

            time.sleep(20)
            alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
            if alt_msg.find('이중로그인 방지로 통합인증이 종료되었습니다') >= 0:
                logt("이중로그인으로 프로그램 종료!!!!!")
                driver.close()
                sys.exit()

            trs = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_body_tbody > tr")
            data_list = []
            for row in range(현재페이지_ROW_수):
                start = time.time()

                tds = trs[row].find_elements(By.TAG_NAME, "td")
                과세연월   = tds[2].text
                신고서종류 = tds[3].text
                신고구분   = tds[4].text
                신고유형   = tds[5].text
                성명       = tds[6].text
                주민번호1  = tds[7].text[0:6]
                접수방법   = tds[8].text
                접수일시   = tds[9].text
                접수번호   = tds[10].text
                제출자ID   = tds[30].text
                부속서류제출여부 = tds[36].text
                납부여부   = tds[38].text

                end = time.time()

                # 성명이 없다면 마지막이라고 판단
                if 성명 == '':
                    break

                try:
                    data = (
                        과세연월, 신고서종류, 신고구분, 신고유형, 성명, 
                        주민번호1, 접수방법, 접수일시, 접수번호, 제출자ID, 
                        부속서류제출여부, 납부여부
                    )
                    data_list.append(data)
                    logt(f"insert page={i} row={row}, 성명={성명}, 주민번호1={주민번호1}, time={end - start:.5f} sec")
                except Exception as e:
                    logt(f" =============> ERROR insert page={i} row={row}, 성명={성명}, 주민번호1={주민번호1}, time={end - start:.5f} sec : {e}")
                
            # end of for(100개씩)
            try:
                affected = dbjob.insert_audit_ht(data_list)
                logt(f"insert page={i} time={end - start:.5f} sec, affected={affected}")
            except Exception as e:
                logt(f" =============> ERROR insert page={i} time={end - start:.5f} sec : {e}")

            p_end = time.time()
            logt(f"{i} page,  소요시간={p_end - p_start:.5f} sec")            

        logt(f"총 insert row count = {추가row수}")
        #######################################################################################`
    
    except Exception as e:
        logt(f"======= 오류발생 : {e}")
        traceback.print_exc()
    
    else:  # 오류없이 정상 처리시
        logt("======= 정상종료")

    driver.close()
    
    exit(0)

