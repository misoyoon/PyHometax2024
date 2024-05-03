from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
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

au_step = "0"
AU_X    = f"au{au_step}"
group_id = 'wize'
dbjob.set_global(group_id, None, None, None, au_step)

def main():
    host_name = config.HOST_NAME
    conn = dbjob.connect_db()

    # (전체자료 업데이트) 신고안내문
    
    # 작업대상 목록
    # #############################################################
    git_infos = dbjob.select_auto_0(group_id)
    # #############################################################
    
    if len(git_infos) == 0:
        logt("진행할 작업이 없습니다. 프로그램을 종료합니다.")
        sys.exit()
    else:
        logt(f"홈택스 종합소득세 파일다운로드 작업 ::: 총 실행 건수 = {len(git_infos)}")
        
        
    driver: WebDriver = auto_login.init_selenium()
    driver.set_window_size(1300, 1150)
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


        login_info = {}
        login_info['name'] = git_info['nm']
        login_info['login_id'] = git_info['hometax_id']
        login_info['login_pw'] = git_info['hometax_pw']
        
        if git_info['hometax_id_confirm'] != 'Y':
            logt("이전에 로그인에 실패하였습니다.  홈택스ID/PWD를 확인 후 다시 시도하세요")
            
        
        # 자동로그인 처리
        logt("로그인 시간", 1)
        auto_login.login_guest(driver, login_info)
        logt("로그인 완료")
        
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
                logt("비밀번호 오류로 다음 차례 진행 ~~~~~~~~")
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
        try:
            sc.click_button_by_id(driver, 'prcpSrvcMenuA0', '종합소득세 이미지', 1)
            time.sleep(1)
        except Exception as e:
            # 비빌번호 변경으로 뜬 경우
            dbjob.update_git_hometaxIdConfirm(group_id, git_seq, 'C')

        # 종합소득세
        try:
            driver.switch_to.frame("txppIframe")
            sc.click_button_by_id(driver, 'sub_a_2602000000', '종합소득세 신고도움 서비스', 1)
        except Exception as e:
            loge("[종합소득세 신고도움 서비스]가 없습니다.")
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'X', '[종합소득세 신고도움 서비스]가 없습니다')
            logout(driver)
            continue

            
        try:
            logt("Alert 확인", 1)
            #alert = driver.switch_to.alert
            alert = driver.switch_to.alert
            alert_msg = alert.text
            logt("Alert메세지: %s" % alert_msg)

            if alert_msg.find("신고도움 자료가 제공되지 않더라도 실제") >= 0  :   # 비밀번호가 [3]회 잘못 입력되었습니다
                alert.accept()
                
        except Exception as e:
            ...

        time.sleep(1)

        try:
            기장의무구분_text = driver.find_element(By.ID, 'group10040').text
            # 미분류 일 경우만 변경
            if 기장의무구분_text.find('간편장부')>=0:
                dbjob.update_git_기장의무구분(group_id, git_seq, 'S')
            elif 기장의무구분_text.find('복식부기')>=0:
                dbjob.update_git_기장의무구분(group_id, git_seq, 'D')
        except:
            # 간혹 아무런 정보가 없는 사람은 이쪽으로 옴
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', '기장의무를 판단하지 못했습니다.')
            continue
        
        # 신고안내자료 탭 클릭
        driver.find_element(By.ID, 'tabControl1_tab_tabs3').click()
        time.sleep(0.3)

        # 리스트 목록
        rows = driver.find_elements(By.CSS_SELECTOR, '#gridList2018_body_tbody > tr')

        # 이전 리스트 삭제
        dbjob.delete_신고안내_소득리스트(group_id, git_seq)

        git_list_info = {}
        try:
            for row in rows:
                cols = row.find_elements(By.CSS_SELECTOR, 'td > span')

                git_list_info['사업자번호']         = cols[0].text
                git_list_info['상호']               = cols[1].text
                git_list_info['수입종류_구분코드']  = cols[2].text
                git_list_info['업종코드']           = cols[3].text
                git_list_info['수입금액']           = to_number(cols[4].text)
                #git_list_info['사업형태']           = cols[5].text
                git_list_info['기장의무']           = cols[6].text
                git_list_info['경비율']             = cols[7].text 
                git_list_info['기준경비율_일반']    = cols[8].text.replace('%', '')
                git_list_info['기준경비율_자가']    = cols[9].text.replace('%', '')
                git_list_info['단순경비율_일반']    = cols[10].text.replace('%', '')
                git_list_info['단순경비율_자가']    = cols[11].text.replace('%', '')
                git_list_info['주요원천징수의무자'] = cols[12].text

                dbjob.insert_신고안내_소득리스트(group_id, git_seq, git_list_info)
        except Exception as e:
            # 소득리스트가 없을 경우 이쪽으로 온다
            logt("사업장 수입금액 없습니다.")


        총계row = driver.find_elements(By.CSS_SELECTOR, '#gridList2018_foot_table > tbody > tr > td')   
        총수입금액 = to_number(총계row[1].text)
        dbjob.update_git_column_val(group_id, git_seq, 'income_amount', 총수입금액)

        소득공제_원천징수세액   = to_number(driver.find_element(By.ID, 'textbox29671').text)
        소득공제_국민연금보험료 = to_number(driver.find_element(By.ID, 'textbox2964').text)
        사업소득외_근로_단일 = driver.find_element(By.ID, 'textbox76165').text
        사업소득외_근로_복수 = driver.find_element(By.ID, 'textbox76166').text
        사업소득외_기타      = driver.find_element(By.ID, 'textbox76168').text

        근로소득 = 사업소득외_근로_단일 + 사업소득외_근로_복수
        if 근로소득.find('O') >= 0:
            dbjob.update_git_column_val(group_id, git_seq, 'earned_income_yn', 'Y')
        else:
            dbjob.update_git_column_val(group_id, git_seq, 'earned_income_yn', 'N')

        # 원천징수세액
        dbjob.update_git_column_val(group_id, git_seq, 'holding_tax', 소득공제_원천징수세액)




        # ---------------------------------------------------
        # 파일 타입
        attach_type = '0' 
        download_file_name = git_file.get_file_name_by_type(attach_type)

        # 이전 파일 타입 삭제 후 추가
        delete_file(git_info['git_seq'], download_file_name)


        # '미리보기' 누르고 다운로드 받기
        sc.click_button_by_id(driver, 'trigger1', '미리보기', 1)
        time.sleep(2.5)    
        ret_val = download_file(git_info, attach_type)


        logt("다른 오픈된 윈도우 닫기")
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

        
    

