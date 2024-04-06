# 참고 페이지 
# https://www.fun-coding.org/mysql_basic6.html

import sys, os
import pymysql

import config
import common
import git_file

def set_global(v_group_id, v_host_name, v_user_id, v_git_seq, v_au_step):
    global group_id
    group_id = v_group_id
    global host_name
    host_name = v_host_name
    global user_id
    user_id = v_user_id
    global git_seq
    git_seq = v_git_seq
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




# 홈택스 로그인 확인/불가 업데이트
def update_git_hometaxIdConfirm(group_id, git_seq, hometax_id_confirm):
    param = (hometax_id_confirm, group_id, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET hometax_id_confirm=%s WHERE group_id=%s AND git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   
    
    
# 신고안내문 다운로드 작업 완료 여부
def update_git_au_x(group_id, git_seq, au_x, au_x_val, au_x_msg=""):
    param = (au_x_val, au_x_msg, group_id, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET "+au_x+"=%s, "+au_x+"_msg=%s WHERE group_id=%s AND git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   
    


# 기장의무구분 업데이트
# 홈택스 로그인 확인/불가 업데이트
def update_git_기장의무구분(group_id, git_seq, booking_type):
    param = (booking_type, group_id, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET booking_type=%s WHERE group_id=%s AND git_seq=%s AND booking_type is null"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   

# 소득금액리스트 삭제
def delete_신고안내_소득리스트(group_id, git_seq):
    param = (group_id, git_seq)
    curs = conn.cursor()
    sql = "DELETE FROM git_list WHERE group_id=%s AND git_seq = %s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()



# 테이블 필드값 업데이트
def update_git_column_val(group_id, git_seq, col_name, col_val):
    param = (col_val, group_id, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET "+ col_name +" =%s WHERE group_id=%s AND git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   



# 소득금액리스트 추가
def insert_신고안내_소득리스트(group_id, git_seq, git_list_info):
    param = ( group_id
            , git_seq
            , git_list_info['수입종류_구분코드']
            , git_list_info['사업자번호'] 
            , git_list_info['상호'] 
            , git_list_info['경비율']
            , git_list_info['수입금액']
            , git_list_info['업종코드']
            , git_list_info['기장의무']
            , git_list_info['기준경비율_일반']
            , git_list_info['기준경비율_자가']
            , git_list_info['단순경비율_일반']
            , git_list_info['단순경비율_자가']
            , git_list_info['주요원천징수의무자']
            , 'SYSTEM'
            )
    curs = conn.cursor()
    sql = """
        INSERT INTO git_list
        ( group_id
        , git_seq
        , earned_type
        , biz_nm
        , biz_num
        , expense_ratio_text
        , income_amount
        , industry_cd
        , booking_type
        , basic_expense_rate
        , basic_expense_rate2
        , simple_expense_ratio
        , simple_expense_ratio2
        , main_job_place
        , reg_id
        ) VALUES( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )
    """
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   



# 사용자별 최신 자동신고 일시변경
def update_git_lastAutoRunDt(user_id) :
    #global conn    
    param = (user_id, )
    curs = conn.cursor()
    
    # 이전 실기록 삭제
    sql = "UPDATE user SET cookie_modi_dt = CURRENT_TIMESTAMP WHERE id = %s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


# 홈택스에 신고된 납부세액
def update_git_hometaxIncomeTax(git_seq, hometax_income_tax) :
    #global conn    
    param = (hometax_income_tax, git_seq)
    curs = conn.cursor()
    
    # 이전 실기록 삭제
    sql = "UPDATE git SET hometax_income_tax = %s WHERE git_seq = %s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


def delete_auHistory_byKey(key, au_step) :
    #global conn    
    param = (key, au_step)
    curs = conn.cursor()
    
    # 이전 실기록 삭제
    sql = "DELETE FROM au_history WHERE git_seq = %s AND au_step=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


def insert_auHistory(title, message="") :
    # global conn 
    # global git_seq
    # global user_id
    # global au_step
    if git_seq == None:
        return

    param = (git_seq, user_id, au_step, title, message, host_name)
    curs = conn.cursor()
    sql = """INSERT INTO au_history (git_seq, user_id, au_step, title, message, host_name)
            VALUES(%s, %s, %s, %s, %s, %s)"""
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

# result = S | F 둘중하나
def update_git_AuX(x, git_seq, au_status, au_message="") :
    #global conn    
    param = (au_status, au_message, git_seq)
    curs = conn.cursor()
    sql = ""
    if x == "0":
        sql = 'UPDATE git SET au0=%s, au1_msg=%s WHERE git_seq=%s'
    elif x == "1":
        sql = 'UPDATE git SET au1=%s, au2_msg=%s WHERE git_seq=%s'
    elif x == "2":
        sql = 'UPDATE git SET au2=%s, au2_msg=%s WHERE git_seq=%s'
    elif x == "3":
        sql = 'UPDATE git SET au3=%s, au3_msg=%s WHERE git_seq=%s'
    elif x == "4":
        sql = 'UPDATE git SET au4=%s, au4_msg=%s WHERE git_seq=%s'
    elif x == "5":
        sql = 'UPDATE git SET au5=%s, au5_msg=%s WHERE git_seq=%s'
    elif x == "6":
        sql = 'UPDATE git SET au6=%s, au6_msg=%s WHERE git_seq=%s'
        
#    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


# =============================================================================== select_auto_1

# 신고안내문 다운로드
def select_auto_0(group_id):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, )

    sql = '''
        SELECT *  
        FROM git
        WHERE group_id=%s 
            AND git_series_yyyymm = '202405'
            AND git_step_cd NOT IN ('CANCEL', 'CANCEL2')
            AND (au0 is null or au0 = '' or au0 = 'E')
            AND (hometax_id_confirm is null or (hometax_id_confirm !='N' and hometax_id_confirm !='C'))
            -- and git_seq=1
        ORDER BY git_seq
    '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()


###################################################################
# 1단계 -  홈택스 신고
###################################################################
# batch_count : 한번에 몇 개씩 가져올지 결정
def select_auto_1(group_id):
    param = (group_id, )
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = '''
        SELECT *  
        FROM git 
        WHERE   group_id=%s
            AND (au1 is null or au1 = '' or au1 = 'E')
            AND git_series_yyyymm = '202405'
            AND git_data_type='AUTO' 
            AND git_step_cd='REPORT'
            AND (
                au1 is Null or au1 = '' 
            -- or au1='E'
            )
            AND reg_id = %s
        ORDER BY git_seq asc
        LIMIT 0, %s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs

###################################################################
# 2단계 - (정상적인 상황) 홈택스 관련 문서 다운로드
###################################################################

def select_auto_2(group_id):
    param = (group_id,)
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT *  FROM git 
        WHERE   group_id=%s
            AND git_series_yyyymm = '202405'
            AND hometax_id_confirm = 'Y'
            AND git_step_cd NOT LIKE ('CANCEL%%')
            AND au2 is null
            -- AND (au2 is null or au2 = '' or au2 = 'E')
            -- AND au1='S' 
            -- AND (  au2 IS NULL  OR au2 = ''  OR au2 = 'E'  )
            -- AND git_seq  = 113
            -- AND git_seq  = 11
            -- and (git_seq  = 113 or  git_seq  = 11)
        ORDER BY git_seq asc
'''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs



###################################################################
# 3단계 - 위택스 신고
###################################################################
def select_auto_3(group_id, user_id, batch_count=100):
    param = (group_id, batch_count, )
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT *  FROM git 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND git_series_yyyymm = '202405'
            AND git_step_cd='REPORT' 
            -- AND git_data_type='AUTO' 
            -- AND hometax_income_tax > 0
            AND au1='S' 
            AND (
                au3 IS NULL 
                OR au3 = ''
                OR au3 = 'E'
                )
            -- AND git_seq = 8016
    '''
    
    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
        ORDER BY git_seq asc
        LIMIT 0, %s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs


###################################################################
# 4단계 - 위택스 다운로드
###################################################################
def select_auto_4(group_id):
    param = (group_id, )
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT *  FROM git 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND git_step_cd NOT LIKE ('CANCEL%%')
        --    AND (git_step_cd ='REPORT' or git_step_cd ='NOTIFY')  -- 임시로 적용
            AND git_series_yyyymm = '202405'
            AND hometax_id_confirm = 'Y'
            AND hometax_reg_num is not null
            AND (au4 is null or au4 = '' or au4 = 'E')            
        ORDER BY git_seq asc
    '''
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
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT *  FROM git 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND git_series_yyyymm = '202405'
            AND git_data_type='AUTO' 
            AND git_step_cd='COMPLETE' 
            AND au1='S' AND au5 is null
    '''

    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
            -- AND git_seq = 2
        ORDER BY git_seq asc
        LIMIT 0, %s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs

# 5단계(점검용) - 증빙자료제출이 잘 되어있는지 확인 (자동/반자동/수동 포함)
def select_auto_5_check(group_id, user_id, batch_count=100):
    param = (group_id, batch_count, )
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT *  FROM git 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND group_id=%s
            AND git_series_yyyymm = '202405'
            AND git_step_cd != 'CANCEL' 
            AND au6 is NULL
    '''

    if user_id.upper() != "MANAGER_ID":
        sql = sql + " AND reg_id = %s "
        param = (group_id, user_id, batch_count)

    sql = sql + '''
            -- AND git_seq in (4724, 4825)
        ORDER BY git_seq asc
        LIMIT 0, %s
    '''
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


# 홈택스 접수번호 업데이트
def update_git_hometaxRegNum(git_seq, hometax_reg_num):
    #global conn    
    param = (hometax_reg_num, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET hometax_reg_num=%s WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

# 홈택스 세액 업데이트
def update_git_hometaxIncomeTax(git_seq, hometax_income_tax):
    #global conn    
    param = (hometax_income_tax, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET hometax_income_tax=%s WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


# 3단계 : 위택스 신고오류 조회용 =========================================
def select_check_3(batch_count):
    param = (batch_count, )
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = '''
        SELECT  git_seq, nm, ssn1, ssn2, hometax_reg_num
        FROM git 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND git_series_yyyymm = '202405'
            AND git_step_cd='REPORT' 
            AND au3 IS NOT NULL 
        ORDER BY git_seq asc
        LIMIT 0, %s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs



# 2단계 초기화 (au2, 첨부파일 정보 삭제, git_file에서 삭제 등)
def update_git_au2_reset(git_seq):

    # file_type별 파일이름 결정
    print("이전 파일 삭제 ---------")
    dir_work = git_file.get_dir_by_gitSeq(git_seq)
    del_files = [
        "down1.pdf", "down2.pdf", "down3.pdf", "down4.pdf", "down8.pdf"
        , "work\\capture_1.png", "work\\capture_2.png", "work\\capture_3.png", "work\\capture_4.png", "work\\capture_8.png"
    ]

    for f in del_files:
        fullpath = dir_work + f
        if os.path.isfile(fullpath):
            print("이전 파일 삭제 : %s" % fullpath)
            os.remove(fullpath)


    rs = select_download_file_list_by_gitSeq(git_seq)
    if rs is not None:
        # if rs['capture1_file_seq']
        #     del_sql = "DELETE FROM git_file WHERE git_file_seq=%s"
        # common.logqry(sql, param)
        # curs.execute(sql, param)


        param = (git_seq, )
        curs = conn.cursor()
        sql = '''
            UPDATE git 
            SET result0_file_seq = null,
                result1_file_seq = null,
                result2_file_seq = null,
                result3_file_seq = null,
                result4_file_seq = null,
                result5_file_seq = null,
                result6_file_seq = null,
                result7_file_seq = null,
                result8_file_seq = null
            WHERE git_seq=%s
        '''

        common.logqry(sql, param)
        curs.execute(sql, param)

        conn.commit()   




# 4단계 초기화 (au4, 첨부파일 정보 삭제, git_file에서 삭제 등)
def update_git_au4_reset(git_seq):

    # file_type별 파일이름 결정
    print("이전 파일 삭제 ---------")
    dir_work = git_file.get_dir_by_gitSeq(git_seq)
    del_files = [
        "down4.pdf",  "down5.pdf",  "down6.pdf" 
    ]

    for f in del_files:
        fullpath = dir_work + f
        if os.path.isfile(fullpath):
            print("이전 파일 삭제 : %s" % fullpath)
            os.remove(fullpath)


    rs = select_download_file_list_by_gitSeq(git_seq)
    if rs is not None:
        param = (git_seq, )
        if rs['result4'] != None:
            del_sql = "DELETE FROM git_file WHERE git_seq=%s AND attach_type='HT_DOWN_4'"
            common.logqry(sql, param)
            curs.execute(sql, param)
        if rs['result5'] != None:
            del_sql = "DELETE FROM git_file WHERE git_seq=%s AND attach_type='HT_DOWN_5'"
            common.logqry(sql, param)
            curs.execute(sql, param)
        if rs['result6'] != None:
            del_sql = "DELETE FROM git_file WHERE git_seq=%s AND attach_type='HT_DOWN_6'"
            common.logqry(sql, param)
            curs.execute(sql, param)


    param = (git_seq, )
    curs = conn.cursor()
    sql = '''
        UPDATE git 
        SET result4_file_seq = null,
            result5_file_seq = null,
            result6_file_seq = null
        WHERE git_seq=%s
    '''

    common.logqry(sql, param)
    curs.execute(sql, param)

    conn.commit()   


# 3단계: 위택스 신고오류 초기화요 =========================================
def update_git_au3_reset(git_seq):
    #global conn    
    param = (git_seq, )
    curs = conn.cursor()
    sql = "UPDATE git SET wetax_addr=null, au3=null, wetax_income_tax=0 WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


def update_job_status(git_seq, py_mode):
    #global conn    
    param = (py_mode, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET py_mode=%s WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

# 홈택스 다운로드 초기화
def update_au2_status(git_seq, status):
    #global conn    
    param = (status, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET au2=%s, git_step_cd='REPORT' WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

def update_au4_status_to_report(git_seq, status):
    #global conn    
    param = (status, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET au4=%s, git_step_cd='REPORT', result5_file_seq=null WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


def update_git_statusCd(git_seq, status_cd):
    # status_cd = WAIT|WORKING|DONE|ERROR 중 하나
    #global conn    
    param = (status_cd, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET status_cd=%s WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

def select_gitFile_ByPk(git_file_seq) :
    #conn = connect_db()
    #global conn    
    # Connection 으로부터 Cursor 생성
    curs = conn.cursor(pymysql.cursors.DictCursor)
    
    param = (git_file_seq,)
    # SQL문 실행
    sql = "SELECT * FROM git_file WHERE git_file_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()

    return rs

def insert_or_update_upload_file (file_type, git_seq, nm) :
    curs = conn.cursor(pymysql.cursors.DictCursor)
    sql_git = "SELECT * FROM git WHERE git_seq=%s"
    common.logqry(sql_git, (git_seq,))
    curs.execute(sql_git,  (git_seq,))
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
            common.logt("이전 자료 조회 : git_file_seq=%d  => 삭제" % file_seq)
            # 기존 파일이 있을 경우 git_file 삭제
            del_sql = "DELETE FROM git_file WHERE git_file_seq=%s"
            common.logqry(del_sql, (file_seq,))
            curs.execute(del_sql, (file_seq,))
            #conn.commit()  


    # 딕셔너리
    ins_data = git_file.make_file_data(git_seq, file_type, nm)

    # 튜플로 변환
    param = tuple(ins_data.values())
    #print(param)
    sql1 = '''
        INSERT INTO git_file (git_seq, attach_file_type_cd, original_file_nm, changed_file_nm, path, uuid, file_size, file_ext, save_yn, reg_id)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''

    common.logqry(sql1, param)
    curs.execute(sql1, param)
    #conn.commit()   

    git_file_seq = curs.lastrowid
    
    common.logt("등록된 파일 git_file_seq= " + str(git_file_seq))
    sql2 = "UPDATE git SET " + field_name + "=%s WHERE git_seq=%s" 

    param2 = (git_file_seq, git_seq)
    common.logqry(sql2, param2)
    curs.execute(sql2, param2)
    conn.commit()   


# 위택스 정보 업데이트
def update_git_wetax(git_seq, wetax_income_tax, wetax_addr, wetax_reg_num):
    param = (wetax_income_tax, wetax_addr, wetax_reg_num, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET wetax_income_tax=%s, wetax_addr=%s, wetax_reg_num=%s WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   


# 위택스 전자납부 번호
def update_git_WetaxRegNum(git_seq, wetax_reg_num):
    param = (wetax_reg_num, git_seq)
    curs = conn.cursor()
    sql = "UPDATE git SET wetax_reg_num=%s WHERE git_seq=%s"
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()   


def select_all_git(git_step_cd=None):
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = '''
        SELECT t.* , u.nm reg_nm
        FROM git t
        JOIN user u on u.id = t.reg_id
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND git_series_yyyymm = '202405'
    '''
    if git_step_cd is not None:
        sql += "AND git_step_cd='%s'" % (git_step_cd, )
    '''
            -- AND git_seq=6
        ORDER BY git_seq asc
    '''
    common.logqry(sql)
    curs.execute(sql)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs


def select_one_gitFile(git_file_seq):
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT *  FROM git_file WHERE git_file_seq = " + str(git_file_seq)

    common.logqry(sql)
    curs.execute(sql)
    
    # 데이타 Fetch
    row = curs.fetchone()
    return row


# 신고안내문 다운로드
def select_git_for_audit_au0(group_id):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, )

    sql = '''
        SELECT *  
        FROM git
        WHERE group_id=%s AND au0 = 'S'
        ORDER BY git_seq
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()





# 거래내역 리스트
def select_git_by_gitSeq(group_id, git_seq):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, git_seq,)

    sql = '''
        SELECT *  
        FROM git
        WHERE group_id=%s AND git_seq = %s
    '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    row = curs.fetchone()
    return row

# 거래내역 리스트
def select_gitList_by_gitSeq(git_seq):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (git_seq,)

    sql = '''
        SELECT *  
        FROM git_list 
        WHERE git_seq = %s
        ORDER BY git_list_seq
    '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    row = curs.fetchall()
    return row



def select_download_file_list_by_gitSeq(git_seq):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (git_seq, )

    sql = '''
        select git_seq, t.git_step_cd , reg_id, git_data_type, nm, ssn1
            , au0, au1, au2, au3, au4, au5
            , (select concat(path, changed_file_nm)  from git_file f where t.result0_file_seq = f.git_file_seq) result0
            , (select concat(path, changed_file_nm)  from git_file f where t.result1_file_seq = f.git_file_seq) result1
            , (select concat(path, changed_file_nm)  from git_file f where t.result2_file_seq = f.git_file_seq) result2
            , (select concat(path, changed_file_nm)  from git_file f where t.result3_file_seq = f.git_file_seq) result3
            , (select concat(path, changed_file_nm)  from git_file f where t.result4_file_seq = f.git_file_seq) result4
            , (select concat(path, changed_file_nm)  from git_file f where t.result5_file_seq = f.git_file_seq) result5
            , (select concat(path, changed_file_nm)  from git_file f where t.result6_file_seq = f.git_file_seq) result6
            , (select concat(path, changed_file_nm)  from git_file f where t.result7_file_seq = f.git_file_seq) result7
            , (select concat(path, changed_file_nm)  from git_file f where t.result8_file_seq = f.git_file_seq) result8
            , IFNULL(t.hometax_income_tax, 0) hometax_income_tax
            , IFNULL(t.wetax_income_tax, 0) wetax_income_tax
        from git t
        where t.git_series_yyyymm ='202405'
            ANd git_seq = %s
        '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()


# 홈택스/위택스 다운로드 파일 점검
def select_download_file_list_2단계(group_id):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id,)

    sql = '''
        select git_seq, t.git_step_cd , reg_id, git_data_type, nm, ssn1
            , au1, au2, au3, au4 
            , IFNULL(au2_msg, '') au2_msg
            , (select concat(path, changed_file_nm)  from git_file f where t.result0_file_seq = f.git_file_seq) result0
            , (select concat(path, changed_file_nm)  from git_file f where t.result1_file_seq = f.git_file_seq) result1
            , (select concat(path, changed_file_nm)  from git_file f where t.result2_file_seq = f.git_file_seq) result2
            , (select concat(path, changed_file_nm)  from git_file f where t.result3_file_seq = f.git_file_seq) result3
            , (select concat(path, changed_file_nm)  from git_file f where t.result4_file_seq = f.git_file_seq) result4
            , (select concat(path, changed_file_nm)  from git_file f where t.result5_file_seq = f.git_file_seq) result5
            , (select concat(path, changed_file_nm)  from git_file f where t.result6_file_seq = f.git_file_seq) result6
            , (select concat(path, changed_file_nm)  from git_file f where t.result7_file_seq = f.git_file_seq) result7
            , (select concat(path, changed_file_nm)  from git_file f where t.result8_file_seq = f.git_file_seq) result8
            , IFNULL(t.hometax_income_tax, 0) hometax_income_tax
            , IFNULL(t.wetax_income_tax, 0) wetax_income_tax
        from git t
        where t.git_series_yyyymm ='202405'
            and t.group_id = %s
            and t.au2 = 'S'
            and t.git_step_cd IN ('REPORT', 'REPORT_DONE', 'NOTIFY')
        order by 	git_seq
        '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()


def select_download_file_list_4단계(group_id):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id,)

    sql = '''
select git_seq, t.git_step_cd , reg_id, git_data_type, nm, ssn1
	, au1, au2, au3, au4 
    , IFNULL(au2_msg, '') au2_msg
	, (select concat(path, changed_file_nm)  from git_file f where t.result1_file_seq = f.git_file_seq) result1
	, (select concat(path, changed_file_nm)  from git_file f where t.result2_file_seq = f.git_file_seq) result2
	, (select concat(path, changed_file_nm)  from git_file f where t.result3_file_seq = f.git_file_seq) result3
	, (select concat(path, changed_file_nm)  from git_file f where t.result4_file_seq = f.git_file_seq) result4
	, (select concat(path, changed_file_nm)  from git_file f where t.result5_file_seq = f.git_file_seq) result5
	, (select concat(path, changed_file_nm)  from git_file f where t.result8_file_seq = f.git_file_seq) result8
	, IFNULL(t.hometax_income_tax, 0) hometax_income_tax
	, IFNULL(t.wetax_income_tax, 0) wetax_income_tax
from git t
where t.git_series_yyyymm ='202405'
    and t.group_id = %s
	and t.au4 = 'S'
	and t.git_step_cd IN ('REPORT', 'REPORT_DONE', 'COMPLETE', 'NOTIFY')
order by 	git_seq
        '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()



# =============================================================================== select_auto_1
# 
def select_audit_위택스신고내역(series_seq_from, series_seq_to):
    param = (series_seq_from, series_seq_to)
    rs = None
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = '''
        SELECT *  
        FROM git 
        WHERE ifnull(use_yn, 'Y') != 'N'
            AND git_series_yyyymm = '202405'
            AND git_data_type IN ('AUTO', 'SEMI') 
            AND git_step_cd='COMPLETE'
            -- AND git_seq > (SELECT IFNULL(MAX(git_seq),0) FROM au_audit WHERE au_step=3)
            AND (series_seq>=%s AND series_seq<= %s)
        ORDER BY git_seq asc

    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()
    common.logrs(rs)
    return rs


def insert_au_audit(au_step, git_seq, nm, ssn1, ssn2, ht_report_cnt, we_report_cnt
                , ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num):
    if git_seq == None:
        return

    param = (au_step, git_seq, nm, ssn1, ssn2, ht_report_cnt, we_report_cnt, ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num)
    curs = conn.cursor()

    sql = """
    INSERT INTO au_audit(au_step, git_seq, nm, ssn1, ssn2, ht_report_cnt, we_report_cnt, ht_income_tax, we_income_tax, status, ht_reg_num, we_reg_num)
    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()

# --------------------------------------------------------------------------------------    
# Git FILE 추가
def insert_git_file(git_file) -> int:
    if git_file == None:
        return -1

    curs = conn.cursor()

    param1 = (git_file['group_id'], git_file['git_seq'], git_file['attach_type'])
    sql1 = """
        DELETE FROM git_file
        WHERE group_id=%s AND git_seq=%s AND attach_type=%s
    """
    common.logqry(sql1, param1)
    curs.execute(sql1, param1)


    sql2 = """
    INSERT INTO git_file(
        group_id
        , git_seq
        , attach_type
        , original_file_nm
        , changed_file_nm
        , path
        , uuid
        , file_size
        , file_ext
        , remark
        , reg_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    param2 = (
        git_file['group_id']
        , git_file['git_seq']
        , git_file['attach_type']
        , git_file['original_file_nm']
        , git_file['changed_file_nm']
        , git_file['path']
        , git_file['uuid']
        , git_file['file_size']
        , git_file['file_ext']
        , git_file['remark']
        , git_file['reg_id']
    )   

    common.logqry(sql2, param2)
    curs.execute(sql2, param2)
    conn.commit()
    
    git_file_seq = curs.lastrowid
    
    return git_file_seq


# Git FILE 타입별 삭제
# guide : 신고안내문 관련 
def delete_git_file_by_attachType(group_id, git_seq, attach_type):
    param = (group_id, git_seq, attach_type)    
    sql = """
        DELETE FROM git_file
        WHERE group_id=%s AND git_seq=%s AND attach_type=%s
    """
    curs = conn.cursor()
    common.logqry(sql, param)
    curs.execute(sql, param)
    conn.commit()


# def select_git_file_by_gitSeq(group_id, git_seq):
#     param = (group_id, batch_count)
#     rs = None
#     curs = conn.cursor(pymysql.cursors.DictCursor)
    
#     sql = """
#         DELETE FROM git_file
#         WHERE group_id=%s AND git_seq=%s AND attach_type=%s
#     """
#     curs = conn.cursor()
#     common.logqry(sql, param)
#     curs.execute(sql, param)
#     conn.commit()




# (전체자료 업데이트) 신고안내문  -  WHERE 조건이 그때그때 다름
def select_git_for_au5_자료업데이트(group_id):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, )

    sql = '''
        SELECT *  
        FROM git
        WHERE group_id=%s
            AND git_step_cd IN ('INIT', 'CHECK')
            AND au0 = 'S'
            -- AND ( hometax_id_confirm is null OR hometax_id_confirm ='Y' )
            AND ( hometax_id_confirm ='Y' )
            AND au5 is null
        ORDER BY git_seq
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()


# (테스트용) 신고안내문 
def TEST_select_git_for_au0(group_id):
    curs = conn.cursor(pymysql.cursors.DictCursor)
    param = (group_id, )

    sql = '''
        SELECT *  
        FROM git
        WHERE group_id=%s
            AND git_seq = 1
        ORDER BY git_seq
    '''

    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    return curs.fetchall()
