from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

import config

from common import *
import dbjob

import pyHometax.auto_login as auto_login 
import auto_step_2

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

# 홈택스 작업2단계D:\WWW\JNK\files\hometax\002\002803\down2.pdf

# 신고2단계 : 홈택스 다운로드 (납부서, 접수증,계산명세서)
au_step = "2"
group_id = "the1"

import config


for_one_user_name = ""
for_one_user_id   = "MANAGER_ID"



logt("###########################################")
logt("서버정보: DB USER=%s, DIR=%s, DEBUG=%s" % (config.DATABASE_CONFIG['user'], config.FILE_ROOT_DIR, config.IS_DEBUG))
logt("###########################################")


dbjob.set_global(group_id, None, None, None, None) 
if __name__ == '__main__':
    host_name = config.HOST_NAME
    conn = dbjob.connect_db()

    logt("홈택스 양도소득세 자동신고 서버 기동 !!!")
    logt("  ==> 신고2단계 : 홈택스 다운로드 (납부서, 접수증,계산명세서)")

    logt("# ------------------------------------------------------------------")
    logt("담당자 작업 정보 : GROUP_DI=%s, ID=%s, Name=%s" % (group_id, for_one_user_id, for_one_user_name))
    logt("# ------------------------------------------------------------------")

    # 한번에 처리한 자료수
    batch_bundle_count = config.BATCH_BUNDLE_COUNT
    logt("배치 처리 건수=%d" % batch_bundle_count)

    dbjob.set_global(group_id, None, for_one_user_id, None, au_step)   # (v_host_name, v_user_id, v_ht_tt_seq, v_au_step):

    # 작업리스트
    jobs = dbjob.select_auto_2_관리자(group_id, for_one_user_id, config.BATCH_BUNDLE_COUNT)

    logt("-------------------------------------------------------------")
    logt("%s님의 이번 처리 건수=%d" % (for_one_user_name, len(jobs)))
    if len(jobs) == 0:
        logt("처리할 자료가 없습니다.")
        exit()
    logt("-------------------------------------------------------------")


    # ------------------------------------------------------------------
    # 로그인
    # ------------------------------------------------------------------
    # 작업자별 로그인 정보
    login_info = config.LOGIN_INFO

    if for_one_user_id == "MANAGER_ID" :
        login_info['name'] = "관리자"
        login_info['login_id'] = "MANAGER_ID"
        login_info['login_pw'] = "xxxx"  # 사용안함
    else :
        user_row = dbjob.get_worker_info(for_one_user_id)
        login_info['name'] = user_row['name']
        login_info['login_id'] = user_row['hometax_id']
        login_info['login_pw'] = user_row['hometax_pw']

    # 셀레니움 드라이버
    driver: WebDriver = auto_login.init_selenium()
    driver.set_window_size(config.BROWSER_SIZE['width'], config.BROWSER_SIZE['height']+150)

    # 자동로그인 처리
    auto_login.login_hometax(driver, login_info, config.IS_DEBUG)
    # ------------------------------------------------------------------
    
    
    # 2단계 홈택스 파일다운로드 리스트

    if len(jobs) == 0:
        logt("작업할 리스트가 없습니다. 작업종료")    

    else:
        try:

            auto_step_2.do_step2(driver, group_id, jobs, for_one_user_id)
        
        except Exception as e:
            logt("======= 오류발생")
            print(e)

            traceback.print_exc()

        
        else:  # 오류없이 정상 처리시
            logt("======= 정상종료")
            driver.close()

    exit(0)

