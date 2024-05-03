import time
import os

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
#from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys

import pyautogui
import pyperclip
import traceback

from common import *
import ht_file
import dbjob
import pyHometax.common_sele as sc
import auto_step_1
import config

# 자동신고단계 -----------------------------
# 증빙자료 업로드
au_step = 6
au_step_name = "증빙자료 업로드"

root_dir = config.FILE_ROOT_DIR

# 메뉴이동 : '신고/납부' 클릭
def click_메뉴_신고납부(driver):
   
    window_handles = driver.window_handles
    main_window_handle = window_handles[0]
    print(main_window_handle)
    logt("메인윈도우 핸들: %s" % main_window_handle)

    logt("메뉴이동 : '신고/납부' 메뉴 이동")
    url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
    driver.get(url)
    
    logt("iframe 이동", 2)
    sc.move_iframe(driver)
    
    # logt("클릭: 신고내역조회(접수증,납부서) 메뉴", 1)
    # element = driver.find_element(By.CSS_SELECTOR, '#tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11 > div.w2tabcontrol_tab_center > a')
    # element.click()

    logt("클릭: 신고내역 조회(접수증,납부서)", 2)
    driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs5_UTERNAAZ11').click()


    try :
        time.sleep(1)
        alert = driver.switch_to_alert()
        alert_msg = alert.text
        if alert_msg.find("로그인 정보가 없습니다.") > -1 :
            logt("현재는 로그아웃 상태")
            alert.accept()
            raise BizException("로그아웃상태")   
        else :
            logt("정상 로그인 상태1")
    except BizException as e:
        raise e
    except :
        pass


def do_step5(driver, jobs, user_id):
    logt(au_step_name, au_step)

    click_메뉴_신고납부(driver)


    # 양도자 반복처리      
    cur_window_handle = driver.current_window_handle      

    # logt("작업프레임 이동: txppIframe", 0.5)
    # driver.switch_to.frame("txppIframe")

    driver.find_element(By.ID, "rtnDtSrt_UTERNAAZ41_input").clear()
    time.sleep(0.2)
    driver.find_element(By.ID, "rtnDtSrt_UTERNAAZ41_input").send_keys("20220501")
    time.sleep(0.2)
    driver.find_element(By.ID, "rtnDtEnd_UTERNAAZ41_input").clear()
    time.sleep(0.2)
    driver.find_element(By.ID, "rtnDtEnd_UTERNAAZ41_input").send_keys("20220531")
    time.sleep(0.2)

    # 작성방식 
    logt("세목 선택")
    select = Select(driver.find_element(By.ID, "selectbox2_UTERNAAZ41"))
    select.select_by_visible_text('양도소득세')
    time.sleep(0.5)

    loop_num = 0
    for job_idx in range(0, len(jobs)):
        ht_info = jobs[job_idx]
        ht_tt_seq = ht_info['ht_tt_seq']

        try:
            logt("####################################################")
            logt("%d / %d 처리 ..." % (job_idx+1, len(jobs)))        
            logt("####################################################")
            ht_info = jobs[job_idx]

            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(cur_window_handle)

            logt("홈택스 조회 윈도우 이동", 0.5)
            driver.switch_to.window(cur_window_handle)

            print(driver.window_handles)
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(cur_window_handle)

            logt("작업프레임 이동: txppIframe", 0.5)
            driver.switch_to.frame("txppIframe")

            # ================================================
            # 반복처리
            do_step5_loop(driver, ht_info)
            # ================================================
        
        except BizException as e:
            logt("#################### except BizException")
            print(e)
            dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'E', e.msg)

        except Exception as e:
            logt("#################### except")
            traceback.print_exc()
            print(e)
            dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'E', None)
        
        else:  # 오류없이 정상 처리시
            logt("#################### (정상처리)")
            dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'S', None)

        # job 완료 처리 
        logt("####### 한건처리 완료 #######", 0.2)






def do_step5_loop(driver, ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    cur_window_handle = driver.current_window_handle
    ssn1 = ht_info['holder_ssn1']
    ssn2 = ht_info['holder_ssn2']

    logt("******************************************************************************************************************")
    logt("양도인=%s, HT_TT_SEQ=%d, SSN= %s %s" % (ht_info['holder_nm'], ht_info['ht_tt_seq'], ssn1, ssn2))
    logt("******************************************************************************************************************")
    
    # 기존 로그 삭제
    dbjob.delete_auHistory_byKey(ht_tt_seq, au_step)

    ssn = ht_info['holder_ssn1'] + ht_info['holder_ssn2']

    # 주민번호 입력
    logt("주민번호 입력: %s %s" % (ssn1, ssn2), 0.5)
    driver.find_element(By.ID, 'inputResno_1').clear()
    time.sleep(0.1)
    driver.find_element(By.ID, 'inputResno_2').clear()
    time.sleep(0.1)
    driver.find_element(By.ID, 'inputResno_1').send_keys(ssn1)
    time.sleep(0.1)
    driver.find_element(By.ID, 'inputResno_2').send_keys(ssn2)
    time.sleep(0.2)

    logt("조회클릭")
    driver.find_element(By.ID, 'trigger45_UTERNAAZ41').click()

    time.sleep(1)
    alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
    print("Alter Message Return=%s" % alt_msg)
    # 결과가 없을 경우 처리
    if alt_msg.find("사업자등록번호") > -1 :
        logt("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음")
    elif alt_msg.find("이중로그인 방지로 통합인증이 종료되었습니다") > -1 :
        logt("이중로그인 방지로 통합인증이 종료되었습니다 => 프로그램 종료")
        sys.exit()
    elif alt_msg.find("조회된 데이터가 없습니다") > -1 :
        logt("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음", f"주민번호:{ssn}, 실행자={ht_info['reg_id']}")

    ele_s = driver.find_element(By.CSS_SELECTOR, "#txtTotal_UTERNAAZ41").text   # 총 1/2 등....
    logt("조회결과 갯수= %d" % int(ele_s))

    if int(ele_s) == 0:
        raise BizException("조회결과없음", f"조회결과없음, 실행자={ht_info['reg_id']}")

    elif int(ele_s) > 1:
        raise BizException("복수신고건", "신고건수= %d" % int(ele_s))

    elif int(ele_s) == 1:  # 정상케이스

        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_16 > span")
        제출유무판단 = ele.text
        if 제출유무판단 == '제출내역보기':
            logt('정상 제출 확인  ~~~~~~~~~~~ ')
        else :
            raise BizException("미제출", "첨부하기")
        
        logt("한건 처리 완료 ###", 0.1)





        # 팝업 윈도우는 자동으로 닫히기 때문에 특별히 close 처리 안함

    else :  # 조회 결과 0
        step_cd = ht_info['step_cd']
        dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'E', '신고가 존재하지 않습니다')
        raise BizException("미제출", "신고서가 제출되지 않았습니다.")


def get_file_path_by_file_seq(ht_tt_file_seq) :
        # 파일키
        if ht_tt_file_seq is not None and ht_tt_file_seq>0 :
            # 파일정보
            file_info = dbjob.select_one_HtTtFile(ht_tt_file_seq)

            if file_info is not None :
                # DB에 있는 파일 정보
                filepath = root_dir + file_info['path'] + file_info['changed_file_nm'] 
                return filepath
            else:
                return None
        else :
            return None
