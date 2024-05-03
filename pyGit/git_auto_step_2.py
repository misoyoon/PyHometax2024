from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import traceback
import pyautogui
import config

from common import *
import dbjob
import git_file
import auto_login 
import sele_common as sc
import config

au_step = "2"
AU_X    = f"au{au_step}"
group_id = 'wize'
dbjob.set_global(group_id, None, None, None, au_step)


def main():
    host_name = config.HOST_NAME
    conn = dbjob.connect_db()

    # (전체자료 업데이트) 신고안내문
    # 작업대상 목록
    # #############################################################
    git_infos = dbjob.select_auto_2(group_id)
    # #############################################################
    
    if len(git_infos) == 0:
        logt("진행할 작업이 없습니다. 프로그램을 종료합니다.")
        sys.exit()
    else:
        logt(f"홈택스 종합소득세 파일다운로드 작업 ::: 총 실행 건수 = {len(git_infos)}")
        
        
    driver: WebDriver = auto_login.init_selenium()
    driver.set_window_size(1300, 1250)
    driver.set_window_position(0, 0)

    i = 0
    for git_info in git_infos:
        i += 1
        logt(f">>>>>>> 현재 실행 위치 {i} / {len(git_infos)} <<<<<<<<")
        logt(f"======= {git_info['git_seq']} =  {git_info['nm']}  {git_info['ssn1']}{git_info['ssn2']} :  {git_info['hometax_id']} / {git_info['hometax_pw']}")

        git_seq = git_info['git_seq']
        
        logt("홈텍스 메인페이지 이동")
        driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml")
        driver.implicitly_wait(10)

        if git_info['hometax_id_confirm'] != 'Y':
            logt("이전에 로그인에 실패하였습니다.  홈택스ID/PWD를 확인 후 다시 시도하세요")
            
        
        # 자동로그인 처리
        if login_guest(driver, git_info) == False:
            continue
        
        # 기타 윈도우 닫기
        close_other_window(driver)
        
        # ---------------------------------------------------
        driver.find_element(By.ID, 'prcpSrvcMenuA0').click()
        time.sleep(1)

        # 종합소득세 신고하기
        try :
            driver.switch_to.frame("txppIframe")
            sc.click_button_by_id(driver, 'sub_a_2601000000', '종합소득세 신고하기', 1.5)
            
            time.sleep(3)
            close_other_window(driver)
            driver.switch_to.frame("txppIframe")
            sc.click_button_by_id(driver, 'tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11', '신고내역 조회(접수증,납부서)')
            
            do_step2(driver, git_info)
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'S')
        
        except Exception as e:
            loge("메뉴 이동 중 오류 발생")
            logt("오류 발생 : %s" % e)
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E')
            
        logout(driver)
        

def close_other_window(driver):
    # 팝업 창이 있으면 모두 닫기
    if len(driver.window_handles) > 1:
        for i in range(len(driver.window_handles)-1, 0, -1):
            driver.switch_to.window(driver.window_handles[i])
            driver.close()
            
        driver.switch_to.window(driver.window_handles[0])
        
        
