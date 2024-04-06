# 참고 페이지 
# https://www.fun-coding.org/mysql_basic6.html

import sys, os
import pymysql

import config
import common
import ht_file

def set_global(v_group_id, v_host_name, v_user_id, v_ht_tt_seq, v_au_step):
    global group_id
    group_id = v_group_id
    global host_name
    host_name = v_host_name
    global user_id
    user_id = v_user_id
    global ht_tt_seq
    ht_tt_seq = v_ht_tt_seq
    global au_step
    au_step = v_au_step

def connect_db():
    #if env != None:
    #    raise ValueError("환경정보를 설정해주세요")
    global conn    
    conn = pymysql.connect(
                            db  =config.DATABASE_CONFIG['db'],
                            user=config.DATABASE_CONFIG['user'],
                            host=config.DATABASE_CONFIG['host'],
                            port=config.DATABASE_CONFIG['port'],
                            password=config.DATABASE_CONFIG['password']
                        )
    return conn

# 업무담당자 리스트 출력
def get_worker_list(group_id, for_one_user) :
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, for_one_user)
    # SQL문 실행
    sql = '''
    SELECT id, nm name, hometax_id, hometax_pw, sms_num  FROM user 
    WHERE hometax_id IS NOT NULL AND hometax_pw IS NOT NULL 
        AND group_id=%s
    AND id=%s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()

    # Connection 닫기
    # conn.close()
    return rs

def get_worker_info(user_id) :
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (user_id,)
    # SQL문 실행
    sql = '''
    SELECT id, nm name, hometax_id, hometax_pw, tel  FROM user 
    WHERE hometax_id IS NOT NULL AND hometax_pw IS NOT NULL 
    AND id=%s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    row = curs.fetchone()

    # Connection 닫기
    # conn.close()
    return row

def select_auto_toss_importSeq(group_id, user_id, import_seq):
    param = (group_id, user_id, import_seq, )
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT *  FROM ht_tt 
        WHERE group_id=%s
            AND ht_series_yyyymm = '202405'
            AND reg_id = %s
            -- AND import_seq = %s
            AND ht_tt_seq=31597
        ORDER BY ht_tt_seq asc
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs

# 홈택스 납부여부 확인
def update_HtTt_hometaxPaidYn(ht_tt_seq, yn):
    #global conn    
    param = (ht_tt_seq, yn)
    curs = conn.cursor()
    sql = '''
        UPDATE ht_tt 
        SET hometax_paid_yn=%s ,
        WHERE ht_tt_seq=%s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

# 위택스 납부여부 확인
def update_HtTt_wetaxPaidYn(ht_tt_seq, yn):
    #global conn    
    param = (ht_tt_seq, yn)
    curs = conn.cursor()
    sql = '''
        UPDATE ht_tt 
        SET wetax_paid_yn=%s ,
        WHERE ht_tt_seq=%s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()    