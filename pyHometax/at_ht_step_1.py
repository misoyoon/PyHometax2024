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
AU_X = '1'
(driver, user_info, verify_stamp) = step_common.init_step_job()
# -------------------------------------------------------------

def do_task(driver: WebDriver, user_info, verify_stamp):

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
                logi(f'Agent Check : Status={status_cd} ==> 작업 중지')
                if status_cd == 'SW':
                    dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'SW 신호로 STOP 합니다.')
                break
        else:
            dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'verify_stamp 변경으로 STOP 합니다.')
            

        # 홈택스 신고서제출 자료            
        ht_info = dbjob.select_next_au1(group_id, worker_id, seq_where_start, seq_where_end)
        
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
        # dbjob.update_htTt_aux_running(ht_tt_seq, au_x)
        
        # 1단계 진행상태 DB 넣기 => 향후 결정할 것
        dbjob.delete_auHistory_byKey(ht_tt_seq, au_x)

        # 담당자 홈택스로그인 가능 여부 확인용(1,2,5 단계만)
        if au_x == '1' or au_x == '2' or au_x == '5' :
            dbjob.update_user_cookieModiDt(worker_id)
        

        logi("******************************************************************************************************************")
        logt("JOB_COUNT=%s : 양도인=%s, HT_TT_SEQ=%d" % (job_cnt, ht_info['holder_nm'], ht_info['ht_tt_seq']))
        logi("******************************************************************************************************************")

        #print(dbjob.select_HtTtFile_ByPk(ht_info['source_file_seq']))

        # logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
        # url = 'https://www.hometax.go.kr/websquare세무대리인 여부 확인websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
        # driver.get(url)
        # logt("iframe 이동", 3)
        # sc.move_iframe(driver)

        # 확정신고 클릭
        try: 
            logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
            url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
            driver.get(url)
            logt("iframe 이동", 3)
            sc.move_iframe(driver)
            go_확정신고(driver)

        except Exception as e:
            logt(f"예외발생 : go_확정신고() => 처음부터 재시도 - {e}")
            logt("처음부터 다시 시작", 0.5)

            try:
                logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
                url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
                driver.get(url)
                logt("iframe 이동", 3)
                sc.move_iframe(driver)
                go_확정신고(driver)                    
            except:
                loge("신고/납부 메뉴 이동 오류로 다음 신청자로 continue함")
                continue

        # FIXME 테스트 용도
        #logt("[클릭] 기한후신고", 0.5)
        #driver.find_element(By.ID, 'textbox86564').click()
        


        # -----------------------------------------------------------------------
        # Step 1. 세금신고 : 기본정보(양도인)
        # -----------------------------------------------------------------------
        try:
            do_step1(driver, ht_info)
        
        except BizException as e:
            if e.name == "기존신청서삭제":
                logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
                url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
                driver.get(url)
                logt("iframe 이동", 3)
                sc.move_iframe(driver)
                go_확정신고(driver)     

                do_step1(driver, ht_info)
            else:
                dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', '')

        except Exception as e:
            loge(f'{e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', '')
        
        else:  # 오류없이 정상 처리시
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S', '')
        # -----------------------------------------------------------------------



        logi("####### 한건처리 완료 #######")            
    # End of while        
    



# 양도소득세 신고확정 메뉴 클릭
def go_확정신고(driver: WebDriver):
    logt("------------------------------------------------------------------")
    logt("FUNC: go_확정신고()")
    logt("------------------------------------------------------------------")    
    #sc.move_iframe(driver)
    
    
    logt("페이지이동: 일반신고 => 확정신고", 2)
    driver.find_element(By.ID, 'textbox8644').click()
    
    logt("페이지이동: 정기신고", 1)
    driver.find_element(By.ID, 'textbox163292957').click()
    logt("단순대기", 1)
    


