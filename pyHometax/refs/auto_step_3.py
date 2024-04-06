import time
import os

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
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
import sele_common as sc

# 자동신고단계 -----------------------------
au_stpe = 3

# 메뉴이동 : '신고/납부' 클릭
def click_메뉴_신고납부(driver: WebDriver):
    logt("메뉴이동 : '신고/납부' 메뉴 이동")
    url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
    driver.get(url)
    
    logt("iframe 이동", 2)
    sc.move_iframe(driver)
    
    logt("클릭: 신고내역조회(접수증,납부서) 메뉴", 1)
    driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11').click()


    # wait = WebDriverWait(driver, 10)
    # element = wait.until(EC.element_to_be_clickable((By.ID, 'sub_a_0405050000')))
    # logt("클릭: 양도소득세")
    # element.click()

    # try :
    #     time.sleep(1)
    #     alert = driver.switch_to_alert()
    #     alert_msg = alert.text
    #     if alert_msg.find("로그인 정보가 없습니다.") > -1 :
    #         logt("현재는 로그아웃 상태")
    #         alert.accept()
    #         raise BizException("로그아웃상태")   
    #     else :
    #         logt("정상 로그인 상태1")
    # except BizException as e:
    #     raise e
    # except :
    #     pass


def do_step3(driver: WebDriver, group_id, jobs, user_id):

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
    driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11').click()


    # 양도자 반복처리      
    cur_window_handle = driver.current_window_handle      
    for job_idx in range(0, len(jobs)):
        ht_info = jobs[job_idx]
        ht_tt_seq = ht_info['ht_tt_seq']

        # 담당자 홈택스로그인 가능 여부 확인용
        dbjob.update_user_cookieModiDt(user_id)

        try:
            logt("%d / %d 처리 ..." % (job_idx+1, len(jobs)))        
            ht_info = jobs[job_idx]

            logt("홈택스 조회 윈도우 이동", 0.5)
            driver.switch_to.window(cur_window_handle)

            print(driver.window_handles)
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(cur_window_handle)

            try :
                logt("작업프레임 이동: txppIframe", 0.5)
                driver.switch_to.frame("txppIframe")
            except:
                logt("로그인 정보가 없습니다.", 0.5)
                driver.close()
                exit()

            # ========================================================
            # 반복 구간
            # ========================================================
            
            do_step3_loop(driver, ht_info)

            # ========================================================
            # 반복 구간
            # ========================================================
            
        
        except BizException as e:
            logt("#################### except BizException")
            print(e)
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', e.msg)

        except Exception as e:
            print(e)
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', None)
            traceback.print_exc()
        
        else:  # 오류없이 정상 처리시
            logt("#################### (정상처리)")
            dbjob.update_HtTt_AuX(au_stpe, ht_tt_seq, 'S', None)
            traceback.print_exc()

        # job 완료 처리 
        logt("####### 한건처리 완료 #######", 0.2)

    # 홈택스 조건검색 윈도우
    driver.switch_to.window(cur_window_handle)