def delete_file(git_seq, filename):
    work_dir = git_file.get_dir_by_gitSeq(git_seq)

    try:
        os.remove(work_dir + filename)
    except OSError as e:
        ...

# 사용안함
def capture_screen(driver, git_info, filename, attach_type):
    work_dir = git_file.get_dir_by_gitSeq(git_info['git_seq'])
    fullpath = work_dir + filename
    time.sleep(1.5)
    driver.save_screenshot(fullpath)
    logt(f"화면 캡쳐 경로={fullpath}")
    
    dic_git_file = git_file.make_file_data(git_info['group_id'], git_info['git_seq'], git_info['nm'], attach_type, True )
    logt(f"화면 캡쳐 정보={dic_git_file}")
    
    dbjob.insert_git_file(dic_git_file)



def download_file(git_info, attach_type):
    time.sleep(1)
    git_seq = git_info['git_seq']
    #guest_nm = git_info['nm']
    filename = git_file.get_file_name_by_type(attach_type)
    # file_type별 파일이름 결정
    dir_basic = git_file.get_dir_by_gitSeq(git_seq)  # True => 폴더 생성
    fullpath = dir_basic + filename
    logt("------------------------------------------------------")
    logt(f"파일다운로드: Filepath: {fullpath}")
    logt("------------------------------------------------------")

    # 이미지 리소스 폴더
    resource_dir = os.path.dirname(os.path.abspath(__file__))  #os.path.dirname(sys.modules['__main__'].__file__)
    if resource_dir:
        resource_dir = resource_dir + os.sep + "..\\pyHometax\\resource\\"


    # --------------------------------
    img_print_path = resource_dir + "img_printer.png"
    logt(f"GUI Click: 프린터아이콘 = {img_print_path}", 1)
    time.sleep(0.5)

    # 이미지의 위치를 찾을 때까지 반복 시도 클릭
    pyautoui_image_click(img_print_path)

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
            time.sleep(600)


    # 이미 존재하면 삭제
    if os.path.isfile(fullpath):
        os.remove(fullpath)

    # [인쇄] 버튼 클릭
    logt("GUI Click: [인쇄]", 5)   #  2023년 상당히 느리게 동작하고 있음
    #img_save_path = resource_dir + "print_blue.png"
    img_save_path = resource_dir + "btn_blue_save.png"
    pyautoui_image_click(img_save_path)

    # 다운로드 팝업창 뜨기 => 여기도 경우에 따라 시간이 좀 걸림
    logt(f"다운로드 팝업창 뜨기")
    time.sleep(5)

    try:
        logt(f"다른이름 저장하기 (경로명 입력) pyautogui.typewrite= {fullpath}")
        pyautogui.typewrite(fullpath)
        time.sleep(0.2)
        pyautogui.press('enter')   # 저장하기 위해 파일경로 넣고 엔터치기

        time.sleep(4)
        if os.path.isfile(fullpath):
            logt(f"파일저장 성공: 파일타입= %s, 경로={fullpath}")
            logt("파일저장 확인완료 => DB 입력하기")
            file_size = os.path.getsize(fullpath)
            print(f"!!!!!!!! filesize 1= {file_size}")

            # if file_size > 0: 
            dic_git_file = git_file.make_file_data(git_info['group_id'], git_info['git_seq'], git_info['nm'], attach_type, False )
            git_file_seq = dbjob.insert_git_file(dic_git_file)
            if git_file_seq > 0:
                dbjob.update_git_column_val(group_id, git_seq, f"result{attach_type}_file_seq", git_file_seq)
            #     return True
            # else:
            #     dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', 'file size is not found')
            #     return False
        else:
            logt(f"파일저장 확인실패 fullpath={fullpath}")
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', 'file size is not found')
            

    except Exception as e:
        dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', e)
        logt("Exception 발생")
        #time.sleep(600)
        return False

    return True

# ------------------------------------------------------------------------------
# 이미지의 위치를 찾을 때까지 반복 시도 후 찾으면 해당 이미지 클릭
def pyautoui_image_click(img_path):
    for retry in range(6):
        # confidence인식 못하는 오류 : pip install opencv-python
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)
        logt(f'pyautoui_image_click() : filepath={img_path}, center={center}')

        if center == None :
            time.sleep(0.5)
            logt(f"        이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            time.sleep(0.3) # 0.3초후 클릭
            pyautogui.click(center)
            logt(f"        이미지 영역 찾기 완료 => Click : {img_path}")
            return True

    #time.sleep(100000)
    return False
    
    


if __name__ == '__main__':
    main()
