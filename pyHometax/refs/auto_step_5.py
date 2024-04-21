import time
import os

from selenium.webdriver.support.ui import WebDriverWait
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
import pyHometax.common_sele as sc
import auto_step_1
import config

# 자동신고단계 -----------------------------
# 증빙자료 업로드
au_step = 5
au_step_name = "증빙자료 업로드"

root_dir = config.FILE_ROOT_DIR

# 메뉴이동 : '신고/납부' 클릭
def click_메뉴_신고납부(driver):

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

    logt("클릭: 신고 부속,증빙서류 제출", 2)
    driver.find_element(By.ID, 'tabControl1_UTERNAAZ11_tab_tabs5_UTERNAAZ11').click()


    try :
        time.sleep(1)
        alert = driver.switch_to_alert()
        alert_msg = alert.text
        if alert_msg.find("로그인 정보가 없습니다.") > -1 :
            logt("현재는 로그아웃 상태")
            alert.accept()
            raise BizException("로그아웃상태")   
        else :
            logt("정상 로그인 상태1")
    except BizException as e:
        raise e
    except :
        pass


def do_step5(driver, jobs, user_id):
    logt(au_step_name, au_step)

    click_메뉴_신고납부(driver)


    # 양도자 반복처리      
    cur_window_handle = driver.current_window_handle      

    # logt("작업프레임 이동: txppIframe", 0.5)
    # driver.switch_to.frame("txppIframe")

    driver.find_element(By.ID, "rtnDtSrt_UTERNAAZ41_input").clear()
    time.sleep(0.2)
    driver.find_element(By.ID, "rtnDtSrt_UTERNAAZ41_input").send_keys("20240501")
    time.sleep(0.2)
    driver.find_element(By.ID, "rtnDtEnd_UTERNAAZ41_input").clear()
    time.sleep(0.2)
    driver.find_element(By.ID, "rtnDtEnd_UTERNAAZ41_input").send_keys("20240531")
    time.sleep(0.2)

    # 작성방식 
    logt("세목 선택")
    select = Select(driver.find_element(By.ID, "selectbox2_UTERNAAZ41"))
    select.select_by_visible_text('양도소득세')
    time.sleep(0.5)

    오류발생건수 = 0
    loop_num = 0
    for job_idx in range(0, len(jobs)):
        ht_info = jobs[job_idx]
        ht_tt_seq = ht_info['ht_tt_seq']

        try:
            logi("####################################################")
            logi("%d / %d 처리 ..." % (job_idx+1, len(jobs)))        
            logi("####################################################")
            ht_info = jobs[job_idx]

            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(cur_window_handle)

            logt("홈택스 조회 윈도우 이동", 0.5)
            driver.switch_to.window(cur_window_handle)

            print(driver.window_handles)
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(cur_window_handle)

            logt("작업프레임 이동: txppIframe", 0.5)
            driver.switch_to.frame("txppIframe")

            # ================================================
            # 반복처리
            do_step5_loop(driver, ht_info)
            # ================================================
        
        except BizException as e:
            오류발생건수 += 1
            logt(f"#################### except BizException : 오류발생건수={오류발생건수}")
            print(e)
            dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'E', f"{e.name}: {e.msg}")

        except Exception as e:
            오류발생건수 += 1
            logt(f"#################### except: 오류발생건수={오류발생건수}")
            traceback.print_exc()
            print(e)
            dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'E', None)
        
        else:  # 오류없이 정상 처리시
            logt("#################### (정상처리)")
            dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'S', None)

        # job 완료 처리 
        logt("####### 한건처리 완료 #######", 0.2)

        if 오류발생건수 >=10 :
            logi(f"연속 오류 발생으로 프로그램을 종료합니다. 오류발생건수={오류발생건수}")
            if driver:
                driver.close
            sys.exit()






