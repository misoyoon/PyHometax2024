from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


import shutil
import time
import os

from common import *
import dbjob
import pymysql

TAX_NAME = "위택스 지방소득세(양도소득세분)"
url = 'https://www.wetax.go.kr/main/https://www.wetax.go.kr/main?cmd=LPEPBC0R0'


# 작업폴더
project_dir = os.path.dirname(sys.modules['__main__'].__file__)

conn = dbjob.connect_db()

def insert_autit_we(pay_type, tax_type, holder_nm, tax, pay_to_date, wetax_reg_dt, si_do, wetax_reg_num) :
    curs = conn.cursor(pymysql.cursors.DictCursor)

    param = (pay_type, tax_type, holder_nm, tax, pay_to_date, wetax_reg_dt, si_do, wetax_reg_num)
    curs = conn.cursor()
    sql = """
        INSERT INTO taxweb.audit_we
        (pay_type, tax_type, holder_nm, tax, pay_to_date, wetax_reg_dt, si_do, wetax_reg_num, holder_ssn1, reg_dt)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, '', CURRENT_TIMESTAMP);
    """
    curs.execute(sql, param)
    conn.commit()


def init_selenium() :
    cur_dir = os.getcwd()
    chromedriver_path =  cur_dir + os.sep + "pyHometax" + os.sep + "chromedriver.exe" #resource_path("chromedriver.exe")
    print("크롬드라이버 위치=%s" % chromedriver_path)

    # 1.크롬접속
    driver = webdriver.Chrome(chromedriver_path)

    # 브라우저 위치 조정하기
    driver.set_window_position(0,0)
    # 브라우저 화면 크기 변경하기
    driver.set_window_size(1250, 1400)

    # Implicitly wait을 10초로 설정하면 페이지가 로딩되는데 10초까지 기다립니다. 
    # 만약 페이지 로딩이 2초에 완료되었다면 더 기다리지 않고 다음 코드를 수행합니다. 
    # 기본 설정은 0초로 되어있고, 
    # 한번만 설정하면 driver를 사용하는 모든 코드에 적용이 됩니다.
    driver.implicitly_wait(5)

    return driver

def login_use_cookie(driver, jsession_id, WMONID=""):
    global url
    driver.get("https://www.wetax.go.kr/main/")

    driver.delete_all_cookies()

    #  1) 홈택스로 이동
    cookie1 = {
        'name'  : 'JSESSIONID', 
        'value' : jsession_id,
        'path'  : '/main',
        'domain': 'www.wetax.go.kr',
        }
    cookie2 = {
        'name'  : 'WMONID', 
        'value' : WMONID,
        'path'  : '/',
        'domain': 'www.wetax.go.kr',
        }
    driver.add_cookie(cookie1)
    driver.add_cookie(cookie2)
    # driver.add_cookie({'name':"nosTodayYn", 'value':'Y', 'path':'/', 'domain':'www.wetax.go.kr'})
    # driver.add_cookie({'name':"scale", 'value':'1', 'path':'/', 'domain':'www.wetax.go.kr'})
    # driver.add_cookie({'name':"chkSimple", 'value':'Y', 'path':'/', 'domain':'www.wetax.go.kr'})
    # driver.add_cookie({'name':"nowZoom", 'value':'100', 'path':'/', 'domain':'www.wetax.go.kr'})

    time.sleep(1)


jsession_id = "LWZP8aOqaf8GElz7zjFZVl3Gm4PFu9eEn0gK964lYN3ydQXExIRMcs6CehPF6jv1.amV1c19pbHRzcHMvaWx0c3BuLXdhczgtMw=="
WMONID = "jlbM8cmzDZJ"
start_date = "20240501"
to_date    = "20240531"
select_text= "지방소득세(양도소득분)"


if __name__ == '__main__':
    driver = init_selenium()
    login_use_cookie(driver, jsession_id, WMONID)

    driver.get("https://www.wetax.go.kr/main/https://www.wetax.go.kr/main?cmd=LPEPBC0R0")
    time.sleep(4)

    # 정렬 : 신고일
    driver.find_element(By.CSS_SELECTOR, "#main_form > fieldset > div.search_box > div.cont_body > div > div.table_row > table > tbody > tr:nth-child(3) > td:nth-child(4) > label:nth-child(1)")
    time.sleep(0.2)

    driver.find_element(By.ID, 'sFrom_date').clear()
    time.sleep(0.5)
    driver.find_element(By.ID, 'sFrom_date').send_keys(start_date)
    time.sleep(0.5)
    driver.find_element(By.ID, 'sTo_date').clear()
    time.sleep(0.5)
    driver.find_element(By.ID, 'sTo_date').send_keys(to_date)
    time.sleep(0.5)

    select = Select(driver.find_element(By.ID, "sTaxItem"))
    select.select_by_visible_text(select_text)
    time.sleep(0.5)

    # 정렬순서 : 신고일 선택
    driver.find_element(By.CSS_SELECTOR, "#orderRadio1 ~ span").click()
    time.sleep(0.5)

    # 검색
    driver.find_element(By.CSS_SELECTOR, "#searchBtn > a").click()
    
    f = open("위택스_지방세_20240518.csv", 'w',encoding='utf8')

    page = 1
    while True:
        time.sleep(2)
        table = None
        try:
            table = driver.find_element(By.CSS_SELECTOR, "#list_form > fieldset > div.content_box > div.cont_body > div.board.half > div.table_list > div.table_col.fixed_table > table > tbody > tr > td > div > table > tbody")
        except:
            print("재시도")
            time.sleep(3)
            table = driver.find_element(By.CSS_SELECTOR, "#list_form > fieldset > div.content_box > div.cont_body > div.board.half > div.table_list > div.table_col.fixed_table > table > tbody > tr > td > div > table > tbody")

        print ("============== page= %d" % (page,))

        row = 0
        for tr in table.find_elements(by=By.TAG_NAME, value="tr"):
            row =+ 1
            td = tr.find_elements(by=By.TAG_NAME, value="td")

            pay_type = td[1].text.strip(),
            tax_type = td[2].text.replace('\n','').strip(),
            holder_nm = td[3].text.strip(),
            tax = int(td[4].text.replace(',','').replace('원','').strip()),
            pay_to_date = td[5].text.strip(),
            wetax_reg_dt = td[6].text.strip(),
            si_do = td[7].text.strip().replace('\n','').replace('대행인 신고건',''),
            wetax_reg_num = td[8].text.strip()
            s = "{}|{}|{}|{}|{}|{}|{}|{}\n".format(pay_type, tax_type, holder_nm, tax, pay_to_date, wetax_reg_dt, si_do, wetax_reg_num)

            # 파일출력
            f.write(s)

            # DB 입력
            insert_autit_we(pay_type, tax_type, holder_nm, tax, pay_to_date, wetax_reg_dt, si_do, wetax_reg_num)

            print(f'    {row} - {holder_nm}')

        next_btn = driver.find_element(By.CSS_SELECTOR, "#list_form > fieldset > div.content_box > div.cont_body > div.board.half > div.table_list > div.pagination > a.next")
        #print(next_btn)

        if next_btn != None:
            page += 1
            next_btn.click()
        else :
            break

    f.close()

    time.sleep(60)
    driver.close()
            
    exit(0)