def login_guest(driver, git_info):
    git_seq = git_info['git_seq']
    
    logt ("종합소득세 게스트 ID/PWD 로그인 시작 = " + git_info['nm'])

    # 1) 홈택스 접속
    logt("홈택스 메인 화면 이동 및 오픈 대기(10초)")
    driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml")
    driver.implicitly_wait(10)


    #  2) 화면 상단 "로그인" 클릭
    logt("화면상단 [로그인] 버튼 클릭", 4)
    driver.find_element(By.CSS_SELECTOR, '#textbox81212912').click()
    
    time.sleep(1)

    #  3) iframe 전환 : 로그인화면은 화면전체가 iframe
    logt("IFrame(=txppIframe) 전환", 2)
    iframe1 = driver.find_element(By.CSS_SELECTOR, '#txppIframe')
    driver.switch_to.frame(iframe1)

    #  4) "아이디로그인" 버튼 클릭
    logt("[아이디-로그인(li)] 클릭", 2.5)
    driver.find_element(By.CSS_SELECTOR, '#group91882156').click()

    logt("[아이디] 값입력", 0.5)
    in_login_id = driver.find_element(By.CSS_SELECTOR, '#iptUserId')
    in_login_id.send_keys(git_info['hometax_id'])
    logt("[비번] 값입력", 0.5)
    in_login_pw = driver.find_element(By.CSS_SELECTOR, '#iptUserPw')
    in_login_pw.send_keys(git_info['hometax_pw'])

    print("[로그인] 버튼 클릭", 2)
    driver.find_element(By.CSS_SELECTOR, '#anchor25').click()

        
    #
    retVal = True
    try:
        logt("비밀번호 오류팝업확인", 1)
        #alert = driver.switch_to.alert
        alert = driver.switch_to.alert
        alert_msg = alert.text
        logt("Alert메세지: %s" % alert_msg)

        if alert_msg.find("비밀번호가") >= 0  :   # 비밀번호가 [3]회 잘못 입력되었습니다
            dbjob.update_git_hometaxIdConfirm(group_id, git_seq, 'N')
            alert.accept()
            logt("비밀번호 오류로 다음 차례 진행 ~~~~~~~~")
            retVal = False

    except Exception as e:
        logt("정상로그인")
        if git_info['hometax_id_confirm'] == None:
            dbjob.update_git_hometaxIdConfirm(group_id, git_seq, 'Y')
        
    return retVal



def logout(driver):
    # 메인윈도우로 다시 돌아오기
    driver.switch_to.window(driver.window_handles[0])
    driver.find_element(By.ID, 'group1544').click()
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

        
    


