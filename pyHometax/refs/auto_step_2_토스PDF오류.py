import time
import os

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
#from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoAlertPresentException


import pyautogui
import pyperclip
import traceback

from common import *
import ht_file
import dbjob
import pyHometax.common_sele as sc
import auto_step_1
import config


#마우스가 모니터 사각형 모서리에 가는 경우 발생하는 에러이다
pyautogui.FAILSAFE = False


# 자동신고단계 -----------------------------
au_stpe = 2

# def delete_old_file(ht_tt_seq):
#     # file_type별 파일이름 결정
#     logi("이전 파일 삭제 ---------")
#     dir_work = ht_file.get_dir_by_htTtSeq(ht_tt_seq)
#     del_files = [
#           "down1.pdf", "down2.pdf", "down3.pdf", "down4.pdf", "down8.pdf"
#         , "work\\capture_1.png", "work\\capture_2.png", "work\\capture_3.png", "work\\capture_4.png", "work\\capture_8.png"
#     ]

#     for f in del_files:
#         fullpath = dir_work + f
#         if os.path.isfile(fullpath):
#             logi("이전 파일 삭제 : %s" % fullpath)
#             os.remove(fullpath)

# Step 1. 세금신고 : 기본정보(양도인)
def do_step2(driver: WebDriver, group_id, jobs, user_id):

    window_handles = driver.window_handles
    main_window_handle = window_handles[0]
    logt("메인윈도우 핸들: %s" % main_window_handle)
    
    logt("페이지이동: '신고/납부' 메뉴 이동", 2)
    url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
    
    driver.get(url)
    
    logt("iframe 이동", 2)
    sc.move_iframe(driver)
    
    logt("클릭: 신고내역 조회(접수증,납부서)", 2)
    driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11').click()

    if len(jobs) == 0:
        logi("처리할 작업이 없습니다.. 작업종료")    

    # 양도자 반복처리      
    error_cnt = 0  # 연속 에러갯수      
    for job_idx in range(0, len(jobs)):

        if error_cnt > 0:
            loge("연속1회 에러로 작업을 중지 시킵니다.")
            driver.close()
            sys.exit()
            break

        # 담당자 홈택스로그인 가능 여부 확인용
        dbjob.update_user_cookieModiDt(user_id)

        ht_info = jobs[job_idx]
        ht_tt_seq = ht_info['ht_tt_seq']

        try :
            window_handles = driver.window_handles
            if len(window_handles) > 1:
                for w_handle in window_handles:
                    if w_handle != main_window_handle:
                        driver.switch_to.window(w_handle)
                        driver.close()

            # 메인 윈도우 선택
            driver.switch_to.window(main_window_handle)
        except:
            loge("브라우저가 닫힌거 같습니다.")
            exit(0)

        # logt함수를 db에 D:\WWW\JNK\files\hometax\001\001239\down1.pdf
        # 키기 위해서는 global에 ht_tt_seq를 넣어줘야한다.
        # set_global(group_id, v_host_name, v_user_id, v_ht_tt_seq, v_au_step):
        dbjob.set_global(group_id, None, user_id, ht_tt_seq, 2)

        # FIXME 이전 한글이름 파일 삭제  => 차후 삭제
        # FIXME 중요 여기 살리기 !!!!
        #delete_old_file(ht_tt_seq)
        dbjob.update_HtTt_au2_reset(ht_tt_seq)

        try:
            logt("%d / %d 처리 ..." % (job_idx+1, len(jobs)))        
            ht_info = jobs[job_idx]
            
            # ========================================================
            # 반복 구간
            # ========================================================
            do_step2_loop(driver, ht_info)
            # ========================================================
            # 반복 구간
            # ========================================================
        
        except BizException as e:
            logt("#################### except BizException")
            logi(e)
            if e.name == '미제출':  # 미제출건으로 해당 작업과는 무관하게 처리
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, None, None)

            elif e.name == "납부할금액없음":
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'S', e.msg)
                error_cnt = 0
            elif e.name == "조회결과없음" :
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', e.msg)
                error_cnt = 0
            elif e.name == "복수신고건":
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', e.msg)
                error_cnt = 0
            else:
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', e.msg)
                traceback.print_exc()
                error_cnt += 1
            

        except Exception as e:
            try :
                logt("#################### except Exception :" + e)
            except:
                pass

            logi(e)
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', f'{e}')
            traceback.print_exc()
            error_cnt += 1
        
        else:  # 오류없이 정상 처리시
            logt("#################### (정상처리)")
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'S', None)
            traceback.print_exc()
            error_cnt = 0

        # job 완료 처리 
        logt("####### 한건처리 완료 #######", 0.2)



