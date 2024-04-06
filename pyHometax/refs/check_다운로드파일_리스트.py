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
rs = dbjob.select_download_file_list()
for ht in rs:
    if ht['holder_nm'] == '장하연':
        print("debug")
    #print(ht)
    ret = ''
    try :
        if ht['au2'] == 'S':
            file = root_dir + ht['result1']
            if os.path.exists(file): ret += '.'
            else: ret += 'X'

            file = root_dir + ht['result2']
            if os.path.exists(file): ret += '.'
            else: ret += 'X'

            file = root_dir + ht['result3']
            if os.path.exists(file): ret += '.'
            else: ret += 'X'

            if ht['data_type']=='AUTO'  and ht['au2_msg']!='이미납부완료' and  ht['hometax_income_tax'] > 0:
                    file = root_dir + ht['result4']
                    if os.path.exists(file): ret += '.'
                    else: ret += 'X'
            else:
                ret += '.'

            if ht['data_type']=='AUTO' and ht['au2_msg']!='이미납부완료' and  ht['hometax_income_tax'] >= 10000000:
                file = root_dir + ht['result8']
                if os.path.exists(file): ret += '.'
                else: ret += 'X'
            else :
                ret += '.'
    except Exception as e:
        ret = 'XXXXXX'

    if ret.find("X")>=0:
        i += 1
        print(f'{i} - {ht}')    
        
        #dbjob.update_au2_status(ht['ht_tt_seq'],  None)
        



    # ret += '-' 

    # try:
    #     if ht['au4'] == 'S':
    #         file = root_dir + ht['result5']
    #         if os.path.exists(file): ret += '.'
    #         else: ret += 'X'        
    #     else:
    #         ret += '.'
    # except Exception as e:
    #     ret += 'X'
    #     print(ht)

#     ret += '-' + str(ht['ht_tt_seq']) + '-' + ht['holder_nm']
#     #print(ret)


#     result.append(ret)

# i=0
# for ret in result:
#     if ret.find("X")>=0:
#         i += 1
#         print(f'{i} - {ret}')    