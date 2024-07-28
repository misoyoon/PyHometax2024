
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
7단계
다른 단계와는 실행 방법이 다름
CMD에서만 실행 
python pyHometax/at_ht_step_7.py 40000 60000 0


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
                {'x': 198, 'y': 629, 'is_set':False, 'val': '', 'title':'홈택스_접수번호',    'filter':''},
                {'x': 544, 'y': 378, 'is_set':False, 'val': '', 'title':'과세표준',    'filter':','},  # 523
            ],
        'HT_DOWN_4' : [  # 4_홈택스_납부서
                {'x': 84 , 'y': 711, 'is_set':False, 'val': '', 'title':'성명',     'filter':''},
                {'x': 220, 'y': 637, 'is_set':False, 'val': '', 'title':'홈택스_납부세액', 'filter':' '},  # filter ' ' 공백에 주의할것, text결과값에서 space 제거하기 위해
                #{'x': 162, 'y': 688, 'is_set':False, 'val': '', 'title':'주소',     'filter':''},
                {'x': 324, 'y': 594, 'is_set':False, 'val': '', 'title':'가상계좌1', 'filter':' '}, # "국세계좌,KEB,국민"중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
                {'x': 493, 'y': 600, 'is_set':False, 'val': '', 'title':'가상계좌2', 'filter':' '},  # "기업,신한,우리" 중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
            ],
        'HT_DOWN_8' : [  # 4_홈택스_납부서(분납)
                {'x': 84 , 'y': 711, 'is_set':False, 'val': '', 'title':'성명',     'filter':''},
                {'x': 205, 'y': 637, 'is_set':False, 'val': '', 'title':'홈택스_납부세액2', 'filter':' '},  # filter ' ' 공백에 주의할것, text결과값에서 space 제거하기 위해
                #{'x': 162, 'y': 688, 'is_set':False, 'val': '', 'title':'주소',     'filter':''},
                {'x': 324, 'y': 594, 'is_set':False, 'val': '', 'title':'홈택스_가상계좌1', 'filter':' '},  # "국세계좌,KEB,국민"중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
                {'x': 493, 'y': 600, 'is_set':False, 'val': '', 'title':'홈택스_가상계좌2', 'filter':' '},  # "기업,신한,우리" 중 하나로 판단, 깨끗한 결과가 나오지 않음, 존재여부만 확인
            ],
        'WE_DOWN_5' : [  # 5_위택스_납부서
                # {'x': 259, 'y': 712, 'is_set':False, 'val': '', 'title':'성명',            'filter':''},
                {'x': 230, 'y': 463, 'is_set':False, 'val': '', 'title':'위택스_납부세액', 'filter':','},
                {'x': 479, 'y': 94,  'is_set':False, 'val': '', 'title':'위택스_납부번호', 'filter':','},
                {'x': 267, 'y': 214, 'is_set':False, 'val': '', 'title':'위택스_가상계좌1',       'filter':''},  # 10글자(전국공통(지방세입)) 넘으면 가상계좌가 있는 것으로 판단
                {'x': 441, 'y': 214, 'is_set':False, 'val': '', 'title':'위택스_가상계좌2',        'filter':''} # 25글자(41463-1-95-24-4-0003813-1) 넘으면 가상계좌가 있는 것으로 판단
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
            and t.data_type IN ('AUTO', 'SEMI')
            AND t.step_cd IN ('REPORT', 'REPORT_DONE', 'NOTIFY', 'COMPLETE')
            -- and t.step_cd IN ('REPORT_DONE', 'NOTIFY', 'COMPLETE')
            AND t.au7 is null
            -- AND t.sec_company_cd != 'SEC07'
            -- AND t.ht_tt_seq  = 40171
            -- and t.other_sec_data = 'Y'

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
            IFNULL(t.wetax_income_tax, 0)   AS wetax_income_tax,
            t.remark,
            IFNULL(t.hometax_reg_num, '') as hometax_reg_num,
            IFNULL(t.wetax_reg_num, '')   as wetax_reg_num,
            IFNULL(t.hometax_installment1, 0) AS hometax_installment1,
            IFNULL(t.hometax_installment2, 0) AS hometax_installment2,
            t.other_sec_data,
            t.hometax_paid_yn,
            t.wetax_paid_yn,
            t.sec_company_cd,
            t.au7 is null,
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

def update_HtTt_audit_au7(ht_tt_seq, au7, au7_msg):
    #global conn    
    param = (au7, au7_msg, ht_tt_seq)
    sql = "UPDATE ht_tt SET au7=%s, au7_msg=%s, au7_reg_dt=now() WHERE ht_tt_seq=%s"

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
AUDIO_LOG_DIR     = f"V:/PyHometax_Log_2024/Audit/PDF검증/{now}"

# 로그 폴더 생성
os.makedirs(f"{AUDIO_LOG_DIR}", exist_ok=True)

# log_filename_d = f"{AUDIO_LOG_DIR}/PDF점검_{now}_detail.log"
# log_filename_s = f"{AUDIO_LOG_DIR}/PDF점검_{now}_summary.log"
# logger_d = set_logger(log_filename_d)
# logger_s = set_logger(log_filename_s)

conn = connect_db()

MARK_MSG = "<<<<<<<<<<<<<<<<<<<<<<<<<<<<< "
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
                    
                    # 키워드 찾을 경우 아래 주석 풀어서 확인하기
                    # print(f'{text} ==>  {cur_x1},{cur_x2},{cur_y1},{cur_y2} => ( {(cur_x1+cur_x2)/2}, {(cur_y1+cur_y2)/2} )')
                    
                    #if (op.text=='성명' and text == '이지수') or (op.text=='주민번호' and text == '821111-2069016'):
                    #if text.find('농협중앙회')>=0:
                    #    print(f'찾는 단어를 찾았음 : {op.text} => {text}')

                    for op in pdf_items:
                        if op.is_set : continue
                        

                        if cur_x1 <= op.x and op.x <= cur_x2 and cur_y1 <= op.y and op.y <= cur_y2 :
                            # 이름이 아닌 주소가 먼저 셋팅되어서 걸러내기
                            if op.title == '성명' or op.title == '위택스_납부세액' :
                                if len(text) >= 30:
                                    continue

                            op.is_set = True
                            if op.filter:
                                op.val = text.replace(op.filter, '').strip()
                            else:
                                op.val = text
                                
                    
                    
                    #if text.replace(' ', '').find("143127") >=0 :
                    #    print(f'{text} ==>  {cur_x1},{cur_x2},{cur_y1},{cur_y2} => ( {(cur_x1+cur_x2)/2}, {(cur_y1+cur_y2)/2} )')

                except Exception as e:
                    logger_d.error(f'### ERROR ###  Except: 검색오류 : {e} => {element}')    

        if isFound: break

    ret = True
    #logger_d.info(f"No = {ht_result['ht_tt_seq']} ----------------------------------------------")

    # 분석 컬럼 결과 확인
    blank = ' ' * 20
    for op in pdf_items:
        err_add = ''

        try:
            #op_msg = f"{op.is_set}, {op.title}  ==> {op.val}"
            #logger_d.info (op_msg)

            if op.is_set : 
                err_add = '' # 정상
            else:
                err_add = f'{blank}{MARK_MSG} NOT값 없음'
                ret = False

            if op.title == '성명':
                if op.val.find(ht_result['holder_nm']) >= 0 or ht_result['holder_nm'].find(op.val) >=0 :
                    ...   # 정상
                else:
                    err_add = f"{blank}{ht_result['holder_nm']} : {op.val} {MARK_MSG}{op.title} 불일치"
                    ret = False

            elif op.title == '양도소득금액':  # 번금액
                int_val = to_number(op.val)

                if ht_result['data_type'] == 'AUTO' : # and ht_result['other_sec_data'] == 'N':
                    if ht_result['sum_income_amount'] != int_val:
                        err_add = f"{blank}{ht_result['sum_income_amount']} : {int_val} {MARK_MSG}{op.title} 불일치"
                        ret = False
            
            elif op.title == '홈택스_접수번호':
                if ht_result['data_type'] == 'AUTO' : #and ht_result['other_sec_data'] == 'N':
                    if ht_result['hometax_reg_num'].replace('-','') != op.val.replace('-',''):
                        err_add = f"{blank}{ht_result['hometax_reg_num'].replace('-','')} : {op.val.replace('-','')} {MARK_MSG}{op.title} 불일치"
                        ret = False

            elif op.title == '위택스_납부번호':
                if ht_result['data_type'] == 'AUTO' : #and ht_result['other_sec_data'] == 'N':
                    if ht_result['wetax_reg_num'].replace('-','') != op.val.replace('-',''):
                        err_add = f"{blank}{ht_result['wetax_reg_num'].replace('-','')} : {op.val.replace('-','')} {MARK_MSG}{op.title} 불일치"
                        ret = False

            elif op.title == '과세표준': #번금액 - 2500000
                int_val = to_number(op.val)

                if ht_result['data_type'] == 'AUTO'  : # and ht_result['other_sec_data'] == 'N':
                    과세표준 = 0
                    if ht_result['sum_income_amount'] >= 2_500_000:
                        과세표준 = ht_result['sum_income_amount'] - 2_500_000

                    if 과세표준 != int_val:
                        err_add = f"{blank}{ht_result['과세표준']} : {int_val} {MARK_MSG}{op.title} 불일치"
                        ret = False

            elif op.title.find('가상계좌') >= 0:
                min_len = 12  # 글자수로 판단

                if len(op.val) < min_len:
                    if op.title.find('위택스_가상계좌')>=0 and ht_result['hometax_income_tax'] < 10:
                        ... # 정상 케이스
                    else:
                        # 15글자 이내이면 국세납입 계좌만 있는 것으로 판단
                        err_add = f"{blank}{op.val} {MARK_MSG}{op.title} 길이조건({min_len}) 불일치"
                        ret = False
                    

            elif op.title == '홈택스_납부세액' :
                int_val = to_number(op.val)

                if ht_result['data_type'] == 'AUTO' : #and ht_result['other_sec_data'] == 'N':
                    if ht_result['hometax_income_tax'] >= 20_000_000:
                        if abs(ht_result['hometax_income_tax'] // 2 - int_val) > 10:
                            err_add = f"{blank}{ht_result['hometax_installmentD1']} : {int_val} {MARK_MSG}{op.title} 불일치1"
                            ret = False
                    elif ht_result['hometax_income_tax'] >= 10_000_000:
                        if  abs(int_val - 10_000_000) > 10:
                            err_add = f"{blank}{ht_result['hometax_installment1']} : {int_val} {MARK_MSG}{op.title} 불일치1"
                            ret = False
                    else:
                        if abs(ht_result['hometax_income_tax'] - int_val) >= 10:
                            err_add = f"{blank}{ht_result['hometax_income_tax']} : {int_val} {MARK_MSG}{op.title} 불일치2"
                            ret = False                        

            elif op.title == '홈택스_납부세액2' :
                int_val = to_number(op.val)

                if ht_result['data_type'] == 'AUTO' : #and ht_result['other_sec_data'] == 'N':
                    if ht_result['hometax_income_tax'] >= 20_000_000:
                        if abs(ht_result['hometax_income_tax'] // 2 - int_val) > 10:
                            err_add = f"{blank}{ht_result['hometax_installment2']} : {int_val} {MARK_MSG}{op.title} 불일치1"
                            ret = False
                    elif ht_result['hometax_income_tax'] >= 10_000_000:
                        if  abs(ht_result['hometax_income_tax'] - 10_000_000 - int_val) > 10:
                            err_add = f"{blank}{ht_result['hometax_installment2']} : {int_val} {MARK_MSG}{op.title} 불일치1"
                            ret = False
                    else:
                        if  int_val >= 10:
                            err_add = f"{blank}0 : {int_val} {MARK_MSG}{op.title} 불일치2"
                            ret = False                        

            elif op.title == '위택스_납부세액' :
                int_val = to_number(op.val)

                if ht_result['data_type'] == 'AUTO' : # and ht_result['other_sec_data'] == 'N':
                    if abs(ht_result['wetax_income_tax'] - int_val) >= 10:
                        err_add = f"{blank}{ht_result['wetax_income_tax']} : {int_val} {MARK_MSG}{op.title} 불일치"
                        ret = False

            logger_d.info(f"    {pdf_type_name} : {op.title} : {op.is_set} : {op.val} {err_add}")

        except Exception as e:
            logger_d.error(f"{e}")

    return ret, pdf_items

def to_number(v_str):
    int_val = 0
    try : 
        int_val = int(v_str.replace(' ','').replace(',',''))
    except: 
        ...
    return int_val


# 스레드에서 실행될 함수
def do_thread_job(task):
    start, end, identifier = task

    log_filename_d = f"{AUDIO_LOG_DIR}/PDF점검_{identifier}_detail.log"
    log_filename_s = f"{AUDIO_LOG_DIR}/PDF점검_{identifier}_summary.log"
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

        # 테스트용 임시 지정
        #if num>2: break

        try:
            ht_tt_seq = ht_result['ht_tt_seq']
            holder_nm = ht_result['holder_nm']
            holder_ssn1 = ht_result['holder_ssn1']
            holder_ssn2 = ht_result['holder_ssn2']
            data_type = ht_result['data_type']

            logger_d.info("=" * 40)
            logger_d.info(f"NO= {ht_tt_seq}, {holder_nm}, {holder_ssn1}{holder_ssn2}, {data_type}")

            dir_work = ht_file.get_dir_by_htTtSeq('the1', ht_tt_seq, True)  # True => 폴더 생성

            # 오류가 발생할 경우 로그에 출력할 내용 작성
            msg = ''

            홈택스_납부세액 = 0
            홈택스_납부세액2= 0
            위택스_납부세액 = 0
            홈택스_접수번호 = ''
            위택스_납부번호 = ''

            v_file_type = ''

            if ht_result['result1'] :
                v_file_type = "HT_DOWN_1"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result1']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                #logger_d.info(f"filename 1 : {db_filename}")
                if os.path.exists(db_filename):
                    ret, ops = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                    if not ret: 
                        msg += f'\n {v_file_type} 분석내용 불일치'
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result2'] :
                v_file_type = "HT_DOWN_2"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result2']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    ret, ops = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                    if not ret: 
                        msg += f'\n {v_file_type} 분석내용 불일치'
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['result3'] :
                v_file_type = "HT_DOWN_3"
                db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result3']}"
                #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                if os.path.exists(db_filename):
                    ret, ops = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                    홈택스_접수번호 = get_op_value(ops, '홈택스_접수번호', False)
                    if not ret: 
                        msg += f'\n {v_file_type} 분석내용 불일치'                    
                else:
                    msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['hometax_paid_yn'] != 'Y':
                if ht_result['result4'] :
                    v_file_type = "HT_DOWN_4"
                    db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result4']}"
                    #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                    if os.path.exists(db_filename):
                        ret, ops = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                        홈택스_납부세액 = get_op_value(ops, '홈택스_납부세액')
                        if not ret: 
                            msg += f'\n {v_file_type} 분석내용 불일치'                    
                    else:
                        msg += f'\n {v_file_type} 파일 없음, path={db_filename}'
            
            if ht_result['hometax_paid_yn'] != 'Y':
                if ht_result['result8'] :
                    v_file_type = "HT_DOWN_8"
                    db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result8']}"
                    #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                    if os.path.exists(db_filename):
                        ret, ops = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                        홈택스_납부세액2 = get_op_value(ops, '홈택스_납부세액2')
                        if not ret: 
                            msg += f'\n {v_file_type} 분석내용 불일치'                    
                    else:
                        msg += f'\n {v_file_type} 파일 없음, path={db_filename}'

            if ht_result['wetax_paid_yn'] != 'Y':
                if ht_result['result5'] : #and ht_result['result4']:
                    v_file_type = "WE_DOWN_5"
                    db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{ht_result['result5']}"
                    #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
                    if os.path.exists(db_filename):
                        ret, ops = check_pdf_content(ht_result, db_filename, v_file_type, logger_d, logger_s)
                        위택스_납부번호 = get_op_value(ops, '위택스_납부번호')
                        위택스_납부세액 = get_op_value(ops, '위택스_납부세액')
                        if not ret: 
                            msg += f'\n {v_file_type} 분석내용 불일치'                    
                    else:
                        msg += f'\n {v_file_type} 파일 없음, path={db_filename}'


            # ----------------------------------------------------------------------
            # 문서간 값 비교
            # ----------------------------------------------------------------------
            #if ht_result['data_type'] == 'AUTO' :
            #    if ht_result['hometax_reg_num'].replace("-", "").strip() != 홈택스_접수번호.replace("-", ""):
            #        msg += f"\n 홈택스_접수번호 비교 오류={ht_result['hometax_reg_num'].replace('-', '')}:{홈택스_접수번호.replace('-', '')}"

            # 홈택스, 위택스 세액 비교 => 10분의1 인지 검사
            if ht_result['data_type'] == 'SEMI':
                if ht_result['hometax_paid_yn'] != 'Y' and ht_result['wetax_paid_yn'] != 'Y':
                    if abs((홈택스_납부세액 + 홈택스_납부세액2) // 10 - 위택스_납부세액) > 9:
                        msg += f'\n 홈택스,위택스 세액비교 오류'

            if msg:
                update_HtTt_audit_au7(ht_tt_seq, 'E', msg)

                # 로그 출력
                logger_d.info('-' * 30)
                logger_d.info(f"ht_tt_seq={ht_tt_seq}, {ht_result['holder_nm']}, {ht_result['holder_ssn1']}{ht_result['holder_ssn2']}")
                logger_d.info(msg)

                logger_s.info('-' * 30)
                logger_s.info(f"ht_tt_seq={ht_tt_seq}, {ht_result['holder_nm']}, {ht_result['holder_ssn1']}{ht_result['holder_ssn2']}")
                logger_s.info(msg)
            else:
                update_HtTt_audit_au7(ht_tt_seq, 'S', '')

        except Exception as e:
            print(f"{e}")
            ...

def get_op_value(ops, title, is_to_int = True):
    for pdf_item in ops:
        if pdf_item.title == title:
            if is_to_int:
                return to_number(pdf_item.val)
            else:
                return pdf_item.val


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
    print(f'평균 자료건수 = {total // thread_count}')

    if total == 0:
        print("검색 자료가 없어 종료합니다.")
        return

    # 주어진 배열을 작업들로 분할
    thread_data = split_tasks(ht_tt_seq_list, thread_count)

    # 작업들을 처리하는 함수 호출
    print(f"쓰레드 수={thread_count}, 데이터 분할 결과 = {thread_data}")


    # 실제 작업 진행
    #return
    execute_tasks(thread_data, thread_count)


def main2(ht_tt_seq_s, ht_tt_seq_e, idx):
    task = (ht_tt_seq_s, ht_tt_seq_e, idx)
    do_thread_job(task)

if __name__ == "__main__":
    ht_tt_seq_s = sys.argv[1]
    ht_tt_seq_e = sys.argv[2]
    idx = sys.argv[3]

    if ht_tt_seq_s and ht_tt_seq_e:
        main2(ht_tt_seq_s, ht_tt_seq_e, idx)
    else:
        print("파라미터 = 시작, 끝")
