import time
import os
import PyPDF2

# --------------------------------------------
# PDF 내용 분석
# --------------------------------------------
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

import config
from common import *
import dbjob
import common_sele as sc
import ht_file

# --------------------------------------------
# 메일 발송 관련
# --------------------------------------------
import imghdr #이미지 첨부를 위한 라이브러리
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from email.header import Header
from email.mime.base import MIMEBase
from email.encoders import encode_base64

# STMP 서버의 url과 port 번호
SMTP_SERVER = 'mail.w.the1kks.com'
SMTP_PORT = 587

# --------------------------------------------
# 카카오 알림톡 관련
# --------------------------------------------
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import sample.sendATS_info_the1 as sendATS_info_the1
from popbill import KakaoService, PopbillException


# -------------------------------------------------------------
# (중요 공통) 아래의 모듈에서 step별 공통 기본 동작 실행
# -------------------------------------------------------------
import common_at_ht_step as step_common
auto_manager_id = step_common.auto_manager_id
conn = step_common.conn
AU_X = '6'
(driver, user_info, verify_stamp) = step_common.init_step_job()
group_id = 'the1'
# -------------------------------------------------------------


def do_task(auto_manager_id, group_id):
    at_info = dbjob.select_autoManager_by_id(auto_manager_id)
    worker_id       = at_info['worker_id']
    verify_stamp    = at_info['verify_stamp'] # 최초 시작시의 stamp

    kakao_TAX_EMAIL   = dbjob.select_kakao_template(group_id, 'TAX_EMAIL')
    kakao_NOTAX_EMAIL = dbjob.select_kakao_template(group_id, 'NOTAX_EMAIL')
    
    # 작업자 정보 조회
    worker_info = dbjob.get_worker_info(worker_id)
    
    # GROUP INFO
    group_info = dbjob.select_group_info(group_id)
    
    job_cnt = 0
    while True:
        job_cnt += 1
        
        # AutoManager 상태 판단 (매 건 처리마다 상태 확인)
        at_info = dbjob.select_autoManager_by_id(auto_manager_id)

        # 홈택스 작업1단계 
        au_x            = at_info['au_x']
        status_cd       = at_info['status_cd']
        worker_id       = at_info['worker_id']
        worker_nm       = at_info['worker_nm']
        group_id        = at_info['group_id']
        seq_where_start = at_info['seq_where_start']
        seq_where_end   = at_info['seq_where_end']
        verify_stamp2   = at_info['verify_stamp']  # 작업시작시의 verify_stamp와 비교하여 상태 변경 여부 확인 
        
        if verify_stamp == verify_stamp2:
            if status_cd == 'RW':
                # AUTO_MANGER: RUN
                dbjob.update_autoManager_statusCd(auto_manager_id, 'R')
            elif status_cd == 'SW' or status_cd == 'S':                 
                logt(f'Agent Check : Status={status_cd} ==> 작업 중지') 
                if status_cd == 'SW':
                    dbjob.update_autoManager_statusCd(auto_manager_id, 'S')
                return
        else:
            logt("verify_stamp 변경으로 STOP 합니다.")
            dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'verify_stamp 변경으로 STOP 합니다.')
            return

        # 고객 통보 자료 가져오기 (6단계)
        ht_info = dbjob.select_next_au6(group_id, worker_id, seq_where_start, seq_where_end)

        if not ht_info:
            logt("처리할 자료가 없어서 FINISH 합니다. ==> 작업 중지")
            dbjob.update_autoManager_statusCd(auto_manager_id, 'F', '처리할 자료가 없어서 FINISH 합니다.')
            return

        #담당자 전화번호 추가
        ht_info['worker_tel'] = worker_info['tel']
        ht_info['worker_nm'] = worker_info['name']
        
        ht_tt_seq          = ht_info['ht_tt_seq']
        notify_type_cd     = ht_info['notify_type_cd']
        

        # TODO 개발 편의로 임시 주석처리
        # 신고건 진행표시 : au1 => R
        #dbjob.update_htTt_aux_running(ht_tt_seq, au_x)
        

        #dbjob.delete_auHistory_byKey(ht_tt_seq, au_x)
        
        logt("******************************************************************************************************************")
        logt("AUX=%s, JOB_COUNT=%s : 양도인=%s, HT_TT_SEQ=%d" % (au_x, job_cnt, ht_info['holder_nm'], ht_info['ht_tt_seq']))
        logt("******************************************************************************************************************")

        #base_dir = ht_file.get_root_dir(group_id)
        #pdf_file = ht_file.get_dir_by_htTtSeq(group_id, ht_tt_seq)
        
        PDF_병합_성공 = False
        메일_발송_성공 = False
        문자_발송_성공 = False

        try:
            # --------------------------------------------------------------
            # PDF 병합
            # --------------------------------------------------------------
            #merged_pdf_filename = f'2023_the1_{ht_tt_seq}.pdf'
            merged_pdf_filename = f'2023년_해외주식_양도소득세_{ht_tt_seq}.pdf'
            (is_success, merged_pdf_path) = merge_pdf(ht_info, merged_pdf_filename)
            if is_success:
                logt(f"PDF병합 ==> 성공")
                PDF_병합_성공 = True
            else:
                e = merged_pdf_path  # 실패의 경우 Exception이 넘어옴

                loge(f"PDF병합오류 : {e}")
                raise Exception(f"PDF병합오류:{e}")


            # --------------------------------------------------------------
            # 메일 발송
            # --------------------------------------------------------------
            # EMAIL,  EMAIL2, EMAIL_SEC 일 경우 메일 발송
            if notify_type_cd.find('EMAIL') >= 0:  
                (is_success, result) = send_mail(merged_pdf_path, merged_pdf_filename, ht_info, worker_info)
                if is_success:
                    logt(f"메일 발송 ==> 성공")
                    dbjob.insert_smsHistory(result)
                    메일_발송_성공 = True
                else:
                    #dbjob.update_HtTt_AuX(au_x, ht_tt_seq, 'E', f'EMAIL 발송 오류={result}')
                    #continue
                    loge(f"메일 발송 오류 : {result}")
                    raise Exception("메일발송오류")
            

            # --------------------------------------------------------------
            # 카카오 알림톡 발송
            # --------------------------------------------------------------
            if notify_type_cd.find('EMAIL') >= 0:  # 고객 이메일 발송만 카카오 알림톡 발송
                (is_success, result) = send_kakao_message(ht_info, worker_info, group_info, kakao_TAX_EMAIL, kakao_NOTAX_EMAIL)
                if is_success:
                    logt(f"일림톡 발송 ==> 성공")
                    문자_발송_성공 = True
                    dbjob.insert_smsHistory(result)
                else:
                    loge(f"알림톡 발송 오류 : {result}")
                    raise Exception("알림톡발송오류")

        except Exception as e:
            logt(e)
            dbjob.update_HtTt_AuX(au_x, ht_tt_seq, 'E', f'{e}')
            dbjob.update_autoManager_statusCd(auto_manager_id, 'F', f'{e}')
            break
        else :
            dbjob.update_HtTt_AuX(au_x, ht_tt_seq, 'S')
            logt("======> 1건 정상처리")
            time.sleep(2)

