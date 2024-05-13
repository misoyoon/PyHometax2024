from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import time
import math
import subprocess

import pyautogui
import pyperclip

import pymysql

from common import *
import dbjob
#import common_sele as sc
import ht_file


#마우스가 모니터 사각형 모서리에 가는 경우 발생하는 에러이다
pyautogui.FAILSAFE = False

IMAGE_SEARCH_TRY_COUNT = 10
RETRY_SLEEP_TIME = 0.5
CONFIDENCE = 0.8

#브라우저 확인을 위해 맨바닥 단순 클릭 위치
CHECK_POINT = (100, 300)

project_dir = os.path.dirname(sys.modules['__main__'].__file__)
IMAGE_DIR = project_dir + "/resource2"
# -------------------------------------------------------------
# (중요 공통) 아래의 모듈에서 step별 공통 기본 동작 실행
# -------------------------------------------------------------
import common_at_ht_step as step_common
auto_manager_id = step_common.auto_manager_id
conn = dbjob.connect_db()
AU_X = '2'
# -------------------------------------------------------------
(driver, user_info, verify_stamp) = step_common.init_step_job()


def image_moveTo(image_file, sleep=0.5, retry=2, offset_x = 0, offset_y = 0):
    time.sleep(sleep)
    image_position = pyautogui.locateCenterOnScreen(image_file, confidence=CONFIDENCE)
    if image_position:
        # 이미지의 중앙 좌표에서 위로 10px 이동한 위치 계산
        click_point = (image_position[0]- offset_x, image_position[1] - offset_y)
        pyautogui.moveTo(image_position)
        return True
    else:
        logt("     <----- 이미지를 찾을 수 없습니다.")
        return False

def image_click(image_file, sleep=1, retry=2, offset_x=0, offset_y=0):
    logt(f"    이미지클릭 : {image_file}, time={sleep}")
    time.sleep(sleep)
    
    found_position = None
    for i in range(1, IMAGE_SEARCH_TRY_COUNT+1):
        image_position = pyautogui.locateCenterOnScreen(image_file, confidence=CONFIDENCE)
        if image_position:
            # 이미지의 중앙 좌표에서 위로 10px 이동한 위치 계산
            click_point = (image_position[0]+offset_x, image_position[1]+offset_y)
            pyautogui.click(click_point)
            logt(f"        try {i} ===> 성공")
            found_position = click_point
            break
        else:
            logt(f"        try {i} ===> 실패")
            
        time.sleep(RETRY_SLEEP_TIME)
    
    time.sleep(RETRY_SLEEP_TIME)
    return found_position


def image_find(image_file, sleep=0.5):
    logt(f"    이미지 찾기 : {image_file}, time={sleep}")
    time.sleep(sleep)
    
    found_position = None
    for i in range(1, IMAGE_SEARCH_TRY_COUNT+1):
        image_position = pyautogui.locateCenterOnScreen(image_file, confidence=CONFIDENCE)
        if image_position:

            logt(f"        try {i} ===> 성공")
            found_position = image_position
            break
        else:
            logt(f"        try {i} ===> 실패")
            
        time.sleep(RETRY_SLEEP_TIME)
    
    time.sleep(RETRY_SLEEP_TIME)
    return found_position

def image_sendkey(copy_str, image_file, sleep=0.5, retry=2, offset_x=0, offset_y=0):
    ret = image_click(image_file, offset_x, offset_y)
    if ret:
        try:
            # 붙여넣기 (Ctrl + V)
            #pyperclip.copy(copy_str)
            #pyautogui.hotkey('ctrl', 'v')
            pyautogui.typewrite(copy_str, interval=0.1)

            time.sleep(0.5)  # 복사가 완료될 때까지 대기
            
            return True
        except Exception as e:
            logt(f"{e}")
            return False
    else:
        return False

