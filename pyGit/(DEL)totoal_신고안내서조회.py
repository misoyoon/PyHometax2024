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
AU_X    = 'au0'
group_id = 'wize'
dbjob.set_global(group_id, None, None, None, au_step)


def main(git_seq):

    host_name = config.HOST_NAME
    conn = dbjob.connect_db()

    git_infos = dbjob.select_git_for_au0(group_id)
    logi(f"총 실행 건수 = {len(git_infos)}")
    if len(git_infos) == 0:
        logi("작업할 내용이 없습니다. 프로그램을 종료합니다.")
        return


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
        
        if git_info['hometax_id'] == 'N':
            logi("이전에 로그인에 실패하였습니다.  홈택스ID/PWD를 확인 후 다시 시도하세요")
            
        
        # 자동로그인 처리
        logt("로그인 시작", 1)
        auto_login.login_guest(driver, login_info)
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
        
        dbjob.update_git_hometaxIdConfirm(group_id, git_seq, 'Y')

        
        # 팝업 창이 있으면 모두 닫기
        if len(driver.window_handles) > 1:
            for i in range(len(driver.window_handles)-1, 0, -1):
                driver.switch_to.window(driver.window_handles[i])
                driver.close()
                
            driver.switch_to.window(driver.window_handles[0])
        
        
        # ---------------------------------------------------

        sc.click_button_by_id(driver, 'prcpSrvcMenuA0', '종합소득세 이미지', 0.5)
        time.sleep(1)
        

        # 종합소득세
        try :
            driver.switch_to.frame("txppIframe")
            sc.click_button_by_id(driver, 'sub_a_2602000000', '종합소득세 신고도움 서비스', 1)
        except Exception as e:
            loge("[종합소득세 신고도움 서비스]가 없습니다.")
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', '[종합소득세 신고도움 서비스]가 없습니다')
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

        # ---------------------------------------------------
        # 파일 타입
        attach_type = 'guide' 
        
        # 이전 파일 타입 삭제 후 추가
        dbjob.delete_git_file_by_attachType(git_info['group_id'], git_info['git_seq'], attach_type)
        delete_file(git_info['git_seq'], "신고안내문_화면1.png")
        delete_file(git_info['git_seq'], "신고안내문_화면2.png")
        delete_file(git_info['git_seq'], "report_guide.pdf")
        

        # 여기서 캡처하고 저장하기
        capture_screen(driver, git_info, "신고안내문_화면1.png", attach_type)
        
        # 조회하기 버튼 클릭
        sc.click_button_by_id(driver, 'tabControl1_tab_tabs3', '신고 안내자료',1)
        time.sleep(1)

        # 여기서 캡처하고 저장하기
        capture_screen(driver, git_info, "신고안내문_화면2.png", attach_type)
        
        # 미리보기
        sc.click_button_by_id(driver, 'trigger1', '미리보기', 1)
        time.sleep(2.5)    
        
        ret_val = file_download(git_info, "report_guide.pdf", attach_type)

        if ret_val:
            # 여기까지 오면 성공이라 판단하고 마킹하기
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'S')

            

        logi("윈도우 닫기")
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # 로그아웃
        logout(driver)  
    # end for   
        
def logout(driver):
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
    work_dir = git_file.get_work_dir_by_gitSeq(git_seq)

    try:
        os.remove(work_dir + filename)
    except OSError as e:
        ...


def capture_screen(driver, git_info, filename, attach_type):
    work_dir = git_file.get_work_dir_by_gitSeq(git_info['git_seq'])
    fullpath = work_dir + filename
    time.sleep(1.5)
    driver.save_screenshot(fullpath)
    logi(f"화면 캡쳐 경로={fullpath}")
    
    dic_git_file = git_file.make_file_data(git_info['group_id'], git_info['git_seq'], git_info['nm'], attach_type, filename, True )
    logi(f"화면 캡쳐 정보={dic_git_file}")
    
    dbjob.insert_git_file(dic_git_file)



