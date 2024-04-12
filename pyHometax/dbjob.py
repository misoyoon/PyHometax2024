# 참고 페이지 
# https://www.fun-coding.org/mysql_basic6.html

import sys, os
import pymysql
from contextlib import closing

import config
import common
import ht_file

# def set_global(v_group_id, v_host_name, v_user_id, v_ht_tt_seq, v_au_step):
#     global group_id
#     group_id = v_group_id
#     global host_name
#     host_name = v_host_name
#     global user_id
#     user_id = v_user_id
#     global ht_tt_seq
#     ht_tt_seq = v_ht_tt_seq
#     global au_step
#     au_step = v_au_step

def connect_db():
    #if env != None:
    #    raise ValueError("환경정보를 설정해주세요")
    global conn    
    conn = pymysql.connect(
                            db  =config.DATABASE_CONFIG['db'],
                            user=config.DATABASE_CONFIG['user'],
                            host=config.DATABASE_CONFIG['host'],
                            port=config.DATABASE_CONFIG['port'],
                            password=config.DATABASE_CONFIG['password'],
                            cursorclass=pymysql.cursors.DictCursor,
                            charset='utf8'
                        )
    print(f"DB HOST = {config.DATABASE_CONFIG['host']}")
    return conn




# ====================================================================================================================
# GBY_AGENT 관련 (시작)
# ====================================================================================================================


def select_autoManager_by_id(auto_manager_id) :
    param = (auto_manager_id, )
    # SQL문 실행
    sql = '''
    SELECT a.*
            , u.nm worker_nm
            , u.txpp_session_id
            , u.teht_session_id
            , IFNULL(TIMESTAMPDIFF(SECOND, current_timestamp(), u.cookie_modi_dt), 9999999) diff_modi_dt
    FROM   auto_manager a
        LEFT JOIN user u ON u.id = a.worker_id
    WHERE  auto_manager_id=%s
    '''
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
    
        # 데이타 Fetch
        row = curs.fetchone()
        conn.commit()
        return row


