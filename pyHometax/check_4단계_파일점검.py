import config
import pymysql
import sys, os, time
import shutil
import traceback
import logging
from datetime import datetime

'''
홈택스/위택스 파일 다운로드가 완료된 것 중 DB & 파일 시스템이 정상적으로 연결되어 있는지 검사
'''


def set_logger(log_filename, level=logging.INFO):
    # 로깅 설정
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # 파일 핸들러 생성
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # 로거에 핸들러 추가
    logger = logging.getLogger(log_filename)  # 로거 이름을 파일 이름으로 설정
    logger.addHandler(file_handler)
    return logger


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
        , wetax_paid_yn
        , remark
    from ht_tt t
    where t.ht_series_yyyymm ='202405'
        AND t.group_id = %s
        and (t.au4 = 'S' or t.au4 = 'Y'  or t.au4 = 'X')
        and t.step_cd IN ('REPORT','REPORT_DONE', 'NOTIFY', 'COMPLETE')
    order by 	ht_tt_seq
        '''

    with conn.cursor() as curs: 
        curs.execute(sql, param)
        # 데이타 Fetch
        return curs.fetchall()


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


conn = connect_db()

# Logger 설정
CUR_CWD = os.getcwd()
current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")

# 점검용 임시 생성 로그
AUDIO_LOG_DIR     = "V:/PyHometax_Log_2024/Audit"

# 로그 폴더 생성
os.makedirs(f"{AUDIO_LOG_DIR}", exist_ok=True)

#log_filename_d = f"{AUDIO_LOG_DIR}/4단계_파일점검_{now}_detail.log"
log_filename_s = f"{AUDIO_LOG_DIR}/4단계_파일점검_{now}_summary.log"
#logger_d = set_logger(log_filename_d)
logger_s = set_logger(log_filename_s)





root_dir = config.FILE_ROOT_DIR_BASE + "the1\\"

result = []
i=0
rs = select_download_file_list_4단계('the1')
print(f"4단계 다운로드 파일 점검, 갯수 = {len(rs)}")

for ht in rs:

    ht_tt_seq = ht['ht_tt_seq']
    if ht_tt_seq % 1000 == 0:
        print(f"{ht_tt_seq} 처리 중 ...")
        
    ret = ''
    try :

        ht_tt_seq = ht['ht_tt_seq']
        # 정상판단되는 seq는 생략
        passlist = [] 
        if ht_tt_seq in passlist:
            continue

        # 세금이 10원 이상,  홈택스에서 이미 납부했으면 위택스에서 납부할 가능성이 있음
        if ht['au4'] == 'S':
            if ht['wetax_paid_yn'] == 'Y':
                ret += '.'    # 정상 
            elif ht['hometax_income_tax'] < 100 and ht['result5'] is None: 
                ret += '.'    # 정상 
            elif ht['hometax_income_tax'] >= 100 and ht['result5'] is None: 
                ret += '5.'   # 비정상
            else:
                file = root_dir + ht['result5']    # result5 => 결과 다운로드 - 위택스 접수증
                if os.path.exists(file): 
                    if os.path.getsize(file) == 0: 
                        ret += '50'   # 비정상
                    else:
                        ret += '.'    # 정상 
                else: 
                    ret += '5X'

    except Exception as e:
        ret = '5E'

    if ret.find("X")>=0 or ret.find("0")>=0 or ret.find("-")>=0:
        i += 1
        logger_s.info(f'{i} : {ret} ===> {ht}\n')    
        #print(f'{i} - {ret}')    
        
        #update_au4_status_to_report(ht['ht_tt_seq'],  None)

        