# 카카오 알림톡 발송
def send_kakao_message(ht_info, worker_info, group_info, kakao_TAX_EMAIL, kakao_NOTAX_EMAIL):
    
    kakaoService                 = KakaoService(group_info['popbill_link_id'], group_info['popbill_secret_key'])
    kakaoService.IsTest          = False # 연동환경 설정값, 개발용(True), 상업용(False)
    kakaoService.IPRestrictOnOff = True  # 발급토큰 IP 제한기능 활성화 여부 (권장-True)
    kakaoService.UseStaticIP     = False # 팝빌 API 서비스 고정 IP 사용여부, true-사용, false-미사용, 기본값(false)
    kakaoService.UseLocalTimeYN  = True  # 로컬시스템 사용여부, 권장(True)
    
    ht_tt_seq = ht_info['ht_tt_seq']
    hometax_income_tax = ht_info.get('hometax_income_tax', 0)
    template_info = kakao_TAX_EMAIL if hometax_income_tax > 10 else kakao_NOTAX_EMAIL
    
    try:
        logt("알림톡 단건 전송 " + "="*15)

        # 팝빌회원 사업자번호("-"제외 10자리)
        CorpNum = group_info['biz_num']  # 팝빌회원 사업자번호

        # 팝빌회원 아이디
        UserID = group_info['popbill_link_id'].lower()  # the1tax

        # 승인된 알림톡 템플릿코드
        templateCode = template_info['template_cd']  #"023050000043"

        # 팝빌에 사전 등록된 발신번호
        snd = group_info['popbill_sender_num'].replace('-', '')  # "07047395596"

        # 알림톡 내용 (최대 1000자)
        # 사전에 승인된 템플릿의 내용과 알림톡 전송내용(content)이 다를 경우 전송실패 처리됩니다.
        content = template_info['content']
        content = content.replace('#{고객명}',       ht_info['holder_nm'])
        if ht_info['notify_type_cd'] == 'EMAIL_SEC':
            content = content.replace('#{고객이메일}',   ht_info['sec_email'])
        else:
            content = content.replace('#{고객이메일}',   ht_info['holder_email'])
        content = content.replace('#{담당자연락처}', worker_info['tel'])
        content = content.replace('#{담당자명}',     worker_info['name'])

        # 대체문자 제목
        # - 메시지 길이(90byte)에 따라 장문(LMS)인 경우에만 적용.
        altSubject = "해외주식 양도소득세 신고 결과 안내"

        # 대체문자 유형(altSendType)이 "A"일 경우, 대체문자로 전송할 내용 (최대 2000byte)
        # └ 팝빌이 메시지 길이에 따라 단문(90byte 이하) 또는 장문(90byte 초과)으로 전송처리
        altContent = content

        # 대체문자 유형 (None , "C" , "A" 중 택 1)
        # None = 미전송, C = 알림톡과 동일 내용 전송 , A = 대체문자 내용(altContent)에 입력한 내용 전송
        altSendType = "C"

        # 예약일시 (작성형식 : yyyyMMddHHmmss)
        sndDT = ""

        # 수신번호
        receiver = ht_info['holder_cellphone'].replace('-', '')   #"01036565574"

        # 수신자 이름
        receiverName = ht_info['holder_nm']

        # 전송요청번호
        # 파트너가 전송 건에 대해 관리번호를 구성하여 관리하는 경우 사용.
        # 1~36자리로 구성. 영문, 숫자, 하이픈(-), 언더바(_)를 조합하여 팝빌 회원별로 중복되지 않도록 할당.
        timestampe = time.time()
        requestNum = f'{str(int(timestampe))}_{ht_tt_seq}' 

        # 알림톡 버튼정보를 템플릿 신청시 기재한 버튼정보와 동일하게 전송하는 경우 btns를 빈 배열로 처리.
        btns = []

        # 알림톡 버튼 URL에 #{템플릿변수}를 기재한경우 템플릿변수 값을 변경하여 버튼정보 구성
        # btns.append(
        #     KakaoButton(
        #         n="템플릿 안내",  # 버튼명
        #         t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
        #         u1="https://www.popbill.com",  # [앱링크-iOS, 웹링크-Mobile]
        #         u2="http://www.popbill.com"  # [앱링크-Android, 웹링크-PC URL]
        #     )
        # )
        receiptNum = ''
        if True:
            receiptNum = kakaoService.sendATS(
                CorpNum,
                templateCode,
                snd,
                content,
                altContent,
                altSendType,
                sndDT,
                receiver,
                receiverName,
                UserID,
                requestNum,
                btns,
                altSubject,
            )
        logt("접수번호 (receiptNum) : %s" % receiptNum)

        sms_history = {
            'group_id' : ht_info['group_id'],
            'fk_seq' : ht_tt_seq,
            'req_source' : 'HTTT',
            'sms_type' : 'KAKAO', 
            'sender_num' : snd,
            'receiver_num': receiver, 
            'receiver_name' : receiverName,
            'content' : content,
            'reserve_dt' : None, 
            'sender_source' : 'A', 
            'ads_yn' : 'N', 
            'request_num' : requestNum, 
            'receipt_num' : receiptNum, 
            'reg_id' : ht_info['reg_id']
        }
        
        return True, sms_history
    except PopbillException as pe:
        logt("Exception Occur : [%d] %s" % (pe.code, pe.message))
        return False, pe

