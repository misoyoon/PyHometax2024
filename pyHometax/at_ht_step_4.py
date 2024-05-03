from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

import pyautogui
#import shutil
import time
import os
import traceback

import config
from common import *
import dbjob
import common_sele as sc
import ht_file


# -------------------------------------------------------------
# (중요 공통) 아래의 모듈에서 step별 공통 기본 동작 실행
# -------------------------------------------------------------
import common_at_ht_step as step_common
group_id = step_common.group_id
auto_manager_id = step_common.auto_manager_id
conn = step_common.conn              
AU_X = '4' 
(driver, user_info, verify_stamp) = step_common.init_step_job()  
# -------------------------------------------------------------


def do_task(driver: WebDriver, user_info, verify_stamp):
    job_cnt = 0
    while True:
        job_cnt += 1

        # # driver 확인
        # if sc.check_availabe_driver(driver) == False:
        #     logt("driver가 close 된 것으로 판단 ==> 작업 중지")
        #     dbjob.update_autoManager_statusCd(auto_manager_id, 'S')
        #     return
        
        # try:
        #     로그인연장 = driver.find_element(By.CSS_SELECTOR, "#header > div.header-menu > div > div.login-time > button").text 
        #     if 로그인연장 != '로그인연장':
        #         logt("로그인 확인 불가로 재실행 필요 ==> 작업 중지")
        #         return # 단순하게 재로그인 처리를 위해 다시 시도하기
        # except:
        #     logt("로그인 확인 불가로 재실행 필요 ==> 작업 중지")
        #     return # 단순하게 재로그인 처리를 위해 다시 시도하기
            
        
        # AutoManager 상태 판단 (매 건 처리마다 상태 확인)
        at_info = dbjob.select_autoManager_by_id(auto_manager_id)

        # 홈택스 작업1단계 
        au_x            = at_info['au_x']
        status_cd       = at_info['status_cd']
        worker_id       = at_info['worker_id']
        worker_nm       = at_info['worker_nm']
        group_id        = at_info['group_id']
        seq_where_start = at_info['seq_where_start']
        seq_where_end   = at_info['seq_where_end']
        verify_stamp2   = at_info['verify_stamp']  # 작업시작시의 verify_stamp와 비교하여 상태 변경 여부 확인 
        
        # if verify_stamp == verify_stamp2:
        #     if status_cd == 'RW':
        #         # AUTO_MANGER: RUN
        #         dbjob.update_autoManager_statusCd(auto_manager_id, 'R')
        #     elif status_cd == 'SW' or status_cd == 'S':                 
        #         logt(f'Agent Check : Status={status_cd} ==> 작업 중지') 
        #         if status_cd == 'SW':
        #             dbjob.update_autoManager_statusCd(auto_manager_id, 'S')
        #         return
        # else:
        #     logt("verify_stamp 변경으로 STOP 합니다.")
        #     dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'verify_stamp 변경으로 STOP 합니다.')
            

        # 작업 대상
        ht_info = dbjob.select_next_au4(group_id, worker_id, seq_where_start, seq_where_end)

        logt("******************************************************************************************************************")
        logt("4단계 : JOB_COUNT=%s : HT_TT_SEQ=%d, 양도인=%s, SSN=%s-%s" % (job_cnt, ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
        logt("******************************************************************************************************************")

        if not ht_info:
            logt("처리할 자료가 없어서 FINISH 합니다. ==> 작업 중지")
            dbjob.update_autoManager_statusCd(auto_manager_id, 'F', '처리할 자료가 없어서 FINISH 합니다.')
            return

        group_id =  ht_info['group_id']
        ht_tt_seq = ht_info['ht_tt_seq']
        holder_nm = ht_info['holder_nm']
        
        #담당자 전화번호 추가
        ht_info['worker_tel'] = user_info['tel']

        # 작업진행을 위한 글로벌 값 지정
        #dbjob.set_global(group_id, auto_manager_id, worker_id, ht_tt_seq, au_x)  # "1" => 자동신고 1단계
        
        # TODO 개발 편의로 임시 주석처리
        # 신고건 진행표시 : au1 => R
        #dbjob.update_htTt_aux_running(ht_tt_seq, au_x)
        
        # 1단계 진행상태 DB 넣기 => 향후 결정할 것
        dbjob.delete_auHistory_byKey(ht_tt_seq, au_x)
        
        # 담당자 홈택스로그인 가능 여부 확인용(1,2,5 단계만)
        if au_x == '1' or au_x == '2' or au_x == '5' :
            dbjob.update_user_cookieModiDt(worker_id)        

        logt("******************************************************************************************************************")
        logt("4단계 : JOB_COUNT=%s : HT_TT_SEQ=%d, 양도인=%s, SSN=%s-%s" % (job_cnt, ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
        logt("******************************************************************************************************************")

        try:
            # 양도소득분 신고내역
            #driver.get('https://www.wetax.go.kr/etr/lit/b0703/B070302M01.do')
            #time.sleep(1)
            
            dclrid = ht_info['wetax_dclrid']
            wetax_url = f"https://www.wetax.go.kr/etr/lit/b0703/B070302M02.do?dclrId={dclrid}&objCd=T&objType=P&bgDclrId=&linkTyp="
            driver.get(wetax_url)
            
            logt("위택스 사이트 오픈", 1.5)

            logt("인쇄 버튼 클릭 -> 인쇄 팝업윈도우")
            driver.find_element(By.CSS_SELECTOR, '#btnPayPrint').click()
            

            # -------------------------------------------------------------------------------
            # 보고서 창 시작
            # -------------------------------------------------------------------------------
            # 최근 열린 창으로 전환
            logt("보고창으로 윈도우 전환", 1)
            driver.switch_to.window(driver.window_handles[-1])
            
            
            # 프린터 누르기 (다른이름으로 저장하기 위해서)
            driver.find_element(By.CSS_SELECTOR, '.btnPRINT').click()
            
            # 파일다운로드:
            file_type = "WE_DOWN_5"
            file_download(ht_info, file_type)
            
            # 메인 윈도우 복귀
            driver.switch_to.window(driver.window_handles[0])
                
            
            
        except Exception as e:
            loge(f'{e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f'{e}')
            dbjob.update_autoManager_statusCd(auto_manager_id, 'E', f'{e}')
        else:  # 오류없이 정상 처리시
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S', None)
        
        logt("####### 1건 처리 완료 #######")    



def file_download(ht_info, v_file_type):
    time.sleep(1)
    group_id =  ht_info['group_id']
    ht_tt_seq = ht_info['ht_tt_seq']
    holder_nm = ht_info['holder_nm']

    # file_type별 파일이름 결정
    dir_work = ht_file.get_dir_by_htTtSeq(group_id, ht_tt_seq, True)  # True => 폴더 생성
    fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
    logt("------------------------------------------------------")
    logt("파일다운로드: Type: %s, Filepath: %s" % (v_file_type, fullpath))
    logt("------------------------------------------------------")

    #time.sleep(3)
    # 이미 존재하면 삭제 (pdf 다운로드시 이미 존재하면 덮어쓰기 하겠냐고 질문하는 것을 회피 하기위해)
    if os.path.isfile(fullpath):
        os.remove(fullpath)

    driver.switch_to.window(driver.window_handles[1])
    logt(f"Driver window전환 : index=1, Title={driver.title}")    
    
    if v_file_type == "HT_DOWN_1" or v_file_type == "HT_DOWN_2"   or v_file_type == "HT_DOWN_4" or v_file_type == "HT_DOWN_8":
        if v_file_type == "HT_DOWN_1" or v_file_type == "HT_DOWN_2":
            driver.switch_to.frame("iframe2_UTERNAAZ34")

        driver.find_element(By.CSS_SELECTOR, "button[title='인쇄']").click()
        time.sleep(0.3)
        pyautogui.press('tab', presses=4, interval=0.1)
        pyautogui.press('enter')
        logt("확인버튼 클릭 후 인쇄화면 출력 대기", 2)    
        # 저장 클릭        
        time.sleep(2)
        pyautogui.press('enter')  
    elif v_file_type == "HT_DOWN_3":
        driver.find_element(By.CSS_SELECTOR, "button[title='인쇄']").click()
        time.sleep(3)
        # 저장 클릭
        pyautogui.press('enter')
    elif v_file_type == "WE_DOWN_5":
        #driver.find_element(By.CSS_SELECTOR, ".btnPRINT").click()
        driver.execute_script("$('.btnPRINT').click();")
        time.sleep(1.5)
        # 저장 클릭
        pyautogui.press('tab', presses=1, interval=0.1)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.press('enter')


    # 팝업: 다른이름으로 저장 
    time.sleep(2)
    logt(f"파일타입={v_file_type}, 파일 경로 Paste = {fullpath}", 0.5)    
    pyautogui.typewrite(fullpath)
    time.sleep(2)
    pyautogui.press('enter')   # 저장하기 위해 파일경로 넣고 엔터치기         

    # 파일 저장 결과 확인
    time.sleep(1)
    if os.path.isfile(fullpath):
        logt("파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
        logt("파일저장 확인완료 => DB 입력하기")
        dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
        return True
    else:
        time.sleep(3.0)
        if os.path.isfile(fullpath):
            logt("(재시도)파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
            logt("(재시도)파일저장 확인완료 => DB 입력하기")
            dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
            return True
        else:
            logt("파일저장 확인실패  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            raise BizException("파일저장 실패", fullpath)
            return False

if __name__ == '__main__':
    if driver:
        driver.set_window_size(1300, 990) # 실제 적용시 : 990
        do_task(driver, user_info, verify_stamp) 
        
    logt(f"{AU_X}단계 작업 완료")

    if conn: 
        conn.close()

    exit(0)    
