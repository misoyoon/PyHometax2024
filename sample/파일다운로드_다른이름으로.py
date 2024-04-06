import sys, os, time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import pyautogui
import pyperclip

def RunChrome(url):
    chromedriver_path = resource_path("chromedriver.exe")
    driver = webdriver.Chrome(chromedriver_path)

    driver.implicitly_wait(1)
    driver.get(url)
    driver.implicitly_wait(1)

    return driver

def resource_path(relative_path):
    try: 
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

url = 'https://www.google.com/'
driver = RunChrome(url)

xPath_Target = '/html/body/div[1]/div[2]/div/img'
elemnet_Target = driver.find_element_by_xpath(xPath_Target)
SaveAs(driver, elemnet_Target)