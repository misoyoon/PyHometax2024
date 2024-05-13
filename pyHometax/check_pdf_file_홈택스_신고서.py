
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTPage, LTChar
import sys, os
import pymysql
import threading

CUR_CWD = os.getcwd()


from datetime import datetime
import logging

import dbjob
import ht_file
import config

'''
홈택스, 위택스에서 다운로드 받은 문서에 대한 검증을 하기 위한 PDF 파싱
각 문서 별로 특정 키워드를 분석하여 원하는 문서가 맞는지 점검한다.

created 2024-03-03
'''

    #def __str__(self):
        # print(f"Title: {item.title}, X: {item.x}, Y: {item.y}, is_set: {item.is_set}, Value: {item.val}, Filter: {item.filter}")

CHECK_LIST = {
        'HT_DOWN_1' : [ # 1_홈택스_신고서
                {'x': 199, 'y': 699, 'is_set':False, 'val': '', 'title':'성명',         'filter':''},
                #{'x': 241, 'y': 682, 'is_set':False, 'val': '', 'title':'주소',         'filter':'성명전 자 우 편소주소'},
                {'x': 208, 'y': 590, 'is_set':False, 'val': '', 'title':'양도소득금액', 'filter':','}
            ],
        'HT_DOWN_2' : [ # 2_홈택스_계산명세서
                {'x': 193, 'y': 186, 'is_set':False, 'val': '', 'title':'양도소득금액', 'filter':','}
            ],
        'HT_DOWN_3' : [  # 3_홈택스_접수증
                {'x': 148, 'y': 559, 'is_set':False, 'val': '', 'title':'성명',        'filter':''},
                {'x': 198, 'y': 629, 'is_set':False, 'val': '', 'title':'접수번호',    'filter':''},
                {'x': 523, 'y': 378, 'is_set':False, 'val': '', 'title':'과세표준',    'filter':','},
            ],
        'HT_DOWN_4' : [  # 4_홈택스_납부서
                {'x': 205, 'y': 637, 'is_set':False, 'val': '', 'title':'홈택스_납부세액', 'filter':' '},  # filter ' ' 공백에 주의할것, text결과값에서 space 제거하기 위해
                {'x': 84 , 'y': 711, 'is_set':False, 'val': '', 'title':'성명',     'filter':''},
                #{'x': 162, 'y': 688, 'is_set':False, 'val': '', 'title':'주소',     'filter':''},
                {'x': 324, 'y': 594, 'is_set':False, 'val': '', 'title':'가상계좌1', 'filter':' '}, # "국세계좌,KEB,국민"중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
                {'x': 493, 'y': 600, 'is_set':False, 'val': '', 'title':'가상계좌2', 'filter':' '},  # "기업,신한,우리" 중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
            ],
        'WE_DOWN_5' : [  # 5_위택스_납부서
                {'x': 259, 'y': 712, 'is_set':False, 'val': '', 'title':'성명',            'filter':''},
                {'x': 213, 'y': 463, 'is_set':False, 'val': '', 'title':'위택스_납부세액', 'filter':','},
                {'x': 267, 'y': 204, 'is_set':False, 'val': '', 'title':'가상계좌1',       'filter':''},  # 10글자(전국공통(지방세입)) 넘으면 가상계좌가 있는 것으로 판단
                {'x': 441, 'y': 204, 'is_set':False, 'val': '', 'title':'가상계좌2',        'filter':''} # 25글자(41463-1-95-24-4-0003813-1) 넘으면 가상계좌가 있는 것으로 판단
            ],
        'HT_DOWN_8' : [  # 4_홈택스_납부서(분납)
                {'x': 205, 'y': 637, 'is_set':False, 'val': '', 'title':'홈택스_납부세액2', 'filter':' '},  # filter ' ' 공백에 주의할것, text결과값에서 space 제거하기 위해
                {'x': 84 , 'y': 711, 'is_set':False, 'val': '', 'title':'성명',     'filter':''},
                {'x': 162, 'y': 688, 'is_set':False, 'val': '', 'title':'주소',     'filter':''},
                {'x': 324, 'y': 594, 'is_set':False, 'val': '', 'title':'가상계좌1', 'filter':' '},  # "국세계좌,KEB,국민"중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
                {'x': 493, 'y': 600, 'is_set':False, 'val': '', 'title':'가상계좌2', 'filter':' '},  # "기업,신한,우리" 중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
            ],
        # '6_위택스_신고서' : [
        #         {'x': 317, 'y': 704, 'is_set':False, 'val': '', 'title':'성명', 'filter':'성    명'}, # 깨끗하게 이름만 나오지 않음
        #         {'x': 213, 'y': 421, 'is_set':False, 'val': '', 'title':'납부세액', 'filter':','},
        #         {'x': 182, 'y': 671, 'is_set':False, 'val': '', 'title':'주소1', 'filter':'전자우편주    소주    소'}, # 주소가 한번에 나오지 않고 일부만 나옴
        #     ],
    }