# ------------------------------------------------------                
# 여기부터는 HTLM영역이 아닌 window프로그램 영역
# ------------------------------------------------------                
def download_file(driver:WebDriver, git_info, attach_type):
    time.sleep(1)
    git_seq = git_info['git_seq']
    nm = git_info['nm']

    # file_type별 파일이름 결정
    base_dir = git_file.get_dir_by_gitSeq(git_seq, True)  # True => 폴더 생성
    filename = f"down{attach_type}.pdf" #git_file.get_file_name_by_type(attach_type)
    fullpath = base_dir + filename
    logt("------------------------------------------------------")
    logt("파일다운로드: attach_type=%s, Filepath=%s" % (attach_type, fullpath))
    logt("------------------------------------------------------")

    # 이미지 리소스 폴더
    resource_dir = os.path.dirname(os.path.abspath(__file__))  #os.path.dirname(sys.modules['__main__'].__file__)
    if resource_dir:
        resource_dir = resource_dir + os.sep + "..\\pyHometax\\resource\\"


    #일괄출력
    if  attach_type == "1":
        driver.find_element(By.ID, "triMatePrint").click()
        time.sleep(0.5)

        retVal = True
        try:
            logt("Alert 확인", 0.5)
            #alert = driver.switch_to.alert
            alert = driver.switch_to.alert
            alert_msg = alert.text
            logt("Alert메세지: %s" % alert_msg)

            if alert_msg.find("자료량에 따라 최대") >= 0  :   # 자료량에 따라 최대 2~3분 정도 소요됩니다.
                alert.accept()
                time.sleep(3)
        except Exception as e:
            logt("[일괄출력] 오류 : %s" % e)


    # --------------------------------
    img_print_path = resource_dir + "img_printer.png"
    logt(f"GUI Click: 프린터아이콘 = {img_print_path}", 1)
    time.sleep(0.5)

    # 이미지의 위치를 찾을 때까지 반복 시도 클릭
    pyautoui_image_click(img_print_path)

    # 접수증(HT_DOWN_2)의 경우 해당 버튼이 없어 단계 생략
    if not attach_type == "2":
        # [인쇄] 클릭
        logt("GUI Click: [인쇄-회색버튼]", 1)
        btn_print_path = resource_dir + "btn_print_gray.png"
        logt("img_print_path=" + btn_print_path)
        ans = pyautoui_image_click(btn_print_path)
        if ans == False:
            # 상단 프린터A 누르기
            logt("상단 프린터A 누르기 (재시도)")
            pyautoui_image_click(img_print_path)
            time.sleep(0.5)
            ans = pyautoui_image_click(btn_print_path)
            if ans == False:
                logt("회색 인쇄버튼 클릭 실패(재시도)")
                time.sleep(1000000)


    # 이미 존재하면 삭제
    if os.path.isfile(fullpath):
        os.remove(fullpath)

    # [인쇄] 버튼 클릭
    if not attach_type == "1":
        logt("GUI Click: [인쇄]", 4.0)   #  2023년 상당히 느리게 동작하고 있음
    else:
        logt("GUI Click: [인쇄]", 4.0)   #  2023년 상당히 느리게 동작하고 있음
        
    #img_save_path = resource_dir + "print_blue.png"
    img_save_path = resource_dir + "btn_blue_save.png"
    pyautoui_image_click(img_save_path)

    # 다운로드 팝업창 뜨기 => 여기도 경우에 따라 시간이 좀 걸림
    logt(f"다운로드 팝업창 뜨기 : attach_type = {attach_type}")
    
    # if not attach_type == "1":
    #     logt("단순대기", 10.0)
    # else:
    #     logt("단순대기", 3.0)
    

    try:
        # 저장 버튼이 보일 때까지 대기
        img_save_path = resource_dir + "save.png"
        is_found = pyautoui_image_wait(img_save_path)
        if not is_found:
            raise BizException("[다른이름으로 저장하기] 노출오류")
        
        
        logt(f"다른이름 저장하기 (경로명 입력) pyautogui.typewrite= {fullpath}")
        pyautogui.typewrite(fullpath)
        time.sleep(0.5)
        pyautogui.press('enter')   # 저장하기 위해 파일경로 넣고 엔터치기

        logt("단순대기 - 파일 저장대기", 5)
        if os.path.isfile(fullpath):
            logt(f"파일저장 성공: 파일타입= %s, 경로={fullpath}")
            logt("파일저장 확인완료 => DB 입력하기")
            file_size = os.path.getsize(fullpath)
            print(f"!!!!!!!! filesize 1= {file_size}")

            # if file_size > 0: 
            dic_git_file = git_file.make_file_data(git_info['group_id'], git_info['git_seq'], git_info['nm'], attach_type, False )
            
            git_file_seq  = dbjob.insert_git_file(dic_git_file)
            if git_file_seq > 0:
                dbjob.update_git_column_val(group_id, git_seq, f"result{attach_type}_file_seq", git_file_seq)

        else:
            logt(f"파일저장 확인실패 fullpath={fullpath}")
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', 'file size is not found')

    except Exception as e:
        logt(e)
        logt("오류로 프로그램 종료대기 600초")
        time.sleep(600)





