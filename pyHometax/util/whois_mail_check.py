import os
import email
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import re
import logging
import datetime
import pandas as pd
import json

# 로깅 설정
current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
log_filename = f"V:\\PyHometax_Log_2024\\WhoisMail\\{current_time}.log"
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_eml_details(file_path):
    with open(file_path, 'rb') as file:
        msg = BytesParser(policy=policy.default).parse(file)

    # 발송시간 추출 및 형식 변환
    send_time = msg['date']
    if send_time:
        send_time_dt = parsedate_to_datetime(send_time)
        local_time = send_time_dt + datetime.timedelta(hours=9)
        formatted_time = local_time.strftime('%Y%m%d%H%M%S')
    else:
        # 유효한 날짜 정보가 없는 경우 현재 시간을 사용
        local_time = datetime.datetime.now() + datetime.timedelta(hours=9)
        formatted_time = local_time.strftime('%Y%m%d%H%M%S')
        logging.warning(f"날짜 정보가 없어 현재 시간을 사용합니다: {file_path}")

    # 수신자 이메일 주소 추출
    to_email = msg['to']

    # 첨부파일명 추출 및 파일명 끝의 숫자 5개 추출
    attachments = []
    last_five_digits = []
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if filename:
            attachments.append(filename)
            # 파일명에서 정확히 숫자 5자리 추출
            digits = re.findall(r'\d{5}', filename)
            if digits:
                last_five_digits.extend(digits)

    return attachments, last_five_digits, to_email, formatted_time

from collections import defaultdict

def process_directory(directory):
    results = defaultdict(list)  # defaultdict를 사용하여 자동으로 리스트 초기화
    for index, filename in enumerate(os.listdir(directory), start=1):
        print(f"{index} ... {filename}")
        if filename.endswith('.eml'):
            file_path = os.path.join(directory, filename)
            attachments, last_five_digits, to_email, send_time = extract_eml_details(file_path)
            for digit in last_five_digits:
                entry = {
                    'index': index,
                    'digit': digit,
                    'attachments': attachments,
                    'to_email': to_email,
                    'send_time': send_time,
                    'filename': filename
                }
                results[digit].append(entry)  # 동일한 digit에 대해 리스트에 추가
        
        #if index>10 : break
    return results



# 결과를 JSON 형식으로 변환하고 pretty print
def print_pretty_results(results):
    json_string = json.dumps(results, indent=4, ensure_ascii=False)
    logging.info(json_string)



def save_results_to_excel(results):
    # 현재 시간을 파일명에 사용
    current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"V:\\PyHometax_Log_2024\\WhoisMail\\email_list_{current_time}.xlsx"
    
    # 모든 결과를 하나의 리스트로 변환
    all_entries = []
    for digit_entries in results.values():
        all_entries.extend(digit_entries)
    
    # 리스트를 DataFrame으로 변환
    df = pd.DataFrame(all_entries)
    
    # Excel 파일로 저장
    df.to_excel(filename, index=False, engine='openpyxl')




# 디렉토리 경로
directory_path = 'E:\\Temp\\whois_mail\\info'
results = process_directory(directory_path)

# 결과를 Excel 파일로 저장
save_results_to_excel(results)

# 결과를 pretty하게 출력
print_pretty_results(results)