from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
#except StaleElementReferenceException:

import time

from common import *

import auto_login
import dbjob

import config
import sele_common as sc



au_step = "종합_간편인증_지급명세서"

dbjob.set_global(group_id, None, None, None, au_step)


def main():
    guest ={}

    guest['id'] = 'xxxxx'
    guest['name'] = '정율섭'
    guest['sms_num'] = '01036565574'
    guest['hometax_id'] = 'imgoodfeel'
    guest['hometax_pw'] = '!topsol01'
    
    간편인증_방식 = "KAKAO(카카오)"
    
    driver: WebDriver = auto_login.init_selenium()
    driver.set_window_size(1550, 1150)
    
    # 작업자별 로그인 정보
    login_info = config.LOGIN_INFO
    login_info['name'] = guest['name']
    login_info['login_id'] = guest['hometax_id']
    login_info['login_pw'] = guest['hometax_pw']
    
    # 자동로그인 처리
    driver.set_window_position(0, 0)
    
    logt("로그인 시간", 1)
    auto_login.login_guest(driver, login_info)
    logt("로그인 완료")
    
    
    # 팝업 창이 있으면 모두 닫기
    if len(driver.window_handles) > 1:
        for i in range(len(driver.window_handles)-1, 0, -1):
            driver.switch_to.window(driver.window_handles[i])
            driver.close()
            
        driver.switch_to.window(driver.window_handles[0])
    
    
    # ---------------------------------------------------
    sc.click_button_by_id(driver, 'myMenuQuickImg1', 'My홈택스 이미지', 0.5)
    time.sleep(1)
    
    
    # ---------------------------------------------------
    # [My홈택스] 시작
    driver.switch_to.frame("txppIframe")
    
    # 연말정산,지급명세서 클릭
    sc.click_button_by_id(driver, 'textbox248', '지급명세서 버튼', 1)
    driver.find_element(by=By.XPATH, value='//*[@id="a_0817020000"]').click()
    
    
    
    # ==========================================================
    # 인증 팝업 창
    # ==========================================================
    time.sleep(0.5)
    
    # 팝업창
    target_window_title = "인증선택"
    
    # 윈도우 전화
    driver.switch_to.window(driver.window_handles[-1])
    driver.set_window_position(0, 0)
    
    cur_title = driver.title
    if target_window_title != cur_title:
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        cur_title = driver.title
        if target_window_title != cur_title:
            print('원하는 창을 찾을 수 없습니다.')    
            sys.exit()
            
    sc.click_button_by_id(driver, 'btnSm_type04', '간편인증 버튼', 0.5)
    
    sc.move_iframe(driver, 'UTECMADA02_iframe', 1)
    sc.move_iframe(driver, 'simple_iframeView', 1)
    
    # 인증방식 선택
    driver.execute_script("$('img[alt=\"" + 간편인증_방식 + "\"]').click()")
    
    
    # 본인인증 이름/생년월일/휴대폰번호 넣기
    driver.find_element(By.CSS_SELECTOR, 'input[data-id="oacx_name"]').send_keys('정율섭')
    driver.find_element(By.CSS_SELECTOR, 'input[data-id="oacx_birth"]').send_keys('19730605')
    driver.find_element(By.CSS_SELECTOR, 'input[data-id="oacx_phone2"]').send_keys('36565574')
    
    # 전체 동의 선택
    driver.execute_script("$('#totalAgree').click()")
    
    
    # 인증 요청 클릭
    driver.execute_script("$('#oacx-request-btn-pc').click()")
    time.sleep(1)
    
    인증_확인_간격Sec = 3
    인증유효시간Sec = 5 * 60
    start_time = time.time()
    isOk = True
    
    nTry = 0
    while (True):
        
        elapsed_time = time.time() - start_time
        if elapsed_time >= 인증유효시간Sec:
            break
    
        time.sleep(인증_확인_간격Sec)
        nTry += 1
        logt(f"{nTry} 시도:  경과 시간 = {elapsed_time}")
        
        try:
            # 인증 완료 버튼 클릭
            driver.execute_script("$('#oacxEmbededContents > div.standby > div > button.basic.sky.w70').click()")
            
            # 오류인 경우
            ele = driver.find_element(By.CLASS_NAME, 'alertArea')
            msg = ele.text
            
            if msg.find('서명되지 않았습니다.') >=0 or msg.find('토큰 유효 시간 만료') >=0:
                isOk = False
                driver.execute_script("$('#oacxEmbededContents > div.alertArea > div > div.btnArea > button').click()")
                continue
        except NoSuchElementException:
            # 정상인 경우
            logt('정상적으로 인증이 되었습니다(1).  ==> 다음단계 진행 (초기 페이지 이동)')
            break
        except Exception as e:
            print (e)
            logt('정상적으로 인증이 되었습니다(2).  ==> 다음단계 진행 (초기 페이지 이동)')
            break
        
        
    # ==========================================================
    # 기본 작업 윈도위 복귀
    # ==========================================================
    
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[0])
    
    # [My홈택스] 시작
    driver.switch_to.frame("txppIframe")
    
    # 연말정산,지급명세서 클릭
    sc.click_button_by_id(driver, 'textbox248', '지급명세서 버튼', 1)
    driver.find_element(by=By.XPATH, value='//*[@id="a_0817020000"]').click()
    
    time.sleep(2.5)
        
    # IFRAME 전환
    #sc.move_iframe(driver, "UTXPPBAA48_iframe")
    driver.switch_to.frame("UTXPPBAA48_iframe")
    
    # 지급명세서 표 읽기
    tbody = driver.find_element(By.ID, 'grdList_body_tbody')
    rows = tbody.find_elements(By.TAG_NAME, 'tr')
    row_cnt = len(rows)    
    
    for row_num in range(row_cnt):
        # 각 행의 td 요소 찾기 (순번/이름/...)
        cells = []
        
        # StaleElementReferenceException 회피하기 위해 사용 직전 재 생성하기
        try :
            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.frame("txppIframe")
            driver.switch_to.frame("UTXPPBAA48_iframe")
            tbody = driver.find_element(By.ID, 'grdList_body_tbody')
            rows = tbody.find_elements(By.TAG_NAME, 'tr') 
            cells = rows[row_num].find_elements(By.TAG_NAME, 'td')
        except NoSuchElementException as e:
            print(e)
        
        # 각 td 요소의 텍스트 출력
        귀속년도 = cells[0].text
        
        if 귀속년도 == '2022':
            지급명세서_종류 = cells[1].text
            if 지급명세서_종류 == '거주자 사업소득지급명세서':
                cells[5].find_element(By.XPATH, './span/button').click()
                time.sleep(1)
                fn_지급명세서_for_거주자사업소득지급명세서(driver, 지급명세서_종류)
                    
            elif 지급명세서_종류 == '근로소득지급명세서':
                print (f"다른 종류의 소득이 있습니다.  ===> {지급명세서_종류}")
                
                cells[5].find_element(By.XPATH, "./span/button").click()
                time.sleep(1)
                fn_지급명세서_for_근로소득지급명세서(driver, 지급명세서_종류)
                
            else:
                print (f"다른 종류의 소득이 있습니다.  ===> {지급명세서_종류}")
                
                cells[5].find_element(By.XPATH, "./span/button").click()
                time.sleep(1)
                fn_지급명세서_for_기타(driver, 지급명세서_종류)
            
            # 부모창으로 이동      
            driver.switch_to.window(driver.window_handles[0])
            
        else:
            break
    # end of for
    
    
    