def image_clear_sendkey(copy_str, image_file, sleep=0.5, retry=2, offset_x=0, offset_y=0):
    logt(f"    이미지영역 => 문자입력 : {image_file}, time={sleep}")
    time.sleep(sleep)
    image_position = pyautogui.locateCenterOnScreen(image_file, confidence=CONFIDENCE)
    if image_position:
        # 이미지의 중앙 좌표에서 위로 10px 이동한 위치 계산
        click_point = (image_position[0]+offset_x, image_position[1]+offset_y)
        #더블클릭
        pyautogui.click(x=click_point[0], y=click_point[1], clicks=2)
        time.sleep(0.1)
        pyautogui.press('back')
        time.sleep(0.1)
        pyautogui.typewrite(copy_str, interval=0.0)

        time.sleep(0.5)  # 복사가 완료될 때까지 대기
        
        return True
    else:
        return False

def which_image_found(image_file_list, after_enter=False, sleep=0.5):
    logt(f"    이미지영역 고르기")
    time.sleep(sleep)
    
    ret = -1
    for idx, image_file in enumerate(image_file_list):
        image_position = pyautogui.locateCenterOnScreen(image_file, confidence=CONFIDENCE+0.5)
        if image_position:
            logt(f"        {idx} <=== fount")
            ret = idx
            break
        else:
            logt(f"        {idx}")
            
    if after_enter:
        time.sleep(0.1)
        pyautogui.press('enter')
        
    return ret

def go_search_page():
    time.sleep(0.5)
    pyautogui.click(CHECK_POINT)
    
    
    try:
        # 상단 이동
        pyautogui.press('home')
        time.sleep(0.5)
        
        # pyautogui.press('end')
        # time.sleep(3)
        
        # logt('주민번호 입력')
        # image_path = f"{IMAGE_DIR}/04_ssn.png" # 주민번호 입력
        # image_sendkey('0409234229944', image_path, 2)
        
        
        
        logt('메인페이지')
        image_path = f"{IMAGE_DIR}/00.main_hometax.png"
        if not image_click(image_path):
            return False
        
        logt('세금신고')
        image_path = f"{IMAGE_DIR}/01_tax_report.png" # [세금신고]
        if not image_moveTo(image_path, sleep=3):
            return False

        logt('확정신고')
        image_path = f"{IMAGE_DIR}/02_fix_report.png" # [확정신고]
        if not image_click(image_path, sleep=2):
            return False

        logt('신고내역 조회(접수증,납부서)')
        image_path = f"{IMAGE_DIR}/03_report_list.png" # [신고내역 조회(접수증,납부서)]
        if not image_click(image_path, sleep=3):
            return False
        
        return True
    except:
        ...
        return False

def copy_screen_text(image_path, offset_x=0, offset_y=0):
    click_point = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE)
    
    if click_point:
        try:
            #더블클릭
            pyautogui.click(x=click_point[0]+offset_x, y=click_point[1]+offset_y, clicks=2)    
            pyautogui.hotkey('ctrl', 'c')
            str = pyperclip.paste()
            if str:
                logt(f"    복사하기 성공: {str}")
                return str
            else:
                logt(f"    복사하기 실패 1")
                return False
        except Exception as e:
            logt(f"화면 copy 중 오류 발생 : {e}")
    else:
        logt(f"    복사하기 실패 1")
        return False
    
