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

# =============================================================================================================================================
# 작업설명 : 위택스 신고내역(3단계) 점검
# =============================================================================================================================================
AU_STEP = 3


TAX_NAME = "지방소득세(양도소득세분)"
url = 'https://www.wetax.go.kr/simple/?cmd=LPEPBZ4R0'


if __name__ == '__main__':

    print("(점검) 3단계 - 위택스 신고내역 점검")
    dbjob.connect_db()

    # 작업자별 로그인 정보
    login_info = config.LOGIN_INFO

    try :
        series_seq_from = 29599 #int(sys.argv[1])
        series_seq_to = 33863 #int(sys.argv[2])
    except:

        print("series_seq from, to 값을 설정해 주세요")
        sys.exit()
    
    # 아래의 쿼리 where 조건 수정하여 사용하기
    jobs = dbjob.select_audit_위택스신고내역(series_seq_from, series_seq_to)
    if len(jobs) == 0:
        print("작업할 리스트가 없습니다. 작업종료") 
        sys.exit()   
    
    try:
        driver = auto_login.init_selenium()
        driver.set_window_size(1200, config.BROWSER_SIZE['height'])
        print("위택스 이동")
        driver.get(url)  

        time.sleep(1)
        print("오늘은 무시")
        driver.find_element(By.CSS_SELECTOR, '#nos_pop > div.pop_foot > label > span').click()
        time.sleep(0.1)


        for k in range(len(jobs)) :
            time.sleep(0.2)
            ht_tt_seq = jobs[k]['ht_tt_seq']
            holder_nm = jobs[k]['holder_nm'] 
            holder_ssn1 = jobs[k]['holder_ssn1']
            holder_ssn2 = jobs[k]['holder_ssn2']
            ht_reg_num = jobs[k]['hometax_reg_num']
            we_reg_num = ''

            print("================================================================================")
            print("%d / %d :: ht_tt_seq= %s , Name= %s , ssn1= %s , ssn2= %s , hometax_reg_num= %s " % 
                            (k+1, len(jobs), ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, ht_reg_num))
            print("================================================================================")

            #dbjob.set_global(group_id, 'AUTOSVR', login_info['login_id'], ht_tt_seq, AU_STEP)
            # 이전값 초기화
            driver.find_element(By.ID, 'regNoFront').clear()
            driver.find_element(By.ID, 'regNoEnd').clear()
            driver.find_element(By.ID, 'taxSeq').clear()
            time.sleep(0.1)

            driver.find_element(By.ID, 'regNoFront').send_keys(jobs[k]['holder_ssn1'])
            time.sleep(0.1)
            driver.find_element(By.ID, 'regNoEnd').send_keys(jobs[k]['holder_ssn2'])
            time.sleep(0.1)
            driver.find_element(By.ID, 'taxSeq').send_keys(jobs[k]['hometax_reg_num'].replace('-',''))
            time.sleep(0.1)

            print(f"주민번호= {jobs[k]['holder_ssn1']}-{jobs[k]['holder_ssn2']}, 홈택스 접수번호= {jobs[k]['hometax_reg_num']}")
            elements = driver.find_elements(By.CSS_SELECTOR, '.searchBtn')
            #print(elements)
            elements[0].click() # 첫번째 것을 조회버튼으로 인식

            time.sleep(0.7)
            #e_trs = driver.find_elements(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr')
            e_trs = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.txt_total > strong > em').text
            if e_trs :
                검색결과수 = int(e_trs)
            else :
                검색결과수 = 0

            print("조회결과 수 = %s" % 검색결과수)
        

            # 신고갯수
            tax: int = 0
            if 검색결과수 == 0:
                ht_report_cnt = -1
                we_report_cnt = 0
                ht_income_tax = -1
                we_income_tax = -1
                status = "결과없음"
                dbjob.insert_au_audit(AU_STEP, ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, ht_report_cnt, we_report_cnt, ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num)
                continue
            else:
                for i in range(검색결과수):
                    ele_trs = driver.find_elements(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr')

                    # 양도자명
                    e_name = None
                    try :
                        # 결과가 하나이거나 결과가 없거나 이곳으로 이동 => 원하는 엘리먼트가 없으면 다음으로 이동
                        e_name = ele_trs[i].find_element(By.CSS_SELECTOR, 'td:nth-child(2)')
                    except:
                        continue

                    i_name = e_name.text.strip()

                    # 세금 항목명
                    e_tax_name = ele_trs[i].find_element(By.CSS_SELECTOR, 'td:nth-child(6)')
                    i_tax_name = e_tax_name.text.strip()
                    if i_tax_name != '지방소득세(양도소득세분)': 
                        continue

                    # 전자납부번호
                    we_reg_num = ele_trs[i].find_element(By.CSS_SELECTOR, 'td:nth-child(5)')
                    we_reg_num = we_reg_num.text.strip().replace("-", "")


                    # 지방소득세 
                    e_tax = ele_trs[i].find_element(By.CSS_SELECTOR, 'td:nth-child(7)')
                    print("지방소득세= " + e_tax.text)
                    tax = int(e_tax.text.replace(",", "").replace("원", "").strip())


                    # 미납/취소
                    e_ispay = ele_trs[i].find_element(By.CSS_SELECTOR, 'td:nth-child(9)')
                    ispay = e_ispay.text.replace(",", "").strip()


                    ht_report_cnt = -1
                    ht_income_tax = -1
                    we_report_cnt = 검색결과수
                    we_income_tax = tax
                    status = ispay
                    dbjob.insert_au_audit(AU_STEP, ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, ht_report_cnt, we_report_cnt, ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num)
                            
                #time.sleep(0.1)


    except Exception as e:
        print(e)
        traceback.print_exc()

    else :
        print("===========정상종료 ")

    print("프로그램 종료")

    driver.close()

    exit(0)