class PdfItem:
    def __init__(self, x, y, is_set=False, val='', title='', filter=''):
        self.x = x
        self.y = y
        self.is_set = is_set
        self.val = val
        self.title = title
        self.filter = filter
    

def create_pdf_item_for(pdf_type):
    pdf_items = []
    pdf_item_infos = CHECK_LIST.get(pdf_type, [])

    for item_info in pdf_item_infos:
        pdf_item = PdfItem(item_info['x'], item_info['y'], item_info['is_set'], item_info['val'], item_info['title'], item_info['filter'])
        pdf_items.append(pdf_item)

    return pdf_items



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

where_common = '''
            AND t.ht_series_yyyymm ='202405'
            AND t.group_id = %s
            AND t.au2 = 'S'
            AND t.au4 = 'S'
            -- AND t.step_cd IN ('REPORT', 'REPORT_DONE', 'NOTIFY', 'COMPLETE')
            and t.step_cd IN ('REPORT_DONE', 'NOTIFY', 'COMPLETE')
            -- AND t.sec_company_cd = 'SEC07'
'''

def select_download_file_keys(group_id='the1'):
    param = (group_id, )

    sql = '''
        SELECT   t.ht_tt_seq
        FROM
            ht_tt t
        WHERE 1=1 
    '''
    sql += where_common
    sql +=  '''
        ORDER BY 
            t.ht_tt_seq;
        '''
    #print(sql)
    with conn.cursor() as curs: 
        curs.execute(sql, param)
        
        # 데이타 Fetch
        return curs.fetchall()