# 문서 파일을 하나의 PDF로 병합하기
def merge_pdf(ht_info, merged_pdf_filename):
    group_id  = ht_info['group_id']
    ht_tt_seq = ht_info['ht_tt_seq']
    base_dir   = ht_file.get_root_dir(group_id)
    work_dir = ht_file.get_work_dir_by_htTtSeq(group_id, ht_tt_seq)

    merged_pdf_path = f'{work_dir}{merged_pdf_filename}'
    
    if os.path.exists(merged_pdf_path) and os.path.isfile(merged_pdf_path):
        logt(f"통합PDF 파일삭제(재작업준비): {merged_pdf_path}")
        os.remove(merged_pdf_path)

    try:
        pdf_list = []
        row = dbjob.select_download_file_list_by_htTtSeq(ht_tt_seq)
        
        file_list = ['result1', 'result2', 'result3', 'result4', 'result8', 'result5']
        
        
        # if row['result1'] and os.path.exists(base_dir + row['result1']):
        #     pdf_list.append(base_dir + row['result1'])
        # if row['result2'] and os.path.exists(base_dir + row['result2']): 
        #     pdf_list.append(base_dir + row['result2'])
        # if row['result3'] and os.path.exists(base_dir + row['result3']): 
        #     pdf_list.append(base_dir + row['result3'])
        # if row['result4'] and os.path.exists(base_dir + row['result4']): 
        #     pdf_list.append(base_dir + row['result4'])
        # if row['result8'] and os.path.exists(base_dir + row['result8']): 
        #     pdf_list.append(base_dir + row['result8'])
        # if row['result5'] and os.path.exists(base_dir + row['result5']): 
        #     pdf_list.append(base_dir + row['result5'])
            
        
        logt(f"통합PDF 생성 : {merged_pdf_path}")
        pdfWriter = PyPDF2.PdfWriter()
        for result_x in file_list:
            if row[result_x]:
                pdf_path = base_dir + row[result_x]
                if os.path.exists(pdf_path):
                    logt(f"   통합할 PDF : {pdf_path}")
                    with open(pdf_path, 'rb') as pdfFile:
                        pdfReader = PyPDF2.PdfReader(pdfFile)
                        for pdf_page in pdfReader.pages:
                            pdfWriter.add_page(pdf_page)
                else:
                    err = f"통합 PDF 파일 없음 : {pdf_path}"
                    loge(err)
                    return False, err

        pdfWriter.encrypt(ht_info['holder_ssn1'])
        with open(merged_pdf_path, 'wb') as resultPdf:
            pdfWriter.write(resultPdf)

        if os.path.exists(merged_pdf_path) and os.path.isfile(merged_pdf_path):
            ...  #정상 확인
        else:
            err = f"통합PDF 생성 확인불가: {merged_pdf_path}"
            loge(err)
            return False, err            

        return True, merged_pdf_path
    except Exception as e:
        logt(f'통합PDF 생성 오류 : {e}')
        return False, e
    