# 현재는 사용 안함
def insert_auto_manager(server_id, agent_id, task_id, worker_id, au_x, pid, remark="") :
    param = (server_id, agent_id, task_id, worker_id, au_x, pid, remark)
    sql = """
        INSERT INTO auto_manager (server_id, agent_id, task_id, worker_id, au_x, pid, remark)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()

def update_autoManager_statusCd(auto_manager_id, status_cd, remark='') :
    param = (status_cd, auto_manager_id)
    sql = '''
        UPDATE auto_manager 
        SET   status_cd = %s
            , modi_dt = CURRENT_TIMESTAMP()
    '''
    if remark:
        sql += ', remark = %s'
        param = (status_cd, remark, auto_manager_id)
        
    sql += '   WHERE  auto_manager_id=%s'
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()
    
def update_autoManager_hthtSeq(auto_manager_id, ht_tt_seq) :
    #global conn    
    param = (ht_tt_seq, auto_manager_id)
    
    sql = '''
        UPDATE auto_manager 
        SET running_ht_tt_seq = %s,
            modi_dt = CURRENT_TIMESTAMP()
        WHERE  auto_manager_id=%s
    '''
    
    try:
        with conn.cursor() as curs:
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")
        
# aux 단계별로 현재 진행중인 상태 표시 'R(unning)'
def update_htTt_aux_running(ht_tt_seq, au_x) :
    #global conn    
    param = ('R', ht_tt_seq)
    
    sql =  'UPDATE HT_TT '
    
    if au_x == '1':
        sql += ' SET au1 = %s'
    elif au_x == '2':
        sql += ' SET au2 = %s'
    elif au_x == '3':
        sql += ' SET au3 = %s'
    elif au_x == '4':
        sql += ' SET au5 = %s'
    elif au_x == '5':
        sql += ' SET au5 = %s'
    elif au_x == '6':
        sql += ' SET au6 = %s'
    
    sql += ' WHERE  ht_tt_seq=%s'

    try:            
        with conn.cursor() as curs:
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")
        
# ====================================================================================================================
# GBY_AGENT 관련 (끝)
# ====================================================================================================================


# =============================================================================== select_auto_1


###################################################################
# 1단계 -  홈택스 신고
###################################################################

def select_next_au1(group_id, worker_id, start_seq=0, end_seq=0):
    rs = None

    where1 = ''
    where2 = ''
    if start_seq!=None and start_seq>0: where1 = f' AND ht_tt_seq >= {start_seq}'
    if end_seq!=None   and end_seq>0:   where2 = f' AND ht_tt_seq <= {end_seq}'

    sql = '''
        SELECT *  
        FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND data_type='AUTO'
            AND step_cd='REPORT'
            AND ( au1 is Null or au1 = '' )
    '''
    
    if worker_id and worker_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, worker_id)
            
    sql += where1
    sql += where2
    sql += '''
        ORDER BY ht_tt_seq asc 
        LIMIT 1
        '''
    param = (group_id, worker_id)
    common.logqry(sql, param)
    
    try:
        with conn.cursor as curs:
            curs.execute(sql, param)
            rs = curs.fetchone()
            common.logrs(rs)
            conn.commit()
    except Exception as e:
        print(f"오류 발생: {e}")
            
    return rs


# 2단계 - (정상적인 상황) 홈택스 관련 문서 다운로드
def select_next_au2(group_id:str, worker_id:str, start_seq=0, end_seq=0):
    param = (group_id, )
    rs = None

    where1 = ''
    where2 = ''
    if start_seq!=None and start_seq>0: where1 = f' AND ht_tt_seq >= {start_seq}'
    if end_seq!=None   and end_seq>0:   where2 = f' AND ht_tt_seq <= {end_seq}'
    
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND (data_type='AUTO' OR data_type='SEMI')
            AND step_cd='REPORT' 
            -- AND step_cd='COMPLETE' 
            AND au1='S' 
            AND ( au2 IS NULL  OR au2 = 'S'
                -- OR au2 = 'E'
                )
            -- and ht_tt_seq in (29599)
    '''
    
    if worker_id and worker_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, worker_id)

    sql += where1
    sql += where2
    sql += '''
        ORDER BY ht_tt_seq asc 
        LIMIT 1
        '''
    common.logqry(sql, param)
    with conn.cursor as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    return rs

# 3단계 - 위택스 신고
def select_next_au3(group_id:str, worker_id:str, start_seq=0, end_seq=0):
    param = (group_id, )
    rs = None

    where1 = ''
    where2 = ''
    if start_seq!=None and start_seq>0: where1 = f' AND ht_tt_seq >= {start_seq}'
    if end_seq!=None   and end_seq>0:   where2 = f' AND ht_tt_seq <= {end_seq}'
        
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE group_id=%s
            AND ht_series_yyyymm = '202405'
            AND (data_type='AUTO' OR data_type='SEMI')
            AND step_cd='REPORT' 
            AND au1='S' 
            AND ( au3 IS NULL OR au3 = '' )
    '''
    
    if worker_id and worker_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, worker_id)

    sql += where1
    sql += where2
    sql += '''
        ORDER BY ht_tt_seq asc 
        LIMIT 1
        '''
    
    common.logqry(sql, param)
    with conn.cursor() as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    
    return rs

# 4단계 - 위택스 문서 다운로드
def select_next_au4(group_id:str, worker_id:str, start_seq=0, end_seq=0):
    param = (group_id, )
    rs = None

    where1 = ''
    where2 = ''
    if start_seq!=None and start_seq>0: where1 = f' AND ht_tt_seq >= {start_seq}'
    if end_seq!=None   and end_seq>0:   where2 = f' AND ht_tt_seq <= {end_seq}'
        
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE group_id=%s
            AND ht_series_yyyymm = '202405'
            AND (data_type='AUTO' OR data_type='SEMI')
            AND step_cd='REPORT' 
            AND au3='S' 
            AND ( au4 IS NULL OR au4 = '' )
    '''
    
    if worker_id and worker_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, worker_id)

    sql += where1
    sql += where2
    sql += '''
        ORDER BY ht_tt_seq asc 
        LIMIT 1
        '''
    
    common.logqry(sql, param)
    with conn.cursor() as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    
    return rs


# 5단계 - 홈택스 증빙자료 업로드
def select_next_au5(group_id:str, worker_id:str, start_seq=0, end_seq=0):
    param = (group_id, )
    rs = None

    where1 = ''
    where2 = ''
    if start_seq!=None and start_seq>0: where1 = f' AND ht_tt_seq >= {start_seq}'
    if end_seq!=None   and end_seq>0:   where2 = f' AND ht_tt_seq <= {end_seq}'
        
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE group_id=%s
            AND ht_series_yyyymm = '202405'
            AND (data_type='AUTO' OR data_type='SEMI')
            AND step_cd='COMPLETE' 
            -- AND au1='S' 
            AND ( au5 IS NULL OR au5 = '' )
    '''
    
    if worker_id and worker_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, worker_id)

    sql += where1
    sql += where2
    sql += '''
        ORDER BY ht_tt_seq asc 
        LIMIT 1
        '''
    
    common.logqry(sql, param)
    with conn.cursor() as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    
    return rs


# 6단계 - 카카오톡 & 메일 발송 
# 조건1: 토스증권은 제외
# 조건2: notify_type_cd = MAIL, MAIL2 만
def select_next_au6(group_id:str, worker_id:str, start_seq=0, end_seq=0):
    param = (group_id, )
    rs = None

    where1 = ''
    where2 = ''
    if start_seq!=None and start_seq>0: where1 = f' AND ht_tt_seq >= {start_seq}'
    if end_seq!=None   and end_seq>0:   where2 = f' AND ht_tt_seq <= {end_seq}'
        
    sql = '''
        SELECT ht.* 
        FROM ht_tt ht
        WHERE ht.group_id=%s
            AND sec_company_cd != 'SEC07'  -- 토스증권
            AND ht_series_yyyymm = '202405'
            AND (data_type='AUTO' OR data_type='SEMI')
            AND (notify_type_cd='EMAIL'  OR notify_type_cd='EMAIL2' OR notify_type_cd='EMAIL_SEC')
            -- AND step_cd='COMPLETE' 
            -- AND ( au1='S' AND au2='S' AND au3='S' AND au4='S' )
            -- AND ( au6 IS NULL OR au6 = '' )
            AND ht_tt_seq = 20000
    '''
    
    if worker_id and worker_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, worker_id)

    sql += where1
    sql += where2
    sql += '''
        ORDER BY ht_tt_seq asc 
        LIMIT 1
        '''
    
    common.logqry(sql, param)
    with conn.cursor() as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    
    return rs


# Group 정보 (Kakao알림톡 정보 포함)
def select_group_info(group_id:str):
    param = (group_id, )
    rs = None

    sql = '''
        SELECT *  FROM group_info 
        WHERE group_id=%s
    '''
    
    common.logqry(sql, param)
    with conn.cursor() as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    
    return rs

# Kakao알림톡 템플릿 정보
def select_kakao_template(group_id:str, type:str):
    param = (group_id, type)
    rs = None

    sql = '''
        SELECT * FROM kakao_template 
        WHERE group_id=%s
            AND type=%s
            AND yyyymm='202405'
    '''
    
    common.logqry(sql, param)
    with conn.cursor() as curs:
        curs.execute(sql, param)
        rs = curs.fetchone()
        common.logrs(rs)
        conn.commit()
    
    return rs


# 업무담당자 리스트 출력
def get_worker_list(group_id, for_one_user) :
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, for_one_user)
    # SQL문 실행
    sql = '''
    SELECT id, nm name, hometax_id, hometax_pw, sms_num  
    FROM user 
    WHERE hometax_id IS NOT NULL 
        AND hometax_pw IS NOT NULL 
        AND group_id=%s
        AND id=%s
    '''
    
    with conn.cursor as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        rs = curs.fetchall()
        conn.commit()
        return rs

def get_worker_info(user_id) :
    param = (user_id,)
    # SQL문 실행
    sql = '''
        SELECT  id
            , replace(nm, '2', '') name
            , tel
            , email
            , hometax_id, hometax_pw, ht_worker_yn
            , txpp_session_id, teht_session_id
            , IFNULL(TIMESTAMPDIFF(minute , cookie_modi_dt, current_timestamp()), 9999) cookie_diff_minute
        FROM user 
        WHERE hometax_id IS NOT NULL AND hometax_pw IS NOT NULL 
            AND isEnabled = 1
            AND id=%s
    '''
    common.logqry(sql, param)
    with conn.cursor() as curs:   
        curs.execute(sql, param)
        row = curs.fetchone()
        conn.commit()
        return row

# 로그인 쿠키 저장
def update_user_hometax_cookie(user_id, txpp_session_id, teht_session_id) :
    param = (txpp_session_id, teht_session_id, user_id)
    curs = conn.cursor()
    sql = '''
        UPDATE user 
        SET   txpp_session_id = %s 
            , teht_session_id = %s 
            , cookie_modi_dt = NOW()
        WHERE id = %s
        '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()
    

# 사용자별 최신 자동신고 일시변경
def update_user_cookieModiDt(user_id) :
    param = (user_id, )
    sql = "UPDATE user SET cookie_modi_dt = CURRENT_TIMESTAMP WHERE id = %s"
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()


# 홈택스에 신고된 납부세액
def update_htTt_hometaxIncomeTax(ht_tt_seq, hometax_income_tax) :
    param = (hometax_income_tax, ht_tt_seq)
    # 이전 실기록 삭제
    sql = "UPDATE ht_tt SET hometax_income_tax = %s WHERE ht_tt_seq = %s"
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()


def delete_auHistory_byKey(ht_tt_seq, au_step) :
    param = (ht_tt_seq, au_step)
    # 이전 실기록 삭제
    sql = "DELETE FROM au_history WHERE ht_tt_seq = %s AND au_step=%s"
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()

# 자동신고 진행중 특이사항 저장
def insert_auHistory(ht_tt_seq, worker_id, au_step, title, message="", host_name="") :
    if ht_tt_seq == None:
        return

    param = (ht_tt_seq, worker_id, au_step, title, message, host_name)
    sql = """
        INSERT INTO au_history (ht_tt_seq, user_id, au_step, title, message, host_name)
        VALUES(%s, %s, %s, %s, %s, %s)
        """
        
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()

# result = S | F 둘중하나
def update_HtTt_AuX(au_x, ht_tt_seq, au_status, au_message="") :
    param = (au_status, au_message, ht_tt_seq)
    sql = ""
    if au_x == '1':
        sql = 'UPDATE ht_tt SET au1=%s, au1_msg=%s WHERE ht_tt_seq=%s'
    elif au_x == '2':
        sql = 'UPDATE ht_tt SET au2=%s, au2_msg=%s WHERE ht_tt_seq=%s'
    elif au_x == '3':
        sql = 'UPDATE ht_tt SET au3=%s, au3_msg=%s WHERE ht_tt_seq=%s'
    elif au_x == '4':
        sql = 'UPDATE ht_tt SET au4=%s, au4_msg=%s WHERE ht_tt_seq=%s'
    elif au_x == '5':
        sql = 'UPDATE ht_tt SET au5=%s, au5_msg=%s WHERE ht_tt_seq=%s'
    elif au_x == '6':
        sql = 'UPDATE ht_tt SET au6=%s, au6_msg=%s WHERE ht_tt_seq=%s'

    with conn.cursor() as curs:        
        common.logqry(sql, param)
        curs.execute(sql, param)
        conn.commit()


###################################################################
# 홈택스 전체 신고 리스트
###################################################################
def select_홈택스_신고리스트(group_id, user_id, batch_count=100000):
    param = (group_id, user_id, batch_count)

    sql = '''
        SELECT *  
        FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND data_type!='CANCEL'
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


# =============================================================================== select_auto_1
###################################################################
# 1단계 -  홈택스 신고
###################################################################
# batch_count : 한번에 몇 개씩 가져올지 결정
def select_auto_1(group_id, user_id, batch_count=100):
    param = (group_id, user_id, batch_count)
    sql = '''
        SELECT *  
        FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND data_type='AUTO'
            AND step_cd='REPORT'
            AND (
                au1 is Null or au1 = '' 
                -- or au1='E'
            )
            AND reg_id = %s
            -- and ht_tt_seq = 30032
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


# 2단계 - (정상적인 상황) 홈택스 관련 문서 다운로드
def select_auto_2(group_id, user_id:str, batch_count=100):
    param = (group_id, batch_count)

    sql = '''
        SELECT *  FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND (data_type='AUTO' OR data_type='SEMI')
            AND step_cd='REPORT' 
            -- AND sec_company_cd = 'SEC07' and  (import_seq = '12' or  import_seq = '13' or  import_seq = '14')
            AND au1='S' 
            AND (
                au2 IS NULL 
                OR au2 = 'S'
                OR au2 = 'E'
                )
        '''
        
    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


# =============================================================================== select_auto_3
# 3단계 - 위택스 신고
def select_auto_3(group_id, user_id, batch_count=100):
    param = (group_id, batch_count, )
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE group_id=%s
            AND ht_series_yyyymm = '202405'
            AND step_cd='REPORT' 
            -- AND data_type='AUTO' 
            -- AND hometax_income_tax > 0
            AND au1='S' 
            AND (
                au3 IS NULL 
                OR au3 = ''
                OR au3 = 'E'
                )
            -- AND ht_tt_seq = 8016
    '''
    
    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs

# 3단계 - 위택스 신고 취소하기
def select_auto_3_위택스_취소목록(group_id, batch_count=500):
    param = (group_id, batch_count, )
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE group_id=%s
            AND ht_series_yyyymm = '202405'
            AND sec_company_cd = 'SEC07'
            AND import_seq = 13
            AND au6 is null
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


# =============================================================================== select_auto_4
# 4단계 - 위택스 다운로드
def select_auto_4(group_id, user_id, batch_count=100):
    param = (group_id, batch_count, )
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND step_cd='REPORT' 
            -- AND sec_company_cd = 'SEC07' and  (import_seq = '12' or  import_seq = '13' or  import_seq = '14')
            AND au1='S' AND au2='S' AND au3='S' 
            AND (au4 is null or au4 = 'E')
    '''

    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
            -- AND ht_tt_seq = 2
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:    
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


# =============================================================================== select_auto_5
# 5단계 - 홈택스 증빙자료 업로드
def select_auto_5(group_id, user_id, batch_count=100):
    param = (group_id, batch_count, )
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE   group_id=%s
            AND ht_series_yyyymm = '202405'
            AND data_type IN ('AUTO', 'SEMI')
            AND step_cd  IN ('REPORT_DONE', 'COMPLETE')
            AND au5 is null
            -- AND au5 = 'E'
    '''

    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
            -- AND ht_tt_seq = 2
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:    
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs

# 5단계(점검용) - 증빙자료제출이 잘 되어있는지 확인 (자동/반자동/수동 포함)
def select_auto_5_check(group_id, user_id, batch_count=100):
    param = (group_id, batch_count, )
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND ht_series_yyyymm = '202405'
            AND step_cd != 'CANCEL' 
            AND au6 is NULL
    '''

    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
            -- AND ht_tt_seq in (4724, 4825)
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


# 1단계 정보 업데이트
# =============================================================================================
# =============================================================================================
# =============================================================================================
# 홈택스 정보 초기화
def update_HtTt_initHometaxInfo(ht_tt_seq):
    #global conn    
    param = (None, None, None, None, ht_tt_seq)
    sql = '''
        UPDATE ht_tt 
        SET hometax_installment1=%s ,
            hometax_installment2=%s ,
            hometax_income_tax=%s ,
            hometax_reg_num=%s
        WHERE ht_tt_seq=%s
    '''
    
    try:    
        with conn.cursor() as curs:    
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")
        
# 홈택스 분납정보 업데이트
def update_HtTt_installment(ht_tt_seq:int, hometax_installment1:int, hometax_installment2:int):
    param = (hometax_installment1, hometax_installment2, ht_tt_seq)
    sql = "UPDATE ht_tt SET hometax_installment1=%s, hometax_installment2=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()   
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

# 홈택스 접수번호 업데이트
def update_HtTt_hometaxRegNum(ht_tt_seq, hometax_reg_num):
    #global conn    
    param = (hometax_reg_num, ht_tt_seq)
    sql = "UPDATE ht_tt SET hometax_reg_num=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

# 홈택스 세액 업데이트
def update_HtTt_hometaxIncomeTax(ht_tt_seq, hometax_income_tax):
    param = (hometax_income_tax, ht_tt_seq)
    sql = "UPDATE ht_tt SET hometax_income_tax=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

def update_HtTt_audit_tmp1(ht_tt_seq, audit_tmp1):
    #global conn    
    param = (audit_tmp1, ht_tt_seq)
    sql = "UPDATE ht_tt SET audit_tmp1=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

def update_HtTt_audit_tmp2(ht_tt_seq, audit_tmp2):
    #global conn    
    param = (audit_tmp2, ht_tt_seq)
    sql = "UPDATE ht_tt SET audit_tmp2=%s WHERE ht_tt_seq=%s"
    
    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

def update_HtTt_audit_tmp3(ht_tt_seq, audit_tmp3):
    #global conn    
    param = (audit_tmp3, ht_tt_seq)
    sql = "UPDATE ht_tt SET audit_tmp3=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

def update_HtTt_audit_tmp4(ht_tt_seq, audit_tmp4):
    #global conn    
    param = (audit_tmp4, ht_tt_seq)
    sql = "UPDATE ht_tt SET audit_tmp4=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


# 3단계 : 위택스 신고오류 조회용 =========================================
def select_check_3(batch_count):
    param = (batch_count, )
    sql = '''
        SELECT  ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, hometax_reg_num
        FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND ht_series_yyyymm = '202405'
            AND step_cd='REPORT' 
            AND au3 IS NOT NULL 
        ORDER BY ht_tt_seq asc
        LIMIT 0, %s
    '''
    
    with conn.cursor() as curs:      
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs



# 2단계 초기화 (au2, 첨부파일 정보 삭제, ht_tt_file에서 삭제 등)
def update_HtTt_au2_reset(ht_tt_seq):

    # file_type별 파일이름 결정
    print("이전 파일 삭제 (홈택스) ---------")
    dir_work = ht_file.get_dir_by_htTtSeq(ht_tt_seq)
    # del_files = [
    #     "down1.pdf", "down2.pdf", "down3.pdf", "down4.pdf", "down8.pdf"
    #     , "work\\capture_1.png", "work\\capture_2.png", "work\\capture_3.png", "work\\capture_4.png", "work\\capture_8.png"
    # ]
    del_files = [
        "down4.pdf", "down8.pdf"
        , "work\\capture_4.png", "work\\capture_8.png"
    ]    

    for f in del_files:
        fullpath = dir_work + f
        if os.path.isfile(fullpath):
            print("이전 파일 삭제 (홈택스) : %s" % fullpath)
            os.remove(fullpath)


    rs = select_download_file_list_by_htTtSeq(ht_tt_seq)
    if rs is not None:
        # if rs['capture1_file_seq']
        #     del_sql = "DELETE FROM ht_tt_file WHERE ht_tt_file_seq=%s"
        # common.logqry(sql, param)
        # curs.execute(sql, param)


        param = (ht_tt_seq, )
        curs = conn.cursor()
        # sql = '''
        #     UPDATE ht_tt 
        #     SET capture1_file_seq = null,
        #         capture2_file_seq = null,
        #         capture3_file_seq = null,
        #         capture4_file_seq = null,
        #         capture8_file_seq = null,
        #         result1_file_seq = null,
        #         result2_file_seq = null,
        #         result3_file_seq = null,
        #         result4_file_seq = null,
        #         result8_file_seq = null
        #     WHERE ht_tt_seq=%s
        # '''
        sql = '''
            UPDATE ht_tt 
            SET 
                capture4_file_seq = null,
                capture8_file_seq = null,
                result4_file_seq = null,
                result8_file_seq = null
            WHERE ht_tt_seq=%s
        '''
        common.logqry(sql, param)
        curs.execute(sql, param)

        conn.commit()   




# 4단계 초기화 (au4, 첨부파일 정보 삭제, ht_tt_file에서 삭제 등)
def update_HtTt_au4_reset(ht_tt_seq):

    # file_type별 파일이름 결정
    print("이전 파일 삭제 (위택스) ---------")
    dir_work = ht_file.get_dir_by_htTtSeq(ht_tt_seq)
    del_files = [
        "down5.pdf",  "work\\capture_5.png"
    ]

    for f in del_files:
        fullpath = dir_work + f
        if os.path.isfile(fullpath):
            print("이전 파일 삭제 (위택스) : %s" % fullpath)
            os.remove(fullpath)


    rs = select_download_file_list_by_htTtSeq(ht_tt_seq)
    if rs is not None:
        # if rs['capture1_file_seq']
        #     del_sql = "DELETE FROM ht_tt_file WHERE ht_tt_file_seq=%s"
        # common.logqry(sql, param)
        # curs.execute(sql, param)


        param = (ht_tt_seq, )
        curs = conn.cursor()
        sql = '''
            UPDATE ht_tt 
            SET capture5_file_seq = null,
                result5_file_seq = null
            WHERE ht_tt_seq=%s
        '''

        common.logqry(sql, param)
        curs.execute(sql, param)

        conn.commit()   


# 3단계: 위택스 신고오류 초기화요 =========================================
def update_HtTt_au3_reset(ht_tt_seq):
    #global conn    
    param = (ht_tt_seq, )
    sql = "UPDATE ht_tt SET wetax_addr=null, au3=null, wetax_income_tax=0 WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


def update_job_status(ht_tt_seq, py_mode):
    #global conn    
    param = (py_mode, ht_tt_seq)
    sql = "UPDATE ht_tt SET py_mode=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

# 홈택스 다운로드 초기화
def update_au2_status(ht_tt_seq, status):
    #global conn    
    param = (status, ht_tt_seq)
    curs = conn.cursor()
    sql = "UPDATE ht_tt SET au2=%s, step_cd='REPORT' WHERE ht_tt_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

def update_au4_status_to_report(ht_tt_seq, status):
    #global conn    
    param = (status, ht_tt_seq)
    sql = "UPDATE ht_tt SET au4=%s, step_cd='REPORT', result5_file_seq=null WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


def update_HtTt_statusCd(ht_tt_seq, status_cd):
    # status_cd = WAIT|WORKING|DONE|ERROR 중 하나
    #global conn    
    param = (status_cd, ht_tt_seq)
    sql = "UPDATE ht_tt SET status_cd=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

def select_HtTtFile_ByPk(ht_tt_file_seq) :
    param = (ht_tt_file_seq,)
    # SQL문 실행
    sql = "SELECT * FROM ht_tt_file WHERE ht_tt_file_seq=%s"

    with conn.cursor() as curs:  
        common.logqry(sql, param)
        curs.execute(sql, param)
        rs = curs.fetchall()
        return rs

def insert_or_update_upload_file (file_type, group_id, ht_tt_seq, holder_nm) :
    curs = conn.cursor(pymysql.cursors.DictCursor)
    sql_httt = "SELECT * FROM ht_tt WHERE ht_tt_seq=%s"
    common.logqry(sql_httt, (ht_tt_seq,))
    curs.execute(sql_httt,  (ht_tt_seq,))
    row = curs.fetchone()

    file_type_idx = file_type[-1]  # 파일타입의 마지막 숫자 (1~7)
    field_name = 'result' + str(file_type_idx) + '_file_seq'

    if file_type_idx == "P":   # 캡쳐 이미지는 _CAP으로 끝남
        file_type_idx= file_type[-5]
        field_name = 'capture' + str(file_type_idx) + '_file_seq'


    common.logt("이전 자료 조회 : 필드명=%s" % field_name)
    # print(row)
    if row != None:
        file_seq = row[field_name]
        if file_seq != None and file_seq>0:
            with conn.cursor() as curs2:
                common.logt("이전 자료 조회 : ht_tt_file_seq=%d  => 삭제" % file_seq)
                # 기존 파일이 있을 경우 ht_tt_file 삭제
                del_sql = "DELETE FROM ht_tt_file WHERE ht_tt_file_seq=%s"
                common.logqry(del_sql, (file_seq,))
                curs2.execute(del_sql, (file_seq,))
            #conn.commit()  


    # 딕셔너리
    ins_data = ht_file.make_file_data(group_id, ht_tt_seq, file_type, holder_nm)

    # 튜플로 변환
    param = tuple(ins_data.values())
    #print(param)
    sql1 = '''
        INSERT INTO ht_tt_file (ht_tt_seq, attach_file_type_cd, original_file_nm, changed_file_nm, path, uuid, file_size, file_ext, save_yn, reg_id)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    ht_tt_file_seq = 0
    with conn.cursor() as curs2:
        common.logqry(sql1, param)
        curs2.execute(sql1, param)
        ht_tt_file_seq = curs2.lastrowid
        #conn.commit()   

    # 파일 정보 UPDATE    
    common.logt("등록된 파일 ht_tt_file_seq= " + str(ht_tt_file_seq))
    sql2 = f"UPDATE ht_tt SET {field_name}=%s WHERE ht_tt_seq=%s"   #  동적 쿼리가 작동하는지 점검
    param2 = (ht_tt_file_seq, ht_tt_seq)
    with conn.cursor() as curs2:
        common.logqry(sql2, param2)
        curs2.execute(sql2, param2)
    
    conn.commit()   


# 위택스 신고 완료
def update_HtTt_wetax_complete(ht_tt_seq, wetax_income_tax, wetax_addr, wetax_reg_num, region):
    param = (wetax_income_tax, wetax_addr, wetax_reg_num, region, ht_tt_seq)
    sql = """
        UPDATE ht_tt 
        SET wetax_income_tax = %s
            , wetax_addr = %s
            , wetax_reg_num = %s 
            , wetax_region = %s
            , au3_reg_dt = NOW()
        WHERE ht_tt_seq = %s
        """
        
    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()   
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")

    
# 위택스 정보 업데이트
def update_HtTt_wetax(ht_tt_seq, wetax_income_tax, wetax_addr, wetax_reg_num):
    param = (wetax_income_tax, wetax_addr, wetax_reg_num, ht_tt_seq)
    sql = "UPDATE ht_tt SET wetax_income_tax=%s, wetax_addr=%s, wetax_reg_num=%s WHERE ht_tt_seq=%s"
    
    
    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()   
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


# 위택스 전자납부 번호
def update_HtTt_WetaxRegNum(ht_tt_seq, wetax_reg_num):
    param = (wetax_reg_num, ht_tt_seq)
    sql = "UPDATE ht_tt SET wetax_reg_num=%s, step_cd='REPORT_DONE' WHERE ht_tt_seq=%s"
    
    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()   
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


def update_HtTt_stepCd(ht_tt_seq, step_cd):
    param = (step_cd, ht_tt_seq)
    sql = "UPDATE ht_tt SET step_cd=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()   
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


def select_all_HtTt(step_cd=None):
    rs = None

    sql = '''
        SELECT t.* , u.nm reg_nm
        FROM ht_tt t
        JOIN user u on u.id = t.reg_id
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND ht_series_yyyymm = '202405'
    '''
    if step_cd is not None:
        sql += "AND step_cd='%s'" % (step_cd, )
    '''
            -- AND ht_tt_seq=6
        ORDER BY ht_tt_seq asc
    '''
    
    with conn.cursor() as curs: 
        common.logqry(sql)
        curs.execute(sql)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


def select_one_HtTtFile(ht_tt_file_seq):
    param = (s,)
    sql = "SELECT *  FROM ht_tt_file WHERE ht_tt_file_seq = %s"

    with conn.cursor() as curs: 
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        row = curs.fetchone()
        return row


# 거래내역 리스트
def select_HtTtList_by_htTtSeq(ht_tt_seq):
    param = (ht_tt_seq,)

    sql = '''
        SELECT *  
        FROM ht_tt_list 
        WHERE ht_tt_seq = %s
        ORDER BY ht_tt_list_seq
    '''
    
    with conn.cursor() as curs: 
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        row = curs.fetchall()
        return row



def select_download_file_list_by_htTtSeq(ht_tt_seq):
    param = (ht_tt_seq, )
    sql = '''
        select ht_tt_seq, t.step_cd , reg_id, data_type, holder_nm, holder_ssn1
            , au1, au2, au3, au4 
            , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result1_file_seq = f.ht_tt_file_seq) result1
            , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result2_file_seq = f.ht_tt_file_seq) result2
            , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result3_file_seq = f.ht_tt_file_seq) result3
            , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result4_file_seq = f.ht_tt_file_seq) result4
            , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result8_file_seq = f.ht_tt_file_seq) result8
            , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result5_file_seq = f.ht_tt_file_seq) result5
            , IFNULL(t.hometax_income_tax, 0) hometax_income_tax
            , IFNULL(t.wetax_income_tax, 0) wetax_income_tax
        from ht_tt t
        where t.ht_series_yyyymm ='202405'
            ANd ht_tt_seq = %s
        '''
        
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as curs:
            common.logqry(sql, param)
            curs.execute(sql, param)
            return curs.fetchone()
    except Exception as e:
        print(f"Error: {e}")
        return None

# 홈택스/위택스 다운로드 파일 점검
def select_download_file_list_2단계(group_id):
    param = (group_id,)

    sql = '''
    select ht_tt_seq, t.step_cd , reg_id, data_type, holder_nm, holder_ssn1, holder_ssn2
        , au1, au2, au3, au4 
        , IFNULL(au2_msg, '') au2_msg
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result1_file_seq = f.ht_tt_file_seq) result1
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result2_file_seq = f.ht_tt_file_seq) result2
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result3_file_seq = f.ht_tt_file_seq) result3
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result4_file_seq = f.ht_tt_file_seq) result4
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result5_file_seq = f.ht_tt_file_seq) result5
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result8_file_seq = f.ht_tt_file_seq) result8
        , IFNULL(t.hometax_income_tax, 0) hometax_income_tax
        , IFNULL(t.wetax_income_tax, 0) wetax_income_tax
        , remark
        , sec_company_cd
    from ht_tt t
    where t.ht_series_yyyymm ='202405'
        and t.group_id = %s
        and t.au2 = 'S'
        and t.step_cd IN ('REPORT', 'REPORT_DONE', 'NOTIFY', 'COMPLETE')
        -- and t.sec_company_cd = 'SEC07'
    order by 	ht_tt_seq
        '''

    with conn.cursor() as curs: 
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        return curs.fetchall()


def select_download_file_list_4단계(group_id):
    param = (group_id,)

    sql = '''
    select ht_tt_seq, t.step_cd , reg_id, data_type, holder_nm, holder_ssn1, holder_ssn2
        , au1, au2, au3, au4 
        , IFNULL(au2_msg, '') au2_msg
        -- , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result1_file_seq = f.ht_tt_file_seq) result1
        -- , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result2_file_seq = f.ht_tt_file_seq) result2
        -- , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result3_file_seq = f.ht_tt_file_seq) result3
        -- , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result4_file_seq = f.ht_tt_file_seq) result4
        , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result5_file_seq = f.ht_tt_file_seq) result5
        -- , (select concat(path, changed_file_nm)  from ht_tt_file f where t.result8_file_seq = f.ht_tt_file_seq) result8
        , IFNULL(t.hometax_income_tax, 0) hometax_income_tax
        , IFNULL(t.wetax_income_tax, 0) wetax_income_tax
        , remark
    from ht_tt t
    where t.ht_series_yyyymm ='202405'
        and t.group_id = %s
        -- and (t.au4 = 'S' or t.au4 = 'Y'  or t.au4 = 'X')
        and t.step_cd IN ('REPORT_DONE', 'NOTIFY', 'COMPLETE')
        and t.sec_company_cd = 'SEC07'
    order by 	ht_tt_seq
        '''

    with conn.cursor() as curs: 
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        return curs.fetchall()



# =============================================================================== select_auto_1
# 
def select_audit_위택스신고내역(series_seq_from, series_seq_to):
    param = (series_seq_from, series_seq_to)
    rs = None
    
    sql = '''
        SELECT *  
        FROM ht_tt 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND ht_series_yyyymm = '202405'
            AND data_type IN ('AUTO', 'SEMI') 
            -- AND sec_company_cd = 'SEC07'
            -- AND step_cd='COMPLETE'
            -- AND ht_tt_seq > (SELECT IFNULL(MAX(ht_tt_seq),0) FROM au_audit WHERE au_step=3)
            -- AND (series_seq>=%s AND series_seq<= %s)
            and ht_tt_seq > 29860
        ORDER BY ht_tt_seq asc

    '''
    
    with conn.cursor() as curs: 
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        common.logrs(rs)
        return rs


def insert_au_audit(au_step, ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, ht_report_cnt, we_report_cnt
                , ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num):
    if ht_tt_seq == None:
        return

    param = (au_step, ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, ht_report_cnt, we_report_cnt, ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num)
    

    sql = """
    INSERT INTO au_audit(au_step, ht_tt_seq, holder_nm, holder_ssn1, holder_ssn2, ht_report_cnt, we_report_cnt, ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num)
    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as curs:
            common.logqry(sql, param)
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        return None


