# 참고문서
# https://digiconfactory.tistory.com/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC-os-%EB%AA%A8%EB%93%88-%ED%8C%8C%EC%9D%BC-%EA%B2%BD%EB%A1%9C-%EC%A1%B0%EC%9E%91%ED%95%98%EA%B8%B0-ospath

import sys, os, time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import pyautogui
import pyperclip
import uuid

import config


def get_root_dir(group_id) :
    return config.FILE_ROOT_DIR_BASE + group_id + os.path.sep

# 1001 => 001\001001\
def get_path_by_htTtSeq(ht_tt_seq):
    if type(ht_tt_seq) is str:
        ht_tt_seq = int(ht_tt_seq)
        print(type(ht_tt_seq))

    path1 = '%03d' % (ht_tt_seq / 1000)
    path2 = '%06d' % ht_tt_seq

    ret = path1 + os.path.sep + path2 + os.path.sep
    #print("get_path_by_htTtSeq()=%s" % ret)
    return ret

# 30 => D:\WWW\JNK\files\hometax\000\000030\
def get_dir_by_htTtSeq(group_id, ht_tt_seq, is_create=False):

    root_dir = get_root_dir(group_id)
    path1 = '%03d' % (ht_tt_seq / 1000)
    path2 = '%06d' % ht_tt_seq
    
    ret = root_dir + path1 + os.path.sep + path2 + os.path.sep
    
    if is_create:
        createFolder(ret + os.path.sep + "work")  # work 폴더 기본생성

    return ret

# 30 => D:\WWW\JNK\files\hometax\000\000030\work\
def get_work_dir_by_htTtSeq(group_id, ht_tt_seq):
    root_dir = get_root_dir(group_id)
    path1 = '%03d' % (ht_tt_seq / 1000)
    path2 = '%06d' % ht_tt_seq
    
    ret = root_dir + path1 + os.path.sep + path2 + os.path.sep + 'work' + os.path.sep
    
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



# save_full_path_name (전체경로) : c:/myfoler/a.txt
def SaveAs(driver, download_ele, save_full_path_name):
    actionChains = ActionChains(driver)
    actionChains.context_click(download_ele).perform()
    
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(3)
    pyautogui.press('left')
    time.sleep(1)
    pyperclip.copy('d:\\python\\')
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(2)

# url = 'https://www.google.com/'
# driver = RunChrome(url)

# xPath_Target = '/html/body/div[1]/div[2]/div/img'
# elemnet_Target = driver.find_element_by_xpath(xPath_Target)
# SaveAs(driver, elemnet_Target)    



# file_type별 파일이름 결정
def get_file_name_by_type(file_type):
    filename = ""
    if   file_type == "HT_DOWN_1":
        filename = "down1.pdf"
    elif file_type == "HT_DOWN_2":
        filename = "down2.pdf"
    elif file_type == "HT_DOWN_3":
        filename = "down3.pdf"
    elif file_type == "HT_DOWN_4":
        filename = "down4.pdf"
    elif file_type == "WE_DOWN_5":
        filename = "down5.pdf"
    elif file_type == "WE_DOWN_6":
        filename = "down6.pdf"
    elif file_type == "WE_DOWN_7":
        filename = "down7.pdf"
    elif file_type == "HT_DOWN_8":  # 홈택스 납부서2 (분납)
        filename = "down8.pdf"

    elif file_type == "HT_DOWN_1_CAP":
        filename = "capture_1.png"
    elif file_type == "HT_DOWN_2_CAP":
        filename = "capture_2.png"
    elif file_type == "HT_DOWN_3_CAP":
        filename = "capture_3.png"
    elif file_type == "HT_DOWN_4_CAP":
        filename = "capture_4.png"
    elif file_type == "WE_DOWN_5_CAP":
        filename = "capture_5.png"
    elif file_type == "we_DOWN_6_CAP":
        filename = "capture_6.png"
    elif file_type == "WE_DOWN_7_CAP":
        filename = "capture_7.pdpngf"
    elif file_type == "HT_DOWN_8_CAP":  # 홈택스 납부서2 (분납)
        filename = "capture_8.png"

    return filename

def make_file_data(v_group_id, v_ht_tt_seq, v_file_type, v_holder_nm):
    changed_file_nm = get_file_name_by_type(v_file_type)

    root_dir = get_root_dir(v_group_id)
    path = get_path_by_htTtSeq(v_ht_tt_seq)
    if v_file_type.find("CAP") >=0 :
        path = path + "work" + os.sep

    fullpath = root_dir + path + changed_file_nm;    
    file_size = os.path.getsize(fullpath) 
    
    fname, ext = os.path.splitext(changed_file_nm)
    ext = ext[1:]

    data = {
        'ht_tt_seq': v_ht_tt_seq, 
        'attach_file_type_cd': v_file_type, 
        'original_file_nm': v_holder_nm + "_" + changed_file_nm, 
        'changed_file_nm': changed_file_nm, 
        'path': path, 
        'uuid': uuid.uuid4(),
        'file_size': file_size,
        'file_ext' : ext, 
        "save_yn" : "Y", 
        "reg_id" : "SYSTEM"
    }
    print(fullpath)
    print(data)

    return data 