def do_step5_loop(driver, ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    cur_window_handle = driver.current_window_handle
    ssn1 = ht_info['holder_ssn1']
    ssn2 = ht_info['holder_ssn2']

    logi("******************************************************************************************************************")
    logt("양도인=%s, HT_TT_SEQ=%d, SSN= %s %s" % (ht_info['holder_nm'], ht_info['ht_tt_seq'], ssn1, ssn2))
    logi("******************************************************************************************************************")
    
    # 기존 로그 삭제
    #dbjob.delete_auHistory_byKey(ht_tt_seq, au_step)

    ssn = ht_info['holder_ssn1'] + ht_info['holder_ssn2']

    # 주민번호 입력
    logt("주민번호 입력: %s %s" % (ssn1, ssn2), 0.5)
    driver.find_element(By.ID, 'inputResno_1').clear()
    time.sleep(0.2)
    driver.find_element(By.ID, 'inputResno_1').send_keys(ssn1)
    time.sleep(0.2)
    driver.find_element(By.ID, 'inputResno_2').clear()
    time.sleep(0.2)
    driver.find_element(By.ID, 'inputResno_2').send_keys(ssn2)
    time.sleep(0.3)

    logt("조회클릭")
    driver.find_element(By.ID, 'trigger45_UTERNAAZ41').click()

    time.sleep(1)
    alt_msg = sc.click_alert(driver, "조회가 완료되었습니다.")
    print("Alter Message Return=%s" % alt_msg)
    # 결과가 없을 경우 처리
    if alt_msg.find("사업자등록번호") > -1 :
        logt("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음")
    elif alt_msg.find("이중로그인 방지로 통합인증이 종료되었습니다") > -1 :
        logt("이중로그인 방지로 통합인증이 종료되었습니다 => 프로그램 종료")
        sys.exit()
    elif alt_msg.find("조회된 데이터가 없습니다") > -1 :
        logt("조회결과 없음, 주민번호: %s" % ssn)
        raise BizException("조회결과없음", f"주민번호:{ssn}, 실행자={ht_info['reg_id']}")

    ele_s = driver.find_element(By.CSS_SELECTOR, "#txtTotal_UTERNAAZ41").text   # 총 1/2 등....
    logt("조회결과 갯수= %d" % int(ele_s))

    if int(ele_s) == 0:
        raise BizException("조회결과없음", f"조회결과없음, 실행자={ht_info['reg_id']}")

    elif int(ele_s) > 1:
        raise BizException("복수신고건", "신고건수= %d" % int(ele_s))

    elif int(ele_s) == 1:  # 정상케이스

        td_index_info = {
            'report_type'     : 3 , # 신고유형
            'holder_nm'       : 4 , # 성명
            'hometax_reg_num' : 6 , # 신고서접수번호
            'upload_btn'      : 16  # 첨부하기
        }

        ele1 = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" + str(td_index_info['report_type'])  + " > span")
        ele2 = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" + str(td_index_info['report_type']+1)+ " > span")
        
        offset = 0
        if ele1.text == "정기신고" :
            offset = 0
        elif ele2.text == "정기신고" :
            offset = 1

        logt("결과 OFFSET= %d" % offset)


        selector = "#ttirnam101DVOListDes_cell_0_" +str(td_index_info['holder_nm']+offset)+ " > span"
        print (selector)
        ele = driver.find_element(By.CSS_SELECTOR, selector)    
        hometax_holder_nm = ele.text

        # 양도인 이름이 같은지 조회
        logt("양도인명 확인 JNK= %s, Hometax= %s" % (ht_info['holder_nm'], hometax_holder_nm))
        if hometax_holder_nm != ht_info['holder_nm']:
            raise BizException("양도인명 불일치", "홈택스 양도인명= %s" % hometax_holder_nm)

        # 홈택스 접수번호
        ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(td_index_info['hometax_reg_num']+offset)+ " > span")
        hometax_reg_num = ele.text
        logt("접수번호 확인 JNK= %s, Hometax= %s" % (ht_info['hometax_reg_num'], hometax_reg_num))
        if hometax_reg_num != ht_info['hometax_reg_num']:
            raise BizException("접수번호 불일치", "홈택스 접수번호= %s" % hometax_reg_num)


        # 첨부파일 존재 확인
        #ht_tt_file_seq = ht_info['source_file_seq']
        source_file_path = ht_file.get_work_dir_by_htTtSeq(ht_tt_seq)
        source_file_path = source_file_path + 'source_upload.pdf'
        logi(f"업로드파일 Path : {source_file_path}")

        # 원본파일(tif, pdf 등) 이 없을 경우 에러처리
        if not os.path.isfile(source_file_path):
            logt("업로드파일 없음") 
            #source_file_path = source_file_path + 'source.pdf'
            raise BizException("업로드파일 없음", source_file_path)

        # 첨부하기 버튼 클릭 => 팝업
        logt("첨부하기", 1)
        try :
            ele = driver.find_element(By.CSS_SELECTOR, "#ttirnam101DVOListDes_cell_0_" +str(td_index_info['upload_btn']+offset)+ " > span > button")
            button_text = ele.text
            if button_text == "첨부하기":
                ele.click()
            elif button_text == "제출내역보기":
                logt("이미 제출 완료... => 다음 작업")    
                return
            else :
                raise BizException("기타의 경우 => 프로그램 수정하기")
        except Exception as e:
            logt("첨부하기 버튼 클릭 오류.")
            raise BizException("첨부하기 버튼클릭 오류")
        

        # =================================================================
        logt("윈도우 로딩 대기", 2) 
        window_handles = driver.window_handles
        print(driver.window_handles)
        try :
            logt("window handle= %s" % ",".join(window_handles)) 
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)
        except :
            logt("윈도우 전환 실패 => 재시도", 2) 
            window_handles = driver.window_handles
            driver.switch_to.window(window_handles[1])
            driver.set_window_position(0,0)     

        window_handles = driver.window_handles
        if len(window_handles) != 2 :
            logt("윈도우 전환 실패 => 해당 작업 에러처리") 
            raise BizException("업로드 윈도우 오픈 실패")

        # 파일선택
        logt("파일선택", 0.2)
        driver.find_element(By.CSS_SELECTOR, "#UTECMGAA06_trigger1").click()


        logt("원본파일 path= %s" % source_file_path, 1) 
        time.sleep(0.6)
        pyautogui.typewrite(source_file_path)
        time.sleep(0.4)
        pyautogui.hotkey("alt", "o")

        # 50메가 이상 올라갔을 경우 임의로 alert이 뜰지 몰라 임시로 1초대기
        time.sleep(1)
        첨부파일50메가_이상 = False
        try:
            alert= driver.switch_to.alert
            alert_msg = alert.text
            if alert_msg.find("첨부 파일 전체 사이즈는 50MB이하로 첨부해주세요") > -1:
                alert.accept()
                첨부파일50메가_이상 = True
        except Exception as e:
            logi(f"정상적인 except 발생")

        if 첨부파일50메가_이상:         
            raise BizException('첨부파일크기오류', "첨부파일 크기 50MB이상")

        # 제출하기
        try:
            logt("제출하기 버튼 클릭", 2.5)   #  이 시간이 업로드에 걸리는 시간
            driver.find_element(By.CSS_SELECTOR, "#trigger2_").click()
        except Exception as e:
            loge(f'제출하기 버튼 클릭 -> 오류발생 : {e}')
            raise BizException('제출하기 버튼 클릭 -> 오류', '제출하기 버튼 클릭 -> 오류')

        try :
            time.sleep(5)
            alert= driver.switch_to.alert
            alert_msg = alert.text
            if alert_msg.find("부속서류 제출이 완료 되었습니다.") > -1 :
                logt("부속서류 제출이 완료 되었습니다.")
                alert.accept()
            elif alert_msg.find("첨부된 서류가 존재하지 않습니다") > -1 :
                logt("첨부된 서류가 존재하지 않습니다")
                alert.accept()
                raise BizException("부속서류 제출 오류", "첨부된 서류가 존재하지 않습니다")
        except :
            #파일 업로드 완료 때까지 반복
            logt("파일업로드 반복시도")
            nTry = 0
            while(True):
                try:
                    time.sleep(1)
                    nTry += 1

                    alert= driver.switch_to.alert
                    alert_msg = alert.text
                    if alert_msg.find("부속서류 제출이 완료 되었습니다.") > -1 :
                        logt("부속서류 제출이 완료 되었습니다.")
                        alert.accept()
                        break
                    elif alert_msg.find("첨부된 서류가 존재하지 않습니다") > -1 :
                        logt("첨부된 서류가 존재하지 않습니다")
                        alert.accept()
                        raise BizException("첨부된 서류가 존재하지 않습니다")

                except :
                    time.sleep(1)
                    logt("파일업로드 반복시도= %d 회" % nTry)
                    # 최대 5번까지만 반복
                    if nTry > 5 : 
                        raise BizException("파일업로드 반복시도 오류", "파일업로드 반복시도: 5회초과")
        
        logt("한건 처리 완료 ###", 0.1)

        try :
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(cur_window_handle)
        except:
            pass
            



        # 팝업 윈도우는 자동으로 닫히기 때문에 특별히 close 처리 안함

    else :  # 조회 결과 0
        step_cd = ht_info['step_cd']
        dbjob.update_HtTt_AuX(au_step, ht_tt_seq, 'E', '신고가 존재하지 않습니다')
        raise BizException("미제출", "신고서가 제출되지 않았습니다.")


def get_file_path_by_file_seq(ht_tt_file_seq) :
        # 파일키
        if ht_tt_file_seq is not None and ht_tt_file_seq>0 :
            # 파일정보
            file_info = dbjob.select_one_HtTtFile(ht_tt_file_seq)

            if file_info is not None :
                # DB에 있는 파일 정보
                filepath = root_dir + file_info['path'] + file_info['changed_file_nm'] 
                return filepath
            else:
                return None
        else :
            return None
