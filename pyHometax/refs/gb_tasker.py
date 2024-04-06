import time
import gb_agent_env_SAMPLE as agent_env
import os, sys
import gb_agent_db as autodb


# 반복 실행 후 대기 시작



autodb.connect_db()

def main(argv):
    pid  = os.getpid()
    print(f'argv={argv}')

    SERVER_ID = argv[1]
    AGENT_ID  = argv[2]
    GROUP_ID  = argv[3]
    auto_manager_id = agent_env.AUTO_MANAGER_ID
    
    rs = autodb.select_auto_manager_by_id(auto_manager_id)
    if rs == None:
        print(f'Agent 실행 정보가 DB에 없습니다. AUTO_MANAGER_ID={auto_manager_id}, PID={pid}')


    status_cd   = rs['status_cd']
    worker_id   = rs['worker_id']
    au_x        = rs['au_x']
    
    if au_x != None:
        autodb.update_autoManager_statusCd(auto_manager_id, 'R')
        # 실행중인 프로세스를 순차적으로 검색

        ht_info = None
        
        loop_cnt = 0
        while True:
            loop_cnt += 1
            print(f'    Tasking ....  PID={pid}')
            
            if au_x == '1':
                pass
            elif au_x == '2':                
                pass
            elif au_x == '3':
                ht_info = autodb.select_next_au3
                
            if ht_info:
                ht_tt_seq = ht_info['ht_tt_seq']
                autodb.update_autoManager_hthtSeq(auto_manager_id, ht_tt_seq) # 진행 상태 표기 (auto_manager)
                autodb.update_htTt_aux_running(ht_tt_seq, au_x)               # 진행 상태 표기 (ht_tt)
                
                time.sleep(30)
                
            
            
            #rs = db.get_worker_list('the1', 'the1tax_5')
            #print(rs)
            print('     hi~~~~~~~~')
            
            
            
            
            
            
            time.sleep(agent_env.LOOP_WAIT_TASKER) 
            
            if loop_cnt>10: 
                #a = 10/0
                
                break
        
    
    
if __name__ == "__main__":
    main(sys.argv)

