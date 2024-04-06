from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import shutil
import time
import os
import traceback
import math
import pyautogui

import config

from common import *
import dbjob
import git_file
import auto_login 
import git_auto_step_4


# 작업4단계 : 위택스 다운로드
au_step = "4"
AU_X    = f"au{au_step}"
group_id = 'wize'
dbjob.set_global(group_id, None, None, None, au_step)

TAX_NAME = "지방소득세(양도소득세분)"
url = 'https://www.wetax.go.kr/simple/?cmd=LPEPBZ4R0'


# 이미지 리소스 폴더
resource_dir = os.path.dirname(os.path.abspath(__file__))  #os.path.dirname(sys.modules['__main__'].__file__)
if resource_dir:
    resource_dir = resource_dir + os.sep + "..\\pyHometax\\resource\\"


print(f"이미지 resource Dir =[{resource_dir}]")




def main():
    print("4단계 : 위택스 파일 다운로드")
    dbjob.connect_db()

    # 작업대상 목록
    # #############################################################
    git_infos = dbjob.select_auto_4(group_id)
    # #############################################################

    if len(git_infos) == 0:
        logi("작업할 리스트가 없습니다. 작업종료")    
        sys.exit()
    
    try:
        driver = auto_login.init_selenium()
        driver.set_window_size(1200, config.BROWSER_SIZE['height'])
        print("위택스 이동")
        driver.get(url)  

        time.sleep(1)
        print("오늘은 무시 - 체크하기")
        driver.find_element(By.CSS_SELECTOR, '#nos_pop > div.pop_foot > label > span').click()
        time.sleep(0.1)
        print("닫기 클릭")
        driver.find_element(By.CSS_SELECTOR, '#nos_pop > div.pop_foot > a').click()
        time.sleep(0.1)

        for k in range(len(git_infos)) :
            git_info = git_infos[k]
            
            git_seq = git_info['git_seq']
            nm = git_info['nm'] 
            
            # 이전 저장 파일 초기화
            #dbjob.update_git_au4_reset(git_seq)

            print("================================================================================")
            print("%d / %d :: git_seq= %s , Name= %s , ssn1= %s , ssn2= %s , hometax_reg_num= %s " % 
                    (k+1, len(git_infos), git_seq, nm, git_info['ssn1'], git_info['ssn2'], git_info['hometax_reg_num']))
            print("================================================================================")
            i = 0
            loop_to = 1
            is_search = True

            
            # ---------------------------
            dir_work = git_file.get_dir_by_gitSeq(git_seq)
            
            dbjob.set_global(group_id, 'AUTOSVR', '', git_seq, au_step)
            # ---------------------------

            # 낼 세금이 없으면 다음작업 => 세금이 없어도 신고
            # hometax_income_tax = git_info['hometax_income_tax']
            # if hometax_income_tax is None :
            #     logt("세금없음 => 다음 작업 진행")
            #     dbjob.update_git_AuX(au_step, git_seq, 'Z', '지방세없음')
            #     continue

            # 양도인별 최초로 미납인 항목 => 파일다운로드 처리
            # 다만 복수개의 미납이 있는지 여부확인을 위해 모든 신고내역을 조회 => WARN으로 au_history에 쓰기
            is_first_found = False

            while True:

                i += 1
                strI = str(i)
                logt ("(job No=%d) : 개인처리수= %d / %d 시도중 ...." % (k, i, loop_to))


                # --------------------------------------
                if is_search == True:
                    driver.get(url)
                    time.sleep(1)


                    driver.find_element(By.ID, 'regNoFront').send_keys(git_info['ssn1'])
                    time.sleep(0.1)
                    driver.find_element(By.ID, 'regNoEnd').send_keys(git_info['ssn2'])
                    time.sleep(0.3)
                    driver.find_element(By.ID, 'taxSeq').send_keys(git_info['hometax_reg_num'])
                    time.sleep(0.3)

                    logi(f"주민번호= {git_info['ssn1']}-{git_info['ssn2']}, 홈택스 접수번호= {git_info['hometax_reg_num']}")
                    elements = driver.find_elements(By.CSS_SELECTOR, '.searchBtn')
                    #print(elements)
                    elements[0].click() # 첫번째 것을 조회버튼으로 인식

                    time.sleep(0.5)
                    e_trs = driver.find_elements(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr')
                    loop_to = len(e_trs)

                    print("조회결과 수 = %s" % loop_to)
                    if loop_to == 1:
                        if e_trs[0].text.find("검색 조건과 일치하는 신고내역이 없습니다") >=0 :
                            # 신고내역 없음
                            dbjob.update_git_AuX(au_step, git_seq, 'E', '신고내역없음')
                            break
                
                    # 조회 결과 분석: 만약1이면 조회 결과 없음으로 다음 사람 조회
                    #if loop_to == 0:
                    #    print("세금없음 (정상처리)=> 다음 작업 진행")
                    #    dbjob.update_git_AuX(au_step, git_seq, 'Z', '지방세없음')
                    #    continue
                # --------------------------------------

                # 신고갯수
                if i > loop_to:
                    break


                # 양도자명
                e_name = None
                try :
                    # 결과가 하나이거나 결과가 없거나 이곳으로 이동 => 원하는 엘리먼트가 없으면 다음으로 이동
                    e_name = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(2)')
                except:
                    dbjob.update_git_AuX(au_step, git_seq, 'E', '신고내역없음')
                    continue
                    
                i_name = e_name.text.strip()

                logi(f"[이름 비교] 작업 예상 이름:현재 결과조회 이름 => {git_info['nm']}:{i_name}")
                if git_info['nm'] != i_name:
                    raise BizException("이름이 달라서 건너뛰기")

                # 세금 항목명
                e_tax_name = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(6)')
                i_tax_name = e_tax_name.text.strip()


                e_tax_name = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(7)')
                i_tax_name = e_tax_name.text.strip()

                # 지방소득세  wetax_income_tax
                e_tax = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(7)')
                logt("지방소득세= " + e_tax.text)
                wetax_income_tax_text = e_tax.text.replace(",", "").replace("원", "").strip()
                wetax_income_tax = int(wetax_income_tax_text)
                dbjob.update_git_column_val(git_info['group_id'], git_seq, 'wetax_income_tax', wetax_income_tax)

                #  전자납부번호 
                e_reg_num = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(5)')
                wetax_reg_num = e_reg_num.text.strip()
                dbjob.update_git_WetaxRegNum(git_seq, wetax_reg_num)

                # 미납/취소
                e_ispay = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(9)')
                ispay = e_ispay.text.replace(",", "").strip()
                


                #상세페이지 이동을 위한 click
                driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(5)').click()
                # 대기
                time.sleep(1)

                # -------------------------------------------|
                # 신고서
                download_doc_type(driver, git_info, "2", "4")
                download_doc_type(driver, git_info, "3", "5")
                if wetax_income_tax>=0 and ispay=='미납':
                    download_doc_type(driver, git_info, "4", "6")
                # -------------------------------------------|

                dbjob.update_git_au_x(group_id, git_seq, AU_X, 'S')

                # 우선 결과가 하나일 경우를 가정해서 break
                break

            # END <while>

            print("한줄처리 완료 --------------------------------------")
            time.sleep(0.2)

        # EOWhile

    except Exception as e:
        print(e)
        traceback.print_exc()

    else :
        print("===========정상종료 ")

    driver.close()




def download_doc_type(driver, git_info, button_index, attach_type):
    # 납부서출력 버튼 ----------------------------------------------------------------------------------------------------------
    print("납부서출력 버튼")
    driver.find_element(By.CSS_SELECTOR, f'#sendForm > div.btn_wrap > ul > li.float_l > a:nth-child({button_index})').click()


    time.sleep(1)
    print("윈도우 핸들 1")
    window_handles = driver.window_handles
    print (window_handles)


    # 윈도우오픈 확인 실패시 재시도
    if len(window_handles) == 1:
        print("윈도우 핸들 2 => 재시도")
        time.sleep(1)
        window_handles = driver.window_handles

    if len(window_handles) == 2:
        print("팝업 윈도우 오픈 확인")


    time.sleep(2)

    #img_save_path = resource_dir + "internet.png"
    try:
        print("화면끝으로 이동")
        #pyautoui_image_click(img_save_path)
        pyautogui.click(x=200, y=400)
        time.sleep(0.2)
        pyautogui.press('esc')
        #pyautogui.press('end')
    except Exception as e:
        try:
            print("화면끝으로 이동 재시도")
            #pyautoui_image_click(img_save_path)
            pyautogui.click(x=200, y=400)
            time.sleep(0.2)
            #pyautogui.press('esc')
            pyautogui.press('end')
        except Exception as e:
            print(f"화면캡쳐 오류  => 프로그램 종료 : {e}")
            sys.exit()

    time.sleep(0.5)
    driver.switch_to.window(driver.window_handles[1])
    #print("팝업 윈도우 크기/위치 이동")
    # 브라우저 화면 크기 변경하기
    driver.set_window_size(810, 900)
    driver.set_window_position(0,0)

    print("윈도우 타이틀= " + driver.title)

    try :
        # ----------------------------------------------------
        download_file(driver, git_info, attach_type)
        # ----------------------------------------------------

        print("팝업윈도우 close()")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])   
    except Exception as e:
        logt("파일저장 확인실패!!!!! => 실패처리 후 다음 건 처리")
        dbjob.update_git_AuX(AU_STEP, git_seq, 'E', f'파일저장실패-{e}')
        
        print("팝업윈도우 close()")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])   
        




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
    logi("------------------------------------------------------")
    logt("파일다운로드: attach_type=%s, Filepath=%s" % (attach_type, fullpath))
    logi("------------------------------------------------------")

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
            logi("상단 프린터A 누르기 (재시도)")
            pyautoui_image_click(img_print_path)
            time.sleep(0.5)
            ans = pyautoui_image_click(btn_print_path)
            if ans == False:
                raise BizException(f"상단 프린터A 누르기 ERROR, path={img_save_path}")



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
    found_ok = pyautoui_image_click(img_save_path)
    if not found_ok:
        raise BizException(f"블루 저장버튼 찾기 ERROR, path={img_save_path}")

    # 다운로드 팝업창 뜨기 => 여기도 경우에 따라 시간이 좀 걸림
    logi(f"다운로드 팝업창 뜨기 : attach_type = {attach_type}")
    
    # if not attach_type == "1":
    #     logt("단순대기", 10.0)
    # else:
    #     logt("단순대기", 3.0)
    

    try:
        # 저장 버튼이 보일 때까지 대기
        img_save_path = resource_dir + "save.png"
        is_found = pyautoui_image_wait(img_save_path)
        if not is_found:
            raise BizException(f"[다른이름으로 저장하기] 노출오류, path={img_save_path}")
        
        
        logi(f"다른이름 저장하기 (경로명 입력) pyautogui.typewrite= {fullpath}")
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
        logi(e)
        logi("오류로 프로그램 종료대기 600초")
        time.sleep(600)





# ------------------------------------------------------------------------------
# 이미지의 위치를 찾을 때까지 반복 시도 후 찾으면 해당 이미지 클릭
def pyautoui_image_click(img_path):
    for retry in range(6):
        # confidence인식 못하는 오류 : pip install opencv-python
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)
        logi(f'pyautoui_image_click() : filepath={img_path}, center={center}')

        if center == None :
            pyautogui.moveTo(10,10)  # 일부러 마우스 움직이기
            time.sleep(0.5)
            logi(f"        이미지 클릭 재시도: {img_path} : retry={retry}")
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
            logi(f"이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            logt(f"이미지 영역 찾기 완료 : {img_path}, center={center}")
            return True
    return False



if __name__ == '__main__':
    main()
    exit(0)    