# Step 1. 세금신고 : 기본정보(양도인)
def do_step1(driver: WebDriver, ht_info):
    #print(ht_info)
    
    window_handles = driver.window_handles
    main_window_handle = window_handles[0]

    logt("------------------------------------------------------------------")
    logt("다음 단계 이동: 01.기본정보(양도인)", 0.5)
    logt("------------------------------------------------------------------")

    ht_tt_seq = ht_info['ht_tt_seq']
    
    # 홈택스 정보 초기화
    dbjob.update_HtTt_initHometaxInfo(ht_tt_seq)
    
    # 작업폴더 : 예 - D:\WWW\JNK\files\hometax\003\003259\work\
    work_dir = ht_file.get_work_dir_by_htTtSeq(ht_tt_seq)

    try:
        time.sleep(0.2)
        팝업체크_유무 = sc.move_iframe(driver, 'UTERNAAV52_iframe')

        if 팝업체크_유무:
            logt("팝업체크 : 확인하였습니다.")
            driver.find_element(By.ID, 'chkYn_input_0').click()
            time.sleep(0.1)

            #하루동안 열지 않음
            driver.find_element(By.ID, 'checkbox1_input_0').click()
            time.sleep(0.1)

            # 클릭 : 닫기
            driver.find_element(By.ID, 'btnClose2').click()
            time.sleep(0.3) 
    except Exception as e:
        logt("iframe 이동 오류: 확인하였습니다.")

    # iframe이동 : 메인
    driver.switch_to.default_content()
    sc.move_iframe(driver, 'txppIframe')

    # 주민번호 입력
    holder_ssn1 = ht_info['holder_ssn1']
    holder_ssn2 = ht_info['holder_ssn2']
    logt("값입력 : 주민번호 %s%s" % (holder_ssn1, holder_ssn2), 0.2)
    driver.find_element(By.ID, 'edtResNo0').send_keys(holder_ssn1)
    driver.find_element(By.ID, 'edtResNo1').send_keys(holder_ssn2)

    # 주민번호 확인 => [확인]버튼 클릭
    logt("주민번호 확인 => [확인]버튼 클릭", 3)
    try :
        driver.find_element(By.ID, 'btnResNo').click()
    except:
        logt("주민번호 확인 재클릭=> [확인]버튼 클릭", 1.5)
        driver.find_element(By.ID, 'btnResNo').click()

    try:
        logt("팝업확인", 1)
        #alert = driver.switch_to.alert
        alert = driver.switch_to.alert
        alert_msg = alert.text
        logt("Alert메세지: %s" % alert_msg)

        if alert_msg.find("신고인(양도인)이 확인되었습니다.") >= 0  :
            ...
        elif alert_msg.find("납세자 정보가 존재하지 않습니다.") > -1 :
            dbjob.insert_auHistory(ht_tt_seq, ht_info['reg_id'], AU_X, "주민번호오류", "납세자 정보가 존재하지 않습니다")
            raise BizException("주민번호오류", "납세자 정보가 존재하지 않습니다")

        alert.accept()
    except BizException as e:
        logt("Exception발생: %s" % e)
        raise 
    except Exception as e:
        logt("Exception발생: %s" % e)
        dbjob.insert_auHistory(ht_tt_seq, ht_info['reg_id'], AU_X, "주민번호오류", "")
        raise BizException("주민번호오류","")

    # FIXME 테스트 주석처리
    logt("Select선택: 국외", 0.5)
    driver.find_element(By.CSS_SELECTOR, '#cmbAbrdAstsYn > option:nth-child(3)').click()
    logt("Select선택: 국외주식", 0.5)
    driver.find_element(By.CSS_SELECTOR, '#cmbTrnRtnDdtClCd > option:nth-child(4)').click()
    
    #logt("Select선택: 2022", 0.5)
    #driver.find_element(By.CSS_SELECTOR, '#cmbTrnYr > option:nth-child(3)').click()
    #logt("Select선택: 한반기", 0.5)
    #driver.find_element(By.CSS_SELECTOR, '#cmbTrnHt > option:nth-child(3)').click()
    
    
    # SELECT 선택: 양도자산종류 > 국외
    #logt("Select선택: 국외",1)
    #driver.find_element(By.CSS_SELECTOR, '#cmbAbrdAstsYn > option:nth-child(3)').click()

    # SELECT 선택 : 국외주식
    #logt("Select선택: 국외주식", 1)
    #driver.find_element(By.CSS_SELECTOR, '#cmbTrnRtnDdtClCd > option:nth-child(4)').click()

    # 팝업창 유무확인
    logt("Alert대기: 권한이 없습니다", 1)
    try:
        alert = driver.switch_to.alert
        alert_msg = alert.text
        logt("Alert확인: %s" % alert_msg)
        alert.accept()
    except Exception as e:
        logt(f'(발생가능예상) 예외가 발생했습니다.')

    # 간혹발생하지만 필수는 아님
    # sc.click_alert(driver, "권한이 없습니다", 1)

    # 클릭 : 조회
    logt("클릭: 양도연월 옆의 [조회]", 0.5)
    driver.find_element(By.ID, 'btnTrnYm').click()
    time.sleep(2)

    # 이전자료 불러오기 혹은 신규등록
    is_call_prev_data = False


    logt("Alert 대기", 1)
    alert = driver.switch_to.alert
    alert_msg = alert.text

    logt(f"Alter메세지={alert_msg}   =>> 경우에 따라 다르게 동작됨")
    # 예상2가지
    #   1)신규등록  => 확인버튼 누르고 계속 진행
    #   2)기존자료 불러오기 => 
    if alert_msg.find("신규 입력하시겠습니까?") == 0 :
        logt("Case1 진행: 신규등록")
        alert.accept()
    else :
        logt("Case2 진행: 작성중인.... => 이전자료 불러오기")

        # 2023년 재신고시 등장한 새로운 케이스 (없지만 간혹 나옴)
        try:
            if alert_msg.find("납부기한연장 신청이 접수된 직전 신고서가 존재합니다") == 0 :
                alert.accept()
                alert = driver.switch_to.alert
                alert_msg = alert.text
        except:
            ...



        if alert_msg.find("작성중인 신고서가 존재합니다.") == 0 :
            sc.click_alert(driver, "작성중인 신고서가 존재합니다.", 0.5)
        
            # 또다른 alert
            #sc.click_alert(driver, "신고인(양도인)이 확인되었습니다", 2)
            
            
            is_call_prev_data = True

            # 개발 : 단계에서는 불러와서 진행하기
            # 운영 : 삭제 후 다시 작성
            if True:
                # 새로작성하기
                logt("클릭: [새로작성하기]", 0.5)
                driver.find_element(By.ID, 'btnClear').click()

                # alert
                logt("Alert대기: 작성중인 신고서는 삭제가 가능합니다. 삭제하시겠습니까?", 0.5)
                alert = driver.switch_to.alert
                alert_msg = alert.text
                logt("Alert확인: %s" % alert_msg)
                alert.accept()

                # 신청서 취소 alert
                logt("Alert대기: 신고서의 취소가 완료되었습니다.", 0.5)
                alert = driver.switch_to.alert
                alert_msg = alert.text
                logt("Alert확인: %s" % alert_msg)
                alert.accept()

                # 처음부터 다시 시작하기
                logt("Exception발생 : 새로작성")
                raise BizException("기존신청서삭제", "기존에 작성중인 신청서를 삭제")
        elif alert_msg.find("해당 과세기간에 이미 제출된 신고서가 있습니다") == 0 :
            sc.click_alert(driver, "해당 과세기간에 이미 제출된 신고서가 있습니다", 0.2)
            # 취소클릭
            sc.click_alert_dismiss(driver, "기존 제출하신 신고서를 불러오려면 확인을 눌러주세요.", 0.3)
            time.sleep(0.2)
            try:
                sc.click_alert(driver, "신고서의 취소가 완료되었습니다", 0.2)
            except:
                logi("Alert skipped")
        else:
            raise BizException("기타 메세지", alert_msg)



    # 이전자료 불러오기 혹은 신규등록 (위의 상황에 따라 달리 실행)
    if is_call_prev_data == False :

        # 전화번호 입력
        logt("양도인 전화번호 입력", 0.1)
        hand_phone_num = ht_info['holder_cellphone']
        logt(f"양도인 전화번호 입력={hand_phone_num}")
        try:
            phone_num = hand_phone_num.split("-")
            driver.find_element(By.ID, 'edtMpno0').clear()
            driver.find_element(By.ID, 'edtMpno1').clear()
            driver.find_element(By.ID, 'edtMpno2').clear()
            driver.find_element(By.ID, 'edtMpno0').send_keys(phone_num[0])
            driver.find_element(By.ID, 'edtMpno1').send_keys(phone_num[1])
            driver.find_element(By.ID, 'edtMpno2').send_keys(phone_num[2])
        except Exception as e:
            logt("예외발생: %s" % e)
            logt(f"양도인 전화번호가 없어서 회사전화번호로 대체")
            
            worker_tel = ht_info['worker_tel']
            li_worker_tel = worker_tel.split("-")
            driver.find_element(By.ID, 'edtMpno0').clear()
            driver.find_element(By.ID, 'edtMpno1').clear()
            driver.find_element(By.ID, 'edtMpno2').clear()
            driver.find_element(By.ID, 'edtMpno0').send_keys(li_worker_tel[0])
            driver.find_element(By.ID, 'edtMpno1').send_keys(li_worker_tel[1])
            driver.find_element(By.ID, 'edtMpno2').send_keys(li_worker_tel[2])

        logt("내외국인/거주구분 선택", 0.1)
        try:
            #time.sleep(0.2)
            driver.find_element(By.CSS_SELECTOR, '#cmbNnfClCd > option:nth-child(2)').click()
            #time.sleep(0.2)
            driver.find_element(By.CSS_SELECTOR, '#cmbRsdtClCd > option:nth-child(2)').click()
        except Exception as e:
            logt("예외발생: %s" % e)
            raise BizException("내외국인/거주구분 선택")



        # 세무대리인 전화번호
        driver.find_element(By.ID, 'edtTxaaFnm').clear()
        driver.find_element(By.ID, 'edtTxaaBhdt_input').clear()
        
        #세무대리인 정보 입력 # FIXME 하드코딩 202405
        driver.find_element(By.ID, 'edtTxaaFnm').send_keys('김경수')
        driver.find_element(By.ID, 'edtTxaaBhdt_input').send_keys('19791203')
        worker_tel = ht_info['worker_tel']
        li_worker_tel = worker_tel.split("-")
        logt("INPUT: 세무대리인 전화번호= %s" % worker_tel, 0.1)
        try:
            driver.find_element(By.ID, 'edtTxaaTelno0').clear()
            driver.find_element(By.ID, 'edtTxaaTelno1').clear()
            driver.find_element(By.ID, 'edtTxaaTelno2').clear()
            driver.find_element(By.ID, 'edtTxaaTelno0').send_keys(li_worker_tel[0])
            driver.find_element(By.ID, 'edtTxaaTelno1').send_keys(li_worker_tel[1])
            driver.find_element(By.ID, 'edtTxaaTelno2').send_keys(li_worker_tel[2])
        except Exception as e:
            raise BizException("세무대리인 전화번호 입력", e)

    else:
        logt("이전 자료 불러와서 주소등 기타 정보 입력은 건너뛰기")


    # 클릭 : 저장 후 다음이동
    logt("클릭 : [저장 후 다음이동]", 1)
    driver.find_element(By.ID, 'btnProcess').click()

    logt("단순대기", 0.5)
    alert = driver.switch_to.alert
    alert_msg = alert.text
    if alert_msg.find("관할서가") == 0 :
        logt("예외발생: 관할서오류:" + alert_msg )
        alert.accept()
        raise BizException("관할지오류", alert_msg)
    else :
        # 저장 후 다음화면으로 이동하시겠습니까?
        logt("팝업확인: 저장 후 다음이동", 0.5)
        alert.accept()


    # -------------------------------------------------------------------------
    # 02.기본정보(양수인)  => 그냥 통과시킴
    # -------------------------------------------------------------------------
    logi("------------------------------------------------------------------")
    logt("다음 단계 이동: 02.기본정보(양수인)", 1)
    logi("------------------------------------------------------------------")
    #logt("IFRAME이동 : 메인", 1)
    #sc.move_iframe(driver) 
    
    logt("클릭 : [저장 후 다음이동]", 1)
    driver.find_element(By.ID, 'btnProcess').click()

    # -------------------------------------------------------------------------
    # 04.주식등양도소득금액계산명세서
    # -------------------------------------------------------------------------
    logi("------------------------------------------------------------------")
    logt("다음 단계 이동: 04.주식등양도소득금액계산명세서", 1)
    logi("------------------------------------------------------------------")
    #logt("IFRAME이동 : 메인", 1)
    #sc.move_iframe(driver) 

    # 거래내역 리스트
    trade_list = dbjob.select_HtTtList_by_htTtSeq(ht_tt_seq)
    for trade in trade_list:
        # FIXME 해외주식에 맞게 수정하기
        # 사업자번호
        #sc.set_input_value_by_id(driver, 'edtStocPblCrpTin1', '617',  '사업자번호1', 0 )
        #sc.set_input_value_by_id(driver, 'edtStocPblCrpTin2', '81',   '사업자번호2', 0 )
        #sc.set_input_value_by_id(driver, 'edtStocPblCrpTin3', '17517','사업자번호3', 0 )
        
        #sc.click_button_by_id(driver, 'btnStocPblCrpTin', '사업자등록번호 조회', 0)

        # 클릭: 확인
        #sc.click_alert(driver, '사업자등록번호가 확인되었습니다.')

        
        # 국가조회 버튼 클릭
        sc.click_button_by_id(driver, 'btnAbrdAstsNtn', '국가조회', 0.5)
        time.sleep(0.5)

        sc.move_iframe(driver, 'UTECMAAA04_iframe', 0.1)
        sc.set_input_value_by_id(driver, 'ntnCd',  'US', '국가코드', 1.0)
        sc.click_button_by_id(driver, 'trigger5', '조회', 1)
        # 결과조회 테이블에서 첫번째 결과인 미국 선택
        time.sleep(0.3)
        ele = driver.find_element(By.CSS_SELECTOR, "#grdNtnCd_cell_0_2 > button")
        ele.click()        
        
        # 상위프레임 이동
        time.sleep(0.5)
        driver.switch_to.parent_frame()
        #sc.select_by_id(driver, 'cmbTrnAstsKndClCd', 2, '양도물건 종류(코드)', 0)
        #sc.select_by_id(driver, 'cmbTxrteCd', 2, '세율구분', 0)
        sc.set_select_by_option_index(driver, 'cmbStocKndCd', 2, '(4)주식등 종류코드', 0.5)
        sc.set_select_by_option_index(driver, 'cmbAcqTypeCd', 2, '(6)취득유형', 0)


        # FIXME 20231231, 20230101 점검
        sc.set_input_value_by_id(driver, 'edtAcqTypeClTrnStocCnt', str(trade['sell_qnt']) , '(7)양도주식 수', 0 )
        #sc.set_input_value_by_id(driver, 'edtTrnDt_input', str(trade['sell_date']).replace('-', ''), '(8)양도일자', 0)
        sc.set_input_value_by_id(driver, 'edtTrnDt_input', '20231231', '(8)양도일자', 0)
        #sc.set_input_value_by_id(driver, 'edtEcstTrnAmt',  str(trade['sell_per_price']), '(9)주당양도가액', 0)
        sc.set_input_value_by_id(driver, 'edtTrnAmt',      str(trade['sell_amount']), '(10)양도가액')
        #sc.set_input_value_by_id(driver, 'edtAcqDt_input', str(trade['buy_date']).replace('-', ''), '(11) 취득일자', 0)
        sc.set_input_value_by_id(driver, 'edtAcqDt_input', '20230101', '(11) 취득일자', 0)
        #sc.set_input_value_by_id(driver, 'edtEcstAcqAmt',  str(trade['buy_per_price']), '(12) 주당취득가액', 0)
        sc.set_input_value_by_id(driver, 'edtAcqAmt',      str(trade['buy_amount']), '(13) 취득가액')
        sc.set_input_value_by_id(driver, 'edtNdXps',       str(trade['fees_amount']), '(14) 필요경비'), 0
        
        # 추가히기 버튼 클릭        
        sc.click_button_by_id(driver, 'trigger101', '등록(추가)하기')
        alert_ret = sc.click_alert(driver, '양도가액이 취득유형별 양도주식수 * 주당양도가액과 같지 않습니다.')
        alert_ret = sc.click_alert(driver, '취득가액이 취득유형별 양도주식수 * 주당취득가액과 같지 않습니다.')
        alert_ret = sc.click_alert(driver, '입력한 주식양도소득금액명세서를 등록하시겠습니까?')
        
    sc.click_button_by_id(driver, 'trigger2', '저장 후 다음이동')
    sc.click_alert(driver, '저장 하시겠습니까?')
    sc.click_alert(driver, '다음화면으로 이동하시겠습니까?')

    

    # -------------------------------------------------------------------------
    # 06.세액계산 및 확인 
    # -------------------------------------------------------------------------
    logi("------------------------------------------------------------------")
    logt("다음 단계 이동: 06.세액계산 및 확인 ", 1)
    logi("------------------------------------------------------------------")
    

    # FIXME 삭제예정 (기한후 신고로 테스트하기 때문에 발생하는 코드)
    #driver.find_element(By.ID, 'edtRtnsAdtTxamt').clear()
    #driver.find_element(By.ID, 'edtPmtInsyAdtTxamt').clear()
    #sc.set_input_value_by_id(driver, 'edtRtnsAdtTxamt', "100000" , '테스트용(삭졔예정)' )
    #sc.set_input_value_by_id(driver, 'edtPmtInsyAdtTxamt', "100000" , '테스트용(삭졔예정)' )

    # 기본공제금액 입력
    driver.find_element(By.ID, 'edtTriBscDdcAmt').clear()
    driver.find_element(By.ID, 'edtTriBscDdcAmt').send_keys("2500000")
    # (주의)재계산 시간을 벌기 위해 다른 곳에 들렸다가 이동하기 
    driver.find_element(By.ID, 'edtReTxamt').send_keys("0")   #edtReTxamt: 감면세액
    time.sleep(0.5)


    # 250만원이 있는지 없는지 검사 
    input = driver.find_element(By.ID, 'edtTriBscDdcAmt')
    감면액확인 = input.get_attribute('value')
    logt("입력된 공제금액 확인=%s" % 감면액확인)
    if 감면액확인 == "0" or 감면액확인 == '':
        driver.find_element(By.ID, 'edtTriBscDdcAmt').clear()
        driver.find_element(By.ID, 'edtTriBscDdcAmt').send_keys("2500000")
        driver.find_element(By.ID, 'edtReTxamt').send_keys("0")

    time.sleep(0.5)
    sc.click_button_by_id(driver, 'trigger28', '등록하기')
    
    try:
        alert= driver.switch_to.alert
        alert_text = alert.text
        if alert_text.find('양도소득기본공제가 입력되지 않았습니다. 계속 진행하시겠습니까?')>=0:
            alert.dismiss()
            driver.find_element(By.ID, 'edtTriBscDdcAmt').clear()
            driver.find_element(By.ID, 'edtTriBscDdcAmt').send_keys("2500000")
            driver.find_element(By.ID, 'edtReTxamt').send_keys("0")
            
            sc.click_button_by_id(driver, 'trigger28', '등록하기')
        else:
            alert.accept()  
    except Exception as e:
        ...


    
    #trigger28 
    #cap_image_1 = work_dir + "capture1.png"
    #logt("이미지캡쳐: %s" %  cap_image_1)
    #driver.save_screenshot(cap_image_1)
        
    sc.click_button_by_id(driver, 'btnProcess', '저장 후 다음이동')
    sc.click_alert(driver, "저장 후 다음화면으로 이동하시겠습니까?", 0.5)

    # -------------------------------------------------------------------------
    # 07.신고서제출 
    # -------------------------------------------------------------------------
    logi("------------------------------------------------------------------")
    logt("다음 단계 이동: 07.신고서제출  ", 3)
    logi("------------------------------------------------------------------")



    #sc.click_button_by_id(driver, 'btnProcess', '신고서 제출')
    #sc.click_alert(driver, "신고서를 제출하시겠습니까?", 0.5)
    감면액확인 = driver.find_element(By.ID, 'genTbody_3_genTr_1_txtItem').text
    if 감면액확인 != '2,500,000':
        dbjob.insert_auHistory(ht_tt_seq, ht_info['reg_id'], AU_X, f"감면액 입력 오류로 이번건 종료 후 다음 처리")
        return
    
    # 분납계산하기
    분납액1 = 0
    분납액2 = 0
    총양도세액 = driver.find_element(By.ID, 'edtTritxVlpyTxamt').get_attribute('value')
    총양도세액 = int(총양도세액.strip().replace(',',''))

    dbjob.update_HtTt_hometaxIncomeTax(ht_tt_seq, 총양도세액)
    if 총양도세액 >= 20_000_000:
        분납액2 = math.floor(총양도세액 / 2)
        분납액1 = 총양도세액 - 분납액2
        driver.find_element(By.ID, 'edtTritxInpmPaygSchuTxamt').send_keys(분납액2)
        dbjob.update_HtTt_installment(ht_tt_seq, 분납액1, 분납액2)
    elif 총양도세액 >= 10_000_000:
        분납액2 = 총양도세액 - 10_000_000
        분납액1 = 10_000_000
        driver.find_element(By.ID, 'edtTritxInpmPaygSchuTxamt').send_keys(분납액2)
        dbjob.update_HtTt_installment(ht_tt_seq, 분납액1, 분납액2)


    # 신고서 제출
    sc.click_button_by_id(driver, 'btnProcess', '신고서 제출')
    sc.click_alert(driver, '신고서를 제출하시겠습니까?')
    sc.click_alert(driver, "신고서 제출이 완료되었습니다", 0.5)

    logt("단순대기: 팝업레이어 & alter동시 뜸", 2)

    try :
        sc.click_alert(driver, "접수증을 확인한 후에 [신고내역 조회")
    except:
        logt("클릭 except 1")

    # 이상한게도 한번에는 해당 alert을 얻을 수 없음
    try :
        sc.click_alert(driver, "접수증을 확인한 후에 [신고내역 조회")
    except:
        logt("클릭 except 2")


    # iframe이동: 양도소득세 신고서 접수증
    logt("iframe 이동")
    sc.move_iframe(driver, "UTERNAAZ01_iframe") 


    # 홈택스 접수번호 저장
    홈택스접수번호 = driver.find_element(By.ID, 'textbox893').text
    logi(f'홈택스접수번호={홈택스접수번호}')
    dbjob.update_HtTt_hometaxRegNum(ht_tt_seq, 홈택스접수번호)


    logt("팝업체크박스 체크 : 확인하였습니다.", 1)
    driver.find_element(By.ID, 'checkbox2_input_0').click()
    
    sc.click_alert(driver, "개인지방소득세는 별도 신고해야 합니다.", 1)

    logi(f"{ht_tt_seq} 번 DB성공처리")
    dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S', '')

    # 팝업iframe 닫기
    logt("클릭: [닫기] 팝업iframe", 1)
    driver.find_element(By.ID, 'trigger15').click()

    # # 증빙서류 제출
    # logt("클릭: [증빙서류 제출]", 0.5)
    # driver.find_element(By.ID, 'trigger22').click()
    
    # sc.click_alert(driver, "증빙서류 제출 화면으로 이동하시겠습니까?", 0.5)


    try :    
        logt("등록완료 후 팝업윈도우 닫기", 0.5)
        window_handles = driver.window_handles
        logd(window_handles)
        if len(window_handles) > 1:
            for tmp_win_handle in window_handles:
                logd(tmp_win_handle)
                if tmp_win_handle != main_window_handle:
                    logd("다른 윈도우")
                    driver.switch_to.window(tmp_win_handle)
                    driver.close()
                else :
                    logd("메인 윈도우")

            driver.switch_to.window(main_window_handle)
    except :
        logt("작업완료 팝업윈도우 close exception")




if __name__ == '__main__':
    if driver:
        do_task(driver, user_info, verify_stamp) 
    
    logi(f"{AU_X}단계 작업 완료")

    if conn:
        conn.close()
            
    exit(0)