def do_step2_loop(ht_info):
    ht_tt_seq = ht_info['ht_tt_seq']
    ssn =  f"{ht_info['holder_ssn1']}{ht_info['holder_ssn2']}"

    if False:
        pyautogui.click(CHECK_POINT)
        
        time.sleep(3)
        pyautogui.press('end')
        #time.sleep(3)
        
        logt(f'주민번호 입력 = {ssn}')
        image_path = f"{IMAGE_DIR}/04_ssn.png" # 주민번호 입력
        image_clear_sendkey(ssn, image_path, offset_x=100)
        
        time.sleep(1)
        logt('조회하기')
        image_path = f"{IMAGE_DIR}/05_btn_search.png" # 조회하기
        if not image_click(image_path):
            return   
        

        logt("조회 결과 확인하기")
        image_path_list = [ f"{IMAGE_DIR}/06_result_fail.png", f"{IMAGE_DIR}/06_result_success.png"]
        ret = which_image_found(image_path_list, after_enter=True, sleep=1)
        logt(f"조회 결과: {ret}")
        if ret >= 0:
            time.sleep(1)
            # 검색 건수 일치 여부 확인
            image_path = f"{IMAGE_DIR}/07_result_count_1.png"
            image_position = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
            if image_position:
                logt("     검색 건수 = 1  (정상)")
                
                # 주민번호 비교
                # image_path = f"{IMAGE_DIR}/08_column_ssn.png"
                # ssn1  = copy_screen_text(image_path, offset_x=0, offset_y=35)
                # if ht_info['holder_ssn1'] != ssn1:
                #     logt(f"주민번호 불일치 : 화면 ssn1={ssn1}")
                #     return

            else:
                logt("     검색 건수가 1이 아닙니다.")
                return
            
        else:
            logt("    신고된 내역이 없습니다.")
            return
    
    
    # -----------------------------------------------
    # 파일 다운로드 타입 1
    # -----------------------------------------------
    if False:
        logt('접수번호 클릭 => 팝업 (type1, type2 다운로드 준비)')
        image_path = f"{IMAGE_DIR}/08_column_1.png"
        if not image_click(image_path, offset_y=50, sleep=0.5):
            return

        logt('개인정보 공개 여부')
        image_path = f"{IMAGE_DIR}/win_01_chk_privacy.png"
        if not image_click(image_path, offset_x=20, sleep=3):
            return
        
        logt('적용 클릭')
        image_path = f"{IMAGE_DIR}/win_01_btn_apply.png"
        if not image_click(image_path):
            return

        download_file(ht_info, "HT_DOWN_1")
    
    # -----------------------------------------------
    # 파일 다운로드 타입 : 주식등 양도소득금액 계산명세서
    # -----------------------------------------------
    if False:
        logt('주식등 양도소득금액 계산명세서 클릭')
        image_path = f"{IMAGE_DIR}/win_01_doc2.png"
        if not image_click(image_path, sleep=0.5):
            return
        
        time.sleep(3)
        
        download_file(ht_info, "HT_DOWN_2")
        
        image_path = f"{IMAGE_DIR}/win_01_btn_close.png"
        if not image_click(image_path, sleep=1):
            return

    # -----------------------------------------------
    # 파일 다운로드 타입 : 접수증
    # -----------------------------------------------
    if False:
        logt('접수증 클릭')
        image_path = f"{IMAGE_DIR}/08_column_2.png"
        if not image_click(image_path, sleep=0.5):
            return

        if download_file(ht_info, "HT_DOWN_3"):
            # 인쇄팝업 창닫기
            image_path = f"{IMAGE_DIR}/alt_f4_down3.png"
            if not send_alt_f4(image_path):
                return
    
    # -----------------------------------------------
    # 파일 다운로드 타입 : 납부서
    # -----------------------------------------------    
    if True:
        # 납부여부 확인
        image_path_list = [ f"{IMAGE_DIR}/08_column_paid_n.png", f"{IMAGE_DIR}/08_column_paid_y.png"]
        ret = which_image_found(image_path_list, after_enter=False, sleep=0.5)
        logt(f"납부완료 조회 결과: {ret}  | 0=미납, 1=납부완료")
        if ret == 0:
            logt("     미납상태")
            
            # 납부서 클릭  ==>  팝업 호출됨

            image_path = f"{IMAGE_DIR}/08_column_3.png"
            image_position = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE)
            if image_position:
                logt("     [납부서보기]버튼 노출상태  ==> 클릭")
                image_path = f"{IMAGE_DIR}/08_column_3.png"
                if not image_click(image_path, sleep=0.5):
                    return
                
                time.sleep(2)
                            
                image_path_list = [ f"{IMAGE_DIR}/10_payment_0.png",   #일반 1개
                                    f"{IMAGE_DIR}/10_payment_1.png",]  #분납있는 경우
                ret = which_image_found(image_path_list, after_enter=False, sleep=0.5)
                # 0 <-- 0 ~ 천만
                # 1 분납
                logt(f"분납 있는지 조회 결과: {ret}  | 0=일반, 1=분납있음")
                if ret == 0 : 
                    # 일반적인 납부서 1개
                    logt('일반적인 납부서 1개')
                    image_path = f"{IMAGE_DIR}/10_payment_0.png"
                    if not image_click(image_path, sleep=0.0):
                        return
                    
                    if download_file(ht_info, "HT_DOWN_4"):
                        # 인쇄팝업 창닫기
                        image_path = f"{IMAGE_DIR}/alt_f4_down4.png"
                        if not send_alt_f4(image_path):
                            return
                        
                    # [닫기] 버튼
                    image_path = f"{IMAGE_DIR}/11_btn_close.png"
                    if not image_click(image_path, sleep=0.0):
                        return
                        
                elif ret == 1:
                    logt('분납 납부서가 있는 경우')
                    # 1.납부서 -----------------------
                    image_path = f"{IMAGE_DIR}/10_payment_1.png"
                    if not image_click(image_path, sleep=0.0):
                        return

                    logt('첫번째 납부서')
                    if download_file(ht_info, "HT_DOWN_4"):
                        # 인쇄팝업 창닫기
                        image_path = f"{IMAGE_DIR}/alt_f4_down4.png"
                        if not send_alt_f4(image_path):
                            return

                    # 2.분납 납부서 -----------------------
                    image_path = f"{IMAGE_DIR}/10_payment_2.png"
                    if not image_click(image_path, sleep=0.0):
                        return

                    logt('두번째 납부서')
                    if download_file(ht_info, "HT_DOWN_8"):
                        # 인쇄팝업 창닫기
                        image_path = f"{IMAGE_DIR}/alt_f4_down4.png"
                        if not send_alt_f4(image_path):
                            return                    

                    # [닫기] 버튼
                    logt('닫기 버튼 클릭')
                    image_path = f"{IMAGE_DIR}/11_btn_close.png"
                    if not image_click(image_path, sleep=0.0):
                        return

                else:
                    logt("FIXME :: 이 경우가 발생한다면 프로그램 수정 필요")
                    return
                
            else:
                logt("     납부서 링크 없음")   # <=========  없어도 정상 일 수 있음
        elif ret == 1:
            # 다시 한번 납부완료인지 검사
            image_path = f"{IMAGE_DIR}/08_column_paid_y.png"
            image_position = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE)
            if image_position:            
                logt(f"     납부완료 처리 ht_tt_seq={ht_tt_seq} <===========")
                dbjob.update_htTt_hometaxPaidYn(ht_tt_seq, 'Y')
            
        else:
            logt("납부여부는 반드시 N, Y여야 하나 찾을 수 없어 다음 건으로 건너뜀")
            return


    
        time.sleep(60)


    