# ------------------------------------------------------------------------------
# 이미지의 위치를 찾을 때까지 반복 시도 후 찾으면 해당 이미지 클릭
def pyautoui_image_click(img_path):
    for retry in range(6):
        # confidence인식 못하는 오류 : pip install opencv-python
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)
        logt(f'pyautoui_image_click() : filepath={img_path}, center={center}')

        if center == None :
            pyautogui.moveTo(10,10)  # 일부러 마우스 움직이기
            time.sleep(0.5)
            logt(f"        이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            time.sleep(0.3) # 0.3초후 클릭
            pyautogui.click(center)
            logt(f"        이미지 영역 찾기 완료 => Click : {img_path}")
            return True

    #time.sleep(100000)
    return False

# ------------------------------------------------------------------------------
# (현재사용 안함) 이미지의 위치를 찾을 때까지 반복 시도
def pyautoui_image_wait(img_path, retry_num=10):
    for retry in range(retry_num):
        time.sleep(1)
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)

        if center == None :
            logt(f"이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            logt(f"이미지 영역 찾기 완료 : {img_path}, center={center}")
            return True
    return False



# ------------------------------------------------------------------------------
def do_step2(driver: WebDriver, git_info):
    # txppIframe 프레임 안에서 동작 중
    
    time.sleep(1.5)
    git_seq = git_info['git_seq']
    default_window_handle = driver.current_window_handle
    
    ssn  = f"{git_info['ssn1']}{git_info['ssn2']}"
    logt("******************************************************************************************************************")
    logt("양도인= %s, git_seq= %d, SSN= %s%s" % (git_info['nm'], git_info['git_seq'], git_info['ssn1'], git_info['ssn2']))
    logt("******************************************************************************************************************")
    

    # ssn = git_info['ssn1'] + git_info['ssn2']
    # logt("주민번호 입력: %s" % ssn, 0.1)
    # driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').clear()
    # time.sleep(0.2)
    # driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').send_keys(ssn)

    time.sleep(0.5)
    logt("조회클릭")
    driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()

    alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
    logt("Alter Message Return=%s" % alt_msg)
    # 결과가 없을 경우 처리
    if alt_msg.find("사업자등록번호") > -1 :
        logt("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음", f"주민번호:{ssn}")
    elif alt_msg.find("이중로그인 방지로 통합인증이 종료되었습니다") > -1 :
        logt("이중로그인 방지로 통합인증이 종료되었습니다 => 프로그램 종료")
        sys.exit()
    elif alt_msg.find("조회된 데이터가 없습니다") > -1 :
        logt("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음", f"주민번호:{ssn}")

    ele_s = driver.find_element(By.CSS_SELECTOR, "#txtTotal887").text   # 총 1/2 등....
    logt("조회결과 갯수= %d" % int(ele_s))
    
    if int(ele_s) == 0:
        raise BizException("조회결과없음")

    elif int(ele_s) > 1:
        raise BizException("복수신고건", "신고건수= %d" % int(ele_s))
    
    elif int(ele_s) == 1:
        ele1 = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_4 > span")
        ele2 = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_5 > span")
        
        offset = 0
        if ele1.text == "정기신고" :
            offset = 0
        elif ele2.text == "정기신고" :
            offset = 1

        logt("결과 OFFSET= %d" % offset)

        selector = "#ttirnam101DVOListDes_cell_0_" +str(5+offset)+ " > span"
        print (selector)
        ele = driver.find_element(By.CSS_SELECTOR, selector)    
        hometax_nm = ele.text
        # 양도인 이름이 같은지 조회

        # 신청_홈택스_이름차이_목록 = ["이해룡", "함경님"]
        # if not git_info['nm'] in 신청_홈택스_이름차이_목록:
        logt("양도인명 확인 DB값= %s, Hometax= %s" % (git_info['nm'], hometax_nm))
        #     if hometax_nm != git_info['nm']:
        #         raise BizException("양도인명 불일치", "홈택스 양도인명= %s" % hometax_nm)

        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(9+offset)+ " > span > a")
        hometax_reg_num = ele.text
        logt("홈택스 접수번호= %s" % hometax_reg_num)
        dbjob.update_git_hometaxRegNum(git_seq, hometax_reg_num)

        try:
            logt('# -----------------------------------------------------------------')
            logt('#                        1) 납부계산서                             ')
            logt('# -----------------------------------------------------------------')

            ele_s = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(9+offset)+ " > span > a")
            ele_s[0].click()
            
            # 팝업윈도우가 2개가 더 오픈되기 위한 충분한 시간을 주기
            logt("팝업 윈도우2개 로딩 대기", 2)
            window_handles = driver.window_handles
            
            if len(window_handles) < 3:  # 윈도우가 모두 뜨지 않았을 경우 대기
                for x in range(15):
                    logt(f"윈도우 수량이 3개가 될때까지 대기, 현재 윈도우 갯수 = {len(window_handles)}")
                    time.sleep(1)
                    window_handles = driver.window_handles
                    if len(window_handles) == 3:
                        break


            # 윈도우 상태 출력 (작업에 꼭 필요한 것은 아님)
            #sc.print_window_by_title(driver)
            driver.switch_to.window(window_handles[1])
            logt("팝업 윈도우 타이틀 확인 #1 : title= %s" % driver.title)
            if (driver.title == "신고서미리보기") :
                # 작업 진행 윈도우가 맞음, 다만 다른 윈도우를 닫아야 함
                try :
                    driver.switch_to.window(window_handles[2])
                    logt("팝업 윈도우 타이틀 확인 #2 (닫아야 할 윈도우) : title= %s" % driver.title)
                    driver.close()
                except Exception as e:
                    logt("window_handles[2] 윈도우 close실패 <-- 정상")

                driver.switch_to.window(window_handles[1])
                logt("팝업 윈도우 타이틀 확인 #3 (작업 윈도우 복귀) : title= %s" % driver.title)
            else :
                logt("불필요한 윈도우 닫기 : title= %s" % driver.title)
                driver.close()

                window_handles = driver.window_handles
                logt("현재 윈도우 갯수 (예상되는 정상수량은 2) : 갯수= %d" % len(window_handles))
                
                driver.switch_to.window(window_handles[1])
                logt("팝업 윈도우 타이틀 확인 #4 (작업 윈도우 전화) : title= %s" % driver.title)

            logt("현재의 작업 윈도우 title= %s" % driver.title, 1)
            driver.set_window_position(0,0)
            driver.set_window_size(1140, 1140)

            # 파일다운로드
            file_type = "1"
            download_file(driver, git_info, file_type)
            
            # # 윈도우 클로우즈
            driver.close()

        except Exception as e:
            raise BizException(f"[납부서] 다운로드 에러 - {e}")

            
        # 원래 조회 윈도우로
        logt("초기 윈도우로 이동", 0.5)
        driver.switch_to.window(default_window_handle)
        driver.set_window_position(0,0)

        logt("작업프레임 이동: txppIframe", 0.5)
        driver.switch_to.frame("txppIframe")                

        # -----------------------------------------------------------------
        # 접수증 (홈택스)
        # -----------------------------------------------------------------
        logt('# -----------------------------------------------------------------')
        logt('#                        2) 접수증                                 ')
        logt('# -----------------------------------------------------------------')

        try:
            logt("접수증 [보기] 클릭", 1)
            driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(11+offset)+ " > span > button").click()
            
            logt("윈도우 로딩 대기", 1)
            window_handles = driver.window_handles
            logt(f"윈도우 갯수= {len(window_handles)}") 
            if len(window_handles) == 1:
                logt("접수증 [보기] 클릭(재시도)", 0.1)
                driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(11+offset)+ " > span > button").click()

                logt("윈도우 전환 재시도", 2) 
                window_handles = driver.window_handles
                if len(window_handles) == 1:
                    logt("윈도우 전환 실패 => 재시도 :윈도우 갯수={len(window_handles)}") 
                    raise BizException("[접수증] 윈도우 전환 실패 - {e}")
            
            # 정상 진행
            logt(f"윈도우 갯수= {len(window_handles)}") 
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)
            driver.set_window_size(850, 860)

        except Exception as e:
            raise BizException(f"[접수증] 윈도우 전환 실패 - {e}")
        
        # 파일다운로드: 
        file_type = "2"
        download_file(driver, git_info, file_type)
        
        driver.close()


        # 원래 조회 윈도우로
        logt("초기 윈도우로 이동", 0.5)
        driver.switch_to.window(default_window_handle)
        driver.set_window_position(0,0)

        logt("작업프레임 이동: txppIframe", 0.5)
        driver.switch_to.frame("txppIframe")              

        logt('# -----------------------------------------------------------------')
        logt('#                        3) 납부서                                 ')
        logt('# -----------------------------------------------------------------')


        # 주의) 납부서가 없을 수 있음
        logt("납부서 [보기] 클릭", 1)
        driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(12+offset)+ " > span > button").click()
        time.sleep(1.5)
        try:
            alert = driver.switch_to.alert
            if alert.text.find("개인지방소득세를 별도 신고해야 합니다") >= 0:
                logt("Alert Text = " + alert.text)
                alert.accept()
            else:
                raise BizException("Alert 오류1", f"{e}")
        except Exception as e:                
            logt(f"{e}")

        try :
            time.sleep(0.2)
            alert = driver.switch_to.alert
            if alert.text.find("종합소득세 납부할금액이 없습니다") >= 0:
                logt("Alert Text = " + alert.text)
                alert.accept()
                
                time.sleep(0.2)
                alert = driver.switch_to.alert
                if alert.text.find("지금 개인지방소득세 신고하기로 이동하시려면") >= 0:
                    logt("Alert Text (dismiss) = " + alert.text)
                    alert.dismiss()
                
            else:
                raise BizException("납세액이 있는 경우 정상적이 케이스", "")
        except Exception as e:

            # =================================================================================
            # 납부액이 있는 경우에만 납부서 다운로드
            # =================================================================================
            logt("납부서가 있는 경우로 정상 과정")


            # 납부서 기본 -------------------------------------------
            try :
                sc.move_iframe(driver, 'UTERNAAZ68_iframe')
                
                #홈택스에 신고된 납부세액
                logt("홈택스에 신고된 납부세액 조회", 0.5)
                hometax_income_tax = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1 > span").text
                if len(hometax_income_tax) > 0:
                    납부할금액 = hometax_income_tax.strip().replace(',', '')
                    dbjob.update_git_hometaxIncomeTax(git_seq, 납부할금액)
                    

                logt("납부서 이미지 클릭", 0.2)
                driver.find_element(By.ID, "ttirnal111DVOListDes_cell_0_3").click()

                logt("윈도우 로딩 대기", 2)
                window_handles = driver.window_handles
                if len(window_handles) == 1:
                    logt("납부서 클릭(재시도)", 0.1)
                    driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_3 > img").click()

                    logt("윈도우 전환 재시도", 2) 
                    window_handles = driver.window_handles
                    if len(window_handles) == 1:
                        logt("윈도우 전환 실패 => 재시도 :윈도우 갯수={len(window_handles)}") 
                        raise BizException("[납부서] 윈도우 전환 실패 - {e}")
                    else:
                        driver.switch_to.window(window_handles[1])
                        driver.set_window_position(0,0)
                        driver.set_window_size(810, 880)

                # 정상진행
                logt(f"윈도우 갯수= {len(window_handles)}") 
                driver.switch_to.window(window_handles[1])
                driver.set_window_position(0,0)
                driver.set_window_size(810, 880)
                
                # 파일다운로드:
                file_type = "3"
                download_file(driver, git_info, file_type)

        
                logt(f"팝업윈도우 닫고 => 메인윈도우 전환")     
                driver.close()                
                
                # 원래 조회 윈도우로
                logt("초기 윈도우로 이동", 0.5)
                driver.switch_to.window(default_window_handle)
                driver.set_window_position(0,0)

                logt("작업프레임 이동: txppIframe", 0.5)
                driver.switch_to.frame("txppIframe")              
                time.sleep(0.2)
                sc.move_iframe(driver, 'UTERNAAZ68_iframe')                
                
                # 팝업레이어 닫기
                logt("팝업레이어 닫기", 1.5)
                # (주의)닫기(trigger1)는 문서내 2개 있음.. 팝업창의 x 클릭으로 대체
                try:
                    driver.find_element(By.ID, "trigger2").click()
                    logt("Alert 창 대기", 0.5)

                    time.sleep(0.2)
                    alert = driver.switch_to.alert
                    if alert.text.find("지금 개인지방소득세 신고하기로") >= 0:
                        logt("Alert Text (dismiss) = " + alert.text)
                        alert.dismiss()
                    else:
                        raise BizException("Alert 오류4")

                    
                except:
                    logt("팝업레이어 닫기 오류", 1)                
                # =================================================================================
                # =================================================================================
                
            except Exception as e:
                raise BizException("납부서", f"{e}")


    else :
        # 접수된 신고가 없음
        step_cd = git_info['step_cd']
        au1 = git_info['au1']
        if step_cd == "REPORT" and au1 == "S":
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', '신고가 존재하지 않습니다. 재신청 하시기 바랍니다.')
            raise BizException("미제출", "신고서가 제출되지 않았습니다.")




if __name__ == '__main__':
    main()

