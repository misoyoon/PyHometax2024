from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import traceback

import dbjob

def init_selenium() :
    cur_dir = os.getcwd()
    chromedriver_path =  cur_dir + os.sep + "pyHometax" + os.sep + "chromedriver.exe" #resource_path("chromedriver.exe")
    print("크롬드라이버 위치=%s" % chromedriver_path)

    # 1.크롬접속
    driver = webdriver.Chrome(chromedriver_path)

    # 브라우저 위치 조정하기
    driver.set_window_position(0,0)
    # 브라우저 화면 크기 변경하기
    driver.set_window_size(1300,1000)

    # Implicitly wait을 10초로 설정하면 페이지가 로딩되는데 10초까지 기다립니다. 
    # 만약 페이지 로딩이 2초에 완료되었다면 더 기다리지 않고 다음 코드를 수행합니다. 
    # 기본 설정은 0초로 되어있고, 
    # 한번만 설정하면 driver를 사용하는 모든 코드에 적용이 됩니다.
    driver.implicitly_wait(5)

    return driver

TAX_NAME = "지방소득세(양도소득세분)"
url = 'https://www.wetax.go.kr/simple/?cmd=LPEPBZ4R0'

dbjob.connect_db()
data = dbjob.select_check_3(100)

if __name__ == '__main__':
    
    try:
        driver = init_selenium()
        print("위택스 이동")
        
        driver.get(url)  

        time.sleep(1)
        print("오늘은 무시")
        driver.find_element(By.CSS_SELECTOR, '#nos_pop > div.pop_foot > label > span').click()
        time.sleep(0.1)


        for k in range(len(data)) :
            print("================================================================================")
            print("ht_tt_seq= %s , Name= %s, ssn1= %s , ssn2= %s reg_num= %s " % 
                            (data[k]['ht_tt_seq'], data[k]['holder_nm'], data[k]['holder_ssn1'], data[k]['holder_ssn2'], data[k]['hometax_reg_num']))
            print("================================================================================")
            i = 0
            loop_to = 1
            is_search = True
            
            while True:

                i += 1
                strI = str(i)
                print ("(%d) : 개인처리수= %d / %d 시도중 ...." % (k, i, loop_to))

                if is_search == True:
                    driver.get(url)
                    time.sleep(1)


                    driver.find_element(By.ID, 'regNoFront').send_keys(data[k]['holder_ssn1'])
                    time.sleep(0.1)
                    driver.find_element(By.ID, 'regNoEnd').send_keys(data[k]['holder_ssn2'])
                    time.sleep(0.2)
                    driver.find_element(By.ID, 'taxSeq').send_keys(data[k]['hometax_reg_num'])
                    time.sleep(0.3)

                    elements = driver.find_elements(By.CSS_SELECTOR, '.searchBtn')
                    print(elements)
                    elements[0].click() # 첫번째 것을 조회버튼으로 인식

                    time.sleep(0.5)
                    e_trs = driver.find_elements(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr')
                    loop_to = len(e_trs)

                    print("조회결과 수 = %s" % loop_to)
                
                    # 조회 결과 분석: 만약1이면 조회 결과 없음으로 다음 사람 조회
                    if loop_to == 1:
                        # DB 업데이트
                        dbjob.update_HtTt_au3_reset(data[k]['ht_tt_seq'])
                        break



                if i > loop_to:
                    print('index 초과 프로그램 종료')
                    driver.close()
                    exit(0)

                # 양도자명
                e_name = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(2)')
                i_name = e_name.text.strip()

                # 세금 항목명
                e_tax_name = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(6)')
                i_tax_name = e_tax_name.text.strip()

                e_tax = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(7)')
                tax = e_tax.text.replace(",", "").replace("원", "").strip()
                
                e_ispay = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(9)')
                ispay = e_ispay.text.replace(",", "").strip()

                if i_name == data[k]['holder_nm'] and i_tax_name == TAX_NAME and "미납" == ispay :

                    print("%d / %d %s, %s, %s, %s ===> 취소대상" % (i, len(e_trs), i_name, i_tax_name, tax,  ispay))    

                    #상세페이지 이동을 위한 click
                    ele = driver.find_element(By.CSS_SELECTOR, '#list_form > fieldset > div > div.cont_body > div.board > div > div > table > tbody > tr > td > div > table > tbody > tr:nth-child('+strI+') > td:nth-child(5)')
                    ele.click()

                    # 대기
                    time.sleep(1)

                    # 신고취소 버튼
                    try :
                        print("신고취소 버튼")
                        ele = driver.find_element(By.CSS_SELECTOR, '#sendForm > div.btn_wrap > ul > li.float_r > a.btn_type01.bg4')
                        ele.click()
                        
                        try :
                            time.sleep(2)
                            print("신고취소 버튼 ===>>> 재시도")
                            ele = driver.find_element(By.CSS_SELECTOR, '#sendForm > div.btn_wrap > ul > li.float_r > a.btn_type01.bg4')
                            ele.click()
                        except:
                            print("신고취소버튼 => NOT FOUND")
                            exit(0)
                    except:
                        pass

                    time.sleep(0.5)
                    window_handles = driver.window_handles
                    print("윈도우 핸들 1")
                    print (window_handles)

                    if len(window_handles) == 2:


                        print("팝업 윈도우 오픈 확인")
                        driver.switch_to.window(driver.window_handles[1])
                        time.sleep(0.3)

                        ele = driver.find_element(By.CSS_SELECTOR, "#cancelReason")
                        ele.send_keys("신고 오류로 인한 취소 요청")

                        print("취소하기 버튼 클릭")
                        ele = driver.find_element(By.CSS_SELECTOR, "#p_cont > div.btn_wrap.text_r > a")
                        print(ele)
                        ele.click()
                        time.sleep(0.3)

                        window_handles = driver.window_handles
                        print("윈도우 핸들 2")
                        print(window_handles)

                        print("팝업윈도우 close()")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                        is_search = True
                else :    
                    print("%d / %d %s, %s, %s, %s ===========> SKIPPING" % (i, len(e_trs), i_name, i_tax_name, tax,  ispay))
                    is_search = False


                # DB 업데이트
                dbjob.update_HtTt_au3_reset(data[k]['ht_tt_seq'])

                print("한줄처리 완료 --------------------------------------")
                time.sleep(0.2)

                if i>= loop_to:
                    break

            # END <while>
            print("작업종료 !!!!!!!!!!!!!!!!!!!!")
            time.sleep(0.2)

    except Exception as e:
        print(e)
        traceback.print_exc()

    else :
        print("===========정상종료 ")

    print("프로그램 종료")

    driver.close()

    exit(0)


            
    exit(0)

