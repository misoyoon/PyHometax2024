from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

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
AU_X = '3'
(driver, user_info, verify_stamp) = step_common.init_step_job()
# -------------------------------------------------------------


def do_task(driver: WebDriver, user_info, verify_stamp):
    연속실패건수 = 0
    job_cnt = 0
    while True:
        job_cnt += 1
        
        # driver 확인
        if sc.check_availabe_driver(driver) == False:
            logt("driver가 close 된 것으로 판단 ==> 작업 중지")
            dbjob.update_autoManager_statusCd(auto_manager_id, 'S')
            return
        
        try:
            로그인연장 = driver.find_element(By.CSS_SELECTOR, "#header > div.header-menu > div > div.login-time > button").text 
            if 로그인연장 != '로그인연장':
                logt("로그인 확인 불가로 재실행 필요 ==> 작업 중지")
                return # 단순하게 재로그인 처리를 위해 다시 시도하기
        except:
            logt("로그인 확인 불가로 재실행 필요 ==> 작업 중지")
            return # 단순하게 재로그인 처리를 위해 다시 시도하기
            
        
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
                    dbjob.update_autoManager_statusCd(auto_manager_id, 'S')
                return
        else:
            logt("verify_stamp 변경으로 STOP 합니다.")
            dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'verify_stamp 변경으로 STOP 합니다.')
            return
            
                            
        # 홈택스 신고서제출 자료            
        ht_info = dbjob.select_next_au3(group_id, worker_id, seq_where_start, seq_where_end)

        if not ht_info:
            logt("처리할 자료가 없어서 FINISH 합니다. ==> 작업 중지")
            dbjob.update_autoManager_statusCd(auto_manager_id, 'F', '처리할 자료가 없어서 FINISH 합니다.')
            return

        #담당자 전화번호 추가
        ht_info['worker_tel'] = user_info['tel']
        ht_tt_seq = ht_info['ht_tt_seq']

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
        logt("3단계 : JOB_COUNT=%s : HT_TT_SEQ=%d, 양도인=%s, SSN=%s-%s" % (job_cnt, ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
        logt("******************************************************************************************************************")

        try:
            # 양도소득분 신고
            driver.get('https://www.wetax.go.kr/etr/lit/b0703/B070301M01.do')
            time.sleep(1)
        
            # 오늘하루 그만보기 click
            try:
                xpath = """//span[text()='오늘하루 그만보기']"""
                text_ele = driver.find_element(By.XPATH, xpath)
                if text_ele and text_ele.is_displayed():
                    # 체크하기
                    text_ele.click() 
                    # 닫기 클릭
                    driver.find_element(By.CSS_SELECTOR, '#nos_pop > div.pop_foot > a').click()
            except:
                ...        
        
            # TODO 사전계발시 임시코드
            # (예정신고)신고서 작성하기
            #driver.find_element(By.CSS_SELECTOR, '#btnPreDclr > span').click()
            # (확정신고)신고서 작성하기 # TODO 필수주석풀기
            driver.find_element(By.CSS_SELECTOR, '#btnFinalDclr > span').click()

            다음버튼_대기시간 = 1.5
            # ------------------------------------------------
            logt("##### 1.신고인", 다음버튼_대기시간)
            # ------------------------------------------------
            
            # 모달팝업이 뜰 경우 닫기 : 임시저장 된 신고서가 있습니다. 확인하시려면 신고내역에서 확인하시기 바랍니다.
            try:
                modal = driver.find_element(By.CSS_SELECTOR, '#divAlertPop')
                if modal:
                    clazz = modal.get_attribute('class')
                    if clazz == 'layer-info initModal on':
                        driver.find_element(By.CSS_SELECTOR, '#divAlertPop > div > div > div > a').click()          
            except:
                pass
            

            for i in range(20):
                try:
                    신고인 = driver.find_element(By.CSS_SELECTOR, '#dclrRlpNm').text
                    if 신고인 == '세무법인 더원':
                        break
                except:
                    logt(f"신고인 정보 노출 대기 중...  {i}")
                time.sleep(1)
            
            # 납세자 조회
            logt("[납세자 조회] 클릭", 0.5)
            driver.find_element(By.CSS_SELECTOR, '#btnDlgp').click()
            
            # ----------------------
            # IFRAME 시작  : 위임자 조회
            # ----------------------
            # 프레임 전환
            logt("프레임 전환", 2)
            driver.switch_to.frame(0)
            
            # 검색결과가 0보다 클때까지 대기 (여기서 오래 걸리는 경우가 있음)
            for i in range(10):
                검색결과수 = driver.find_element(By.ID, "spnTotCnt").text
                logt(f"위임자목록 조회 결과 = {검색결과수}")
                if int(검색결과수) > 0: break
                time.sleep(1)


            logt("[주민번호 입력 대기]", 0.5)
            driver.find_element(By.CSS_SELECTOR, '#condDlgpNoEnc1').clear()
            driver.find_element(By.CSS_SELECTOR, '#condDlgpNoEnc1').send_keys(ht_info['holder_ssn1'])
            time.sleep(0.1)
            driver.find_element(By.CSS_SELECTOR, '#condDlgpNoEnc2').clear()
            driver.find_element(By.CSS_SELECTOR, '#condDlgpNoEnc2').send_keys(ht_info['holder_ssn2'])
            time.sleep(0.1)
            logt(f"[주민번호 입력 : {ht_info['holder_ssn1']}-{ht_info['holder_ssn2']}]")
            
            # 검색 버튼 클릭
            driver.find_element(By.CSS_SELECTOR, '#btnDlgpSearch').click()
            time.sleep(0.3)
            
            # 검색결과 x건 찾기
            검색결과건수 = driver.find_element(By.CSS_SELECTOR, '#spnTotCnt').text
            if int(검색결과건수) == 0:
                # 위임자목록에 없음
                logt(f"위임자목록 조회결과 없음  ==>  다음 양도인 처리 진행")
                dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', "위임자목록 조회결과 없음")
                dbjob.insert_auHistory(ht_tt_seq, worker_id, au_x, '위임자목록 조회', ' 검색결과건수 : 0', auto_manager_id)
                driver.switch_to.default_content()
                driver.find_element(By.CSS_SELECTOR, "#cmnPopup_dlgp > div > button").click()
                continue
                
            # 첫번째 조회결과 클릭
            driver.find_element(By.CSS_SELECTOR, '#tbl_listDlgpUser > tbody > tr:nth-child(1) > td:nth-child(1) > span').click()
            time.sleep(0.1)
            
            logt("[선택] 버튼 클릭", 0.2)
            driver.find_element(By.CSS_SELECTOR, '#btnDlgpSelect').click()
            
            driver.switch_to.default_content() #메인프레임으로 이동


            # ----------------------
            # IFRAME 끝
            # ----------------------
            
            # 이름 확인
            양도인명 = driver.find_element(By.CSS_SELECTOR, '#txpNm').text
            if ht_info['holder_nm'] != 양도인명:
                dbjob.insert_auHistory(ht_tt_seq, worker_id, au_x, '양도인명 불일치', f"DB={ht_info['holder_nm']}, 위택스={양도인명}", auto_manager_id)
                # 에러처리하지 않고 성공처리하기, 다만 au_history에 이력 남기기
                # dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f"양도인명불일치 : DB={ht_info['holder_nm']}, 위택스={양도인명}")
            
            #국적선택
            # [다음] 버튼 클릭
            driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
            ret = sc.click_alert(driver, '저장 후 다음화면으로 이동 하시겠습니까?')
            if ret == 'ALERT_ERROR':
                logt("국적 선택 필요")

                driver.find_element(By.CSS_SELECTOR, '#btnTrnrNtnSrch').click()
                time.sleep(0.5)
                driver.find_element(By.CSS_SELECTOR, '#ntnNm').send_keys('대한민국')
                time.sleep(0.5)
                driver.find_element(By.CSS_SELECTOR, '#btnNationSrh').click()
                time.sleep(0.5)
                driver.execute_script("$('#rdo_nat_1').prop('checked', true)")
                time.sleep(0.5)
                driver.find_element(By.CSS_SELECTOR, '#btnNationSel').click()
                time.sleep(0.5)
                

                driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
                ret = sc.click_alert(driver, '저장 후 다음화면으로 이동 하시겠습니까?')

            time.sleep(1)
            
            # ------------------------------------------------
            logt("##### 2.신고기본정보", 다음버튼_대기시간)
            if check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, 2) == False : continue
            # ------------------------------------------------
            
            
            
            
            # # TODO SELECT박스 : 확정신고-국외주식 선택  (3 -> 4)
            # sc.set_select_by_option_index(driver, 'trnEarnDclrTypCd', 3, '신고유형')  
            # # sc.set_select_by_option_index(driver, 'trnEarnDclrTypCd', 4, '신고유형') 
            
            # # 양도일자
            # driver.find_element(By.CSS_SELECTOR, '#trnYmd').send_keys('20231231')
            # # 거주구분 선택 : 거주자
            # driver.find_element(By.CSS_SELECTOR, "label[for='rdo_03_01']").click()
            # # 기타 항목이 자동으로 채우기 위해 일정시간 반드시 대기
            
            
            logt("[홈택스 조회] 버튼 클릭", 1)
            
            # 홈택스 조회
            driver.find_element(By.CSS_SELECTOR, "#btnHtxPopup").click()
            time.sleep(0.5)
            
            # 팝업 DIV - 검색버튼
            driver.find_element(By.CSS_SELECTOR, "#btnSchHomeTax").click()
            time.sleep(1.5)
            
            홈택스_접수번호 = ht_info['hometax_reg_num']
            if 홈택스_접수번호: 홈택스_접수번호 = 홈택스_접수번호.replace('-', '')
            
            is_found = False
            검색결과건수 = driver.find_element(By.CSS_SELECTOR, '#homeTotCnt').text
            if int(검색결과건수) == 0:
                dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', "홈택스신고 조회결과 없음")
            else:
                trs = driver.find_elements(By.CSS_SELECTOR, "#tbl_homeTaxList > tbody > tr")
                for idx, tr in enumerate(trs, 0):
                    tds = tr.find_elements(By.CSS_SELECTOR, "td")
                    td2_text = tds[1].text  #홈택스 접수번호
                    td4_text = tds[4].text
                    if td2_text == 홈택스_접수번호: # or (ht_info['data_type'] == 'SEMI'):
                        driver.find_element(By.CSS_SELECTOR, f"label[for='chkItem_{idx}']").click()
                        driver.find_element(By.CSS_SELECTOR, "#btnHomeSel").click() # [선택]
                        is_found = True

                        # 여기서 SEMI 업데이트 하면 암됨!!!
                        # 반자동 신고된 홈택스 접수번호 업데이트
                        #if not 홈택스_접수번호 or (ht_info['data_type'] == 'SEMI'):
                        #    dbjob.update_HtTt_hometaxRegNum(ht_tt_seq, td2_text)

                        break
                
            if not is_found:
                # 위임자목록에 없음
                dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f"홈택스신고 조회결과 : {검색결과건수}")
                dbjob.insert_auHistory(ht_tt_seq, worker_id, au_x, '홈택스신고 조회', f"검색결과건수 : {검색결과건수}, 홈택스접수번호={ht_info['hometax_reg_num']}", auto_manager_id)
                # 닫기버튼
                driver.find_element(By.CSS_SELECTOR, "#btnHomeClose").click()
                logt(f"홈택스신고 조회결과 없음  ====================================>  다음 양도인 처리 진행")
                continue
            else:
                # 팝업닫기 : 홈택스에서 신고된 내용을 자동채움하였습니다. 계속 진행하세요.                 
                driver.find_element(By.CSS_SELECTOR, "#btnOk").click()
            
            time.sleep(0.5)


            주소 = driver.find_element(By.CSS_SELECTOR, "#txpAllAddr").get_attribute("value")
            try:
                # select_sido 선택 요소 가져오기
                select_sido = Select(driver.find_element(By.ID, "sel_jrsLgvCdSido"))
                # 현재 선택된 옵션 가져오기
                selected_option = select_sido.first_selected_option
                # 옵션의 value 및 text 값 가져오기
                selected_value = selected_option.get_attribute("value")
                selected_text = selected_option.text

                print("법정동 시도 선택 value:", selected_value)
                print("법정동 시도 선택 value:", selected_text)
            except NoSuchElementException:
                print("법정동 시도 선택 없음")
                if 주소.find('세종') >= 0:
                    select_sido.select_by_visible_text("세종특별자치시")
                    time.sleep(1)
                else:
                    dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f"법정동 오류, 시도: {주소}단계")
                    continue

            #법정동 마지막 항목 선택하기
            # 셀렉트 요소 찾기
            select_box = None
            관할지_동 = ""
            try:
                select_box = Select(driver.find_element(By.ID, "sel_jrsLgvCdDong"))
                관할지_동 = select_box.first_selected_option.text
                logt(f"관할지_동 : [{관할지_동}]")
            except NoSuchElementException:
                sc.set_select_by_option_index(driver, 'sel_jrsLgvCdDong', 2, '관할지_동', 0)
                관할지_동 = select_box.first_selected_option.text
                dbjob.append_HtTt_remark(ht_tt_seq, f'위택스_신고시_법정동_임의선택 => [{관할지_동}]' )
                logt(f"관할지_동 : [{관할지_동}]  <=== 위택스_신고시_법정동_임의선택")


            # [다음] 버튼 클릭
            driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
            ret = sc.click_alert(driver, '저장 후 다음화면으로 이동 하시겠습니까?')
            try:
                if ret == 'ALERT_ERROR':
                    logt("행정동 선택 필요")
                    driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
                    ret = sc.click_alert(driver, '저장 후 다음화면으로 이동 하시겠습니까?')            
            except:
                logt("행정동 선택 패스")

            time.sleep(1)
            # ------------------------------------------------
            logt("##### 3.신고세액", 다음버튼_대기시간)
            if check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, 3) == False : continue
            # ------------------------------------------------
            # driver.find_element(By.CSS_SELECTOR, '#btnAddRow').click()
            
            # # [양도소득분 신고세액 등록]  DIV 팝업
            # # 국내외구분 : 국외 선택
            # driver.find_element(By.CSS_SELECTOR, '#layerTaxAmount > div > div > div:nth-child(2) > table > tbody > tr:nth-child(2) > td > span:nth-child(2) > label').click()
            
            # sc.set_select_by_option_index(driver, 'txrCd', 4, '세율구분') 
            
            # # 5.과세표준
            # 양도소득금액 = ht_info['total_income_amount']
            # if not 양도소득금액: 양도소득금액 = 0
            # 과세표준금액 = 양도소득금액 - 2_500_000
            # if 과세표준금액 == 0: 
            #     과세표준금액 = -1   #과세표준은 0원 입력이 불가로 0원 대신 -1 입력
            # logt(f"과세표준금액 = {str(과세표준금액)}")
            
            # # [주의] 1.기본 입력 0값 제거하기  2.과세표준은 0원 입력이 불가
            # driver.find_element(By.CSS_SELECTOR, '#txbAmt').send_keys(Keys.BACKSPACE)
            # driver.find_element(By.CSS_SELECTOR, '#txbAmt').send_keys(str(과세표준금액))
            
            # # [등록] 버튼 클릭
            # driver.find_element(By.CSS_SELECTOR, '#btnTaxAdd').click()

            # [다음] 버튼 클릭
            driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
            sc.click_alert(driver, '저장 후 다음화면으로 이동 하시겠습니까?')

            # ------------------------------------------------
            logt("##### 4.산출세액", 다음버튼_대기시간)
            if check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, 4) == False : continue
            # ------------------------------------------------
            # (이 단계에서는 입력 항목 없이 그냥 다음으로 넘어가기)
            
            # [다음] 버튼 클릭
            driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
            sc.click_alert(driver, '등록하시겠습니까?')

            
            # ------------------------------------------------
            logt("##### 5.구비서류등록", 다음버튼_대기시간)
            if check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, 5) == False : continue
            # ------------------------------------------------
            # (이 단계에서는 입력 항목 없이 그냥 다음으로 넘어가기)
            
            # [다음] 버튼 클릭
            driver.find_element(By.CSS_SELECTOR, '#btnNext').click()
            sc.click_alert(driver, '등록하시겠습니까?')

            # ------------------------------------------------
            logt("##### 6.신고서제출", 다음버튼_대기시간)
            if check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, 6) == False : continue
            # ------------------------------------------------

            # 동의합니다. [주의] 해당 체크박스는 기존방식의 .click()로 클릭이 잘 안됨 (스크롤 등의 이유로)
            driver.execute_script("$('#terms_agree_one01').prop('checked', true)")
            
            # [미리보기] 눌러 신고 및 납부계산서 미리보기 화면 캡쳐 저장여부 나중에 판단하기
            #driver.find_element(By.CSS_SELECTOR, '#btnPrvw').click()
            
            # TODO 아래 부분 주석                   풀기
            # [제출]                ㅏㅏ너ㅜㄴ1203!     

            driver.find_element(By.CSS_SELECTOR, '#btnSbmsn').click()
            sc.click_alert(driver, '양도소득분 신고서을(를) 제출 하시겠습니까?')

            # ------------------------------------------------
            logt("##### 7.납부", 다음버튼_대기시간)
            if check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, 7) == False : continue
            # ------------------------------------------------
            result = driver.find_element(By.CSS_SELECTOR, "#title").text
            if result.find('정상') >= 0:  # 지방소득세(양도소득분) 신고가 정상적으로 완료되었습니다.
                ...


            # TODO 4단계 진행을 이어서 할 경우
            위택스본세   = driver.find_element(By.CSS_SELECTOR, "#tblReportTaxAmount > tbody > tr > td:nth-child(4) > span.roboto").text
            주소         = driver.find_element(By.CSS_SELECTOR, "#txpAllAddr").text
            전자납부번호 = driver.find_element(By.CSS_SELECTOR, "#elpn").text
            
            위택스본세 = int(위택스본세.replace(',', ''))
            관할지  = driver.find_element(By.CSS_SELECTOR, "#jrsLgvNm").text
            dbjob.update_HtTt_wetax_complete(ht_tt_seq, 위택스본세, 주소, 전자납부번호, 관할지)

            # try:
            #     # 신고서 출력
            #     download_file(driver, ht_info, 'WE_DOWN_5')  # 납부서
            #     #download_file(driver, ht_info, 'WE_DOWN_6') # 신고서
            # except Exception as e:
            #     print('문서 다운로드 오류 발생')
            #     print(e)
            #     traceback.print_exc()
            # else:
            #         dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S')
            
        except Exception as e:
            연속실패건수 += 1
            loge(f'{str(e)[:100]}')
            #traceback.print_exc()
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f"{str(e)[:100]}")
            if 연속실패건수>3:
                dbjob.update_autoManager_statusCd(auto_manager_id, 'E', f'연속3회에러 : {str(e)[:100]}')
                break
        else : # 오류가 없을 경우만 실행
            연속실패건수 = 0
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S', None)
            logt("####### 1건 처리 완료 #######")     

    # End of while