# 메일 내용 템블릿 읽기    
def read_mail_template(group_id, mail_type):
    file_path = f'{os.getcwd()}\\pyHometax\\mail_template\\{group_id}\\mail_{mail_type}_2023.html'
    logt(file_path)
    with open(file_path, 'r', encoding="utf-8") as f:
        data = f.read()
        #logt(data)
        f.close()
        return data
    return None



def send_mail(attach_file_path, attach_filename, ht_info, worker_info):
    #EMAIL_ADDR = 'the1tax_1@the1kks.com'
    EMAIL_PASSWORD = 'kksjns1203!'

    title = '2023년 귀속 해외주식 양도소득세 신고 결과 안내'
    
    group_id        = ht_info['group_id']
    notify_type_cd  = ht_info['notify_type_cd']

    hometax_income_tax = ht_info.get('hometax_income_tax', 0)  # 10원보다 크면 세금이 있는 상태
    
    type = 'tax' if hometax_income_tax >= 10 else 'notax'
    content = read_mail_template(group_id, type)
    content = content.replace("<<고객>>",     ht_info['holder_nm'])
    content = content.replace("<<전화번호>>", worker_info['tel'])
    content = content.replace("<<담당자>>",   worker_info['name'])

    #from_addr = worker_info['email']
    from_addr = "no-reply@the1kks.com"
    
    # 받는 사람 email => EMAIL, EMAIL_SEC 두개의 경우 존재
    to_addr = ht_info['holder_email'] 
    if notify_type_cd == "EMAIL_SEC" and ht_info['sec_email']:
        to_addr = ht_info['sec_email']

    # 증권사 담당자에게 메일 발송 (히든 참조 bcc)
    bcc_addr = ht_info['sec_email'] if notify_type_cd == "EMAIL2" and ht_info['sec_email'] else None

    try:
        # 1. SMTP 서버 연결
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.ehlo()
        smtp.starttls()
        # 2. SMTP 서버에 로그인
        smtp.login(from_addr, EMAIL_PASSWORD)

        # 3. MIME 형태의 이메일 메세지 작성
        message = MIMEMultipart()
        html = MIMEText(content, 'html')
        message.attach(html)
        message["Subject"] = Header(s=title, charset='utf-8')
        message["From"] = from_addr  #보내는 사람의 이메일 계정
        message["To"]   = to_addr
        message["Cc"]   = "info@the1kks.com"
        if bcc_addr:
            message["Bcc"] = bcc_addr

        #4. 첨부파일
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(attach_file_path, 'rb').read())
        encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=attach_filename)
        message.attach(part)

        # 5. 서버로 메일 보내기
        smtp.send_message(message)

        # 5. 메일을 보내면 서버와의 연결 끊기
        smtp.quit()
        
        timestampe = time.time()
        requestNum = f"{str(int(timestampe))}_{ht_info['ht_tt_seq']}"
        
        # 받는 사람이 복수인 경우 대비 (증권사PB이 포함될 경우)
        receiver_num = to_addr
        if bcc_addr:
            receiver_num = to_addr + ';' + bcc_addr
        
        
        sms_history = {
            'group_id' : ht_info['group_id'],
            'fk_seq' : ht_info['ht_tt_seq'],
            'req_source' : 'HTTT',
            'sms_type' : 'MAIL', 
            'sender_num' : from_addr,
            'receiver_num': receiver_num, 
            'receiver_name' : ht_info['holder_nm'],
            'content' : type + ' 타입의 메일 발송',
            'reserve_dt' : None, 
            'sender_source' : 'A', 
            'ads_yn' : 'N', 
            'request_num' : requestNum, 
            'receipt_num' : None, 
            'reg_id' : ht_info['reg_id']
        }

        return True, sms_history
    except Exception as e:
        logt(f'메일 발송 오류 : {e}')
        return False, e


if __name__ == '__main__':
    do_task(auto_manager_id, group_id) 
        
    logt("프로그램 종료")

    if conn: 
        conn.close()

    exit(0)    
