import config
import dbjob


import sys, os, time
import shutil


'''
홈택스/위택스 파일 다운로드가 완료된 것 중 DB & 파일 시스템이 정상적으로 연결되어 있는지 검사
'''



dbjob.connect_db()

root_dir = config.FILE_ROOT_DIR
result = []
i=0
rs = dbjob.select_download_file_list_4단계('the1')
print(f"4단계 다운로드 파일 점검, 갯수 = {len(rs)}")

for ht in rs:

    ret = ''
    try :

        ht_tt_seq = ht['ht_tt_seq']
        # 정상판단되는 seq는 생략
        passlist = [] # [21708,22157,24416,30261,32058,31946,33653,32632,32732,32767,32804]
        if ht_tt_seq in passlist:
            continue

        # 세금이 10원 이상,  홈택스에서 이미 납부했으면 위택스에서 납부할 가능성이 있음
        if ht['au4'] == 'S' or ht['au4'] == 'Y':
            if ht['hometax_income_tax'] < 100 and ht['result5'] is None: 
                ret += '.'    # 정상 
            elif ht['hometax_income_tax'] >= 100 and ht['result5'] is None: 
                ret += '5.'   # 비정상
            else:
                file = root_dir + ht['result5']    # result5 => 결과 다운로드 - 위택스 접수증
                if os.path.exists(file): 
                    if os.path.getsize(file) == 0: 
                        ret += '50'   # 비정상
                    else:
                        ret += '.'    # 정상 
                else: 
                    ret += '5X'

    except Exception as e:
        ret = '5E'

    if ret.find("X")>=0 or ret.find("0")>=0 or ret.find("-")>=0:
        i += 1
        print(f'{i} : {ret} ===> {ht}\n')    
        #print(f'{i} - {ret}')    
        
        #dbjob.update_au4_status_to_report(ht['ht_tt_seq'],  None)

        
