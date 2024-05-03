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
# 토스에 제출한 PDF의 text가 추출되지 않아서 다시 다운로드 받을 때 사용함
AU_STEP = 4
group_id = ""

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



for_one_user_name = ""
for_one_user_id   = ""
if len(sys.argv) == 1:
    logt("실행할 담당자 정보가 없습니다.")
    for_one_user_name = "관리자"
    for_one_user_id = config.USER_LIST[for_one_user_name]    
else :
    try:
        if len(for_one_user_name) == 0 :
            for_one_user_name = sys.argv[1]

        for_one_user_id = config.USER_LIST[for_one_user_name]
    except :
        loge("실행할 담당자 정보를 찾을 수 없습니다.  config.py")
        exit()

# 그룹 정보 얻기
try:
    if len(group_id) == 0 :
        group_id = sys.argv[2]
except :
    loge("그룹 정보를 입력하지 않으셨습니다.")
    exit()



if __name__ == '__main__':

    print("4단계 : 위택스 파일 다운로드")
    dbjob.connect_db()

    # 작업자별 로그인 정보
    login_info = config.LOGIN_INFO
    
    if for_one_user_id == "MANAGER_ID" :
        login_info['name'] = "관리자"
        login_info['login_id'] = "MANAGER_ID"
        login_info['login_pw'] = "xxxx"  # 사용안함
    else :
        user_row = dbjob.get_worker_info(for_one_user_id)
        login_info['name'] = user_row['name']
        login_info['login_id'] = for_one_user_id
        login_info['login_pw'] = ''

    jobs = dbjob.select_auto_4_토스PDF오류(group_id, login_info['login_id'], config.BATCH_BUNDLE_COUNT)
    if len(jobs) == 0:
        logt("작업할 리스트가 없습니다. 작업종료")    
        sys.exit()
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
            dbjob.update_HtTt_au4_reset(ht_tt_seq)

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
                    driver.find_element(By.ID, 'taxSeq').send_keys(jobs[k]['hometax_reg_num'])
                    time.sleep(0.3)

                    logt(f"주민번호= {jobs[k]['holder_ssn1']}-{jobs[k]['holder_ssn2']}, 홈택스 접수번호= {jobs[k]['hometax_reg_num']}")
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
                    if jobs[k]['data_type'] == 'AUTO' and ex_wetax_income_tax != wetax_income_tax:
                        dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '세금액비교오류: 예상=%d, 살제=%d' % (wetax_income_tax, ex_wetax_income_tax))
                        break

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
                        # 납부서출력 버튼 ----------------------------------------------------------------------------------------------------------
                        try :
                            print("납부서출력 버튼")
                            ele = driver.find_element(By.CSS_SELECTOR, '#sendForm > div.btn_wrap > ul > li.float_l > a:nth-child(4)')
                            ele.click()
                        except:
                            try :
                                time.sleep(2)
                                print("납부서출력 버튼 ===>>> 재시도")
                                ele = driver.find_element(By.CSS_SELECTOR, '#sendForm > div.btn_wrap > ul > li.float_l > a:nth-child(4)')
                                ele.click()
                            except:
                                print("납부서출력 => NOT FOUND")
                                exit(0)
    
                        time.sleep(1)
                        print("윈도우 핸들 1")
                        window_handles = driver.window_handles
                        print (window_handles)


                        # 윈도우오픈 확인 실패시 재시도
                        if len(window_handles) == 1:
                            print("윈도우 핸들 2 => 재시도")
                            time.sleep(1)
                            window_handles = driver.window_handles

                        if len(window_handles) == 2:
                            print("팝업 윈도우 오픈 확인")


                        time.sleep(2)

                        #img_save_path = project_dir + os.sep + "resource" + os.sep + "internet.png"
                        #img_save_path = resource_dir + "internet.png"
                        try:
                            print("화면끝으로 이동")
                            #pyautoui_image_click(img_save_path)
                            pyautogui.click(x=200, y=400)
                            time.sleep(0.2)
                            pyautogui.press('esc')
                            pyautogui.press('end')
                        except Exception as e:
                            try:
                                print("화면끝으로 이동 재시도")
                                #pyautoui_image_click(img_save_path)
                                pyautogui.click(x=200, y=400)
                                time.sleep(0.2)
                                pyautogui.press('esc')
                                pyautogui.press('end')
                            except Exception as e:
                                print(f"화면캡쳐 오류  => 프로그램 종료 : {e}")
                                sys.exit()

                        time.sleep(0.5)
                        driver.switch_to.window(driver.window_handles[1])
                        #print("팝업 윈도우 크기/위치 이동")
                        # 브라우저 화면 크기 변경하기
                        driver.set_window_size(810, 900)
                        driver.set_window_position(0,0)

                        print("윈도우 타이틀= " + driver.title)

                        # 이미지 캡쳐  -----------------
                        cap_filename = "NO_NAME_CAP"
                        region=(0, 0, 10, 10)
                        cap_filename = ht_file.get_file_name_by_type("WE_DOWN_5_CAP")
                        region=(10, 180, 810-20, 900-180)
                        capture_img_fullpath = dir_work + "work" + os.sep + cap_filename
                        print("캡쳐 다운로드path= %s" % capture_img_fullpath)

                        try :
                            pyautogui.screenshot(capture_img_fullpath, region=region)
                        except:
                            logt("이미지캡쳐 오류")
                            traceback.print_exc()
                        
                        time.sleep(0.5)
                        if os.path.isfile(capture_img_fullpath):
                            logt("이미지캡쳐 => DB 입력하기")
                            dbjob.insert_or_update_upload_file("WE_DOWN_5_CAP", ht_tt_seq, holder_nm)
                        else:
                            logt("이미지캡쳐 확인실패!!!!!")



                        # # 납부서 파일 다운로드 ------------

                        # # 다운로드 파일
                        # print("GUI 다운로드파일선택팝업 대기")

                        # # file_type별 파일이름 결정
                        # dir_work = ht_file.get_dir_by_htTtSeq(ht_tt_seq, True)  # True => 폴더 생성
                        # fullpath = dir_work + ht_file.get_file_name_by_type("WE_DOWN_5")
                        # logt("납부서 다운로드 경로= %s" % fullpath, 0.5)

                        # # 이미 존재하면 삭제
                        # tmp_down_path = "C:\\Users\\lm\\Downloads\\report.pdf"
                        # if os.path.isfile(tmp_down_path):
                        #     os.remove(tmp_down_path)
                        # if os.path.isfile(fullpath):
                        #     os.remove(fullpath)

                        # img_save_path = resource_dir + "wetax_pdf_save.png"
                        # print("PDF버튼 클릭 :: " + img_save_path)

                        # # 이미지만 클릭해도 다운로드 폴더에 내려받기가 가능해짐
                        # # 아래의 함수에서 PDF내려 받기를 개별PC 다운로드 폴더에 report.pdf라는 이름으로 다운로드한다 
                        # pyautoui_image_click(img_save_path)


                        # time.sleep(1)

                        # # 다운로드 폴더에서 작업폴더로 파일 이동
                        # if os.path.isfile(tmp_down_path):
                        #     shutil.move(tmp_down_path, fullpath)
                        
                        # time.sleep(0.5)
                        # if os.path.isfile(fullpath):
                        #     logt("파일저장 성공: 파일타입= %s, 경로= %s" % ("WE_DOWN_5", fullpath))
                        #     logt("파일저장 확인완료 => DB 입력하기")
                        #     dbjob.insert_or_update_upload_file("WE_DOWN_5", ht_tt_seq, holder_nm)

                        #     # 4단계 정상처리 
                        #     dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'S', None)

                        #     print("팝업윈도우 close()")
                        #     driver.close()
                        #     driver.switch_to.window(driver.window_handles[0])
                        # else:
                        #     logt("파일저장 확인실패!!!!! => 실패처리 후 다음 건 처리")
                        #     dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '파일저장실패')

                        #     print("팝업윈도우 close()")
                        #     driver.close()
                        #     continue
                        
                        try :
                            auto_step_2.file_download(jobs[k], 'WE_DOWN_5')

                            # 4단계 정상처리 
                            dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'S', None)

                            print("팝업윈도우 close()")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])   
                        except Exception as e:
                            logt("파일저장 확인실패!!!!! => 실패처리 후 다음 건 처리")
                            dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', f'파일저장실패-{e}')
                            
                            print("팝업윈도우 close()")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])   
                            continue


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
                    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'S', '면세')
                    dbjob.update_HtTt_stepCd(ht_tt_seq, 'REPORT_DONE')
                    is_search = True
                elif "취소" == ispay  and i_tax_name == TAX_NAME:  # and i_name == jobs[k]['holder_nm']   ==> 간혹 이름이 다른 사람존재
                    dbjob.update_HtTt_AuX(AU_STEP, ht_tt_seq, 'E', '취소')
                    is_search = True
                else :    
                    print("%d / %d %s, %s, %s, %s ===========> SKIPPING" % (i, len(e_trs), i_name, i_tax_name, tax,  ispay))
                    is_search = False


                time.sleep(0.2)

                if i>= loop_to:
                    break

            # END <while>

            print("한줄처리 완료 --------------------------------------")
            time.sleep(0.2)

        # EOWhile

    except Exception as e:
        print(e)
        traceback.print_exc()

    else :
        print("===========정상종료 ")

    print("프로그램 종료")

    driver.close()

    exit(0)