# 리스트를 값으로 전달하는 방법 사용
def insert_audit_ht(data_list) -> int:
    # param = (
    #     year_month, tax_type, report_type1, report_type2, holder_nm, 
    #     holder_ssn1, reg_type, ht_reg_dt, hometax_reg_num, hometax_reg_id, 
    #     upload_yn, payment_yn)

    curs = conn.cursor()

    sql = """
    INSERT INTO audit_ht (
        `year_month`, tax_type, report_type1, report_type2, holder_nm, 
        holder_ssn1, reg_type, ht_reg_dt, hometax_reg_num, hometax_reg_id, 
        upload_yn, payment_yn)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """


        # (data_list[i][], data_list[i][], data_list[i][], data_list[i][], data_list[i][], 
        # data_list[i][], data_list[i][], data_list[i][], data_list[i][], data_list[i][], 
        # data_list[i][], data_list[i][])

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as curs:
            #common.logqry(sql, param)
            affected = curs.executemany(sql, data_list)
            conn.commit()
            return affected
    except Exception as e:
        print(f"Error: {e}")
        return None




def insert_smsHistory(data):
    columns = ', '.join(data.keys())
    values_template = ', '.join(['%s'] * len(data))

    sql = f"INSERT INTO sms_history ({columns})  VALUES ({values_template})"

    try:
        with conn.cursor() as curs:
            curs.execute(sql, tuple(data.values()))
            conn.commit()
        return True
    except Exception as e:
        print("Error inserting into", "sms_history", ":", e)
        return False

