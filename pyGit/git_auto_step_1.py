from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
import pyautogui
#except StaleElementReferenceException:

import time

from common import *

import auto_login
import dbjob

import config
import git_file
import sele_common as sc



au_step = "1"
AU_X    = f"au{au_step}"
group_id = 'wize'
dbjob.set_global(group_id, None, None, None, au_step)


def main():
    host_name = config.HOST_NAME
    conn = dbjob.connect_db()

    # (전체자료 업데이트) 신고안내문
    
    # 작업대상 목록
    # #############################################################
    git_infos = dbjob.select_git_auto_au1(group_id)
    # #############################################################
    
    if len(git_infos) == 0:
        logi("진행할 작업이 없습니다. 프로그램을 종료합니다.")
        sys.exit()
    else:
        logi(f"홈택스 종합소득세 파일다운로드 작업 ::: 총 실행 건수 = {len(git_infos)}")
        
        
    driver: WebDriver = auto_login.init_selenium()
    driver.set_window_size(1300, 1150)
    driver.set_window_position(0, 0)
    
    i = 0
    for git_info in git_infos:
        i += 1
        logi(f">>>>>>> 현재 실행 위치 {i} / {len(git_infos)} <<<<<<<<")
        logi(f"======= {git_info['git_seq']} =  {git_info['nm']}  {git_info['ssn1']}{git_info['ssn2']} :  {git_info['hometax_id']} / {git_info['hometax_pw']}")

        git_seq = git_info['git_seq']
        
        logi("홈텍스 메인페이지 이동")
        driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml")
        driver.implicitly_wait(10)


        login_info = {}
        login_info['name'] = git_info['nm']
        login_info['login_id'] = git_info['hometax_id']
        login_info['login_pw'] = git_info['hometax_pw']
        
        if git_info['hometax_id_confirm'] != 'Y':
            logi("이전에 로그인에 실패하였습니다.  홈택스ID/PWD를 확인 후 다시 시도하세요")
            
        
        # 자동로그인 처리
        logt("로그인 시간", 1)
        auto_login.login_guest(driver, login_info)
        driver.set_window_size(1350, 1700)
        logi("로그인 완료")
        
        #
        try:
            logt("비밀번호 오류팝업확인", 1)
            #alert = driver.switch_to.alert
            alert = driver.switch_to.alert
            alert_msg = alert.text
            logt("Alert메세지: %s" % alert_msg)

            if alert_msg.find("비밀번호가") >= 0  :   # 비밀번호가 [3]회 잘못 입력되었습니다
                dbjob.update_git_hometaxIdConfirm(group_id, git_seq, 'N')
                alert.accept()
                logi("비밀번호 오류로 다음 차례 진행 ~~~~~~~~")
                continue
        except Exception as e:
            logt("정상로그인")
            if git_info['hometax_id_confirm'] == None:
                dbjob.update_git_hometaxIdConfirm(group_id, git_seq, 'Y')

        
        # 팝업 창이 있으면 모두 닫기
        if len(driver.window_handles) > 1:
            for i in range(len(driver.window_handles)-1, 0, -1):
                driver.switch_to.window(driver.window_handles[i])
                driver.close()
                
            driver.switch_to.window(driver.window_handles[0])
        
        
        # ---------------------------------------------------

        sc.click_button_by_id(driver, 'prcpSrvcMenuA0', '종합소득세 이미지', 1.5)
        time.sleep(1)
        

        # 종합소득세
        driver.switch_to.frame("txppIframe")
        sc.click_button_by_id(driver, 'sub_a_2601000000', '종합소득세 신고하기', 1)

        time.sleep(3)
        if len(driver.window_handles) > 1:
            for i in range(len(driver.window_handles)-1, 0, -1):
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
        
        # 메인 윈도우 복귀
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.frame("txppIframe")
            
        time.sleep(0.5)
        sc.click_button_by_id(driver, 'tboxt0201', '일반 신고', 1)
        time.sleep(0.5)
        sc.click_button_by_id(driver, 'grpt02l0101', '정기신고', 1)
        
        
        # ==================================================================================================
        # 01.기본사항
        # ==================================================================================================
        sc.click_button_by_id(driver, 'trigger106', '조회', 1)
        time.sleep(0.5)
            
        try:
            alert = driver.switch_to.alert
            alert_msg = alert.text
            logt("Alert메세지: %s" % alert_msg)
            if alert_msg.find("작성중인 신고서가 존재합니다") >= 0  : 
                alert.accept()
                
                time.sleep(1)
                alert = driver.switch_to.alert
                alert_msg = alert.text
                alert_exp = "조회가 완료되었습니다"
                logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")

                if alert_msg.find(alert_exp) >= 0  : 
                    alert.accept()              
                    
                    # 새로작성하기  
                    sc.click_button_by_id(driver, 'trigger110', '새로 작성하기', 1)
                    time.sleep(0.5)
                    alert = driver.switch_to.alert
                    alert_msg = alert.text
                    alert_exp = "작성중인 신고서는 삭제가 가능합니다. 삭제하시겠습니까?"
                    logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
                    if alert_msg.find(alert_exp) >= 0  : 
                        alert.accept()

                        time.sleep(0.5)
                        alert = driver.switch_to.alert
                        alert_msg = alert.text
                        alert_exp = "신고서의 취소가 완료되었습니다"
                        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
                        if alert_msg.find(alert_exp) >= 0  : 
                            alert.accept()                        
                            
                            # 처음부터 다시 시작하는 "조회"버튼 클릭
                            sc.click_button_by_id(driver, 'trigger106', '조회', 1)
                            time.sleep(0.5)
                            alert = driver.switch_to.alert
                            alert_msg = alert.text
                            alert_exp = "신규입력하시겠습니까"
                            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
                            if alert_msg.find(alert_exp) >= 0  : 
                                alert.accept()                        
                            
                            
            elif alert_msg.find("신규입력하시겠습니까?") >=0 :
                alert.accept()
                
                
        except Exception as e:
            loge(f"Exception 발생(1) : {e}" )


        # 나의 소득종류 찾기
        time.sleep(1)
        # 팝업 창이 있으면 모두 닫기
        if len(driver.window_handles) > 1:
            for i in range(len(driver.window_handles)-1, 0, -1):
                driver.switch_to.window(driver.window_handles[i])
                if driver.title.find("나의소득종류찾기") == -1:
                    driver.close()
                
        # 마지막 오픈 윈도우 전환 -> 나의소득종류찾기
        driver.switch_to.window(driver.window_handles[-1])
        driver.set_window_position(0, 0)
        sc.click_button_by_id(driver, 'trigger3', '나의소득종류찾기 > 적용하기', 1)
        

        time.sleep(1)
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.frame("txppIframe")        


        # 사업소득 사업장 명세
        trs = driver.find_elements(By.CSS_SELECTOR, "#grdTTIRNDL008_body_tbody > tr")
        for i in range(len(trs)):
            driver.find_element(By.CSS_SELECTOR, f"#G_grdTTIRNDL008___checkbox_chk_{i}").click()
            sc.click_button_by_id(driver, 'trigger104', '선택내용 수정', 0.5)
            
            # 기장의무 => 간편장부대상자 확인
            time.sleep(0.5)
            select_기장의무 = Select(driver.find_element(By.ID, 'selectbox50'))
            select_option = select_기장의무.first_selected_option
            기장의무 = select_option.text
            
            time.sleep(0.5)
            select_신고유형 = Select(driver.find_element(By.ID, 'selectbox48'))
            select_신고유형.select_by_visible_text('간편장부')
            
            sc.click_button_by_id(driver, 'trigger109', '등록하기', 0.5)
            time.sleep(0.5)

            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "위의 [사업소득 사업장 명세] 표에 등록되었습니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()              
        
        # 휴대전화 번호 넣기
        try:
            휴대전화번호 = git_info['tel'].split("-")
            driver.find_element(By.ID, "input104").clear()
            driver.find_element(By.ID, "input105").clear()
            select_휴대전화 = Select(driver.find_element(By.ID, 'selectbox1'))
            select_휴대전화.select_by_visible_text(휴대전화번호[0])
            time.sleep(0.2)
            driver.find_element(By.ID, "input104").send_keys(휴대전화번호[1])
            time.sleep(0.2)
            driver.find_element(By.ID, "input105").send_keys(휴대전화번호[2])
        except Exception as e:
            # 휴대전화번호 넣기 오류 처리    
            loge(f"휴대전화 번호 넣기 오류 : {e}")
            
            
        sc.click_button_by_id(driver, 'trigger90', '저장 후 다음이동', 0.2)
        time.sleep(0.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()     
        
            time.sleep(2)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "조회가 완료되었습니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()     
            

            
            
        # ==================================================================================================
        # 02.소득금액명세서
        #  -> 간편장부 : 총수입금액 및 필요경비 계산명세서
        # ==================================================================================================
        
        # 매출액
        time.sleep(0.2)
        driver.find_element(By.ID, "edtTTIRNDL023boksIcmSlsAmt").send_keys(git_info['income_amount'])
        # 접대비
        time.sleep(0.2)
        driver.find_element(By.ID, "edtTTIRNDL023gnrlAdxpEntmXpns").send_keys(git_info['entertainment_expenses'])
        # 지급수수료
        time.sleep(0.2)
        driver.find_element(By.ID, "edtTTIRNDL023pymnFee").send_keys(git_info['commission_fee'])
        # 소모품비
        time.sleep(0.2)
        driver.find_element(By.ID, "edtTTIRNDL023gnrlAdxpSuplXpns").send_keys(git_info['supplies_expense'])
        # 광고선전비
        time.sleep(0.2)
        driver.find_element(By.ID, "edtTTIRNDL023avxp").send_keys(git_info['advertising_expenses'])
        # 여비교통비
        time.sleep(0.2)
        driver.find_element(By.ID, "edtTTIRNDL023teTrpXpns").send_keys(git_info['transportation_expenses'])
        
        sc.click_button_by_id(driver, 'trigger93', '등록하기', 1)
        time.sleep(0.5)
        
        try:
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "사업장정보 목록에 등록 되었습니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()             
        except Exception as e:
            loge(f"Alert 오류 : {e}")
        
        sc.click_button_by_id(driver, 'trigger94', '저장 후 다음이동', 0.2)
        time.sleep(0.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()             
                
            time.sleep(2)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "조회가 완료되었습니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()             

        # ==================================================================================================
        # 02.소득금액명세서
        #  -> 간편장부 : 간편장부소득금액계산서
        # ==================================================================================================

        try:
            sc.click_button_by_id(driver, 'trigger93', '등록하기', 1)
            time.sleep(0.5)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "사업장정보 목록에 등록 되었습니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()          
        except Exception as e:
            loge(f"Alert Error(2) : {e}")
        
        
        sc.click_button_by_id(driver, 'trigger94', '저장 후 다음이동', 0.2)
        time.sleep(0.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()             
                
            time.sleep(1.5)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "조회가 완료되었습니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()             


        # ==================================================================================================
        # 02.소득금액명세서
        #  -> 사업소득 원천징수명세서
        # ==================================================================================================

        sc.click_button_by_id(driver, 'trigger211', '사업소득 원천징수세액 불러오기', 1)
        time.sleep(1.5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.set_window_position(0, 0)
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, "#grdTTIRNDS170__chk > input").click()
            
            sc.click_button_by_id(driver, 'trigger7', '적용하기', 0.5)
            time.sleep(0.5)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "적용하시겠습니까?"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()        
                
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.frame("txppIframe")        

        sc.click_button_by_id(driver, 'trigger67', '저장 후 다음이동', 0.2)
        time.sleep(0.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()             


        # ==================================================================================================
        # 02.소득금액명세서
        #  -> 사업소득 원천징수명세서
        # ==================================================================================================
        sc.click_button_by_id(driver, 'trigger20', '저장 후 다음이동', 1)
        time.sleep(0.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "조회가 완료되었습니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()             

        # ==================================================================================================
        # 03.종합소득금액 및 결손금
        #  -> 종합소득금액및결손금.이월결손금공제명세서
        # ==================================================================================================
        sc.click_button_by_id(driver, 'trigger67', '저장 후 다음이동', 1)
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()                    

            time.sleep(0.5)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            alert_exp = "이월결손금명세서가 먼저 입력되어야 작성이 가능합니다"
            logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
            if alert_msg.find(alert_exp) >= 0  : 
                alert.accept()        
                
                        
        # ==================================================================================================
        # 03.종합소득금액 및 결손금
        #  -> 결손금 소급공제세액 환급신청서
        # ==================================================================================================
        sc.click_button_by_id(driver, 'trigger67', '저장 후 다음이동', 1)
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()                    

                        
        # ==================================================================================================
        # 05.소득공제명세서
        # ==================================================================================================
        sc.click_button_by_id(driver, 'trigger9', '저장 후 다음이동', 1)
        time.sleep(1.5)

        # ==================================================================================================
        # 06.기부금 및 조정명세서
        # ==================================================================================================

        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "기부금 내역이 없는 경우 기부금 명세서를 입력하지 않아도 됩니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()        

        # ==================================================================================================
        # 08.세액공제.감명.준비금
        #  -> 세액감면(면제)신청서
        # ==================================================================================================
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "세액감면 대상이 아닌 경우 세액감면(면제) 신청서를 입력하지 않아도 됩니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()        

        # ==================================================================================================
        # 08.세액공제.감명.준비금
        #  -> 세액공제신청서
        # ==================================================================================================
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "세액공제 대상이 아닌 경우 세액공제신청서를 입력하지 않아도 됩니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()    
            

        # ==================================================================================================
        # 08.세액공제.감명.준비금
        #  -> 세액감면.공제.준비금명세서
        # ==================================================================================================
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "조회가 완료되었습니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()    


        sc.click_button_by_id(driver, 'trigger111', '저장 후 다음이동', 1)
        time.sleep(0.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "저장 후 다음화면으로 이동하시겠습니까?"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()                    


        # ==================================================================================================
        # 09.기납부세액명세서
        # ==================================================================================================
        sc.click_button_by_id(driver, 'trigger111', '저장 후 다음이동', 1)
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "조회가 완료되었습니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()    
            

        # ==================================================================================================
        # 10.가산세명세서
        # ==================================================================================================
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "가산세 적용 대상이 아닌 경우 가산세 명세서를 입력하지 않아도 됩니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()    
            
        # ==================================================================================================
        # 11.세액계산
        # ==================================================================================================
        time.sleep(1.5)
        alert = driver.switch_to.alert
        alert_msg = alert.text
        alert_exp = "조회가 완료되었습니다"
        logt(f"Alert메세지: (예상){alert_exp}, (실제){alert_msg} ==> {alert_msg.find(alert_exp)}")
        if alert_msg.find(alert_exp) >= 0  : 
            alert.accept()    
            
        sc.click_button_by_id(driver, 'checkbox1_input_0', '이에 동의합니다', 1)
        sc.click_button_by_id(driver, 'trigger9', '제출화면 이동', 1)

        logi("다른 오픈된 윈도우 닫기")
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])


        # 정상처리
        dbjob.update_git_au_x(group_id, git_seq, AU_X, 'S')

        # 로그아웃
        logout(driver)  
    # end for   

def to_number(str):
    return str.strip().replace(',','').replace('원','').replace(' ','')

def logout(driver):
    # 메인윈도우로 다시 돌아오기
    driver.switch_to.window(driver.window_handles[0])

    sc.click_button_by_id(driver, 'group1544', '로그아웃', 0.5)
    time.sleep(1)    
    try:
        logt("Alert 창 확인 : 로그아웃 하시겠습니까?", 1)
        #alert = driver.switch_to.alert
        alert = driver.switch_to.alert
        alert_msg = alert.text
        logt("Alert메세지: %s" % alert_msg)

        if alert_msg.find("로그아웃") >= 0  :
            alert.accept()
    except Exception as e:
        logt("Alert메세지 오류 : %s" % e)

        
    


if __name__ == '__main__':
    main()