def file_download(git_info, filename, attach_type):
    time.sleep(1)
    git_seq = git_info['git_seq']
    #guest_nm = git_info['nm']
    
    # file_type별 파일이름 결정
    dir_work = git_file.get_work_dir_by_gitSeq(git_seq)  # True => 폴더 생성
    fullpath = dir_work + filename
    logi("------------------------------------------------------")
    logt(f"파일다운로드: Filepath: {fullpath}")
    logi("------------------------------------------------------")

    # 작업폴더
    project_dir = os.getcwd() + os.sep + 'pyHometax' #os.path.dirname(sys.modules['__main__'].__file__)
    if project_dir:
        project_dir = project_dir + os.sep


    # --------------------------------
    img_print_path = project_dir  + "resource" + os.sep + "img_printer.png"
    logt(f"GUI Click: 프린터아이콘 = {img_print_path}", 1)
    time.sleep(0.5)

    # 이미지의 위치를 찾을 때까지 반복 시도 클릭
    pyautoui_image_click(img_print_path)

    # [인쇄] 클릭
    logt("GUI Click: [인쇄-회색버튼]", 1)
    btn_print_path = project_dir  + "resource" + os.sep + "btn_print_gray.png"
    logt("img_print_path=" + btn_print_path)
    ans = pyautoui_image_click(btn_print_path)
    if ans == False:
        # 상단 프린터A 누르기
        logi("상단 프린터A 누르기 (재시도)")
        pyautoui_image_click(img_print_path)
        time.sleep(0.5)
        ans = pyautoui_image_click(btn_print_path)
        if ans == False:
            logi("회색 인쇄버튼 클릭 실패(재시도)")
            time.sleep(600)


    # 이미 존재하면 삭제
    if os.path.isfile(fullpath):
        os.remove(fullpath)

    # [인쇄] 버튼 클릭
    logt("GUI Click: [인쇄]", 3)   #  2023년 상당히 느리게 동작하고 있음
    img_save_path = project_dir  + "resource" + os.sep + "print_blue.png"
    pyautoui_image_click(img_save_path)

    # 다운로드 팝업창 뜨기 => 여기도 경우에 따라 시간이 좀 걸림
    logi(f"다운로드 팝업창 뜨기")
    time.sleep(4)

    try:
        logi(f"다른이름 저장하기 (경로명 입력) pyautogui.typewrite= {fullpath}")
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
            dic_git_file = git_file.make_file_data(git_info['group_id'], git_info['git_seq'], git_info['nm'], attach_type, filename, True )
            dbjob.insert_git_file(dic_git_file)
            #     return True
            # else:
            #     dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', 'file size is 0')
            #     return False
        else:
            logt(f"파일저장 확인실패 fullpath={fullpath}")
            dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', 'file size is not found')
            

    except Exception as e:
        dbjob.update_git_au_x(group_id, git_seq, AU_X, 'E', e)
        logi("Exception 발생")
        #time.sleep(600)
        return False

    return True

# ------------------------------------------------------------------------------
# 이미지의 위치를 찾을 때까지 반복 시도 후 찾으면 해당 이미지 클릭
def pyautoui_image_click(img_path):
    for retry in range(6):
        # confidence인식 못하는 오류 : pip install opencv-python
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)
        logi(f'pyautoui_image_click() : filepath={img_path}, center={center}')

        if center == None :
            time.sleep(0.5)
            logi(f"        이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            time.sleep(0.3) # 0.3초후 클릭
            pyautogui.click(center)
            logt(f"        이미지 영역 찾기 완료 => Click : {img_path}")
            return True

    #time.sleep(100000)
    return False
    
    


if __name__ == '__main__':
    git_seq = 1
    if len(sys.argv) == 1:
        logi("git_seq가 없습니다.")
        #exit()
    else:
        git_seq = sys.argv
        
    main(git_seq)
    
    logi("프로그램 종료")
    sys.exit()