# 문서 다운로드
def download_file(driver, ht_info, v_file_type):
    retVal = False
    
    ht_tt_seq = ht_info['ht_tt_seq']
    holder_nm = ht_info['holder_nm']

    filename = ''
    if v_file_type == 'WE_DOWN_6':  # 위택스 신고서
        driver.find_element(By.CSS_SELECTOR, "#btnPayCalcPrint").click()
        filename = 'down6.pdf'
    elif v_file_type == 'WE_DOWN_5': # 위택스 납부서
        driver.find_element(By.CSS_SELECTOR, "#btnPayPrint").click()
        filename = 'down5.pdf'

    # file_type별 파일이름 결정
    dir_work = ht_file.get_dir_by_htTtSeq(group_id, ht_tt_seq, True)  # True => work 폴더 생성
    fullpath = dir_work +filename    
    logt("------------------------------------------------------")
    logt("파일다운로드: Type: %s, Filepath: %s" % (v_file_type, fullpath))
    logt("------------------------------------------------------")
    

    logt("인쇄팝업 window 오픈 대기", 2)    

    # -------------------------------------------------------------------------------
    # 보고서 창 시작
    # -------------------------------------------------------------------------------
    try:
        # 최근 열린 창으로 전환
        driver.switch_to.window(driver.window_handles[-1])
        
        # 프린터 누르기 (다른이름으로 저장하기 위해서)
        driver.find_element(By.CSS_SELECTOR, '.btnPRINT').click()
        time.sleep(0.5)
        #pyautogui.press('down', presses=1, interval=0.1)
        
        try:
            # -------------------------------------------------------------------------------
            # 보고서 창 => pyautogui
            # -------------------------------------------------------------------------------
            pyautogui.press('tab', presses=1, interval=0.1)
            pyautogui.press('enter')
            logt("확인버튼 클릭 후 인쇄화면 출력 대기", 2)    

            # 인쇄화면 출력
            pyautogui.press('enter')
            logt("인쇄화면 출력 대기", 2)    
            
            # 이미 존재하면 삭제 (pdf 다운로드시 이미 존재하면 덮어쓰기 하겠냐고 질문하는 것을 회피 하기위해)
            if os.path.isfile(fullpath):
                os.remove(fullpath)
            
            pyautogui.typewrite(fullpath)
            time.sleep(2)
            pyautogui.press('enter')   # 저장하기 위해 파일경로 넣고 엔터치기            
            # -------------------------------------------------------------------------------
            # 보고서 창 끝
            # -------------------------------------------------------------------------------
            
            logt(f"문서다운로드 : 위택스 {type}, 경로={fullpath}", 2) 

            if os.path.isfile(fullpath):
                logt("파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
                logt("파일저장 확인완료 => DB 입력하기")
                dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
                retVal = True
            else:
                time.sleep(1.0)
                if os.path.isfile(fullpath):
                    logt("(재시도)파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
                    logt("(재시도)파일저장 확인완료 => DB 입력하기")
                    dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
                    retVal = True
                else:
                    logt("파일저장 확인실패  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    time.sleep(10)
                    # raise BizException("파일저장 실패", fullpath)
        except Exception as e:
            logt(e)
        
    
    except Exception as e:
        logt(e)
    
    finally:
        # 현재 작업창 닫기
        driver.close()
        # 메인 윈도우 복귀
        driver.switch_to.window(driver.window_handles[0])
    # -------------------------------------------------------------------------------
    # 보고서 창 종료
    # -------------------------------------------------------------------------------



    return retVal


def check_report_step(driver, ht_tt_seq, worker_id, au_x, auto_manager_id, step):
    clazz = driver.find_element(By.CSS_SELECTOR, f'#olStepList > li:nth-child({step})').get_attribute('class')
    if clazz != 'on':
        dbjob.insert_auHistory(ht_tt_seq, worker_id, au_x, '진행단계 불일치', f'{step}단계 불일치', auto_manager_id)
        dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f"진행단계 불일치 : {step}단계")
        return False
    else:
        return True    


if __name__ == '__main__':
    if driver:
        driver.set_window_size(1300, 990) # 실제 적용시 : 990
        do_task(driver, user_info, verify_stamp) 
        
    logt(f"{AU_X}단계 작업 완료")

    if conn: 
        conn.close()

    exit(0)    
