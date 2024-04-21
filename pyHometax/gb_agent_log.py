import time
import psutil
import subprocess 
import os, sys
import signal
from threading import Thread
from datetime import datetime

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

LOG_DIR = f"{CUR_CWD}\\pyHometax\\LOG"

current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")
log_filename = f"{LOG_DIR}\\WS_LOG_WATCHER_{now}.log"
logger = common.set_logger(log_filename)    


def main():
    '''
    서버에서 VM으로 실행되는 각각의 Agent
    '''

    CURRENT_THREAD = None
    while True:
        # --------------------------------------------------------
        # 진행단계에 맞는 하위 작업 선택하기
        # --------------------------------------------------------
        run_py_file = 'web_socket_server.py'
        run_py_fullpath = f'{CUR_CWD}\\pyHometax\\{run_py_file}'
        
        found_proc_count, pids = find_process_count(run_py_file, "1", "2", "3")

        if found_proc_count == 0:
            CURRENT_THREAD = Thread(target=start_thread, args=(run_py_fullpath, "1", "2", "3"))
            CURRENT_THREAD.start()
            logger.info(f'[LogAgent LOOPING] 프로세스 개수=[{found_proc_count}], pids={pids}')
            logger.info('   ==> START Thread !!!')
        else:
            logger.info(f'[LogAgent LOOPING] 프로세스 개수=[{found_proc_count}], pids={pids}  ==> RUNNING')
        
        time.sleep(LOOP_WAIT_AGENT)
    
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
    pids = []
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
                        pids.append(pid)
                        #logger.info(f'check_process() pid={pid} ==> found count={found_proc}')
                    else:
                        logger.info(f'PID={pid}, NAME:{ps_name} CMD:{cmdline}')
                
        except Exception as e:
            logger.error(e)
        
    return found_proc, pids



# 
if __name__ == "__main__":
    main()

