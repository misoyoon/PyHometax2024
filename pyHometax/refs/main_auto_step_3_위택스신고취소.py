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
import ht_file
import pyHometax.auto_login as auto_login 
import auto_step_2


# 작업4단계 : 위택스 다운로드
AU_STEP = 6
group_id = "the1"

TAX_NAME = "지방소득세(양도소득세분)"
url = 'https://www.wetax.go.kr/simple/?cmd=LPEPBZ4R0'


# 작업폴더
project_dir = os.path.dirname(sys.modules['__main__'].__file__)
resource_dir = "resource" + os.sep
if project_dir:
    resource_dir = project_dir + os.sep + resource_dir

print(f"이미지 resource Dir =[{resource_dir}]")

# 이미지의 위치를 찾을 때까지 반복 시도 클릭
def pyautoui_image_click(img_path):
    for retry in range(6):
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.8)
        print(center)
        print(img_path)
        if center == None :
            time.sleep(0.5)
            print("이미지 클릭 재시도: retry=%d" % retry)
        else :
            time.sleep(0.3) # 0.3초후 클릭
            pyautogui.click(center)
            print("이미지 클릭: %s" % img_path)
            return True
    return False




if __name__ == '__main__':

    print("4단계 : 위택스 파일 다운로드")
    dbjob.connect_db()

    # 작업자별 로그인 정보
    login_info = config.LOGIN_INFO
    print(f"DB정보 {login_info}")

    # ============================================================
    # 작업 목록
    # ============================================================
    jobs = dbjob.select_auto_3_위택스_취소목록(group_id)
    
    if len(jobs) == 0:
        logt("작업할 리스트가 없습니다. 작업종료")    
    else:
        logt(f"작업 수량={len(jobs)}")
    
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

        for k in range(len(jobs)) :
            #print(jobs[k])
            ht_tt_seq = jobs[k]['ht_tt_seq']
            holder_nm = jobs[k]['holder_nm'] 
            
            # 이전 저장 파일 초기화
            #dbjob.update_HtTt_au4_reset(ht_tt_seq)

            print("================================================================================")
            print("%d / %d :: ht_tt_seq= %s , Name= %s , ssn1= %s , ssn2= %s , hometax_reg_num= %s " % 
                            (k+1, len(jobs), ht_tt_seq, holder_nm, jobs[k]['holder_ssn1'], jobs[k]['holder_ssn2'], jobs[k]['hometax_reg_num']))
            print("================================================================================")
            i = 0
            loop_to = 1
            is_search = True

            
            # ---------------------------
            dir_work = ht_file.get_dir_by_htTtSeq(ht_tt_seq)
            
            dbjob.set_global(group_id, 'AUTOSVR', login_info['login_id'], ht_tt_seq, AU_STEP)
            # ---------------------------

            # 낼 세금이 없으면 다음작업 => 세금이 없어도 신고
            # hometax_income_tax = jobs[k]['hometax_income_tax']
            # if hometax_income_tax is None :
            #     logt("세금없음 => 다음 작업 진행")
            #     dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'Z', '지방세없음')
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


                    driver.find_element(By.ID, 'regNoFront').send_keys(jobs[k]['holder_ssn1'])
                    time.sleep(0.1)
                    driver.find_element(By.ID, 'regNoEnd').send_keys(jobs[k]['holder_ssn2'])
                    time.sleep(0.3)
                    driver.find_element(By.ID, 'taxSeq').send_keys(jobs[k]['hometax_reg_num_backup'])
                    time.sleep(0.3)

                    logt(f"주민번호= {jobs[k]['holder_ssn1']}-{jobs[k]['holder_ssn2']}, 홈택스 접수번호= {jobs[k]['hometax_reg_num_backup']}")
                    elements = driver.find_elements(By.CSS_SELECTOR, '.searchBtn')
                    #print(elements)
                    elements[0].click() # 첫번째 것을 조회버튼으로 인식

                    time.sleep(0.5)
                    e_trs = driver.find_elements(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr')
                    loop_to = len(e_trs)

                    print("조회결과 수 = %s" % loop_to)
                
                    # 조회 결과 분석: 만약1이면 조회 결과 없음으로 다음 사람 조회
                    #if loop_to == 0:
                    #    print("세금없음 (정상처리)=> 다음 작업 진행")
                    #    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'Z', '지방세없음')
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
                    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '신고내역없음')
                    continue
                    
                i_name = e_name.text.strip()

                # 세금 항목명
                e_tax_name = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(6)')
                i_tax_name = e_tax_name.text.strip()

                # 지방소득세 
                e_tax = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(7)')
                logt("지방소득세= " + e_tax.text)
                tax = e_tax.text.replace(",", "").replace("원", "").strip()
                # 전자납부번호 
                e_reg_num = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(5)')
                reg_num = e_reg_num.text.strip()

                # 미납/취소
                e_ispay = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(9)')
                ispay = e_ispay.text.replace(",", "").strip()
                

                # 홈택시 양도세
                hometax_income_tax = jobs[k]['hometax_income_tax']
                
                #if is_first_found==False and i_name == jobs[k]['holder_nm'] and i_tax_name == TAX_NAME and ("미납" == ispay or "납부" == ispay) :
                if is_first_found==False and i_tax_name == TAX_NAME and ("미납" == ispay or "납부" == ispay) :

                    print("%d / %d %s, %s, %s, %s ===> 작업대상" % (i, len(e_trs), i_name, i_tax_name, tax,  ispay))    

                    # 홈택스 세금과 비교
                    wetax_income_tax = int(tax)
                    if hometax_income_tax is None:
                        hometax_income_tax = 0

                    ex_wetax_income_tax = math.floor(hometax_income_tax/100) * 10
                    print("홈택스 세금비교 : hometax=%d ==> 예상지방세=%d 화면출력지방세=%d" % (hometax_income_tax, wetax_income_tax, ex_wetax_income_tax))
                    #if jobs[k]['data_type'] == 'AUTO' and ex_wetax_income_tax != wetax_income_tax:
                    #    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '세금액비교오류: 예상=%d, 살제=%d' % (wetax_income_tax, ex_wetax_income_tax))
                    #    break

                    #상세페이지 이동을 위한 click
                    ele = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(5)')
                    ele.click()

                    # 대기
                    time.sleep(0.5)

                    # 전자납부번호
                    e_wetax_reg_num = driver.find_element(By.CSS_SELECTOR, '#section > div.hackshim.mar_t20 > div > table > tbody > tr > td:nth-child(2)')
                    wetax_reg_num = e_wetax_reg_num.text.strip()
                    logt("전자납부번호: " + wetax_reg_num)

                    if ispay == "미납":
                        # 신고취소 버튼 ----------------------------------------------------------------------------------------------------------
                        try :
                            print("신고취소 버튼")
                            ele = driver.find_element(By.CSS_SELECTOR, '#sendForm > div.btn_wrap > ul > li.float_r > a.btn_type01.bg4.wid130')
                            ele.click()
                        except:
                            try :
                                time.sleep(2)
                                print("신고취소 버튼 ===>>> 재시도")
                                ele = driver.find_element(By.CSS_SELECTOR, '#sendForm > div.btn_wrap > ul > li.float_r > a.btn_type01.bg4.wid130')
                                
                                ele.click()
                            except:
                                print("신고취소 => NOT FOUND")
                                exit(0)
    
                        time.sleep(1)
                        print("윈도우 핸들 1")
                        window_handles = driver.window_handles
                        print (window_handles)
                        
                        if len(window_handles) == 2:
                            driver.switch_to.window(window_handles[1])
                            time.sleep(0.5)
                            if driver.title == '신고취소 (팝업윈도우)':
                                driver.find_element(By.ID, 'cancelReason').send_keys('세액 변동')
                                time.sleep(0.2)
                                driver.find_element(By.CSS_SELECTOR, '#p_cont > div.btn_wrap.text_r > a').click()
                                logt("창닫기", 0.2)
                                driver.find_element(By.CSS_SELECTOR, '#p_cont > div > div > div > a').click()
                                
                                # ===============================================================
                                # 신고취소 하기
                                # ===============================================================
                                dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'S')
                                # ===============================================================
                            else:
                                print(f"팝업창 오류, 현재 팝업창={driver.title }")
                                sys.exit()
                        else:
                            print(f"팝업창 오류, 현재 팝업창={driver.title }")
                            sys.exit()                                

                    elif ispay == "납부":
                        dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'Y', '납부완료')

                    # 아래 업데이트에서 REPORT_DONE 처리포함
                    # step_cd => REPORT_DONE 처리
                    #dbjob.update_HtTt_WetaxRegNum(ht_tt_seq, wetax_reg_num)

                    is_search = True
                    is_first_found = True
                        
                elif "미납" == ispay and is_first_found==True and i_tax_name == TAX_NAME:  # and i_name == jobs[k]['holder_nm']   ==> 간혹 이름이 다른 사람존재
                    # 추가 미납 항목 있음
                    dbjob.insert_auHistory("미납추가로있음", None)

                elif "면세" == ispay  and i_tax_name == TAX_NAME:  # and i_name == jobs[k]['holder_nm']   ==> 간혹 이름이 다른 사람존재
                    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '면세')
                    dbjob.update_HtTt_stepCd(ht_tt_seq, 'REPORT_DONE')
                    is_search = True
                elif "취소" == ispay  and i_tax_name == TAX_NAME:  # and i_name == jobs[k]['holder_nm']   ==> 간혹 이름이 다른 사람존재
                    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '취소')
                    is_search = True
                else :    
                    print("%d / %d %s, %s, %s, %s ===========> SKIPPING" % (i, len(e_trs), i_name, i_tax_name, tax,  ispay))
                    is_search = False


                if i>= loop_to:
                    break

            # END <while>

            print("한줄처리 완료 --------------------------------------")
            time.sleep(0.2)

            driver.switch_to.window(driver.window_handles[0])

        # EOD <for>

    except Exception as e:
        print(e)
        traceback.print_exc()

    else :
        print("===========정상종료 ")

    print("프로그램 종료")

    driver.close()

    exit(0)
