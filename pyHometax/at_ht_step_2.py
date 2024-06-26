from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import time
import math

import pyautogui
from common import *
import dbjob
import common_sele as sc
import ht_file


# -------------------------------------------------------------
# (중요 공통) 아래의 모듈에서 step별 공통 기본 동작 실행
# -------------------------------------------------------------
import common_at_ht_step as step_common
auto_manager_id = step_common.auto_manager_id
conn = step_common.conn
AU_X = '2'
(driver, user_info, verify_stamp) = step_common.init_step_job()
# -------------------------------------------------------------

def do_task(driver: WebDriver, verify_stamp):

    window_handles = driver.window_handles
    main_window_handle = window_handles[0]
    logt("메인윈도우 핸들: %s" % main_window_handle)

    # 페이지 로딩 완료를 기다리는 시간 설정 (최대 10초까지 대기)
    logt("페이지이동: '신고/납부' 메뉴 이동", 2)
    url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
    driver.get(url)
    
    logt("iframe 이동", 2)
    sc.move_iframe(driver)
    
    logt("클릭: 신고내역 조회(접수증,납부서)", 2)
    driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11').click()

    job_cnt = 0
    while True:
        job_cnt += 1
        
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
        
        if verify_stamp == verify_stamp2:
            if status_cd == 'RW':
                # AUTO_MANGER: RUN
                dbjob.update_autoManager_statusCd(auto_manager_id, 'R')
            elif status_cd == 'SW' or status_cd == 'S':
                logt(f'Agent Check : Status={status_cd} ==> 작업 중지')
                if status_cd == 'SW':
                    dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'SW 신호로 STOP 합니다.')
                return
        else:
            dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'verify_stamp 변경으로 STOP 합니다.')
            return
            
        # 작업자 정보 조회
        user_info = dbjob.get_worker_info(worker_id)
        
        # 쿠키점검
        cookie_TXPPsessionID = get_cookie_value(driver, 'TXPPsessionID')
        cookie_TEHTsessionID = get_cookie_value(driver, 'TEHTsessionID')
        if user_info['txpp_session_id'] != cookie_TXPPsessionID:
            logt(f"DRIVER TXPP=: {cookie_TXPPsessionID}")
            logt(f"UserDB TXPP=: {user_info['txpp_session_id']}")
        if user_info['teht_session_id'] != cookie_TEHTsessionID:
            logt(f"DRIVER TXPP=: {cookie_TEHTsessionID}")
            logt(f"UserDB TXPP=: {user_info['teht_session_id']}")
        
        # ----------------------------------------------
        # 홈택스 신고서제출 자료            
        # ----------------------------------------------
        ht_info = dbjob.select_next_au2(group_id, worker_id, seq_where_start, seq_where_end)
        
        if not ht_info:
            dbjob.update_autoManager_statusCd(auto_manager_id, 'F', '처리할 자료가 없어서 FINISH 합니다.')
            break
            
        #담당자 전화번호 추가
        ht_info['worker_tel'] = user_info['tel']
        ht_tt_seq = ht_info['ht_tt_seq']
        
        # 작업진행을 위한 글로벌 값 지정
        #dbjob.set_global(group_id, auto_manager_id, worker_id, ht_tt_seq, au_x)  # "1" => 자동신고 1단계
        
        # TODO 개발 편의로 임시 주석처리
        # 신고건 진행표시 : au1 => R
        # dbjob.update_htTt_aux_running(ht_tt_seq, AU_X)
        
        # 1단계 진행상태 DB 넣기 => 향후 결정할 것
        dbjob.delete_auHistory_byKey(ht_tt_seq, AU_X)

        # 담당자 홈택스로그인 가능 여부 확인용(1,2,5 단계만)
        if au_x == '1' or au_x == '2' or au_x == '5' :
            dbjob.update_user_cookieModiDt(worker_id)

        logt("******************************************************************************************************************")
        logt("2단계 : JOB_COUNT=%s : HT_TT_SEQ=%d, 양도인=%s, SSN=%s-%s" % (job_cnt, ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
        logt("******************************************************************************************************************")

        try:
            # -----------------------------------------------------------------------
            # 문서 다운로드 반복
            # -----------------------------------------------------------------------
            do_step2_loop(driver, ht_info)

        except BizNextLoopException as e:
            loge(f'do_step2_loop :: BizNextLoopException(정상동작) - {e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, e.aux_result, e.msg)
        except BizException as e:
            loge(f'do_step2_loop :: BizException ERROR - {e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f'{e.name}:{e.msg}')
            #dbjob.update_autoManager_statusCd(auto_manager_id, 'E', f'{e.name}:{e.msg}')
            loge("오류 발생으로 해당 단계 작업 중지!!!")
            break
        except Exception as e:
            loge(f'do_step2_loop :: Exception ERROR - {e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f'{e}')
            #dbjob.update_autoManager_statusCd(auto_manager_id, 'E', f'{e}')
            loge("오류 발생으로 해당 단계 작업 중지!!!")
            break
        else:  # 오류없이 정상 처리시
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S', None)
        # -----------------------------------------------------------------------

        logt("####### 한건처리 완료 #######")
            
    # End of while



def file_download(ht_info, v_file_type):
    ht_sleep(1)
    group_id =  ht_info['group_id']
    ht_tt_seq = ht_info['ht_tt_seq']
    holder_nm = ht_info['holder_nm']

    # file_type별 파일이름 결정
    dir_work = ht_file.get_dir_by_htTtSeq(group_id, ht_tt_seq, True)  # True => 폴더 생성
    fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
    logt("------------------------------------------------------")
    logt("파일다운로드: Type: %s, Filepath: %s" % (v_file_type, fullpath))
    logt("------------------------------------------------------")

    #ht_sleep(3)
    # 이미 존재하면 삭제 (pdf 다운로드시 이미 존재하면 덮어쓰기 하겠냐고 질문하는 것을 회피 하기위해)
    if os.path.isfile(fullpath):
        os.remove(fullpath)

    driver.switch_to.window(driver.window_handles[1])
    logt(f"Driver window전환 : index=1, Title={driver.title}")    
    
    if v_file_type == "HT_DOWN_1" or v_file_type == "HT_DOWN_2"   or v_file_type == "HT_DOWN_4" or v_file_type == "HT_DOWN_8":
        if v_file_type == "HT_DOWN_1" or v_file_type == "HT_DOWN_2":
            driver.switch_to.frame("iframe2_UTERNAAZ34")

        driver.find_element(By.CSS_SELECTOR, "button[title='인쇄']").click()
        ht_sleep(0.3)
        pyautogui.press('tab', presses=4, interval=0.1)
        pyautogui.press('enter')
        logt("확인버튼 클릭 후 인쇄화면 출력 대기", 2)    
        # 저장 클릭        
        ht_sleep(2)
        pyautogui.press('enter')  
    elif v_file_type == "HT_DOWN_3":
        driver.find_element(By.CSS_SELECTOR, "button[title='인쇄']").click()
        ht_sleep(3)
        # 저장 클릭
        pyautogui.press('enter')

    # 팝업: 다른이름으로 저장 
    logt(f"파일타입={v_file_type}, 파일 경로 쓰기 = {fullpath}", 2)    
    pyautogui.typewrite(fullpath)
    ht_sleep(2)
    pyautogui.press('enter')   # 저장하기 위해 파일경로 넣고 엔터치기         

    # 파일 저장 결과 확인
    ht_sleep(1)
    if os.path.isfile(fullpath):
        logt("파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
        logt("파일저장 확인완료 => DB 입력하기")
        dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
        return True
    else:
        ht_sleep(3.0)
        if os.path.isfile(fullpath):
            logt("(재시도)파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
            logt("(재시도)파일저장 확인완료 => DB 입력하기")
            dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
            return True
        else:
            logt("파일저장 확인실패  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            raise BizException("파일저장 실패", fullpath)
            return False

# 오류등으로 인해 안 닫혀진 iframe을 사전에 조회 후 닫기
def checkIFrame(driver: WebDriver):
    target_iframe = 'UTERNAAZ70_iframe'
    driver.switch_to.default_content()    
    driver.switch_to.frame("txppIframe")
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    
    for iframe in iframes:
        iframe_name = iframe.get_attribute('name')
        iframe_id = iframe.get_attribute('id')
        if iframe_name == target_iframe or iframe_id == target_iframe:
            # 팝업레이어 닫기
            logt("팝업레이어 닫기", 1.5)
            # (주의)닫기(trigger1)는 문서내 2개 있음.. 팝업창의 x 클릭으로 대체
            try:
                #driver.find_element(By.CSS_SELECTOR, "#trigger1").click()
                driver.execute_script("$('#trigger1').click();")
            except:
                logt("팝업레이어 닫기 오류 => 재시도", 1)
                driver.switch_to.default_content()
                driver.switch_to.frame("txppIframe")
                logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
                driver.switch_to.frame("UTERNAAZ70_iframe")           
                driver.find_element(By.CSS_SELECTOR, "#trigger2").click()                

            break

    driver.switch_to.default_content()

# ------------------------------------------------------------------------------
def do_step2_loop(driver: WebDriver, ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    #cur_window_handle = driver.current_window_handle
    #driver.switch_to.frame("txppIframe")
    
    logt("******************************************************************************************************************")
    logt("양도인= %s, HT_TT_SEQ= %d, SSN= %s%s" % (ht_info['holder_nm'], ht_info['ht_tt_seq'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
    logt("******************************************************************************************************************")
    
    # 기존 로그 삭제
    dbjob.delete_auHistory_byKey(ht_tt_seq, "2")

    # 작성방식 
    #logt("작성방식 선택")
    #select = Select(driver.find_element(By.ID, "selectbox_wrtMthCd_406_UTERNAAZ31"))
    #select.select_by_visible_text('작성방식')

    # 작업 window 초기화
    driver.switch_to.window(driver.window_handles[0])
    try:
        driver.execute_script("$('#trigger1').click();")
    except:
        pass

    driver.switch_to.frame("txppIframe")

    # FIXME 향후 삭제
    driver.find_element(By.ID, 'rtnDtSrt_UTERNAAZ31_input').clear()
    logt("조회 시작날짜", 0.1)
    driver.find_element(By.ID, 'rtnDtSrt_UTERNAAZ31_input').send_keys('20240501')
    
    driver.find_element(By.ID, 'rtnDtEnd_UTERNAAZ31_input').clear()
    logt("조회 종료날짜", 0.1)
    driver.find_element(By.ID, 'rtnDtEnd_UTERNAAZ31_input').send_keys('20240531')

    ssn = ht_info['holder_ssn1'] + ht_info['holder_ssn2']
    logt("주민번호 입력: %s" % ssn, 0.1)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').clear()
    ht_sleep(0.2)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').send_keys(ssn)

    #driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()
    sc.click_button_by_id(driver, 'trigger70_UTERNAAZ31', '신고내역 조회', 1)

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
            raise BizException(f"offset 불일치", "신고종류={ele1.text}")
        elif ele2.text == "정기신고" :
            offset = 1

        logt("정기신고 OFFSET= %d" % offset)

        # 양도인명
        ele = driver.find_element(By.CSS_SELECTOR,  "#ttirnam101DVOListDes_cell_0_6 > span")    
        hometax_holder_nm = ele.text

        ele = driver.find_element(By.CSS_SELECTOR,  "#ttirnam101DVOListDes_cell_0_7 > span")    
        hometax_holder_ssn = ele.text

        # 신청_홈택스_이름차이_목록 = ["이해룡", "함경님"]
        # if not ht_info['holder_nm'] in 신청_홈택스_이름차이_목록:
        logt("양도인 확인1 = %s, Hometax= %s" % (ht_info['holder_nm'],   hometax_holder_nm))
        logt("양도인 확인2 = %s, Hometax= %s" % (ht_info['holder_ssn1'], hometax_holder_ssn))

        if hometax_holder_nm.find(ht_info['holder_nm']) == -1 :
            #이름 불일치 하면 생년월일 비교
            if hometax_holder_ssn.find(ht_info['holder_ssn1']) == -1 :
                raise BizException("양도인명 불일치", "홈택스 양도인명= %s" % hometax_holder_nm)

        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_10 > span > a")
        hometax_reg_num = ele.text
        logt("홈택스 접수번호= %s" % hometax_reg_num)
        
        if ht_info['data_type'] == 'SEMI':
            dbjob.update_HtTt_hometaxRegNum(ht_tt_seq, hometax_reg_num)  
            logt("[반자동] 홈택스 접수번호 업데이트 = %s" % hometax_reg_num)


        try:
            logt('# -----------------------------------------------------------------')
            logt('#                        1) 납부계산서                             ')
            logt('# -----------------------------------------------------------------')

            ele_s = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_10 > span > a")
            ele_s[0].click()
            
            # 팝업윈도우가 2개가 더 오픈되기 위한 충분한 시간을 주기
            logt("팝업 윈도우2개 로딩 대기", 2)
            window_handles = driver.window_handles
            
            if len(window_handles) < 3:  # 윈도우가 모두 뜨지 않았을 경우 대기
                for x in range(15):
                    logt(f"윈도우 수량이 3개가 될때까지 대기, 현재 윈도우 갯수 = {len(window_handles)}")
                    ht_sleep(1)
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
                    ht_sleep(1)
                    driver.switch_to.window(window_handles[2])

                    logt("현재창  : title= %s  ==> [개인정보 공개] 선택" % driver.title)
                    driver.find_element(By.ID, "ntplInfpYn_input_0").click()
                    ht_sleep(0.2)
                    driver.find_element(By.ID, "trigger1").click()
                    ht_sleep(1)

                    logt("현재 윈도우 갯수 (예상되는 정상수량은 2) : 갯수= %d" % len(driver.window_handles))
                    if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
                    if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
                    if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)

                    driver.switch_to.window(driver.window_handles[1])

                except Exception as e:
                    logt("window_handles[2] 윈도우 close실패 <-- 정상")

                driver.switch_to.window(window_handles[1])
                logt("팝업 윈도우 타이틀 확인 #3 (작업 윈도우 복귀) : title= %s" % driver.title)
            elif (driver.title == "신고서 보기 개인정보 공개여부") :
                # "신고서 보기 개인정보 공개여부"
                logt("현재창  : title= %s  ==> [개인정보 공개] 선택" % driver.title)
                driver.find_element(By.ID, "ntplInfpYn_input_0").click()
                ht_sleep(0.2)
                driver.find_element(By.ID, "trigger1").click()
                ht_sleep(1)

                logt("현재 윈도우 갯수 (예상되는 정상수량은 2) : 갯수= %d" % len(driver.window_handles))
                if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
                if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
                if len(driver.window_handles) == 3: logt("창이 닫기를 좀더 기다리기", 1)
                
                driver.switch_to.window(driver.window_handles[1])
                logt("팝업 윈도우 타이틀 확인 #4 (작업 윈도우 전화) : title= %s" % driver.title)
            else:
                # 원하는 창이 없음
                loge("원하는 창이 없어서 프로그램을 종료합니다.")
                sys.exit()

            logt("현재의 작업 윈도우 title= %s" % driver.title, 1)
            driver.set_window_position(0,0)
            #driver.set_window_size(1140, 1140)

            # 파일다운로드
            file_type = "HT_DOWN_1"             
            
            file_download(ht_info, file_type)

            # # 윈도우 전환
            driver.switch_to.window(driver.window_handles[1])
            
            # -----------------------------------------------------------------
            # 계산명세서 (신고서 보기 팝업에 함께 존재 -> 링크로 눌러 선택하기)
            # -----------------------------------------------------------------
            logt('# -----------------------------------------------------------------')
            logt('#                        2) 계산명세서                             ')
            logt('# -----------------------------------------------------------------')


            logt("클릭: 계산명세서 선택", 0.5)
            driver.find_element(By.ID, 'gen_FrmlList_1_txt_Frml').click()
            
            logt("계산명세서 로딩 대기", 1.5)
            file_type = "HT_DOWN_2"
            file_download(ht_info, file_type)

            # # 윈도우 클로우즈
            driver.close()
            
            # 원래 조회 윈도우로
            logt("초기 윈도우로 이동", 0.5)
            driver.switch_to.window(driver.window_handles[0])
            #driver.set_window_position(0,0)

            logt("작업프레임 이동: txppIframe", 0.5)
            driver.switch_to.frame("txppIframe")
        except Exception as e:
            raise BizException(f"[신고서] 다운로드 중 오류 발생 - {e}")

            
        # -----------------------------------------------------------------
        # 접수증 (홈택스)
        # -----------------------------------------------------------------
        logt('# -----------------------------------------------------------------')
        logt('#                        3) 접수증                                 ')
        logt('# -----------------------------------------------------------------')

        try:
            logt("접수증 [보기] 클릭", 1)
            driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_12 > span > button").click()
            
            logt("윈도우 로딩 대기", 1)
            window_handles = driver.window_handles
            logt(f"윈도우 갯수= {len(window_handles)}") 
            if len(window_handles) == 1:
                logt("접수증 [보기] 클릭(재시도)", 0.1)
                driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_12 > span > button").click()

                logt("윈도우 전환 재시도", 2) 
                window_handles = driver.window_handles
                if len(window_handles) == 1:
                    logt("윈도우 전환 실패 => 재시도 :윈도우 갯수={len(window_handles)}") 
                    raise BizException(f"[접수증] 윈도우 전환 실패 - {e}")
            
            # 정상 진행
            logt(f"윈도우 갯수= {len(window_handles)}") 
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)
            #driver.set_window_size(850, 860)

            # 파일다운로드: 
            file_type = "HT_DOWN_3"
            file_download(ht_info, file_type)
            
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
        except Exception as e:
            raise BizException(f"[접수증] 윈도우 전환 실패 - {e}")
        

        # -----------------------------------------------------------------
        # 납부서
        # -----------------------------------------------------------------
        #if ht_info['total_income_amount'] > 
        if True:
            logt('# -----------------------------------------------------------------')
            logt('#                        4) 납부서                                 ')
            logt('# -----------------------------------------------------------------')

            # ttirnam101DVOListDes_cell_0_13 납부서_버튼_text => "보기"
            # ttirnam101DVOListDes_cell_0_38 납부여부 => 'N', 'Y', '-'
            logt(f"현재 양도인 정보 : {ht_tt_seq}, {ht_info['holder_nm']}, {ht_info['holder_ssn1']}{ht_info['holder_ssn2']}")

            logt("4) 납부서 > 작업프레임 이동: txppIframe", 0.5)
            driver.switch_to.frame("txppIframe")

            납부여부 = ''
            # Y,N인 경우는 아래 A태그 있음, '-' A태그 없음
            ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_38 > span")  
            납부여부 = ele.text
            logt(f"납부여부 ====> [{납부여부}]")
            if 납부여부 == 'Y':
                dbjob.update_htTt_hometaxPaidYn(ht_tt_seq, 'Y')
                raise BizNextLoopException("납부", "납부완료", "S")
            elif 납부여부 == '-':
                logt(f"납부서 없음 !!")
                raise BizNextLoopException("납부", "납부서 없음", "S")
                
            # 주의) 납부서가 없을 수 있음
            납부서_버튼_text = ''
            try :
                ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_13 > span > button")
                납부서_버튼_text = ele.text
                logt(f"납부서 버튼명 ====> [{납부서_버튼_text}]")
                if 납부서_버튼_text.strip() == '보기':
                    ele.click()
            except Exception as e:
                logt(f"납부서 버튼 클릭 중 오류 발생 : {str(e)[:100]}")
                raise BizException("납부할금액없음", f"납부서 Click불가: [{납부서_버튼_text}]")


            logt("납부서 작업프레임 이동: UTERNAAZ70_iframe", 1.5)
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
                logt("납부서 이미지 클릭", 1)
                driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_3 > img").click()
                
                logt("윈도우 로딩 대기", 1.5)
                window_handles = driver.window_handles
                if len(window_handles) == 1:
                    logt("납부서 클릭(재시도)", 0.1)
                    driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_3 > img").click()

                    logt("윈도우 전환 재시도", 2) 
                    window_handles = driver.window_handles
                    if len(window_handles) == 1:
                        logt("윈도우 전환 실패 => 재시도 :윈도우 갯수={len(window_handles)}") 
                        raise BizException(f"[납부서] 윈도우 전환 실패 - {e}")
                    else:
                        driver.switch_to.window(window_handles[1])
                        driver.set_window_position(0,0)
                        #driver.set_window_size(810, 880)

                # 정상진행
                logt(f"윈도우 갯수= {len(window_handles)}") 
                driver.switch_to.window(window_handles[1])
                driver.set_window_position(0,0)
                #driver.set_window_size(810, 880)
            except Exception as e:
                raise BizException("납부서", f"{e}")

            # 파일다운로드:
            file_type = "HT_DOWN_4"
            file_download(ht_info, file_type)


            logt(f"팝업윈도우 닫고 => 메인윈도우 전환")     
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            logt("작업프레임 이동: txppIframe", 0.2)
            driver.switch_to.frame("txppIframe")
            logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
            driver.switch_to.frame("UTERNAAZ70_iframe")

            # 납부서 2 (분납이 있는 경우) -------------------------------------------
            납부서개수 = len(driver.find_elements(By.CSS_SELECTOR, "#ttirnal111DVOListDes_body_tbody > tr"))
            logt(f"납부서 개수 = {납부서개수}") 
            if 납부서개수 == 2:
                try :
                    logt("납부서2(분납) 이미지 클릭", 0.5)
                    driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_1_3 > img").click()

                    logt("윈도우 로딩 대기", 2) 
                    window_handles = driver.window_handles


                    logt("윈도우 갯수= %d" % len(window_handles)) 
                    driver.switch_to.window(window_handles[1])
                    driver.set_window_position(0,0)
                    #driver.set_window_size(810, 880)

                    # 파일다운로드:
                    file_type = "HT_DOWN_8"
                    file_download(ht_info, file_type)

                    logt(f"팝업윈도우 닫고 => 메인윈도우 전환")     
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    logt("윈도우 갯수= %d" % len(window_handles)) 

                    logt("작업프레임 이동: txppIframe", 0.2)
                    driver.switch_to.frame("txppIframe")
                    logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
                    driver.switch_to.frame("UTERNAAZ70_iframe")

                    if ht_info['data_type'] == 'SEMI' or ht_info['data_type'] == 'MANUAL':
                        분납금1 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1 > span").text
                        분납금2 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_1_1 > span").text
                        분납금1 = int(분납금1.strip().replace(',', ''))
                        분납금2 = int(분납금2.strip().replace(',', ''))
                        logt(f"반자동 분납금 업데이트 : 분납1={분납금1}, 분납2={분납금2}")
                        dbjob.update_HtTt_installment(ht_tt_seq, 분납금1, 분납금2)
                        dbjob.update_HtTt_hometaxIncomeTax(ht_tt_seq, 분납금1 + 분납금2)

                except Exception as e:
                    raise BizException("납분서(분납)", f"{e}")
            else:
                logt("납부서(분납) 없음 => 정상")
                if ht_info['data_type'] == 'SEMI' or ht_info['data_type'] == 'MANUAL':
                    분납금1 = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_1 > span").text
                    분납금1 = int(분납금1.strip().replace(',', ''))
                    분납금2 = 0
                    logt(f"반자동 분납금 업데이트 : 분납1={분납금1}, 분납2={분납금2}")
                    dbjob.update_HtTt_hometaxIncomeTax(ht_tt_seq, 분납금1 + 분납금2)

            # ---------------------------------------------------------------------------
            
            # 팝업레이어 닫기
            logt("팝업레이어 닫기", 1.5)
            # (주의)닫기(trigger1)는 문서내 2개 있음.. 팝업창의 x 클릭으로 대체
            try:
                #driver.find_element(By.CSS_SELECTOR, "#trigger1").click()
                driver.execute_script("$('#trigger1').click();")
            except:
                logt("팝업레이어 닫기 오류 => 재시도", 1)
                driver.switch_to.default_content()
                driver.switch_to.frame("txppIframe")
                logt("작업프레임 이동: UTERNAAZ70_iframe", 0.2)
                driver.switch_to.frame("UTERNAAZ70_iframe")           
                driver.find_element(By.CSS_SELECTOR, "#trigger2").click()

            #logt("작업프레임 이동: txppIframe", 0.5)
            #driver.switch_to.frame("txppIframe")
            #logt(driver.window_handles)


    else :
        # 접수된 신고가 없음
        step_cd = ht_info['step_cd']
        au1 = ht_info['au1']
        if step_cd == "REPORT" and au1 == "S":
            dbjob.update_HtTt_AuX(1, ht_tt_seq, 'E', '신고가 존재하지 않습니다. 재신청 하시기 바랍니다.')
            raise BizException("미제출", "신고서가 제출되지 않았습니다.")


if __name__ == '__main__':
    if driver:
        driver.set_window_size(1200, 990) # 실제 적용시 : 990
        로그인_이름 = driver.find_element(By.ID, 'hdTxtUserNm').text
        logt(f"현재 담당자={user_info['id']}, ID={user_info['name']}, 로그인 이름 = {로그인_이름}")
        
        if 로그인_이름.find('세무법인') == -1:
            logt("로그인 실패로 재로그인 진행")
            driver.close()
            dbjob.reset_user_hometax_cookie(user_info['id'])
            logt(f'로그인 쿠키 초기화')
            (driver, user_info, verify_stamp) = step_common.init_step_job()

        do_task(driver, verify_stamp) 
    
    logt(f"=======================================================")
    logt(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>       2단계 작업 완료")
    logt(f"=======================================================")

    if conn:
        conn.close()
            
    exit(0)
