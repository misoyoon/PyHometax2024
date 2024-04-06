import pyautogui
import time

print('현재 마우스위치=' + str(pyautogui.position()))

""" 
# 이미지 저장
#pyautogui.screenshot('9.png', region=(2285, 604, 30, 30))


# 방법1
b7 = pyautogui.locateOnScreen('7.png')
bq = pyautogui.center(b7)
pyautogui.click(bq)

"""
# 방법2
num7 = pyautogui.locateCenterOnScreen('7.png')
num8 = pyautogui.locateCenterOnScreen('8.png')
num9 = pyautogui.locateCenterOnScreen('9.png')
pyautogui.click(num7)
pyautogui.click(num8)
pyautogui.click(num9)

