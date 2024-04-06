from selenium import webdriver
from selenium.webdriver.common.by import By
import sys
from common import *
import dbjob
import auto_login 
import sele_common as sc
#import auto_login_위택스 as auto_login_wetax

if len(sys.argv) < 4:
    loge("실행 Parameter가 정상적이지 않습니다.")
    exit()

server_id = sys.argv[1]
agent_id = sys.argv[2]
group_id = sys.argv[3]
auto_manager_id = server_id + '_' + agent_id + '_' + group_id 


# DB 접속
conn = dbjob.connect_db()

def init_step_job():
    at_info = dbjob.select_autoManager_by_id(auto_manager_id)
    au_x            = at_info['au_x']
    status_cd       = at_info['status_cd']
    worker_id       = at_info['worker_id']
    worker_nm       = at_info['worker_nm']
    group_id        = at_info['group_id']
    seq_where_start = at_info['seq_where_start']
    seq_where_end   = at_info['seq_where_end']
    verify_stamp    = at_info['verify_stamp']
    
    logi("###########################################")
    logi("서버정보: auto_manager_id=%s,  WORKER=%s(%s), AUX=%s" % (auto_manager_id, worker_nm, worker_id, au_x))
    logi("###########################################")

    if not (status_cd == 'RW' or status_cd == 'R'):
        logi(f"현재 상태 : status cd = {status_cd}  ==> 작업 중료")
        exit()

    # 작업자 정보 조회
    user_info = dbjob.get_worker_info(worker_id)
    # 홈피 로그인 정보
    login_info = get_login_info(user_info)

    ht_info = None
    if au_x == '1':
        ht_info = dbjob.select_next_au1(group_id, worker_id, seq_where_start, seq_where_end)
    elif au_x == '2':
        ht_info = dbjob.select_next_au2(group_id, worker_id, seq_where_start, seq_where_end)
    elif au_x == '3':
        ht_info = dbjob.select_next_au3(group_id, worker_id, seq_where_start, seq_where_end)
    elif au_x == '4':
        ht_info = dbjob.select_next_au4(group_id, worker_id, seq_where_start, seq_where_end)
    elif au_x == '5':
        ht_info = dbjob.select_next_au5(group_id, worker_id, seq_where_start, seq_where_end)
        
    if not ht_info:
        logi(f"처리할 자료가 없어서 FINISH 합니다. AUX={au_x}")
        dbjob.update_autoManager_statusCd(auto_manager_id, 'F', '처리할 자료가 없어서 FINISH 합니다.')
        return (None, None, None)
        

    # 셀레니움 초기화
    driver = auto_login.init_selenium()

    if au_x == '1' or au_x == '2' or au_x == '5':
        # ----------------------------------------------------------------------------
        # 자동로그인 처리 (홈택스)
        # ----------------------------------------------------------------------------
        if user_info['cookie_diff_minute'] <= 27:
            # 쿠키로그인
            logi(f"홈택스 로그인 : 쿠키방식 TXPPsessionID={user_info['txpp_session_id']}, TEHTsessionID={user_info['teht_session_id']}")
            auto_login.login_hometax_use_cookie(driver, user_info['txpp_session_id'], user_info['teht_session_id'])
            dbjob.update_user_cookieModiDt(worker_id)
        else:
            # 인증서 로그인
            auto_login.login_hometax(driver, login_info, False)
            
            # 로그인 정보 갱신
            cookie_TXPPsessionID = get_cookie_value(driver, 'TXPPsessionID')
            cookie_TEHTsessionID = get_cookie_value(driver, 'TEHTsessionID')
            dbjob.update_user_hometax_cookie(worker_id, cookie_TXPPsessionID, cookie_TEHTsessionID)
        
        logt("홈택스 로그인 완료 : %s (%s)" % (worker_id, worker_nm), 1)
    elif au_x == '3' or au_x == '4':
        # ----------------------------------------------------------------------------
        # 자동로그인 처리 (위택스)
        # ----------------------------------------------------------------------------        
        auto_login.login_wetax(driver)
        logt("위택스 로그인 완료 : %s (%s)" % (worker_id, worker_nm), 1)        


    logt(f"해외주식 양도소득세 자동신고 기동 : {au_x}단계")

    logi("# ------------------------------------------------------------------")
    logi("# 담당자 작업 정보 : GROUP_ID=%s, ID=%s, Name=%s" % (group_id, worker_id, worker_nm))
    logi("# ------------------------------------------------------------------")
        
    sc.close_other_windows(driver)
    return (driver, user_info, verify_stamp)
    