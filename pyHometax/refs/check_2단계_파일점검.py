import config
import dbjob


import sys, os, time
import shutil
import traceback


'''
홈택스/위택스 파일 다운로드가 완료된 것 중 DB & 파일 시스템이 정상적으로 연결되어 있는지 검사
'''



dbjob.connect_db()

root_dir = config.FILE_ROOT_DIR
result = []
i=0
rs = dbjob.select_download_file_list_2단계('the1')
print(f"2단계 다운로드 파일 점검, 갯수 = {len(rs)}")

for ht in rs:
    #if ht['holder_nm'] == '장하연':  print("debug")

    ht_tt_seq = ht['ht_tt_seq']
    # 정상판단되는 seq는 생략
    passlist = [22460,20590,21769,20553,21258,24416,23132,24416]
    if ht_tt_seq in passlist:
        continue

    ret = ''
    try :
        if ht['au2'] == 'S':
            # 파일 1
            file = root_dir + ht['result1']
            if os.path.exists(file): ret += '.'
            else: ret += '1X'

            if os.path.getsize(file) == 0 : ret += '10'

            # 파일 2
            file = root_dir + ht['result2']
            if os.path.exists(file): ret += '.'
            else: ret += '2X'
            
            if os.path.getsize(file) == 0 : ret += '20'

            # 파일 3
            file = root_dir + ht['result3']
            if os.path.exists(file): ret += '.'
            else: ret += '3X'

            if os.path.getsize(file) == 0 : ret += '30'

            # 파일 4
            # 납부서 : result4
            if ht['au2_msg'].find('이미납부완료')>=0 or ht['au2_msg'].find('납부할금액이 없습니다')>=0 or ht['au2_msg'].find('납부서 Click불가')>=0:
                ret += '.'
            else:
                if ht['hometax_income_tax'] > 10:
                    file = root_dir + ht['result4']
                    if os.path.exists(file): 
                        if os.path.getsize(file) == 0:  ret += '40'   # 비정상
                    else: 
                        ret += '4X'       # 비정상
                else :
                    ret += '.'           # 정상

            # 납부서 분납분 : result8
            if ht['au2_msg'].find('이미납부완료')>=0 or ht['au2_msg'].find('납부할금액이 없습니다')>=0 or ht['au2_msg'].find('납부서 Click불가')>=0:
                ret += '.'
            else:
                if ht['hometax_income_tax'] > 10000000:
                    file = root_dir + ht['result8']
                    if os.path.exists(file): 
                        if os.path.getsize(file) == 0:  ret += '80'   # 비정상
                    else: 
                        ret += '8X'
                else :
                    ret += '.'
                    
    except Exception as e:
        print(f'ERROR:: {i} - {ht}') 
        print(traceback.format_exc())
        ret = 'E'

    if ret.find("X")>=0 or ret.find("0")>=0:
        i += 1
        print(f'{i} : {ret} ===> {ht}\n')    
        
        #dbjob.update_au2_status(ht['ht_tt_seq'],  None)

        

