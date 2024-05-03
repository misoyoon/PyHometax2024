from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
import time

from common import *

import pyHometax.auto_login as auto_login 
import auto_step_1
import dbjob

import config
import pyHometax.common_sele as sc


# venv activate
# Set-ExecutionPolicy Unrestricted 


# login_info = {
#     'name' : '김경연' 
#     # 담당자로그인 정보
#     ,'login_id': 'the1kks1'in
#     ,'login_pw' : 'kksjns1203!'

#     # 인증서 비밀번호
#     ,'cert_login_pw' : 'kksjns1203!'

#     # 세무대리인 (Pxxxxx)
#     ,'rep_id' : "P24335"
#     ,'rep_pw' : 'kksjns1203!'
# }


# 홈택스 작업1단계 
au_step = "1"
group_id = ""

for_one_user_name = ""
for_one_user_id   = ""
if len(sys.argv) == 1:
    logt("실행할 담당자 정보가 없습니다.")
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


logt("###########################################")
logt("서버정보: DB USER=%s, DIR=%s, DEBUG=%s" % (config.DATABASE_CONFIG['user'], config.FILE_ROOT_DIR, config.IS_DEBUG))
logt("###########################################")


dbjob.set_global(group_id, None, None, None, au_step) 
if __name__ == '__main__':
    host_name = config.HOST_NAME
    conn = dbjob.connect_db()

    logt(f"홈택스 양도소득세 자동신고 서버 기동 !!! - {au_step}단계")

    logt("# ------------------------------------------------------------------")
    logt("담당자 작업 정보 : GROUP_ID=%s, ID=%s, Name=%s" % (group_id, for_one_user_id, for_one_user_name))
    logt("# ------------------------------------------------------------------")

    # 세무대리인(담당자) 리스트
    user_list = dbjob.get_worker_list(group_id, for_one_user_id)
    print(user_list)

    # 담당자별로 한번에 처리한 자료수
    batch_bundle_count = config.BATCH_BUNDLE_COUNT
    logt("배치 처리 건수=%d" % batch_bundle_count)

    # 무한 루프
    while True:  

        # 담당자별로 순환
        for user_idx in range(0, len(user_list)):
            dbjob.set_global(group_id, None, None, None, au_step)   # (v_host_name, v_user_id, v_ht_tt_seq, v_au_step):
            # 다음 처리 담당자 정보
            user_info = user_list[user_idx]

            user_id   = user_info['id']
            user_name = user_info['name']
            user_tel  = user_info['sms_num']
            
            logt('다음 처리 담당자 정보 : Index=%d, ID=%s, Name=%s' % (user_idx, user_id, user_name))

            # 홈택스 신고서제출 자료            
            jobs = dbjob.select_auto_1(group_id, user_id,  batch_bundle_count)

            logt("-------------------------------------------------------------")
            logt("%s님의 이번 처리 건수=%d" % (user_name, len(jobs)))
            if len(jobs) == 0:
                logt("처리할 자료가 없습니다.")
                exit()
            logt("-------------------------------------------------------------")

            # 셀레니움 드라이버
            driver: WebDriver = auto_login.init_selenium()

            # ------------------------------------------------------------------
            # 로그인
            # ------------------------------------------------------------------
            login_info = config.LOGIN_INFO

            # 작업자별 로그인 정보
            login_info['name'] = user_name
            login_info['login_id'] = user_info['hometax_id']
            login_info['login_pw'] = user_info['hometax_pw']

            # 자동로그인 처리
            auto_login.login_hometax(driver, login_info, config.IS_DEBUG )
            # ------------------------------------------------------------------
            logt("###########################################")
            logt("담당자 전환: %s %s" % (user_id, user_name))
            logt("###########################################")
            
            for job_idx in range(0, len(jobs)):
                ht_info = jobs[job_idx]

                #담당자 전화번호 추가
                ht_info['worker_tel'] = user_tel

                ht_tt_seq = ht_info['ht_tt_seq']
                dbjob.set_global(group_id, host_name, user_id, ht_tt_seq, "1")  # "1" => 자동신고 1단계

                dbjob.delete_auHistory_byKey(ht_tt_seq, au_step)
                dbjob.insert_auHistory("시작")

                # 담당자 홈택스로그인 가능 여부 확인용
                dbjob.update_user_cookieModiDt(user_id)

                logt("******************************************************************************************************************")
                logt("%s/%s : 양도인=%s, HT_TT_SEQ=%d" % (job_idx+1, len(jobs), ht_info['holder_nm'], ht_info['ht_tt_seq']))
                logt("******************************************************************************************************************")

                #print(dbjob.select_HtTtFile_ByPk(ht_info['source_file_seq']))

                # logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
                # url = 'https://www.hometax.go.kr/websquare세무대리인 여부 확인websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
                # driver.get(url)
                # logt("iframe 이동", 3)
                # sc.move_iframe(driver)

                # 확정신고 클릭
                try: 
                    logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
                    url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
                    driver.get(url)
                    logt("iframe 이동", 3)
                    sc.move_iframe(driver)
                    auto_step_1.go_확정신고(driver)

                except Exception as e:
                    logt(f"예외발생 : go_확정신고() => 처음부터 재시도 - {e}")
                    logt("처음부터 다시 시작", 0.5)

                    try:
                        logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
                        url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
                        driver.get(url)
                        logt("iframe 이동", 3)
                        sc.move_iframe(driver)
                        auto_step_1.go_확정신고(driver)                    
                    except:
                        loge("신고/납부 메뉴 이동 오류로 다음 신청자로 continue함")
                        continue

                # FIXME 테스트 용도
                #logt("[클릭] 기한후신고", 0.5)
                #driver.find_element(By.ID, 'textbox86564').click()
                


                # Step 1. 세금신고 : 기본정보(양도인)
                try:
                    auto_step_1.do_step1(driver, ht_info)

                
                except BizException as e:
                    if e.name == "기존신청서삭제":
                        logt("페이지이동: '신고/납부' 메뉴 이동", 0.5)
                        url = 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=4&tm2lIdx=0405050000&tm3lIdx='
                        driver.get(url)
                        logt("iframe 이동", 3)
                        sc.move_iframe(driver)
                        auto_step_1.go_확정신고(driver)     

                        auto_step_1.do_step1(driver, ht_info)
                    # elif e.name == "관할지오류":
                    #     dbjob.update_HtTt_AuX(1, ht_tt_seq, 'E', e.msg)
                    # elif e.name == "이미제출된신고서":
                    #     dbjob.update_HtTt_AuX(1, ht_tt_seq, 'S', e.msg)
                    else:
                        dbjob.update_HtTt_AuX(1, ht_tt_seq, 'E', '')

                except Exception as e:
                    print(e)
                    dbjob.update_HtTt_AuX(1, ht_tt_seq, 'E', '')
                
                else:  # 오류없이 정상 처리시
                    dbjob.update_HtTt_AuX(1, ht_tt_seq, 'S', '')



                # job 완료 처리 
                logt("#######한건처리 완료 #######")
                
                
            # 담당자별로 다시 로그인하기 위해 로그아웃
            driver.close()
            
            # dbjob.update_HtTt_statusCd(ht_tt_seq, 'DONE')
            # end for [신고서순환]
        # end for [담당자순환]


        logt(">>>>>>>>>> 반복순환 마무리 => 처음부터 다시 시작 <<<<<<<<<<<<< ") 
        #time.sleep(300)            
        break;
        # Insert 테스트
        #dbjob.insert_pyRunHistory(1, 'imgood', 'start')

        # 사용자의 다음 작업n개 가져오기


        # 30 => D:\WWW\JNK_DEV\files\hometax\000\000030\
        #ht_file.get_dir_by_htTtSeq(30)

logt("프로그램 종료")        
exit(0)

