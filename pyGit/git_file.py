# 참고문서
# https://digiconfactory.tistory.com/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC-os-%EB%AA%A8%EB%93%88-%ED%8C%8C%EC%9D%BC-%EA%B2%BD%EB%A1%9C-%EC%A1%B0%EC%9E%91%ED%95%98%EA%B8%B0-ospath

import sys, os, time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import pyautogui
import pyperclip
import uuid

import config


def get_root_dir() :
    return config.FILE_ROOT_DIR

# 1001 => 01001\
def get_path_by_gitSeq(git_seq):
    if type(git_seq) is str:
        git_seq = int(git_seq)

    path2 = '%05d' % git_seq

    ret = path2 + os.path.sep
        
    return ret

# 30 => D:\WWW\JNK\files\git\wize\00030\
def get_dir_by_gitSeq(git_seq, is_create=True):

    root_dir = get_root_dir()

    path2 = '%05d' % git_seq
    
    ret = root_dir + path2 + os.path.sep
    
    if is_create:
        createFolder(ret + os.path.sep + "work")  # work 폴더 기본생성

    return ret

# 30 => D:\WWW\JNK\files\hometax\wize\00030\work\
def get_work_dir_by_gitSeq(git_seq):
    root_dir = get_root_dir()
    path2 = '%05d' % git_seq
    
    ret = root_dir + path2 + os.path.sep + 'work' + os.path.sep
    
    # work 폴더 기본생성
    createFolder(ret)  

    return ret


def createFolder(directory):
    try:
        if not os.path.exists(directory):
            print("폴더생성: " + directory)
            os.makedirs(directory, exist_ok=True)
    except OSError:
        print ('Error: Creating directory. ' +  directory)



# file_type별 파일이름 결정
def get_file_name_by_type(file_type):
    filename = f"down{file_type}.pdf"
    return filename
    
    # if   file_type == "0": # 신고안내문
    #     filename = "down0.pdf"
    # elif file_type == "1": # 일괄출력물
    #     filename = "down1.pdf"
    # elif file_type == "2": # 접수증
    #     filename = "down2.pdf"
    # elif file_type == "3": # 납부서
    #     filename = "down3.pdf"
    # elif file_type == "4": # (위택스)신고서
    #     filename = "down4.pdf"
    # elif file_type == "5": # (위택스)접수증
    #     filename = "down5.pdf"
    # elif file_type == "6": # (위택스)납부서
    #     filename = "down6.pdf"
    # elif file_type == "7": # 신고안내문
    #     filename = "down7.pdf"
    # elif file_type == "8":  # 홈택스 납부서2 (분납)
    #     filename = "down8.pdf"

    # return filename

def get_showing_file_name_by_type(file_type, nm):
    filename = ""
    if   file_type == "0": # 신고안내문
        filename = f"{nm}_신고안내문.pdf"
    elif file_type == "1": # 일괄출력물
        filename = f"{nm}_종합소득세_납부계산서.pdf"
    elif file_type == "2": # 접수증
        filename = f"{nm}_종합소득세_접수증.pdf"
    elif file_type == "3": # 납부서
        filename = f"{nm}_종합소득세_납부서.pdf"
    elif file_type == "4": # (위택스)신고서
        filename = f"{nm}_지방세_신고서.pdf"
    elif file_type == "5": # (위택스)접수증
        filename = f"{nm}_지방세_접수증.pdf"
    elif file_type == "6": # (위택스)납부서
        filename = f"{nm}_지방세_납부서.pdf"
    elif file_type == "7": # 신고안내문
        filename = f"미정.pdf"
    elif file_type == "8":  # 홈택스 납부서2 (분납)
        filename = f"{nm}_납부서(분납).pdf"

    return filename    

def make_file_data(group_id, git_seq,  nm, attach_type, is_work_folder = False):
    changed_file_nm = get_file_name_by_type(attach_type)
    root_dir = get_root_dir()
    path = get_path_by_gitSeq(git_seq)
    if is_work_folder :
        path = path + "work" + os.sep

    fullpath = root_dir + path + changed_file_nm;    
    file_size = os.path.getsize(fullpath) 

    print(f"FILE_DATA : FILENAME={fullpath}, SIZE={file_size}")
    
    fname, ext = os.path.splitext(changed_file_nm)
    ext = ext[1:]  # .을 빼기 위해 1로 시작

    data = {
        'group_id'        : group_id,
        'git_seq'         : git_seq, 
        'attach_type'     : f"HT_DOWN_{attach_type}", 
        'original_file_nm': get_showing_file_name_by_type(attach_type, nm),
        'changed_file_nm' : changed_file_nm,
        'path'            : path, 
        'uuid'            : uuid.uuid4(),
        'file_size'       : file_size,
        'file_ext'        : ext.lower(), 
        'remark'          : '',
        "reg_id"          : "SYSTEM"
    }

    return data 

