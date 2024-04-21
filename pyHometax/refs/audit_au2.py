import time
import os

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
au_stpe = 2

# 메뉴이동 : '신고/납부' 클릭
def click_메뉴_신고납부(driver):
    print("메뉴이동 : '신고/납부' 메뉴 이동")
    url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index.xml&tmIdx=9&tm2lIdx=&tm3lIdx='
    driver.get(url)
    
    print("클릭: [신고/납부] 화면상단 메뉴",2)
    driver.find_element(By.ID, 'group1314').click()

    print("iframe 이동", 2)
    sc.move_iframe(driver)

    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.ID, 'sub_a_0405050000')))
    print("클릭: 양도소득세")
    element.click()

    try :
        time.sleep(1)
        alert = driver.switch_to_alert()
        alert_msg = alert.text
        if alert_msg.find("로그인 정보가 없습니다.") > -1 :
            print("현재는 로그아웃 상태")
            alert.accept()
            raise BizException("로그아웃상태")   
        else :
            print("정상 로그인 상태1")
    except BizException as e:
        raise e
    except :
        pass


def do_step2(driver, jobs, user_id):

    window_handles = driver.window_handles
    main_window_handle = window_handles[0]
    print(main_window_handle)
    print("메인윈도우 핸들: %s" % main_window_handle)
    click_메뉴_신고납부(driver)

    print("Step 2.신고내역 이동하기", 1.5)
    
    element = driver.find_element(By.CSS_SELECTOR, '#tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11 > div.w2tabcontrol_tab_center > a')
    print(element)
    element.click()

    # jobs = dbjob.select_auto_2(user_id, config.BATCH_BUNDLE_COUNT)
    
    if len(jobs) == 0:
        logi("모든 자료를 다운로드 받았습니다. 작업종료")    

    # 양도자 반복처리      
    error_cnt = 0  # 연속 에러갯수      
    for job_idx in range(0, len(jobs)):

        if error_cnt > 5:
            loge("연속5회 에러로 작업을 중지 시킵니다.")
            break

        ht_info = jobs[job_idx]
        ht_tt_seq = ht_info['ht_tt_seq']

        try :
            driver.switch_to.window(main_window_handle)
        except:
            loge("브라우저가 닫힌거 같습니다.")
            exit(0)

        # print함수를 db에 D:\WWW\JNK\files\hometax\001\001239\down1.pdf
        # 키기 위해서는 global에 ht_tt_seq를 넣어줘야한다.
        # set_global(group_id, v_host_name, v_user_id, v_ht_tt_seq, v_au_step):
        dbjob.set_global(group_id, None, user_id, ht_tt_seq, 2)

        try:
            print("%d / %d 처리 ..." % (job_idx+1, len(jobs)))        
            ht_info = jobs[job_idx]
            do_step2_loop(driver, ht_info)
        
        except BizException as e:
            print("#################### except BizException")
            print(e)
            if e.name == '미제출':  # 미제출건으로 해당 작업과는 무관하게 처리
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, None, None)

            elif e.name == "납부할금액없음":
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'S', e.msg)
                error_cnt = 0
            else:
                dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', e.msg)
                traceback.print_exc()
                error_cnt += 1
            

        except Exception as e:
            try :
                print("#################### except Exception :" + e)
            except:
                pass

            print(e)
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', f'{e}')
            traceback.print_exc()
            error_cnt += 1
        
        else:  # 오류없이 정상 처리시
            print("#################### (정상처리)")
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'S', None)
            traceback.print_exc()
            error_cnt = 0

        # job 완료 처리 
        print("####### 한건처리 완료 #######", 0.2)



def do_step2_loop(driver, ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    cur_window_handle = driver.current_window_handle
    driver.switch_to.frame("txppIframe")
    
    logi("******************************************************************************************************************")
    print("양도인= %s, HT_TT_SEQ= %d, SSN= %s%s" % (ht_info['holder_nm'], ht_info['ht_tt_seq'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
    logi("******************************************************************************************************************")
    
    # 기존 로그 삭제
    dbjob.delete_auHistory_byKey(ht_tt_seq, "2")

    ssn = ht_info['holder_ssn1'] + ht_info['holder_ssn2']

    print("주민번호 입력: %s" % ssn, 0.5)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').clear()
    time.sleep(0.2)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').send_keys(ssn)

    time.sleep(0.5)
    driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()
    print("조회결과 대기", 1)

    alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
    print("Alter Message Return=%s" % alt_msg)
    # 결과가 없을 경우 처리
    if alt_msg.find("사업자등록번호") > -1 :
        print("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음")
    elif alt_msg.find("이중로그인 방지로 통합인증이 종료되었습니다") > -1 :
        logt("이중로그인 방지로 통합인증이 종료되었습니다 => 프로그램 종료")
        sys.exit()

    time.sleep(0.2)
    ele_s = driver.find_element(By.CSS_SELECTOR, "#txtTotal887").text   # 총 1/2 등....
    print("조회결과 갯수= %d" % int(ele_s))

    if int(ele_s) > 1:
        raise BizException("복수신고건", "신고건수= %d" % int(ele_s))
    
    elif len(ele_s) == 1:
        ele1 = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_4 > nobr")
        ele2 = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_5 > nobr")
        
        offset = 0
        if ele1.text == "정기신고" :
            offset = 0
        elif ele2.text == "정기신고" :
            offset = 1

        print("결과 OFFSET= %d" % offset)

        selector = "#ttirnam101DVOListDes_cell_0_" +str(5+offset)+ " > nobr"
        print (selector)
        ele = driver.find_element(By.CSS_SELECTOR, selector)    
        hometax_holder_nm = ele.text
        # 양도인 이름이 같은지 조회
        print("양도인명 확인 GBY= %s, Hometax= %s" % (ht_info['holder_nm'], hometax_holder_nm))
        if hometax_holder_nm != ht_info['holder_nm']:
            raise BizException("양도인명 불일치", "홈택스 양도인명= %s" % hometax_holder_nm)

        time.sleep(0.5)
        
        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(9+offset)+ " > nobr > a")
        hometax_reg_num = ele.text
        print("홈택스 접수번호= %s" % hometax_reg_num)
        dbjob.update_HtTt_hometaxRegNum(ht_tt_seq, hometax_reg_num)

        # -

    else :
        # 접수된 신고가 없음
        step_cd = ht_info['step_cd']
        au1 = ht_info['au1']
        if step_cd == "REPORT" and au1 == "S":
            dbjob.update_AuAudit_AuX(1, ht_tt_seq, 'E', '신고가 존재하지 않습니다. 재신청 하시기 바랍니다.')
            raise BizException("미제출", "신고서가 제출되지 않았습니다.")

