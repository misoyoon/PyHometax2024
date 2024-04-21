from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

from common import *
import dbjob_toss

import pyHometax.auto_login as auto_login 
import ht_file
import pyHometax.common_sele as sc
import config


from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
#from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoAlertPresentException



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
            dbjob_toss.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', e.msg)

        except Exception as e:
            print(e)
            dbjob_toss.update_HtTt_AuX(au_stpe, ht_tt_seq, 'E', None)
            traceback.print_exc()
        
        else:  # 오류없이 정상 처리시
            logt("#################### (정상처리)")
            dbjob_toss.update_HtTt_AuX(au_stpe, ht_tt_seq, 'S', None)
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

            logt("작업프레임 이동: UTERNAAZ70_iframe", 1)
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
                logt("   이미 납부 처리됨", 1)
                #time.sleep(200)
                # 여기는 offset 안적용 되는 듯.. ㅠㅠ
                dbjob_toss.update_HtTt_hometaxPaidYn(ht_tt_seq, 'Y')

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

            dbjob_toss.update_HtTt_hometaxPaidYn(ht_tt_seq, 'Y')


    else :
        print('신고가 존재하지 않습니다. 재신청 하시기 바랍니다.')




#import config

# venv activate
# Set-ExecutionPolicy Unrestricted 


# login_info = {
#     'name' : '김경연' 
#     # 담당자로그인 정보
#     ,'login_id': 'the1kks1'
#     ,'login_pw' : 'kksjns1203!'

#     # 인증서 비밀번호
#     ,'cert_login_pw' : 'kksjns1203!'

#     # 세무대리인 (Pxxxxx)
#     ,'rep_id' : "P24335"
#     ,'rep_pw' : 'kksjns1203!'
# }

# 위택스 : https://www.wetax.go.kr/simple/?cmd=LPEPBZ4R0

# 위택스 신고하기
au_step = "5"
group_id = ""

for_one_user_name = ""
for_one_user_id   = ""
if len(sys.argv) == 1:
    logi("실행할 담당자 정보가 없습니다.")
    exit()
else :
    try:
        if len(for_one_user_name) == 0 :
            for_one_user_name = sys.argv[1]

        for_one_user_id = config.USER_LIST[for_one_user_name]
    except :
        loge("실행할 담당자 정보를 찾을 수 없습니다.  config.py")
        exit()

    try:
        if len(group_id) == 0 :
            group_id = sys.argv[2]
    except :
        loge("그룹 정보를 입력하지 않으셨습니다.")
        exit()

logi("###########################################")
logi("서버정보: DB USER=%s, DIR=%s, DEBUG=%s" % (config.DATABASE_CONFIG['user'], config.FILE_ROOT_DIR, config.IS_DEBUG))
logi("###########################################")


dbjob_toss.set_global(group_id, None, None, None, None) 
if __name__ == '__main__':
    host_name = config.HOST_NAME
    conn = dbjob_toss.connect_db()

    logt("홈택스 양도소득세 자동신고 서버 기동 !!!")
    logt("  ==> 신고3단계 : 위택스 신고")

    logi("# ------------------------------------------------------------------")
    logi("담당자 작업 정보 : GROUP_DI=%s, ID=%s, Name=%s" % (group_id, for_one_user_id, for_one_user_name))
    logi("# ------------------------------------------------------------------")

    # 세무대리인(담당자) 리스트
    user_list = dbjob_toss.get_worker_list(group_id, for_one_user_id)
    print(user_list)
    
    # 담당자별로 한번에 처리한 자료수
    batch_bundle_count = config.BATCH_BUNDLE_COUNT
    logi("배치 처리 건수=%d" % batch_bundle_count)


    dbjob_toss.set_global(group_id, None, None, None, au_step)   # (v_host_name, v_user_id, v_ht_tt_seq, v_au_step):

    # 3단계 위택스 신고 작업리스트
    import_seq = 13
    jobs = dbjob_toss.select_auto_toss_importSeq(group_id, for_one_user_id, import_seq)
    
    logi("-------------------------------------------------------------")
    logi("%s님의 이번 처리 건수=%d" % (for_one_user_name, len(jobs)))
    if len(jobs) == 0:
        logi("처리할 자료가 없습니다.")
        exit()
    logi("-------------------------------------------------------------")


    # ------------------------------------------------------------------
    # 로그인
    # ------------------------------------------------------------------
    # 작업자별 로그인 정보
    login_info = config.LOGIN_INFO

    # 작업자별 로그인 정보
    if for_one_user_id == "MANAGER_ID" :
        login_info['name'] = "관리자"
        login_info['login_id'] = "MANAGER_ID"
        login_info['login_pw'] = "xxxx"  # 사용안함
    else :
        user_row = dbjob_toss.get_worker_info(for_one_user_id)
        login_info['name'] = user_row['name']
        login_info['login_id'] = user_row['hometax_id']
        login_info['login_pw'] = user_row['hometax_pw']


    # 셀레니움 드라이버
    driver: WebDriver = auto_login.init_selenium()
    

    # 자동로그인 처리
    auto_login.login_hometax(driver, login_info, config.IS_DEBUG)
    # ------------------------------------------------------------------
    
    try:

        do_step3(driver, group_id, jobs, for_one_user_id)
    
    except Exception as e:
        logt("======= 오류발생")
        print(e)
        traceback.print_exc()

    
    else:  # 오류없이 정상 처리시
        logt("======= 정상종료")

    driver.close()
    
    exit(0)


company_info = {
    "name"      : "세무법인 더원"
    , "regi_num_1" : "110171"
    , "regi_num_2" : "0068286"
    , "biz_num"    : "1208777823"   # 사업자번호
    , "tel"        : "025140910"
}