def fn_지급명세서_for_거주자사업소득지급명세서(driver: WebDriver, 지급명세서_종류):
    driver.switch_to.window(driver.window_handles[-1])
    driver.set_window_position(0, 0)
    driver.set_window_size(1250, 1150)
    
    # 개인정보 공개 선택
    driver.find_element(By.ID, 'mskApplcYn_input_1').click()
    time.sleep(1.5)
    
    # 지급명세서 표 읽기
    tbody = driver.find_element(By.ID, 'gridIeXampCtlInqr_body_tbody')
    rows = tbody.find_elements(By.TAG_NAME, 'tr')
    
    row_num = -1
    for row in rows:
        row_num += 1
        
        #각 행의 td 요소 찾기
        cells = row.find_elements(By.TAG_NAME, 'td')
        
        #각 td요소의 텍츠스 출력
        성명 = cells[2].text
        
        # 성명 클릭 
        if row_num>0:  # 첫 라인은 클릭 생략
            cells[2].find_element(By.XPATH, './span/a').click()
            time.sleep(3)
        
        # 화면캡쳐
        driver.save_screenshot(f"{지급명세서_종류}_{row_num}.png")
        
        # 테이블 값 읽기
        # IFRAME 전환
        sc.move_iframe(driver, "iframe2_UTESFAAZ01")
        
        table = driver.find_element(By.CSS_SELECTOR, "#targetDiv1 > div > div.report_paint_div > div:nth-child(2)")
        tcells = table.find_elements(By.XPATH, "./span")
        
        
        지급총액_sum = 0
        소득세_sum = 0
        지방소득세_sum = 0
        
        idx_start = 66
        while(idx_start < 200):   # <span>이 208개 존재함
            # 지급총액
            tcell = tcells[idx_start]
            지급총액 = tcell.get_attribute("aria-label")
            if 지급총액 == "":
                break
            
            # 소득세
            tcell = tcells[idx_start + 2]
            소득세 = tcell.get_attribute("aria-label")
        
            # 지방소득세
            tcell = tcells[idx_start + 3]
            지방소득세 = tcell.get_attribute("aria-label")
        
            지급총액_sum   += int(지급총액.replace(",", ""))
            소득세_sum     += int(소득세.replace(",", ""))
            지방소득세_sum += int(지방소득세.replace(",", ""))
            
            # 다음 라인 읽기
            idx_start += 10
            
            logt(f'{지급명세서_종류} 순번={row_num}: 지급총액_sum   = {지급총액_sum}')
            logt(f'{지급명세서_종류} 순번={row_num}: 소득세_sum     = {소득세_sum}')
            logt(f'{지급명세서_종류} 순번={row_num}: 지방소득세_sum = {지방소득세_sum}')
    
        logt(f'{지급명세서_종류} 합계: 지급총액_sum   = {지급총액_sum}')
        logt(f'{지급명세서_종류} 합계: 소득세_sum     = {소득세_sum}')
        logt(f'{지급명세서_종류} 합계: 지방소득세_sum = {지방소득세_sum}')

    # 오픈된 지급명세서 미리보기 창 닫기
    driver.close()
    
    
