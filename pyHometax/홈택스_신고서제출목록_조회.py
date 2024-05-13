from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import time
import traceback

import config

from common import *
import dbjob

import auto_login as auto_login 
import common_sele as sc


company_info = {
    "name"      : "세무법인 더원"
    , "regi_num_1" : "110171"
    , "regi_num_2" : "0068286"
    , "biz_num"    : "1208777823"   # 사업자번호
    , "tel"        : "025140910"
}

# 위택스 신고하기
au_step = "3"
group_id = "the1"

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


if __name__ == '__main__':
    # host_name = config.HOST_NAME
    # conn = dbjob.connect_db()

    # logt("홈택스 양도소득세 자동신고 서버 기동 !!!")
    # logt("  ==> 신고3단계 : 위택스 신고")

    # logt("# ------------------------------------------------------------------")
    # logt("담당자 작업 정보 : GROUP_DI=%s, ID=%s, Name=%s" % (group_id, for_one_user_id, for_one_user_name))
    # logt("# ------------------------------------------------------------------")

    # # 세무대리인(담당자) 리스트
    # user_list = dbjob.get_worker_list(group_id, for_one_user_id)
    # print(user_list)
    
    # # 담당자별로 한번에 처리한 자료수
    # batch_bundle_count = config.BATCH_BUNDLE_COUNT
    # logt("배치 처리 건수=%d" % batch_bundle_count)


    # #dbjob.set_global(group_id, None, None, None, au_step)   # (v_host_name, v_user_id, v_ht_tt_seq, v_au_step):


    # # ------------------------------------------------------------------
    # # 로그인
    # # ------------------------------------------------------------------
    # # 작업자별 로그인 정보
    # login_info = config.LOGIN_INFO

    # # 작업자별 로그인 정보
    # if for_one_user_id == "MANAGER_ID" :
    #     login_info['name'] = "관리자"
    #     login_info['login_id'] = "MANAGER_ID"
    #     login_info['login_pw'] = "xxxx"  # 사용안함
    # else :
    #     user_row = dbjob.get_worker_info(for_one_user_id)
    #     login_info['name'] = user_row['name']
    #     login_info['login_id'] = user_row['hometax_id']
    #     login_info['login_pw'] = user_row['hometax_pw']


    # 셀레니움 드라이버
    driver: WebDriver = auto_login.init_selenium()
    

    # 자동로그인 처리
    #auto_login.login_hometax(driver, login_info, config.IS_DEBUG)
    # ------------------------------------------------------------------
    
    try:

        #######################################################################################

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

        time.sleep(0.5)
        logt("조회클릭")
        driver.find_element(By.ID, 'trigger70_UTERNAAZ31').click()
        time.sleep(5)
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


        # 100건씩
        select = Select(driver.find_element(By.ID, "edtGrdRowNum"))
        select.select_by_visible_text("100건")
        time.sleep(0.2)
        driver.find_element(By.ID, 'trigger6_UTERNAAZ31').click()
        time.sleep(5)
        
        alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")



        조회건수 = driver.find_element(By.CSS_SELECTOR, "#txtTotal887").text   # 총 1/2 등....
        조회건수 = int(조회건수)
        조회_페이지수 = driver.find_element(By.CSS_SELECTOR, "#txtTotalPage887").text
        조회_페이지수 = int(조회_페이지수)
        logt("조회결과수=%d, 페이지수=%d" % (조회건수, 조회_페이지수))
        
        trs = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_body_tbody > tr")
        현재페이지_ROW_수 = len(trs)

        시작페이지_index = 100   # 1 베이스 시작페이지 지정 (오류 후 재시작용)
        추가row수 = 0
        for i in range(시작페이지_index, 조회_페이지수+1):  # 시작은 1부터 ~
            p_start = time.time()
            logt(f"조회페이지 = {i} page -------------------------")


            # 조회 페이지 클릭        
            if i>10 and i%10 == 1:
                driver.find_element(By.ID, f'pglNavi887_next_btn').click()
            else:
                driver.find_element(By.ID, f'pglNavi887_page_{i}').click()

            time.sleep(7)
            alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
            if alt_msg.find('이중로그인 방지로 통합인증이 종료되었습니다') >= 0:
                logt("이중로그인으로 프로그램 종료!!!!!")
                driver.close()
                sys.exit()

            trs = driver.find_elements(By.CSS_SELECTOR, "#ttirnam101DVOListDes_body_tbody > tr")
            data_list = []
            for row in range(현재페이지_ROW_수):
                start = time.time()

                tds = trs[row].find_elements(By.TAG_NAME, "td")
                과세연월   = tds[2].text
                신고서종류 = tds[3].text
                신고구분   = tds[4].text
                신고유형   = tds[5].text
                성명       = tds[6].text
                주민번호1  = tds[7].text[0:6]
                접수방법   = tds[8].text
                접수일시   = tds[9].text
                접수번호   = tds[10].text
                제출자ID   = tds[30].text
                부속서류제출여부 = tds[36].text
                납부여부   = tds[38].text

                end = time.time()

                # 성명이 없다면 마지막이라고 판단
                if 성명 == '':
                    break

                try:
                    data = (
                        과세연월, 신고서종류, 신고구분, 신고유형, 성명, 
                        주민번호1, 접수방법, 접수일시, 접수번호, 제출자ID, 
                        부속서류제출여부, 납부여부
                    )
                    data_list.append(data)
                    logt(f"insert page={i} row={row}, 성명={성명}, 주민번호1={주민번호1}, time={end - start:.5f} sec")
                except Exception as e:
                    logt(f" =============> ERROR insert page={i} row={row}, 성명={성명}, 주민번호1={주민번호1}, time={end - start:.5f} sec : {e}")
                
            # end of for(100개씩)
            try:
                affected = dbjob.insert_audit_ht(data_list)
                logt(f"insert page={i} time={end - start:.5f} sec, affected={affected}")
            except Exception as e:
                logt(f" =============> ERROR insert page={i} time={end - start:.5f} sec : {e}")

            p_end = time.time()
            logt(f"{i} page,  소요시간={p_end - p_start:.5f} sec")            

        logt(f"총 insert row count = {추가row수}")
        #######################################################################################`
    
    except Exception as e:
        logt(f"======= 오류발생 : {e}")
        traceback.print_exc()
    
    else:  # 오류없이 정상 처리시
        logt("======= 정상종료")

    driver.close()
    
    exit(0)

