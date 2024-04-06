import config
import dbjob
import ht_file


import sys, os, time
import shutil


'''
자동 일 경우 source_upload.pdf이 존재하는 점검
'''


def get_file_path_by_file_seq(ht_tt_file_seq) :
        # 파일키
        if ht_tt_file_seq is not None and ht_tt_file_seq>0 :
            # 파일정보
            file_info = dbjob.select_one_HtTtFile(ht_tt_file_seq)

            if file_info is not None :
                # DB에 있는 파일 정보
                filepath = root_dir + file_info['path'] + file_info['changed_file_nm'] 
                return filepath
            else:
                return None
        else :
            return None


def main():
    DB_QUERY_PRINT = True
    dbjob.connect_db()

    root_dir = config.FILE_ROOT_DIR
    result = []
    i=0
    rs = dbjob.select_auto_5('the1', 'MANAGER_ID', 1000000)
    print(f"5단계 작업대상 수량 = {len(rs)}")

    num = 0
    for ht in rs:

        ret = ''
        try :
            ht_tt_seq = ht['ht_tt_seq']
            #ht_tt_file_seq = ht['source_file_seq']

            '''
            source_file_path = get_file_path_by_file_seq(ht_tt_file_seq)
            # 원본자료가 업로드된 이후 추가 증빙자료 업로드된 경우 하나의 pdf로 통합됨
            source_file_path = source_file_path.replace('source.pdf', 'source_upload.pdf')
            if not os.path.exists(source_file_path):
                num += 1
                print(f"{num} - {source_file_path} : {ht['ht_tt_seq']} {ht['holder_nm']} {ht['holder_ssn1']} {ht['holder_ssn2']} : {ht['au1']}{ht['au2']}{ht['au3']}{ht['au4']}")
            '''

            source_file_path = ht_file.get_work_dir_by_htTtSeq(ht_tt_seq)
            source_file_path = source_file_path + 'source_upload.pdf'
            

            # 원본파일(tif, pdf 등) 이 없을 경우 에러처리
            if  os.path.exists(source_file_path):
                # 파일 크기가 50메가가 넘는지 조회
                file_size = os.path.getsize(source_file_path)
                if file_size > 49.5*1024*1024 :
                    num += 1
                    print(f"50MB 넘음 {num} filesize={file_size} : {ht['ht_tt_seq']} {ht['holder_nm']} {ht['holder_ssn1']} {ht['holder_ssn2']} {ht['data_type']} {ht['step_cd']} : {ht['au1']}{ht['au2']}{ht['au3']}{ht['au4']}{ht['au5']} - {source_file_path}")
            else:
                num += 1
                print(f"NOT FOUND!! {num} : {ht['ht_tt_seq']} {ht['holder_nm']} {ht['holder_ssn1']} {ht['holder_ssn2']} {ht['data_type']} {ht['step_cd']} : {ht['au1']}{ht['au2']}{ht['au3']}{ht['au4']}{ht['au5']} - {source_file_path}")


        except Exception as e:
            ret = 'X'

main()