def fn_지급명세서_for_근로소득지급명세서(driver: WebDriver, 지급명세서_종류):
    driver.switch_to.window(driver.window_handles[-1])
    driver.set_window_position(0, 0)
    driver.set_window_size(1250, 1150)
    
    # 개인정보 공개 선택
    driver.find_element(By.ID, 'mskApplcYn_input_1').click()
    time.sleep(1.5)
    
    # 지급명세서 표 읽기
    tbody = driver.find_element(By.ID, 'gridIeXampCtlInqr_body_tbody')
    rows = tbody.find_elements(By.TAG_NAME, 'tr')
    
    지급총액_sum = 0

    row_num = -1
    for row in rows:
        row_num += 1
        
        #각 행의 td 요소 찾기
        cells = row.find_elements(By.TAG_NAME, 'td')
        
        #각 td요소의 텍츠스 출력
        성명 = cells[2].text
        
        # 성명 클릭
        if row_num>0:  # 첫 라인은 클릭 생략
            cells[2].find_element(By.XPATH, './span/a').click()
        
        time.sleep(2.5)
        
        # IFRAME 전환
        sc.move_iframe(driver, "iframe2_UTESFAAZ01")
        
        # 테이블 맨 아래로 스코롤 하기
        div_table = driver.find_element(By.CLASS_NAME, 'report_paint_div')
        driver.execute_script("arguments[0].scrollBy(0, 2000)", div_table)
        time.sleep(0.5)

        # 화면캡쳐
        driver.save_screenshot(f"{지급명세서_종류}_{row_num}.png")
        

        # 테이블 값 읽기
        table = driver.find_element(By.CSS_SELECTOR, "#targetDiv1 > div > div.report_paint_div > div:nth-child(2)")
        tcells = table.find_elements(By.XPATH, "./span")
        
        
        소득세_sum = 0
        지방소득세_sum = 0
        
        idx_합계 = 128
        지급총액 = tcells[idx_합계].get_attribute("aria-label").replace(",", "")   # 지급총액 idx = 128
        logt(f'{지급명세서_종류} 순번={row_num}: 지급총액={지급총액}')
        지급총액_sum += int(지급총액)
    
    # 오픈된 지급명세서 미리보기 창 닫기
    logt(f'{지급명세서_종류} 합계: 지급총액 {지급총액_sum}')
    
    driver.close()
    return 지급총액_sum



def fn_지급명세서_for_기타(driver: WebDriver, 지급명세서_종류):
    driver.switch_to.window(driver.window_handles[-1])
    driver.set_window_position(0, 0)
    driver.set_window_size(1250, 1150)
    
    time.sleep(1)
    
    driver.save_screenshot(f"{지급명세서_종류}.png")
    driver.close()


if __name__ == '__main__':
    main()
    
    logt("프로그램 종료")
    sys.exit()