def do_step3_loop(driver: WebDriver, ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    cur_window_handle = driver.current_window_handle

    logi("******************************************************************************************************************")
    logt("양도인=%s, HT_TT_SEQ=%d, SSN= %s%s" % (ht_info['holder_nm'], ht_info['ht_tt_seq'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
    logi("******************************************************************************************************************")
    
    # 기존 로그 삭제
    dbjob.delete_auHistory_byKey(ht_tt_seq, "3")


    # 작성방식 
    #logt("작성방식 선택")
    #select = Select(driver.find_element(By.ID, "selectbox_wrtMthCd_406_UTERNAAZ31"))
    #select.select_by_visible_text('작성방식')

    ssn = ht_info['holder_ssn1'] + ht_info['holder_ssn2']

    # 주민번호 입력
    logt("주민번호 입력: %s" % ssn, 0.5)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').clear()
    time.sleep(0.2)
    driver.find_element(By.ID, 'input_txprRgtNo_UTERNAAZ31').send_keys(ssn)

    time.sleep(0.5)
    logt("조회클릭")
    driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()

    alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
    print("Alter Message Return=%s" % alt_msg)
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
        logt("양도인명 확인 JNK= %s, Hometax= %s" % (ht_info['holder_nm'], hometax_holder_nm))
        #if hometax_holder_nm != ht_info['holder_nm']:
        #    raise BizException("양도인명 불일치", "홈택스 양도인명= %s" % hometax_holder_nm)

        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(9+offset)+ " > span > a")
        hometax_reg_num = ele.text
        logt(f"data_type={ht_info['data_type']}, 홈택스 접수번호= {hometax_reg_num}")
        if ht_info['data_type'] == 'AUTO' and  hometax_reg_num != ht_info['hometax_reg_num']:
            print("홈택스 접수번호 불일치", "DB=%s, 홈택스접수번호= %s" % ( ht_info['hometax_reg_num'], hometax_reg_num))
            sys.exit()
            raise BizException("홈택스 접수번호 불일치", "DB=%s, 홈택스접수번호= %s" % ( ht_info['hometax_reg_num'], hometax_reg_num))

        if ht_info['data_type'] == 'AUTO':
            logi(f"자동신고의 홈텍스 납입세액 = {ht_info['hometax_income_tax']}")
        else:
            logi(f"자동신고외의 현재 기준 홈텍스 예상 납입세액(정확하지 않음) = {ht_info['hometax_income_tax']}")

        # 주의) 납부서가 없을 수 있음
        logt("납부서 [보기] 클릭", 1)
        try :
            ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(12+offset)+ " > span > button")
            ele.click()

            # 홈택스 세액 납부 여부 (뒤에서 홈택스 세액을 저장하기 위해)
            is_already_pay = False

            logt("작업프레임 이동: UTERNAAZ70_iframe", 3)
            # #sc.move_iframe(driver, "UTERNAAZ70_iframe")
            try :
                driver.switch_to.frame("UTERNAAZ70_iframe")

                logt("지방소득세(위택스) 신고 클릭", 1.5)
                ele = driver.find_element(By.CSS_SELECTOR, "#ttirnal111DVOListDes_cell_0_4 > img").click()
                
                # 팝업레이어 닫기
                logt("팝업레이어 닫기", 0.5)
                # (주의)닫기(trigger1)는 문서내 2개 있음.. 팝업창의 x 클릭으로 대체
                ele = driver.find_element(By.CSS_SELECTOR, "#trigger2")  
                ele.click()

            except:
                #alert = driver.switch_to.alert
                #alert_msg = alert.text
                #if alert_msg.find("양도소득세 납부할금액이 없습니다") == 0 :
                #    alert.accept()
                
                # 이미납부한 사람은 납부서를 볼 수 없음
                # 신고 이동 클릭
                logt("   [신고이동] 클릭", 1)
                #time.sleep(200)
                # 여기는 offset 안적용 되는 듯.. ㅠㅠ
                ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(37)+ " > span > button")
                ele.click()
                
                logt("Alert처리", 0.5)
                alert = driver.switch_to.alert
                alert_msg = alert.text
                if alert_msg.find("양도소득세 납부할 세액이 있는 경우") == 0 :
                    alert.accept()
                    is_already_pay = True

            logt("윈도우 로딩 대기", 2) 
            window_handles = driver.window_handles
            print(driver.window_handles)
            try :
                logt("window handle= %s" % ",".join(window_handles)) 
                driver.switch_to.window(window_handles[1])
                driver.set_window_position(0,0)
            except :
                logt("윈도우 전환 실패 => 재시도", 3) 
                window_handles = driver.window_handles
                driver.switch_to.window(window_handles[1])
                driver.set_window_position(0,0)    
                
                
        except Exception as e:
            logt("납부서가 없습니다. 납부세금이 없거나 이미납부")
            
            ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(37)+ " > span > button")
            ele.click()
            
            logt("Alert처리", 0.5)
            alert = driver.switch_to.alert
            alert_msg = alert.text
            if alert_msg.find("양도소득세 납부할 세액이 있는 경우") == 0 :
                alert.accept()


        logt("윈도우 로딩 대기", 2) 
        window_handles = driver.window_handles
        print(driver.window_handles)
        try :
            logt("window handle= %s" % ",".join(window_handles)) 
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)
        except :
            logt("윈도우 전환 실패 => 재시도", 3) 
            window_handles = driver.window_handles
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)           
        

        time.sleep(0.5)

        # 원래는 2단계에서 납부서 안에서 저장하지만 이미 납부한 경우에는 세액을 저장하지 못하기 때문에 여기서 저장
        # if is_already_pay:
        #     logt("홈택스 세액 저장")
        #     income_tax = driver.find_element(By.ID, "rstxRtn").get_attribute("value")
        #     tax = income_tax.replace(",","").replace("원","").strip() # 컴마제거
        #     hometax_income_tax = int(tax) * 10
        #     logt("홈택스에 신고된 납부세액 DB저장 = %s" % hometax_income_tax)
        #     dbjob.update_htTt_hometaxIncomeTax(ht_tt_seq, hometax_income_tax) 

        # ===============================================================================================
        # 위택스 시작
        # ===============================================================================================
        try:
            logt(f"위택스 주민번호 뒷자리 입력 = {ht_info['holder_ssn2']}", 2) 
            ele = driver.find_element(By.CSS_SELECTOR, '#jumin')
            ele.send_keys(ht_info['holder_ssn2'])

            sc.click_button_by_id(driver, 'btn_jumin', '주민번호입력 [확인]클릭')
        except:
            raise BizException("신고불가", "홈택스로부터 전송된 자료가 없습니다")
        
        time.sleep(1)
        
        alert = driver.switch_to.alert
        msg = alert.text
        logt("메세지 => 신규등록 혹은 기등록 : %s" % msg)
        
        # 정상적 메세지       : 이미 지방소득세를 신고하신 경우에는 위택스 접속 후
        # 이미 신고가 된 경우 : 홈택스를 통한 신고세액 내역이 존재합니다. 
        if msg.find('홈택스를 통한 신고세액 내역이 존재합니다') >= 0:
            logi(f"홈택스를 통한 신고세액 내역이 존재합니다  ==> 종료처리") 
            alert.dismiss()
            time.sleep(0.3)
            alert = driver.switch_to.alert
            alert.accept()   #  ==> 이미 지방소득세를 신고하신 경우에는 위택스 접속 후
            time.sleep(0.3)
            driver.close()
            return
        else:
            alert.accept()
        


        # 발생예외케이스 : 홈택스로부터 정송된 자료가 없습니다.
        try :
            logt("세무대리인 정보 - 법인명: " + company_info['name'], 0.2) 
            ele = driver.find_element(By.CSS_SELECTOR, '#rptNm')
            ele.send_keys(company_info['name'])
        except:
            driver.close()
            raise BizException("신고불가", "홈택스로부터 전송된 자료가 없습니다")

        logt("세무대리인 정보 - 법인번호1: " + company_info['regi_num_1'], 0.2) 
        ele = driver.find_element(By.CSS_SELECTOR, '#rptRegNo1')
        ele.send_keys(company_info['regi_num_1'])

        logt("세무대리인 정보 - 법인번호2: " + company_info['regi_num_2'], 0.2) 
        ele = driver.find_element(By.CSS_SELECTOR, '#rptRegNo2')
        ele.send_keys(company_info['regi_num_2'])

        # 법인 체크박스 rptDiv
        driver.find_element(By.CSS_SELECTOR, "#mainForm > fieldset > div:nth-child(3) > div.cont_body > div > div > table > tbody > tr:nth-child(1) > th:nth-child(3) > label > i").click()

        # 실명인증 realname4
        sc.click_button_by_id(driver, 'realname4', '실명인증')
        sc.click_alert(driver, '법인명과 법인등록번호가 일치합니다!')

        logt("세무대리인 정보 - 사업자번호: " + company_info['biz_num'], 0.2) 
        ele = driver.find_element(By.CSS_SELECTOR, '#rptBizNo')
        ele.send_keys(company_info['biz_num'])
        
        logt("세무대리인 정보 - 전화번호: " + company_info['biz_num'], 0.2) 
        ele = driver.find_element(By.CSS_SELECTOR, '#rptTel')
        ele.send_keys(company_info['tel'])
        
        # 양도인 휴대전화
        #holder_cellphone = ht_info['holder_cellphone'].replace("-", "")
        logt("납세자 정보 - 전화번호: " + company_info['tel'] , 0.2) 
        ele = driver.find_element(By.CSS_SELECTOR, '#bizTel')
        ele.send_keys(company_info['tel'])

        # 최종산출세액 추출
        ele = driver.find_element(By.CSS_SELECTOR, "#totAmt")
        wetax_income_tax = ele.get_attribute('value').replace(',', '').strip()
        logt("최종세액= %s" % wetax_income_tax)

        # 주소
        ele = driver.find_element(By.CSS_SELECTOR, "#tprAddr")
        wetax_addr = ele.get_attribute('value')
        logt("주소= %s" % wetax_addr)

        # 동의 클릭        
        driver.find_element(By.CSS_SELECTOR, "#mainForm > fieldset > div:nth-child(11) > div.cont_body > div > div > div.agree_chk > label > i").click()

        # 신고클릭
        logt("신고클릭", 0.2)
        driver.find_element(By.CSS_SELECTOR, "#singo").click()

        try:
            alert = driver.switch_to.alert
            msg = alert.text
            logt("(가끔 alert가 뜸) 납세지의 동을 선택하십시오 : %s" % msg)    
            alert.accept()
            time.sleep(0.2)
            sc.move_iframe(driver, 'setSelDong') 
            driver.find_element(By.CSS_SELECTOR, '#selDongCod > option:nth-child(2)').click() 
            time.sleep(0.2)
            # 기본 iframe으로 돌아가기
            driver.switch_to.parent_frame()
            logt("신고클릭", 0.2)
            driver.find_element(By.CSS_SELECTOR, "#singo").click()
        except Exception as e:
            ...

        # 신고 완료 페이지 이동 후
        전자납부번호 = driver.find_element(By.CSS_SELECTOR, "#mainForm > div:nth-child(10) > div.cont_body > div > div > table > tbody > tr > td:nth-child(4)").text
        logi(f"위택스 전자납부번호={전자납부번호}")

        dbjob.update_HtTt_wetax(ht_tt_seq, int(wetax_income_tax), wetax_addr, 전자납부번호)
        # DB Update
        logt("신고클릭", 0.2)
 
        
        logt("위택스 윈도우 닫기", 1)
        driver.close()


    else :
        # 접수된 신고가 없음
        step_cd = ht_info['step_cd']
        au1 = ht_info['au1']
        if step_cd == "REPORT" and au1 == "S":
            dbjob.update_HtTt_AuX(1, ht_tt_seq, 'E', '신고가 존재하지 않습니다. 재신청 하시기 바랍니다.')
            raise BizException("미제출", "신고서가 제출되지 않았습니다.")


company_info = {
    "name"      : "세무법인 더원"
    , "regi_num_1" : "110171"
    , "regi_num_2" : "0068286"
    , "biz_num"    : "1208777823"   # 사업자번호
    , "tel"        : "025140910"
}