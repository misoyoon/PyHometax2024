import time
import os

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.common.exceptions import TimeoutException

import pyautogui
from common import *

#iframe 전환 : 로그인화면은 화면전체가 iframe
def move_iframe(driver: WebDriver, target_iframe:str='txppIframe', sleep=0.5):
    if sleep > 0:
        time.sleep(sleep)
        
    logt("ifreme 전환: ID=%s" % target_iframe)
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    
    is_exist_iframe = False
    frame_idx = 0
    for iframe in iframes:
        frame_idx += 1
        iframe_name = iframe.get_attribute('name')
        iframe_id = iframe.get_attribute('id')
        if iframe_name == target_iframe or iframe_id == target_iframe:
            is_exist_iframe = True
            logt(f"    IFRAME 정보: id={iframe_id}, name={iframe_name}                     <=== Selected")
        else:
            logt(f"    IFRAME 정보: id={iframe_id}, name={iframe_name}")

    if is_exist_iframe == False:
        time.sleep(2)
        logt(f"    IFRAME을 찾을 수 없어 다시 한번 시도합니다.")
        for iframe in iframes:
            frame_idx += 1
            iframe_name = iframe.get_attribute('name')
            iframe_id = iframe.get_attribute('id')
            if iframe_name == target_iframe or iframe_id == target_iframe:
                is_exist_iframe = True
                logt(f"    IFRAME 정보: id={iframe_id}, name={iframe_name}                 <=== Selected")
            else:
                logt(f"    IFRAME 정보: id={iframe_id}, name={iframe_name}")

    try :
        if is_exist_iframe :
            driver.switch_to.frame(target_iframe)
            return True
        else :
            logt("iframe 전환실패 : %s를 찾을 수 없음" % target_iframe, 1)
            return False

    except Exception as e:
        loge("iframe 전환 예외")
        #loge(f'{e}')
        return False


def wait_id_and_click(driver: WebDriver, id, timeout=5):
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.element_to_be_clickable((By.ID, id)))
    element.click()

def go_main_page(driver: WebDriver):
    driver.get('https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml')
    #driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml")
    driver.implicitly_wait(10)

# Window 전환
def change_window(driver: WebDriver, from_index: int, to_index: int):
    time.sleep(0.5)
    print_window_by_title(driver)
    logt("(f)Window 이동: %s -> %s" % (from_index, to_index))
    
    if len(driver.window_handles):
        # child window close
        if from_index > to_index :
            driver.close()
            
        driver.switch_to.window(driver.window_handles[to_index])

# Window 전환
def print_window_by_title(driver: WebDriver, title=""):
    window_handles = driver.window_handles
    logt(window_handles)
    
    idx = -1
    logt(f'윈도우 리스트')
    for w_handle in window_handles:     
        idx += 1
        logt(f'{idx} : {w_handle.title}')

# Alert처리
def click_alert(driver: WebDriver, msg, sleep=0.5) -> str:
    if sleep > 0:
        time.sleep(sleep)

    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present(), 'Timed out waiting for alerts to appear')
        alert= driver.switch_to.alert
        logt("(f)Alert 예상메세지: %s" % msg)
        logt("(f)Alert 실제메세지: %s" % alert.text)
        if alert.text.find(msg)>=0:
            alert.accept()
            return 'TRUE'
        else:
            alert.accept()
            return alert.text
    except TimeoutException:
        return 'TimeoutException'
    except :
        return 'ALERT_ERROR'

    # try:
    #     logt("(f)Alert 예상메세지: %s" % msg)
    #     alert = driver.switch_to_alert()
    #     #alert = Alter(driver)
    #     logt("(f)Alert 실제메세지: %s" % alert.text)
    #     alert.accept()
    #     return alert.text

    # except Exception as e:
    #     logt('(f)Alert 예외: 예외가 발생했습니다. e=%s' % e)
    #     return 'ALERT_ERROR'

def click_alert_dismiss(driver: WebDriver, msg, sleep=0.5) -> str:
    if sleep > 0:
        time.sleep(sleep)

    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present(), 'Timed out waiting for alerts to appear')
        alert= driver.switch_to.alert
        logt("(f)Alert 예상메세지: %s" % msg)
        logt("(f)Alert 실제메세지: %s" % alert.text)
        alert_text = alert.text
        if alert_text.find(msg)>=0:
            alert.dismiss()
            return 'TRUE'
        else:
            alert.dismiss()
            return 'ALERT_ERROR'
    except TimeoutException:
        return 'TimeoutException'
    except :
        return 'ALERT_ERROR'        


# INPUT 박스에 값 넣기
def set_input_value_by_id(driver: WebDriver, id:str, value: str, title: str, sleep=0.2):
    if sleep > 0:
        time.sleep(sleep)
    logt(f"INPUT Set value id={id}: {title} => [{value}]", sleep)
    driver.find_element(By.ID, id).send_keys(value)

# BUTTON 클릭
def click_button_by_id(driver: WebDriver, id:str, title: str, sleep=0.2):
    if sleep > 0:
        time.sleep(sleep)
    
    logt(f"Click button (id={id}): {title} 클릭", sleep)
    driver.find_element(By.ID, id).click()
    
def set_select_by_option_index(driver: WebDriver, id:str, select_index: int, title: str, sleep=0.2):    
    if sleep > 0:
        time.sleep(sleep)
    
    logt(f"INPUT SELECT (id={id}): [{title}]에서 [{select_index}]번째 선택", sleep)         
    driver.find_element(By.CSS_SELECTOR, f'#{id} > option:nth-child({select_index})').click()


def close_other_windows(driver: WebDriver):
        # 팝업 창이 있으면 모두 닫기
    if len(driver.window_handles) > 1:
        for i in range(len(driver.window_handles)-1, 0, -1):
            driver.switch_to.window(driver.window_handles[i])
            time.sleep(0.2)
            driver.close()
            
        driver.switch_to.window(driver.window_handles[0])


# 이미지의 위치를 찾을 때까지 반복 시도 클릭
def pyautoui_image_click(img_path, retry_cnt=10):
    for retry in range(retry_cnt):
        center = pyautogui.locateCenterOnScreen(img_path, confidence=0.8)
        logt(center)
        logt(img_path)
        if center == None :
            time.sleep(0.5)
            logt("이미지 클릭 재시도: retry=%d" % retry)
        else :
            time.sleep(0.3) # 0.3초후 클릭
            pyautogui.click(center)
            logt("이미지 클릭: %s" % img_path)
            return True
    return False

# driver의 close 혹은 에러로 인해 닫힘 체크
def check_availabe_driver(driver):
    try:
        title = driver.title
        return True
    except Exception as e:
        loge(f'{e}')
        return False
    