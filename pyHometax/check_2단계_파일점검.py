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


# 홈택스/위택스 다운로드 파일 점검
def select_download_file_list_2단계(group_id):
    param = (group_id,)

    sql = '''
        SELECT 
            t.ht_tt_seq,
            t.step_cd,
            t.reg_id,
            t.data_type,
            t.holder_nm,
            t.holder_ssn1,
            t.holder_ssn2,
            t.au1,
            t.au2,
            t.au3,
            t.au4,
            IFNULL(t.au2_msg, '') AS au2_msg,
            (SELECT CONCAT(path, changed_file_nm) FROM ht_tt_file f WHERE t.result1_file_seq = f.ht_tt_file_seq) AS result1,
            (SELECT CONCAT(path, changed_file_nm) FROM ht_tt_file f WHERE t.result2_file_seq = f.ht_tt_file_seq) AS result2,
            (SELECT CONCAT(path, changed_file_nm) FROM ht_tt_file f WHERE t.result3_file_seq = f.ht_tt_file_seq) AS result3,
            (SELECT CONCAT(path, changed_file_nm) FROM ht_tt_file f WHERE t.result4_file_seq = f.ht_tt_file_seq) AS result4,
            (SELECT CONCAT(path, changed_file_nm) FROM ht_tt_file f WHERE t.result5_file_seq = f.ht_tt_file_seq) AS result5,
            (SELECT CONCAT(path, changed_file_nm) FROM ht_tt_file f WHERE t.result8_file_seq = f.ht_tt_file_seq) AS result8,
            IFNULL(t.hometax_income_tax, 0) AS hometax_income_tax,
            IFNULL(t.wetax_income_tax, 0) AS wetax_income_tax,
            t.remark,
            t.hometax_paid_yn,
            t.sec_company_cd,
            IF((SELECT SUM(li.income_amount) - 2500000 FROM ht_tt_list li WHERE t.ht_tt_seq = li.ht_tt_seq) < 0, 0, (SELECT SUM(li.income_amount) - 2500000 FROM ht_tt_list li WHERE t.ht_tt_seq = li.ht_tt_seq)) AS sum_income_amount
        FROM 
            ht_tt t
        WHERE 
            t.ht_series_yyyymm ='202405'
            AND t.group_id = %s
            AND t.au2 = 'S'
            AND t.step_cd IN ('REPORT', 'REPORT_DONE', 'NOTIFY', 'COMPLETE')
            -- AND t.sec_company_cd = 'SEC07'
        ORDER BY 
            t.ht_tt_seq;

        '''

    with conn.cursor() as curs: 
        curs.execute(sql, param)
        
        # 데이타 Fetch
        return curs.fetchall()

# 홈택스 다운로드 초기화
def update_au2_status(ht_tt_seq, status):
    #global conn    
    param = (status, ht_tt_seq)
    curs = conn.cursor()
    sql = "UPDATE ht_tt SET au2=%s, step_cd='REPORT' WHERE ht_tt_seq=%s"
    curs.execute(sql, param)
    conn.commit()


conn = connect_db()

# Logger 설정
CUR_CWD = os.getcwd()
current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")

AUDIO_LOG_DIR     = "V:/PyHometax_Log_2024/Audit"

# 로그 폴더 생성
os.makedirs(f"{AUDIO_LOG_DIR}", exist_ok=True)

#log_filename_d = f"{AUDIO_LOG_DIR}/2단계_파일점검_{now}_detail.log"
log_filename_s = f"{AUDIO_LOG_DIR}/2단계_파일점검_{now}_summary.log"
#logger_d = set_logger(log_filename_d)
logger_s = set_logger(log_filename_s)


root_dir = config.FILE_ROOT_DIR_BASE + "the1\\"

result = []
i=0
rs = select_download_file_list_2단계('the1')
print(f"2단계 다운로드 파일 점검, 갯수 = {len(rs)}")


for ht in rs:
    #if ht['holder_nm'] == '장하연':  print("debug")
    
    ht_tt_seq = ht['ht_tt_seq']
    # 정상판단되는 seq는 생략
    passlist = []
    if ht_tt_seq in passlist:
        continue

    if ht_tt_seq % 1000 == 0:
        print(f"{ht_tt_seq} 처리 중 ...")

    ret = ''
    try :
        if ht['au2'] == 'S':
            # 파일 1
            if ht['result1']:
                file = root_dir + ht['result1']
                if os.path.exists(file): 
                    ret += '.'
                    if os.path.getsize(file) == 0 : ret += '10'
                else: 
                    ret += '1X'
            else: 
                ret += '1X'


            # 파일 2
            if ht['result1']:
                file = root_dir + ht['result2']
                if os.path.exists(file): 
                    ret += '.'
                    if os.path.getsize(file) == 0 : ret += '20'
                else: 
                    ret += '2X'
            else: 
                ret += '2X'
            

            # 파일 3
            if ht['result1']:
                file = root_dir + ht['result3']
                if os.path.exists(file): 
                    ret += '.'
                    if os.path.getsize(file) == 0 : ret += '30'
                else: 
                    ret += '3X'
            else: 
                ret += '3X'


            # 파일 4
            # 납부서 : result4
            if ht['result4']:
                if ht['hometax_paid_yn'] == 'Y' or \
                        (ht['sum_income_amount']==0 and ht['data_type']=='AUTO' and ht['au2_msg'].find('납부서 Click불가')>=0) :
                    ret += '.'
                else:
                    if ht['hometax_income_tax'] >= 10:
                        file = root_dir + ht['result4']
                        if os.path.exists(file): 
                            if os.path.getsize(file) == 0:  ret += '40'   # 비정상
                        else: 
                            ret += '4X'       # 비정상
                    else :
                        ret += '.'           # 정상
            else:
                if ht['hometax_paid_yn'] == 'Y':
                    ret += '.'
                elif ht['hometax_income_tax'] >= 10:
                    ret += '4X'


            # 납부서 분납분 : result8
            if ht['result8']:
                if ht['hometax_paid_yn'] == 'Y' or \
                        (ht['sum_income_amount']==0 and ht['data_type']=='AUTO' and ht['au2_msg'].find('납부서 Click불가')>=0) :
                    ret += '.'
                else:
                    if ht['hometax_income_tax'] > 10000000:
                        file = root_dir + ht['result8']
                        if os.path.exists(file): 
                            if os.path.getsize(file) == 0:  ret += '80'   # 비정상
                        else: 
                            ret += '8X'
                    else :
                        ret += '.'
            else:
                if ht['hometax_paid_yn'] == 'Y' :
                    ret += '.'
                elif ht['hometax_income_tax'] >= 10000000:
                    ret += '8X'                
                else :
                    ret += '.'         

    except Exception as e:
        logger_s.error(f'ERROR:: {i} - {ht}') 
        #print(traceback.format_exc())
        ret = 'E'

    if ret.find("X")>=0 or ret.find("0")>=0:
        i += 1
        logger_s.info(f'{i} : {ret} ===> {ht}\n')    
        
        #update_au2_status(ht['ht_tt_seq'],  None)

        

