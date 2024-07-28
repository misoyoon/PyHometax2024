import sys, os
import glob

from typing import List, Dict, Set, Final, Any
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTPage, LTChar

#from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from datetime import datetime
#from PdfParse import *

import shutil

import config
from common import *
import dbjob
import common_sele as sc
import ht_file


import warnings
warnings.simplefilter('ignore')

group_id = 'the1'

current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")
log_filename = f"LOG\\업로드PDF병합_{now}.log"
logger = set_logger(log_filename)


conn = dbjob.connect_db()
        
def main():
    rs = dbjob.select_HtTt_증빙자료업로드_PDF병합(group_id)
    logger.info(f"자료 건수={len(rs)}")
    seq = 0
    for index, htTt in enumerate(rs):
        ht_tt_seq = htTt['ht_tt_seq']
        work_dir = ht_file.get_work_dir_by_htTtSeq(group_id, ht_tt_seq)

        upload_pdf = f"{work_dir}source_upload.pdf"
        #print (f'upload_pdf= {upload_pdf}')
        

        # 파일이 존재하는지 확인하고, 존재하면 삭제
        if os.path.exists(upload_pdf):
            os.remove(upload_pdf)

        # 패턴에 맞는 파일 목록 찾기
        file_pattern = os.path.join(work_dir, 'source*.pdf')
        pdf_file_list_from = glob.glob(file_pattern)

        try:
            # PDF 업로드용 PDF 통합하기
            if len(pdf_file_list_from) == 1:
                # 하나이기 때문에 그대로 옮기기
                pdf_file = pdf_file_list_from[0]
                shutil.copy(pdf_file, upload_pdf)
            else:
                # 2개 이상으로 하나로 통합하기
                mergeFile  = PdfMerger()
                for pdf_file in pdf_file_list_from:
                    input1 = PdfReader(pdf_file, 'rb')
                    mergeFile.append(input1)
                
                mergeFile.write(upload_pdf)
            
            file_size_bytes = os.path.getsize(upload_pdf)
            file_size_kb = round(file_size_bytes / 1024)

            over_50_mb = ''
            if file_size_kb > 49_000:
                over_50_mb = ' <<<==================  50메가 넘음'

            logger.info(f"i={index} ht_tt_seq={ht_tt_seq} :: {upload_pdf},  파일개수={len(pdf_file_list_from)}, size= {file_size_kb} KB  {over_50_mb}")

        except Exception as e:
            err_msg =f"PDF통합 오류 index={index},  ht_tt_seq={ht_tt_seq}  : {e}"
            logger.error(err_msg)

        # 테스트용
        # if seq > 3: break  
        

main()

logger.info('...끝')