# ------------------------------------------------------                
# 여기부터는 HTLM영역이 아닌 window프로그램 영역
# ------------------------------------------------------                
def file_download(ht_info, v_file_type):
    time.sleep(1)
    ht_tt_seq = ht_info['ht_tt_seq']
    holder_nm = ht_info['holder_nm']

    # file_type별 파일이름 결정
    dir_work = ht_file.get_dir_by_htTtSeq(ht_tt_seq, True)  # True => 폴더 생성
    fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
    logi("------------------------------------------------------")
    logt("파일다운로드: Type: %s, Filepath: %s" % (v_file_type, fullpath))
    logi("------------------------------------------------------")

    # 작업폴더
    project_dir = os.path.dirname(sys.modules['__main__'].__file__)
    if project_dir:
        project_dir = project_dir + os.sep


    # 이미지 캡쳐  -----------------
    cap_filename = "image"
    region=(0, 0, 10, 10)
    cap_filename = ht_file.get_file_name_by_type(v_file_type+"_CAP")

    if   v_file_type == "HT_DOWN_1": # 납부계산서
        region=(277, 300, 1050-277, 1100-300)
    elif v_file_type == "HT_DOWN_2": # 계산명세서
        region=(277, 300, 1050-277, 1100-300)
    elif v_file_type == "HT_DOWN_3":    # 접수증
        region=(10, 104, 800, 880-104)
    elif v_file_type == "HT_DOWN_4":   # 납부서    
        region=(0, 104, 800, 860-104)
    elif v_file_type == "HT_DOWN_8":    # 납부서2 (분납)
        region=(0, 104, 800, 860-104)
    elif v_file_type == "WE_DOWN_5":    # 위택스 납부서
        region=(10, 180, 810-20, 900-180)


    # 스크린 캡쳐
    capture_img_fullpath = dir_work + "work" + os.sep + cap_filename
    try :
        time.sleep(0.5)
        pyautogui.screenshot(capture_img_fullpath, region=region)
    except:
        logt("이미지캡쳐 오류 => 재시도", 0.5)
        pyautogui.screenshot(capture_img_fullpath, region=region)
        traceback.print_exc()
    
    time.sleep(0.2)
    if os.path.isfile(capture_img_fullpath):
        logt("이미지캡쳐 => DB 입력하기")
        dbjob.insert_or_update_upload_file(v_file_type+"_CAP", ht_tt_seq, holder_nm)
    else:
        logt("이미지캡쳐 확인실패!!!!!")
        raise BizException("캡쳐 이미지 파일저장 실패", fullpath)

    # --------------------------------
    img_print_path = project_dir  + "resource" + os.sep + "img_printer.png"
    logt(f"GUI Click: 프린터아이콘 = {img_print_path}", 1)
    time.sleep(0.5)

    # 이미지의 위치를 찾을 때까지 반복 시도 클릭
    pyautoui_image_click(img_print_path)

    # 접수증(HT_DOWN_3)의 경우 해당 버튼이 없어 단계 생략
    if not v_file_type == "HT_DOWN_3":
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
                time.sleep(1000000)


    # 이미 존재하면 삭제
    if os.path.isfile(fullpath):
        os.remove(fullpath)

    # [인쇄] 버튼 클릭
    logt("GUI Click: [인쇄]", 3.0)   #  2023년 상당히 느리게 동작하고 있음
    #img_save_path = project_dir  + "resource" + os.sep + "print_blue.png"
    img_save_path = project_dir  + "resource" + os.sep + "btn_blue_save.png"
    pyautoui_image_click(img_save_path)

    # 다운로드 팝업창 뜨기 => 여기도 경우에 따라 시간이 좀 걸림
    logi(f"다운로드 팝업창 뜨기 = {v_file_type}")
    time.sleep(3)

    # 파일 저장
    #pyperclip.copy(fullpath)
    #pyautogui.hotkey("ctrl", "v")
    try:
        logi(f"다른이름 저장하기 (경로명 입력) pyautogui.typewrite= {fullpath}")
        pyautogui.typewrite(fullpath)
        time.sleep(0.2)
        pyautogui.press('enter')   # 저장하기 위해 파일경로 넣고 엔터치기

        time.sleep(3)
        if os.path.isfile(fullpath):
            logt("파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
            logt("파일저장 확인완료 => DB 입력하기")
            dbjob.insert_or_update_upload_file(v_file_type, ht_tt_seq, holder_nm)
            return True
        else:
            time.sleep(1.0)
            if os.path.isfile(fullpath):
                logt("(재시도)파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
                logt("(재시도)파일저장 확인완료 => DB 입력하기")
                dbjob.insert_or_update_upload_file(v_file_type, ht_tt_seq, holder_nm)
                return True
            else:
                logt("파일저장 확인실패  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                time.sleep(10)
                # raise BizException("파일저장 실패", fullpath)
                return False

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
            time.sleep(0.5)
            logi(f"        이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            time.sleep(0.3) # 0.3초후 클릭
            pyautogui.click(center)
            logt(f"        이미지 영역 찾기 완료 => Click : {img_path}")
            return True

        pyautogui.moveTo(10,10)  # 일부러 마우스 움직이기
        time.sleep(0.2)

    #time.sleep(100000)
    return False

# ------------------------------------------------------------------------------
# (현재사용 안함) 이미지의 위치를 찾을 때까지 반복 시도
def pyautoui_image_wait(img_path):
    for retry in range(10):
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.5)
        #logi(center)

        if center == None :
            time.sleep(0.5)
            logi(f"이미지 클릭 재시도: {img_path} : retry={retry}")
        else :
            logt(f"이미지 영역 찾기 완료 : {img_path}")
            return True
    return False



# ------------------------------------------------------------------------------
def do_step2_loop(driver: WebDriver, ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    cur_window_handle = driver.current_window_handle
    time.sleep(0.2)
    driver.switch_to.frame("txppIframe")
    
    logi("******************************************************************************************************************")
    logt("양도인= %s, HT_TT_SEQ= %d, SSN= %s%s" % (ht_info['holder_nm'], ht_info['ht_tt_seq'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
    logi("******************************************************************************************************************")
    
    # 기존 로그 삭제
    #dbjob.delete_auHistory_byKey(ht_tt_seq, "2")

    # 작성방식 
    #logt("작성방식 선택")
    #select = Select(driver.find_element(By.ID, "selectbox_wrtMthCd_406_UTERNAAZ31"))
    #select.select_by_visible_text('작성방식')
            
    # FIXME 향후 삭제
    # driver.find_element(By.ID, 'rtnDtSrt_UTERNAAZ31_input').clear()
    # logt("조회 시작날짜", 0.1)
    # driver.find_element(By.ID, 'rtnDtSrt_UTERNAAZ31_input').send_keys('20230101')
    
    # driver.find_element(By.ID, 'rtnDtEnd_UTERNAAZ31_input').clear()
    # logt("조회 종료날짜", 0.1)
    # driver.find_element(By.ID, 'rtnDtEnd_UTERNAAZ31_input').send_keys('20230131')

    ssn = ht_info['holder_ssn1'] + ht_info['holder_ssn2']
    logt("주민번호 입력: %s" % ssn, 0.1)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').clear()
    time.sleep(0.2)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').send_keys(ssn)

    time.sleep(1)
    logt("조회클릭")
    driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()

    alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
    logi("Alter Message Return=%s" % alt_msg)
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

    ele_s = driver.find_element(By.CSS_SELECTOR, "#txtTotal887").text   # 총 1/2 등....
    logt("조회결과 갯수= %d" % int(ele_s))
    
    if int(ele_s) == 0:
        raise BizException("조회결과없음", f"실행자={ht_info['reg_id']}")

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
        hometax_holder_nm = ele.text
        # 양도인 이름이 같은지 조회

        # 신청_홈택스_이름차이_목록 = ["이해룡", "함경님"]
        # if not ht_info['holder_nm'] in 신청_홈택스_이름차이_목록:
        logi("양도인명 확인 JNK= %s, Hometax= %s" % (ht_info['holder_nm'], hometax_holder_nm))
        #     if hometax_holder_nm != ht_info['holder_nm']:
        #         raise BizException("양도인명 불일치", "홈택스 양도인명= %s" % hometax_holder_nm)

        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(9+offset)+ " > span > a")
        hometax_reg_num = ele.text
        logt("홈택스 접수번호= %s" % hometax_reg_num)
        # FIXME 중요 여기 살리기 !!!!
        dbjob.update_HtTt_audit_tmp1(ht_tt_seq, hometax_reg_num)
        # dbjob.update_HtTt_hometaxRegNum(ht_tt_seq, hometax_reg_num)

        #try:
        #     logi('# -----------------------------------------------------------------')
        #     logi('#                        1) 납부계산서                             ')
        #     logi('# -----------------------------------------------------------------')

        #     ele_s = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(9+offset)+ " > span > a")
        #     ele_s[0].click()
            
        #     # 팝업윈도우가 2개가 더 오픈되기 위한 충분한 시간을 주기
        #     logt("팝업 윈도우2개 로딩 대기", 2)
        #     window_handles = driver.window_handles
            
        #     if len(window_handles) < 3:  # 윈도우가 모두 뜨지 않았을 경우 대기
        #         for x in range(15):
        #             logi(f"윈도우 수량이 3개가 될때까지 대기, 현재 윈도우 갯수 = {len(window_handles)}")
        #             time.sleep(1)
        #             window_handles = driver.window_handles
        #             if len(window_handles) == 3:
        #                 break


        #     # 윈도우 상태 출력 (작업에 꼭 필요한 것은 아님)
        #     #sc.print_window_by_title(driver)
        #     driver.switch_to.window(window_handles[1])
        #     logt("팝업 윈도우 타이틀 확인 #1 : title= %s" % driver.title)
        #     if (driver.title == "신고서미리보기") :
        #         # 작업 진행 윈도우가 맞음, 다만 다른 윈도우를 닫아야 함
        #         try :
        #             time.sleep(1)
        #             driver.switch_to.window(window_handles[2])

        #             logt("현재창  : title= %s  ==> [개인정보 공개] 선택" % driver.title)
        #             driver.find_element(By.ID, "ntplInfpYn_input_0").click()
        #             time.sleep(0.2)
        #             driver.find_element(By.ID, "trigger1").click()
        #             time.sleep(1)

        #             logt("현재 윈도우 갯수 (예상되는 정상수량은 2) : 갯수= %d" % len(driver.window_handles))
        #             if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
        #             if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
        #             if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)

        #             driver.switch_to.window(driver.window_handles[1])

        #         except Exception as e:
        #             logi("window_handles[2] 윈도우 close실패 <-- 정상")

        #         driver.switch_to.window(window_handles[1])
        #         logt("팝업 윈도우 타이틀 확인 #3 (작업 윈도우 복귀) : title= %s" % driver.title)
        #     elif (driver.title == "신고서 보기 개인정보 공개여부") :
        #         # "신고서 보기 개인정보 공개여부"
        #         logt("현재창  : title= %s  ==> [개인정보 공개] 선택" % driver.title)
        #         driver.find_element(By.ID, "ntplInfpYn_input_0").click()
        #         time.sleep(0.2)
        #         driver.find_element(By.ID, "trigger1").click()
        #         time.sleep(1)

        #         logt("현재 윈도우 갯수 (예상되는 정상수량은 2) : 갯수= %d" % len(driver.window_handles))
        #         if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
        #         if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
        #         if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
                
        #         driver.switch_to.window(driver.window_handles[1])
        #         logt("팝업 윈도우 타이틀 확인 #4 (작업 윈도우 전화) : title= %s" % driver.title)
        #     else:
        #         # 원하는 창이 없음
        #         loge("원하는 창이 없어서 프로그램을 종료합니다.")
        #         sys.exit()

        #     logt("현재의 작업 윈도우 title= %s" % driver.title, 1)
        #     driver.set_window_position(0,0)
        #     driver.set_window_size(1140, 1140)

        #     # 파일다운로드
        #     file_type = "HT_DOWN_1"
        #     file_download(ht_info, file_type)

        
        #     # -----------------------------------------------------------------
        #     # 계산명세서 (신고서 보기 팝업에 함께 존재 -> 링크로 눌러 선택하기)
        #     # -----------------------------------------------------------------
        #     logi('# -----------------------------------------------------------------')
        #     logi('#                        2) 계산명세서                             ')
        #     logi('# -----------------------------------------------------------------')


        #     logt("클릭: 계산명세서 선택", 0.5)
        #     driver.find_element(By.ID, 'gen_FrmlList_1_txt_Frml').click()
            
        #     logt("계산명세서 로딩 대기", 1.5)
        #     file_type = "HT_DOWN_2"
        #     file_download(ht_info, file_type)

        #     # # 윈도우 클로우즈
        #     driver.close()
            
        #     # 원래 조회 윈도우로
        #     logt("초기 윈도우로 이동", 0.5)
        #     driver.switch_to.window(cur_window_handle)
        #     driver.set_window_position(0,0)

        #     logt("작업프레임 이동: txppIframe", 0.5)
        #     driver.switch_to.frame("txppIframe")
        # except Exception as e:
        #     raise BizException(f"[신고서] 다운로드 중 오류 발생 - {e}")

            
        # # -----------------------------------------------------------------
        # # 접수증 (홈택스)
        # # -----------------------------------------------------------------
        # logi('# -----------------------------------------------------------------')
        # logi('#                        3) 접수증                                 ')
        # logi('# -----------------------------------------------------------------')

        # try:
        #     logt("접수증 [보기] 클릭", 1)
        #     driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(11+offset)+ " > span > button").click()
            
        #     logt("윈도우 로딩 대기", 1)
        #     window_handles = driver.window_handles
        #     logi(f"윈도우 갯수= {len(window_handles)}") 
        #     if len(window_handles) == 1:
        #         logt("접수증 [보기] 클릭(재시도)", 0.1)
        #         driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(11+offset)+ " > span > button").click()

        #         logi("윈도우 전환 재시도", 2) 
        #         window_handles = driver.window_handles
        #         if len(window_handles) == 1:
        #             logi("윈도우 전환 실패 => 재시도 :윈도우 갯수={len(window_handles)}") 
        #             raise BizException("[접수증] 윈도우 전환 실패 - {e}")
            
        #     # 정상 진행
        #     logi(f"윈도우 갯수= {len(window_handles)}") 
        #     driver.switch_to.window(window_handles[1])
        #     driver.set_window_position(0,0)
        #     driver.set_window_size(850, 860)

        # except Exception as e:
        #     raise BizException("[접수증] 윈도우 전환 실패 - {e}")
        
        # # 파일다운로드: 
        # file_type = "HT_DOWN_3"
        # file_download(ht_info, file_type)
        
        # driver.close()
        # driver.switch_to.window(cur_window_handle)

        # -----------------------------------------------------------------
        # 납부서
        # -----------------------------------------------------------------

        logi('# -----------------------------------------------------------------')
        logi('#                        4) 납부서                                 ')
        logi('# -----------------------------------------------------------------')

        #logt("작업프레임 이동: txppIframe", 0.5)
        #driver.switch_to.frame("txppIframe")

        # 주의) 납부서가 없을 수 있음
        logt("납부서 [보기] 클릭", 1)
        try :
            ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(12+offset)+ " > span > button")
            ele.click()
        except Exception as e:
            logt("납부서가 없습니다.")
            raise BizException("납부할금액없음", f"납부서 Click불가")
        
        logt("작업프레임 이동: UTERNAAZ70_iframe", 2)
        try :
            driver.switch_to.frame("UTERNAAZ70_iframe")

        except Exception as e:
            #alert = driver.switch_to_alert()
            #if alert_msg.find("양도소득세 납부할금액이 없습니다") == 0 :
            #    alert.accept()
            raise BizException("납부할금액없음", f"(팝업) 납부서 Click불가")
        
        # 홈택스에 신고된 납부세액
        # logt("홈택스에 신고된 납부세액 조회", 0.5)
        # ele = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1 > span")
        # hometax_income_tax = ele.text
        # if len(hometax_income_tax) > 0:
        #     tax = hometax_income_tax.replace(",","").strip() # 컴마제거
        #     logt("홈택스에 신고된 납부세액 DB저장 = %s" % tax)
        #     dbjob.update_htTt_hometaxIncomeTax(ht_tt_seq, tax) 

        # 납부서 기본 -------------------------------------------
        try :

            납부액1 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1").text
            납부액1 = 납부액1.strip().replace(',','')
            dbjob.update_HtTt_audit_tmp2(ht_tt_seq, 납부액1)

            logt("납부서 이미지 클릭", 1)
            driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_3 > img").click()
            
            logt("윈도우 로딩 대기", 1.5)
            window_handles = driver.window_handles
            if len(window_handles) == 1:
                logt("납부서 클릭(재시도)", 0.1)
                driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_3 > img").click()

                logi("윈도우 전환 재시도", 2) 
                window_handles = driver.window_handles
                if len(window_handles) == 1:
                    logi("윈도우 전환 실패 => 재시도 :윈도우 갯수={len(window_handles)}") 
                    raise BizException("[납부서] 윈도우 전환 실패 - {e}")
                else:
                    driver.switch_to.window(window_handles[1])
                    driver.set_window_position(0,0)
                    driver.set_window_size(810, 880)

            # 정상진행
            logi(f"윈도우 갯수= {len(window_handles)}") 
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)
            driver.set_window_size(810, 880)
        except Exception as e:
            raise BizException("납부서", f"{e}")

        # 파일다운로드:
        file_type = "HT_DOWN_4"
        file_download(ht_info, file_type)


        logi(f"팝업윈도우 닫고 => 메인윈도우 전환")     
        driver.close()
        driver.switch_to.window(cur_window_handle)
        
        logt("작업프레임 이동: txppIframe", 0.2)
        driver.switch_to.frame("txppIframe")
        logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
        driver.switch_to.frame("UTERNAAZ70_iframe")

        # 납부서 2 (분납이 있는 경우) -------------------------------------------
        납부서갯수 = len(driver.find_elements(By.CSS_SELECTOR, "#ttirnal111DVOListDes_body_tbody > tr"))
        logi(f"납부서 갯수 = {납부서갯수}") 
        if 납부서갯수 == 2:
            try :
                # FIXME 토스 납부서 다시 받기로 수정 된 곳
                납부액2 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_1_1").text
                납부액2 = 납부액2.strip().replace(',','')
                dbjob.update_HtTt_audit_tmp3(ht_tt_seq, 납부액2)

                logt("납부서2(분납) 이미지 클릭", 0.5)
                driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_1_3 > img").click()

                logt("윈도우 로딩 대기", 2) 
                window_handles = driver.window_handles


                logt("윈도우 갯수= %d" % len(window_handles)) 
                driver.switch_to.window(window_handles[1])
                driver.set_window_position(0,0)
                driver.set_window_size(810, 880)

                # 파일다운로드:
                file_type = "HT_DOWN_8"
                file_download(ht_info, file_type)

                logi(f"팝업윈도우 닫고 => 메인윈도우 전환")     
                driver.close()
                driver.switch_to.window(cur_window_handle)
                logt("윈도우 갯수= %d" % len(window_handles)) 

                logt("작업프레임 이동: txppIframe", 0.2)
                driver.switch_to.frame("txppIframe")
                logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
                driver.switch_to.frame("UTERNAAZ70_iframe")

                if ht_info['data_type'] == 'SEMI':
                    분납금1 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1 > span").text
                    분납금2 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_1_1 > span").text
                    분납금1 = int(분납금1.strip().replace(',', ''))
                    분납금2 = int(분납금2.strip().replace(',', ''))
                    logi(f"반자동 분납금 업데이트 : 분납1={분납금1}, 분납2={분납금2}")
                    dbjob.update_HtTt_installment(ht_tt_seq, 분납금1, 분납금2)
                    dbjob.update_HtTt_hometaxIncomeTax(ht_tt_seq, 분납금1 + 분납금2)

            except Exception as e:
                raise BizException("납분서(분납)", f"{e}")
        else:
            logi("납부서(분납) 없음 => 정상")
            if ht_info['data_type'] == 'SEMI':
                분납금1 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1 > span").text
                분납금1 = int(분납금1.strip().replace(',', ''))
                분납금2 = 0
                logi(f"반자동 분납금 업데이트 : 분납1={분납금1}, 분납2={분납금2}")
                dbjob.update_HtTt_hometaxIncomeTax(ht_tt_seq, 분납금1 + 분납금2)

        # ---------------------------------------------------------------------------
        
        # 팝업레이어 닫기
        logt("팝업레이어 닫기", 1.5)
        # (주의)닫기(trigger1)는 문서내 2개 있음.. 팝업창의 x 클릭으로 대체
        try:
            driver.find_element(By.CSS_SELECTOR, "#trigger2").click()
        except:
            logt("팝업레이어 닫기 오류 => 재시도", 1)
            driver.switch_to.default_content
            driver.switch_to.frame("txppIframe")
            logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
            driver.switch_to.frame("UTERNAAZ70_iframe")           
            driver.find_element(By.CSS_SELECTOR, "#trigger2").click()

        #logt("작업프레임 이동: txppIframe", 0.5)
        #driver.switch_to.frame("txppIframe")
        #logi(driver.window_handles)


    else :
        # 접수된 신고가 없음
        step_cd = ht_info['step_cd']
        au1 = ht_info['au1']
        if step_cd == "REPORT" and au1 == "S":
            dbjob.update_HtTt_AuX(1, ht_tt_seq, 'E', '신고가 존재하지 않습니다. 재신청 하시기 바랍니다.')
            raise BizException("미제출", "신고서가 제출되지 않았습니다.")