def select_download_file_list(ht_tt_seq_s, ht_tt_seq_e, group_id='the1'):
    param = (group_id, ht_tt_seq_s, ht_tt_seq_e)

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
            audit_tmp1 is null,
            (SELECT SUM(li.income_amount) FROM ht_tt_list li WHERE t.ht_tt_seq = li.ht_tt_seq) as sum_income_amount
            -- IF((SELECT SUM(li.income_amount) - 2500000 FROM ht_tt_list li WHERE t.ht_tt_seq = li.ht_tt_seq) < 0, 0, (SELECT SUM(li.income_amount) - 2500000 FROM ht_tt_list li WHERE t.ht_tt_seq = li.ht_tt_seq)) AS sum_income_amount
        FROM 
            ht_tt t
        WHERE 1=1
    '''
    sql += where_common
    sql +=  '''
            and ht_tt_seq >= %s and ht_tt_seq <= %s
        ORDER BY 
            t.ht_tt_seq;
        '''
    #print(sql)
    with conn.cursor() as curs: 
        curs.execute(sql, param)
        
        # 데이타 Fetch
        return curs.fetchall()

def update_HtTt_audit_tmp1(ht_tt_seq, audit_tmp1):
    #global conn    
    param = (audit_tmp1, ht_tt_seq)
    sql = "UPDATE ht_tt SET audit_tmp1=%s WHERE ht_tt_seq=%s"

    try:    
        with conn.cursor() as curs:  
            curs.execute(sql, param)
            conn.commit()
    except Exception as e:
        # 변경 사항 롤백
        conn.rollback()
        print(f"오류 발생: {e}")


# Logger 설정
CUR_CWD = os.getcwd()
current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")

# 점검용 임시 생성 로그
AUDIO_LOG_DIR     = "V:/PyHometax_Log_2024/Audit"

# 로그 폴더 생성
os.makedirs(f"{AUDIO_LOG_DIR}", exist_ok=True)

# log_filename_d = f"{AUDIO_LOG_DIR}/PDF점검_{now}_detail.log"
# log_filename_s = f"{AUDIO_LOG_DIR}/PDF점검_{now}_summary.log"
# logger_d = set_logger(log_filename_d)
# logger_s = set_logger(log_filename_s)

conn = connect_db()


def check_pdf_content(ht_result, pdf_file, pdf_type_name, logger_d, logger_s, page=1):
    pdf_items = create_pdf_item_for(pdf_type_name)

    for pdf_page in extract_pages(pdf_file):
        isFound = False
        cur_page = pdf_page.pageid

        #특정 페이지에서만 검색
        if page > 0 and page != cur_page : continue
    
        for element in pdf_page:
            if isinstance(element, LTTextContainer):
                try:
                    text = element.get_text().strip().replace('\n', '')
                    cur_x1 = round(element.x0)
                    cur_x2 = round(element.x1)
                    cur_y1 = round(element.y0)
                    cur_y2 = round(element.y1)
                    #print(f'{text} ==>  {cur_x1},{cur_x2},{cur_y1},{cur_y2} => ( {(cur_x1+cur_x2)/2}, {(cur_y1+cur_y2)/2} )')
                    
                    #if (op.text=='성명' and text == '이지수') or (op.text=='주민번호' and text == '821111-2069016'):
                    #if text.find('농협중앙회')>=0:
                    #    print(f'찾는 단어를 찾았음 : {op.text} => {text}')

                    for op in pdf_items:
                        if op.is_set : continue
                        
                        if cur_x1 <= op.x and op.x <= cur_x2 and cur_y1 <= op.y and op.y <= cur_y2 :
                            op.is_set = True
                            if op.filter:
                                op.val = text.replace(op.filter, '').strip()
                            else:
                                op.val = text
                                
                    
                    
                    #if text.replace(' ', '').find("143127") >=0 :
                    #    print(f'{text} ==>  {cur_x1},{cur_x2},{cur_y1},{cur_y2} => ( {(cur_x1+cur_x2)/2}, {(cur_y1+cur_y2)/2} )')

                except Exception as e:
                    print(f'### ERROR ###  Except: 검색오류 : {e} => {element}')    

        if isFound: break

    ret = True
    logger_d.info('----------------------------------------------')
    for op in pdf_items:            
        if op.is_set : 
            err_add = '' # 정상
        else:
            err_add = '                                  <<<<<<<<<<<<<<<<<<<<<<<<<<<< ================ 값 없음'
            ret = False

        if op.title == '성명' and op.val != ht_result['holder_nm']:
            err_add = '                                  <<<<<<<<<<<<<<<<<<<<<<<<<<<< ================ 성명 불일치'
            ret = False

        if op.title == '양도소득금액':
            int_val = 0
            try : int_val = int(op['val'].replace(' ','').replace(',',''))
            except: ...

            if ht_result['other_sec_data'] == 'N' and ht_result['sum_income_amount'] != int_val:
                err_add = '                                  <<<<<<<<<<<<<<<<<<<<<<<<<<<< ================ 양도소득금액 불일치'
                ret = False
        
        if op.title.find('가상계좌') >= 0 and len(op.val) < 15:
            err_add = f'                                  <<<<<<<<<<<<<<<<<<<<<<<<<<<< ================ {op["title"]} 없음'
            ret = False

        if op.title.find('홈택스_납부세액') and int(op.val) < 15:
            int_val = 0
            try : int_val = int(op.val.replace(' ','').replace(',',''))
            except: ...

            if ht_result['other_sec_data'] == 'N' and ht_result['sum_income_amount'] != int_val:
                err_add = '                                  <<<<<<<<<<<<<<<<<<<<<<<<<<<< ================ 양도소득금액 불일치'
                ret = False

        logger_d.info(f"{pdf_type_name} : {op.title} : {op.is_set} => [{op.val}] {err_add}")

    return ret



# 스레드에서 실행될 함수
def do_thread_job(task):
    start, end, identifier = task

    log_filename_d = f"{AUDIO_LOG_DIR}/PDF점검/PDF점검_{now}_{identifier}_detail.log"
    log_filename_s = f"{AUDIO_LOG_DIR}/PDF점검/PDF점검_{now}_{identifier}_summary.log"
    logger_d = set_logger(log_filename_d) # detail
    logger_s = set_logger(log_filename_s) # summary
    
    logger_d.info(f'JOB :: No={identifier},  start={start}, end={end}')
    logger_s.info(f'JOB :: No={identifier},  start={start}, end={end}')

    #for 숫자 in range(start, end + 1):
    
    #    logger_d.info(f"숫자: {숫자}")
        
    rs = select_download_file_list(start, end)

    num  = 0
    for ht_result in rs:            
        num += 1
        if num>3: break
        try:
            ht_tt_seq = ht_result['ht_tt_seq']

            dir_work = ht_file.get_dir_by_htTtSeq('the1', ht_tt_seq, True)  # True => 폴더 생성

            # 오류가 발생할 경우 로그에 출력할 내용 작성
            msg = '-----------------------------------------------------------------------------'
            msg += f"\nht_tt_seq={ht_tt_seq}, {ht_result['holder_nm']}, {ht_result['holder_ssn1']}{ht_result['holder_ssn2']}"
            
            v_file_type = ''
            if ht_result['result1'] :
                v_file_type = "HT_DOWN_1"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result1']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                #logger_d.info(f"filename 1 : {db_filename}")
                if os.path.exists(db_filename):
                    check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                    if not ret: 
                        msg += f'\n {v_file_type} 분석내용 불일치'
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result2'] :
                v_file_type = "HT_DOWN_2"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result2']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    ret = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                    if not ret: 
                        msg += f'\n {v_file_type} 분석내용 불일치'
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result3'] :
                v_file_type = "HT_DOWN_3"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result3']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result4'] :
                v_file_type = "HT_DOWN_4"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result4']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result8'] :
                v_file_type = "HT_DOWN_8"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result8']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result5'] :
                v_file_type = "WE_DOWN_5"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result5']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

        except Exception as e:
            ...
# 주어진 배열을 작업들로 분할하는 함수
def split_tasks(sequence_list, thread_count):
    thread_data = []
    sequence_length = len(sequence_list)
    task_length = sequence_length // thread_count
    for i in range(0, sequence_length, task_length):
        end = min(i + task_length - 1, sequence_length - 1)
        thread_data.append((sequence_list[i], sequence_list[end], i // task_length))
    return thread_data



# 주어진 작업들을 처리하는 함수
def execute_tasks(thread_data, thread_count):
    threads = []

    for data in thread_data:
        thread = threading.Thread(target=do_thread_job, args=(data,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def main():
    # 원하는 스레드 개수
    thread_count = 1


    # 작업 대상 Key목록  ->  멀티쓰레드 생성을 통해 위해 전체 작업리스트 얻기
    rs = select_download_file_keys()
    ht_tt_seq_list = []
    for seqs in rs:
        ht_tt_seq_list.append(seqs['ht_tt_seq'])
    #ht_result_rs = dbjob.select_download_ht_result(ht_tt_seq)

    total = len(rs)
    print(f'rs count = {total}')

    print(f'평균 자료건수 = {total//thread_count}')

    return

    # 주어진 배열을 작업들로 분할
    thread_data = split_tasks(ht_tt_seq_list, thread_count)

    # 작업들을 처리하는 함수 호출
    print(f"쓰레드 수={thread_count}, 데이터 분할 결과 = {thread_data}")
    execute_tasks(thread_data, thread_count)


# 테스트를 위한 예제
if __name__ == "__main__":

    main()