def download_file(ht_info, v_file_type):
    try:
        logt('납부계산서의 프린트 이미지 클릭')
        group_id =  ht_info['group_id']
        ht_tt_seq = ht_info['ht_tt_seq']
        holder_nm = ht_info['holder_nm']   

        # file_type별 파일이름 결정
        dir_work = ht_file.get_dir_by_htTtSeq(group_id, ht_tt_seq, True)  # True => 폴더 생성
        fullpath = dir_work + ht_file.get_file_name_by_type(v_file_type)
        
        logt("------------------------------------------------------")
        logt("파일다운로드: Type: %s, Filepath: %s" % (v_file_type, fullpath))
        logt("------------------------------------------------------")

        # 이미 존재하면 삭제 (pdf 다운로드시 이미 존재하면 덮어쓰기 하겠냐고 질문하는 것을 회피 하기위해)
        if os.path.isfile(fullpath):
            os.remove(fullpath)
                    
        image_path = f"{IMAGE_DIR}/win_00_img_printer.png"
        if not image_click(image_path, sleep=3):
            return

        if v_file_type != 'HT_DOWN_3':
            logt('인쇄 버튼 클릭')
            image_path = f"{IMAGE_DIR}/win_00_btn_print.png"
            if not image_click(image_path, sleep=1):
                return

        logt("신고서 미리보기 ==> 오픈 대기")
        time.sleep(3)
        image_path = f"{IMAGE_DIR}/win_00_img_pdf_save.png"
        image_position = image_find(image_path)
        if image_position:
            logt("     인쇄:PDF 저장하기 확인 : 성공")
        else:
            logt("     인쇄:PDF 저장하기 확인 : 실패 !!!!!!!!!!!!!!!")
            return
        
        logt("저장 버튼 클릭  ==> Save As 팝업 준비")

        pyautogui.press('enter')
        time.sleep(3)
        
        # 저장하기
        ret = save_as(fullpath, v_file_type, ht_info)
        return ret

    except Exception as e:
        logt(f"파일 다운로드 받는 중 오류 발생 : {e}")
        return False
    return True

