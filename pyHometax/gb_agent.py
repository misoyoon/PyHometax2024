import time
import psutil
import subprocess 
import os, sys
import signal
from threading import Thread
from datetime import datetime

sys.path.insert(0, "C:/gby/pyHometax")  # gb_agent_env_개별(탬플릿).py를 해당 위치로 이동하기

import gb_agent_env_개별 as agent_env
import dbjob
import common

# # 로깅 설정
# import logging
# # 로깅 설정
# logging.basicConfig(level=logging.DEBUG,  format='%(asctime)s - %(levelname)s - %(message)s')

# # 파일 핸들러 생성
# file_handler = logging.FileHandler('example.log')
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# # 콘솔 핸들러 생성
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

# # 로거에 핸들러 추가
# logger = logging.getLogger()
# logger.addHandler(file_handler)
# #logger.addHandler(console_handler)

# 반복 실행 후 대기 시작
LOOP_WAIT_AGENT  = 10

pid  = os.getpid()
CUR_CWD = os.getcwd()
auto_manager_id = agent_env.AUTO_MANAGER_ID

current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")
log_filename = f"{CUR_CWD}\\pyHometax\\LOG\\{auto_manager_id}_A_{now}.log"
logger = common.set_logger(log_filename)    

logger.info("##############################")
logger.info(f"설정 정보 : {agent_env.AUTO_MANAGER_ID}")
logger.info("##############################")

def main():
    '''
    서버에서 VM으로 실행되는 각각의 Agent
    '''

    # DB 접속
    dbjob.connect_db()
    
    # FIXME 강제 시작용
    #dbjob.update_autoManager_statusCd(auto_manager_id, 'RW')
    
    CURRENT_THROED = None
    while True:
        #logger.info(f'')
        
        rs = dbjob.select_autoManager_by_id(auto_manager_id)
        if rs == None:
            print_line2(f'Agent 실행 정보가 DB에 없습니다. AUTO_MANAGER_ID={auto_manager_id}, PID={pid}')
            break
        
        status_cd   = rs['status_cd']
        au_x        = rs['au_x']

        # --------------------------------------------------------
        # 진행단계에 맞는 하위 작업 선택하기
        # --------------------------------------------------------
        run_py_file = f'at_ht_step_{au_x}.py'
        run_py_fullpath = f'{CUR_CWD}\\pyHometax\\{run_py_file}'
        
        found_proc_count = find_process_count(run_py_file, agent_env.SERVER_ID, agent_env.AGENT_ID, agent_env.GROUP_ID)
        logger.info(f'[GBAgent LOOPING] ID={auto_manager_id}, PID={pid}, 진행상태=[{status_cd}], 자동화단계=[{au_x}], 프로세스 개수=[{found_proc_count}]')

        #if found_proc_count>0 and status_cd == 'RW':
        #    kill_process(run_py_file, agent_env.SERVER_ID, agent_env.AGENT_ID, agent_env.GROUP_ID)
        
        '''
        상태코드 : 
            W  : WAIT
            RW : RUN WAIT
            SW : STOP WAIT
            R  : RUNNING
            S  : STOP
            E  : ERROR
            SF : STOPForced -> 일정시간 업데이트가 없어서 강제종료처리
            F  : FINISH (작업 정상 종료)
        '''
        
        #logger.info(f'[GBAgent LOOPING] AGENT_ID=[{auto_manager_id}], STATUS_CD=[{status_cd}]')
        if status_cd == 'R' or status_cd == 'RW':
            if au_x != None:
                if found_proc_count == 0:
                    logger.info('   ==> START Thread !!!')
                    CURRENT_THROED = Thread(target=start_thread, args=(run_py_fullpath, agent_env.SERVER_ID, agent_env.AGENT_ID, agent_env.GROUP_ID))
                    CURRENT_THROED.start()
                else:
                    logger.info('   ==> 실행 중 ...')
            else:
                remark = '(AGENT) au_x가 존재하지 않아 STOP 합니다.'
                logger.warning(remark)
                dbjob.update_autoManager_statusCd(auto_manager_id, 'S', remark)
            
            #a = 10/0
            #th1.join()
        elif status_cd == 'SW':
            if found_proc_count == 0:
                dbjob.update_autoManager_statusCd(auto_manager_id, 'S')
            logger.info('Task STOP WAIT  ==> STOP Thread !!!')
            

        elif status_cd == 'SF':
            logger.info('Task STOP WAIT  ==> STOP Thread !!!')
            
        #else:
        #    logger.info(f'현재 상태 = {status_cd}')
        
        
        time.sleep(LOOP_WAIT_AGENT)
        #logger.info('End of loop')
        #break
        
        
PRINT_LINE_1 = '---------------------------------------------------------'        
PRINT_LINE_2 = '========================================================='
def print_line1(msg):
    logger.info(PRINT_LINE_1)
    logger.info(msg)
    logger.info(PRINT_LINE_1)

def print_line2(msg):
    logger.info(PRINT_LINE_2)
    logger.info(msg)
    logger.info(PRINT_LINE_2)

    
def start_thread(py_file, server_id, agent_id, group_id):
        p = subprocess.run(['python', py_file, server_id, agent_id, group_id], capture_output=False, text=True)
        #output = os.popen("python D:\Project\py\PyHometax2024\pyHometax\gb_tasker.py").read()
        logger.info("start_thread() 함수 실행을 끝냈습니다.")
        logger.info(p)
        

def kill_process(run_py_file, server_id, agent_id, group_id):
    for proc in psutil.process_iter():
        try:
            # 프로세스 이름을 ps_name에 할당
            ps_name = proc.name()
            if ps_name.find('python.exe') >= 0:
                # 실행 명령어와 인자(argument)를 리스트 형식으로 가져와 cmdline에 할당
                cmdline = proc.cmdline()
                pid = proc.pid
                #logger.info(f'PID={pid}, NAME:{ps_name} CMD:{cmdline}')
                if cmdline[1].find(run_py_file) >= 0:
                    if len(cmdline) >= 4 and cmdline[2] == server_id and cmdline[3] == agent_id :
                        os.kill(pid, signal.SIGTERM)
                        logger.info(f'프로세스 pid={pid}를 종료했습니다.')
                    else:
                        logger.info(f'PID={pid}, NAME:{ps_name} CMD:{cmdline}')
                
        except Exception as e:
            logger.error(e)
            
# 쓰레드에서 실행되고 있는 process가 존재하는지 검사 
def find_process_count(run_py_file, server_id, agent_id, group_id) -> int:
    time.sleep(2)
    # 혹여나 복수의 같은 task가 실행되고 있는지를 확인하기 위해 전체 조회
    found_proc = 0
    for proc in psutil.process_iter():
        try:
            # 프로세스 이름을 ps_name에 할당
            ps_name = proc.name()
            if ps_name.find('python') >= 0:
                # 실행 명령어와 인자(argument)를 리스트 형식으로 가져와 cmdline에 할당
                cmdline = proc.cmdline()
                pid = proc.pid
                #logger.info(f'PID={pid}, NAME:{ps_name} CMD:{cmdline}')
                if len(cmdline) >= 5 and cmdline[-4].find(run_py_file) >= 0:
                    if cmdline[-3] == server_id and cmdline[-2] == agent_id and cmdline[-1] == group_id :
                        found_proc += 1
                        #logger.info(f'check_process() pid={pid} ==> found count={found_proc}')
                    else:
                        logger.info(f'PID={pid}, NAME:{ps_name} CMD:{cmdline}')
                
        except Exception as e:
            logger.error(e)
        
    return found_proc



# 
if __name__ == "__main__":
    main()

