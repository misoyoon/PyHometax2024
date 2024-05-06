from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTPage, LTChar
import sys, os

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

# Logger 설정
CUR_CWD = os.getcwd()
current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")

# 점검용 임시 생성 로그
AUDIO_LOG_DIR     = "V:/PyHometax_Log_2024/Audio"

# 로그 폴더 생성
os.makedirs(f"{AUDIO_LOG_DIR}", exist_ok=True)

log_filename_d = f"{AUDIO_LOG_DIR}/PDF점검_{now}_detail.log"
log_filename_s = f"{AUDIO_LOG_DIR}/PDF점검_{now}_summary.log"
logger_d = set_logger(log_filename_d)
logger_s = set_logger(log_filename_s)




check_list = {
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
                {'x': 267, 'y': 186, 'is_set':False, 'val': '', 'title':'가상계좌1',          'filter':''},  # 10글자(전국공통(지방세입)) 넘으면 가상계좌가 있는 것으로 판단
                {'x': 441, 'y': 186, 'is_set':False, 'val': '', 'title':'가상계좌2',        'filter':''} # 25글자(41463-1-95-24-4-0003813-1) 넘으면 가상계좌가 있는 것으로 판단
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

def parse_doc1_홈택스_신고서(pdf_file, pdf_type_name, page=1):
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
                    #if text == '10,081,082':
                    #    print(f'찾는 단어를 찾았음 : {op.text} => {text}')

                    for op in check_list[pdf_type_name]:
                        if op['is_set']: continue
                        
                        if cur_x1 <= op['x'] and op['x'] <= cur_x2 and cur_y1 <= op['y'] and op['y'] <= cur_y2 :
                            op['is_set'] = True
                            if op['filter']:
                                op['val'] = text.replace(op['filter'], '').strip()
                            else:
                                op['val'] = text
                                
                    
                    
                    if text.replace(' ', '').find("143127") >=0 :
                        print(f'{text} ==>  {cur_x1},{cur_x2},{cur_y1},{cur_y2} => ( {(cur_x1+cur_x2)/2}, {(cur_y1+cur_y2)/2} )')

                except Exception as e:
                    print(f'### ERROR ###  Except: 검색오류 : {e} => {element}')    

        if isFound: break
        
    for op in check_list[pdf_type_name]:            
        logger_d.info(f"{pdf_type_name} : {op['title']} : {op['is_set']} => [{op['val']}]")

#pdf_file = 'test_data\\down1.pdf'
#parse_doc1_홈택스_신고서(pdf_file, '1_홈택스_신고서')

#pdf_file = 'test_data\\down2.pdf'
#parse_doc1_홈택스_신고서(pdf_file, '2_홈택스_계산명세서')

#pdf_file = 'test_data\\down3.pdf'
#parse_doc1_홈택스_신고서(pdf_file, '3_홈택스_접수증')

#pdf_file = 'test_data\\down4.pdf'
#parse_doc1_홈택스_신고서(pdf_file, '4_홈택스_납부서')


#pdf_file = 'test_data\\위택스_신고서_박승기.pdf'
#parse_doc1_홈택스_신고서(pdf_file, '6_위택스_신고서')

conn = dbjob.connect_db()
def main():
    ht_tt_seq = 40112
    ht_info = dbjob.select_htTt_by_key(ht_tt_seq)
    #print(ht_info)
    
    file_info = dbjob.select_download_file_info(ht_tt_seq)
    #print(file_info)
    
    dir_work = ht_file.get_dir_by_htTtSeq('the1', ht_tt_seq, True)  # True => 폴더 생성

    v_file_type = ''
    
    if file_info['result1'] :
        v_file_type = "HT_DOWN_1"
        db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{file_info['result1']}"
        #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        if os.path.exists(db_filename):
            parse_doc1_홈택스_신고서(db_filename, v_file_type)

    if file_info['result2'] :
        v_file_type = "HT_DOWN_2"
        db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{file_info['result2']}"
        #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        if os.path.exists(db_filename):
            parse_doc1_홈택스_신고서(db_filename, v_file_type)

    if file_info['result3'] :
        v_file_type = "HT_DOWN_3"
        db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{file_info['result3']}"
        #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        if os.path.exists(db_filename):
            parse_doc1_홈택스_신고서(db_filename, v_file_type)

    if file_info['result4'] :
        v_file_type = "HT_DOWN_4"
        db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{file_info['result4']}"
        #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        if os.path.exists(db_filename):
            parse_doc1_홈택스_신고서(db_filename, v_file_type)

    if file_info['result8'] :
        v_file_type = "HT_DOWN_8"
        db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{file_info['result8']}"
        #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        if os.path.exists(db_filename):
            parse_doc1_홈택스_신고서(db_filename, v_file_type)

    if file_info['result5'] :
        v_file_type = "WE_DOWN_5"
        db_filename = f"{config.FILE_ROOT_DIR_BASE}the1\\{file_info['result5']}"
        #fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        if os.path.exists(db_filename):
            parse_doc1_홈택스_신고서(db_filename, v_file_type)



if __name__ == '__main__':    
    main()    