def save_as(fullpath, v_file_type, ht_info):
    try:
        logt(f"Save As ....  path={fullpath}")
        # 이미 존재하면 삭제 (pdf 다운로드시 이미 존재하면 덮어쓰기 하겠냐고 질문하는 것을 회피 하기위해)
        if os.path.isfile(fullpath):
            logt(f"이전 파일 삭제: path={fullpath}")
            os.remove(fullpath)
            
        # 붙여넣기 (Ctrl + V)
        #pyperclip.copy(fullpath)
        #pyautogui.hotkey('ctrl', 'v')
        pyautogui.typewrite(fullpath)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1)
        
        group_id  = ht_info['group_id']
        ht_tt_seq = ht_info['ht_tt_seq']
        holder_nm = ht_info['holder_nm']
        # 파일이 실제 저장되었는지 검사
        if os.path.isfile(fullpath):
            logt("파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
            logt("파일저장 확인완료 => DB 입력하기")
            dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
            return True
        else:
            time.sleep(3.0)
            if os.path.isfile(fullpath):            
                logt("(재시도)파일저장 성공: 파일타입= %s, 경로= %s" % (v_file_type,fullpath))
                logt("(재시도)파일저장 확인완료 => DB 입력하기")
                dbjob.insert_or_update_upload_file(v_file_type, group_id, ht_tt_seq, holder_nm)
                return True
            else:
                logt(f"실제 저장 여부 확인 실패,  path={fullpath}")
                return False
    except Exception as e:
        logt(f"파일 Save as 후 저장 오류 : {e}")
    
    return False


# 창닫기
def send_alt_f4(image_path):
    # 프린터 버튼을 가리고 있을 경우를 대비해 임의의 위치로 이동
    pyautogui.move(100, 100)
    
    image_position = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
    if image_position:
        image_click(image_path)
            
        time.sleep(0.3)
        pyautogui.keyDown('alt')
        pyautogui.typewrite(['f4'])
        pyautogui.keyUp('alt')
        time.sleep(0.3)
        return True
    else:
        logt(f"창 닫기 Alt+F4 실패 : {image_path}")
        return False

def insert_or_update_upload_file (file_type, group_id, ht_tt_seq, holder_nm) :
    curs = conn.cursor(pymysql.cursors.DictCursor)
    sql_httt = "SELECT * FROM ht_tt WHERE ht_tt_seq=%s"
    curs.execute(sql_httt,  (ht_tt_seq,))
    row = curs.fetchone()

    file_type_idx = file_type[-1]  # 파일타입의 마지막 숫자 (1~7)
    field_name = 'result' + str(file_type_idx) + '_file_seq'

    if file_type_idx == "P":   # 캡쳐 이미지는 _CAP으로 끝남
        file_type_idx= file_type[-5]
        field_name = 'capture' + str(file_type_idx) + '_file_seq'


    logt("이전 자료 조회 : 필드명=%s" % field_name)
    # logt(row)
    if row != None:
        file_seq = row[field_name]
        if file_seq != None and file_seq>0:
            with conn.cursor() as curs2:
                logt("이전 자료 조회 : ht_tt_file_seq=%d  => 삭제" % file_seq)
                # 기존 파일이 있을 경우 ht_tt_file 삭제
                del_sql = "DELETE FROM ht_tt_file WHERE ht_tt_file_seq=%s"
                logqry(del_sql, (file_seq,))
                curs2.execute(del_sql, (file_seq,))
            #conn.commit()  


    # 딕셔너리
    ins_data = ht_file.make_file_data(group_id, ht_tt_seq, file_type, holder_nm)

    # 튜플로 변환
    param = tuple(ins_data.values())
    #logt(param)
    sql1 = '''
        INSERT INTO ht_tt_file (ht_tt_seq, attach_file_type_cd, original_file_nm, changed_file_nm, path, uuid, file_size, file_ext, save_yn, reg_id)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    ht_tt_file_seq = 0
    with conn.cursor() as curs2:
        logqry(sql1, param)
        curs2.execute(sql1, param)
        ht_tt_file_seq = curs2.lastrowid
        #conn.commit()   

    # 파일 정보 UPDATE    
    logt("등록된 파일 ht_tt_file_seq= " + str(ht_tt_file_seq))
    sql2 = f"UPDATE ht_tt SET {field_name}=%s WHERE ht_tt_seq=%s"   #  동적 쿼리가 작동하는지 점검
    param2 = (ht_tt_file_seq, ht_tt_seq)
    with conn.cursor() as curs2:
        logqry(sql2, param2)
        curs2.execute(sql2, param2)
    
    conn.commit()   


def do_task(user_info, verify_stamp):
    job_cnt = 0
    처음부터_시작하기 = False
    while True:
        job_cnt += 1
        
        if 처음부터_시작하기:
            go_search_page()
            처음부터_시작하기 = False

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
                    dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'SW 신호로 STOP 합니다.')
                return
        else:
            dbjob.update_autoManager_statusCd(auto_manager_id, 'S', 'verify_stamp 변경으로 STOP 합니다.')
            return
            
        # =============================================================================
        # 홈택스 신고서제출 자료            
        ht_info = dbjob.select_next_au2(group_id, worker_id, seq_where_start, seq_where_end)
        # =============================================================================
        
        if not ht_info:
            dbjob.update_autoManager_statusCd(auto_manager_id, 'F', '처리할 자료가 없어서 FINISH 합니다.')
            break
            
        #담당자 전화번호 추가
        ht_info['worker_tel'] = user_info['tel']
        ht_tt_seq = ht_info['ht_tt_seq']
        
        
        logt("******************************************************************************************************************")
        logt("2단계 (New): JOB_COUNT=%s : HT_TT_SEQ=%d, 양도인=%s, SSN=%s%s" % (job_cnt, ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2']))
        logt("******************************************************************************************************************")
        
        # 2단계 초기화 
        #dbjob.update_HtTt_au2_reset(group_id, ht_tt_seq)
        
            
        try:
            # -----------------------------------------------------------------------
            # 문서 다운로드 반복
            # -----------------------------------------------------------------------
            do_step2_loop(ht_info)

        except BizException as e:
            loge(f'do_step2_loop :: BizException ERROR - {e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f'{e.name}:{e.msg}')
            #dbjob.update_autoManager_statusCd(auto_manager_id, 'E', f'{e.name}:{e.msg}')
            loge("오류 발생으로 해당 단계 작업 중지!!!")
            # break
            처음부터_시작하기 = True
        except Exception as e:
            loge(f'do_step2_loop :: Exception ERROR - {e}')
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'E', f'{e}')
            #dbjob.update_autoManager_statusCd(auto_manager_id, 'E', f'{e}')
            loge("오류 발생으로 해당 단계 작업 중지!!!")
            # break
            처음부터_시작하기 = True
        else:  # 오류없이 정상 처리시
            dbjob.update_HtTt_AuX(AU_X, ht_tt_seq, 'S', "NEW")
        # -----------------------------------------------------------------------

        logt("####### 한건처리 완료 #######")
            
                    
if __name__ == '__main__':
    # 이전에 실행되던 모든 크롬 프로세스를 종료합니다.
    if False:
        #os.system("taskkill /f /im chrome.exe")

        # 실행할 명령어
        command = 'start chrome --no-restore-session --window-size=1450,990 --window-position=0,0 "https://hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml&tmIdx=0&tm2lIdx=100907&tm3lIdx="'
        subprocess.run(command, shell=True)
        time.sleep(3)

    do_task(user_info, verify_stamp) 
    logt(f"{AU_X}단계 작업 완료")
    
    if conn:
        conn.close()
            
    exit(0)
