import config
import dbjob
import git_file

import sys, os, time
import shutil


'''
홈택스/위택스 파일 다운로드가 완료된 것 중 DB & 파일 시스템이 정상적으로 연결되어 있는지 검사
'''



dbjob.connect_db()

root_dir = config.FILE_ROOT_DIR
result = []
i=0
git_infos = dbjob.select_git_for_audit_au0('wize')
for git_info in git_infos:

    ret = ''
    try :
        git_seq = git_info['git_seq']
        
        # 정상판단되는 seq는 생략
        passlist = []
        if git_seq in passlist:
            continue

        work_dir = git_file.get_work_dir_by_gitSeq(git_seq)


        # 세금이 10원 이상,  홈택스에서 이미 납부했으면 위택스에서 납부할 가능성이 있음
        if git_info['au0'] == 'S': 
            file = work_dir + 'report_guide.pdf'
            if os.path.exists(file): 
                filesize = os.path.getsize(file)
                if filesize == 0: 
                    ret += '00'   # 비정상
                else:
                    ret += '.'    # 정상 
                    print(f"{git_seq} {file} ==> {filesize} bytes")
            else: ret += '0X'

    except Exception as e:
        ret = '0X'

    if ret.find("X")>=0 or ret.find("0")>=0:
        i += 1
        print(f'{i} : {git_seq} {git_info["nm"]}===> {ret}\n')    
        #print(f'{i} - {ret}')    
        
        #dbjob.update_au4_status_to_report(ht['git_seq'],  None)

        
