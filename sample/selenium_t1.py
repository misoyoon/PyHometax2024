from selenium import webdriver
import pandas as pd
import time 

df = pd.read_csv("tmp_data.csv")
print(df)

# 크롤링 프로그램 제작 
def confirm_closure(df): 
    driver = webdriver.Chrome("chromedriver") # chromedriver.exe 파일 위치
    url = "https://teht.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/ab/a/a/UTEABAAA13.xml"
    driver.get(url)
    
    time.sleep(3)
    
    result_list = [] 
    for reg_no in df['가맹점 번호'] : 
        driver.find_element(By.ID, 'bsno').send_keys(reg_no) # 가맹점 번호 입력칸 
        driver.find_element(By.ID, 'trigger5').click() # 확인 버튼
        time.sleep(2)
        result = driver.find_element(By.ID, "grid2_cell_0_1").text # 결과값 리턴
#         print(result)
        rst = None
        if '폐업자' in result:
            rst = '폐업/' + result.split("폐업일자:")[1].split(")")[0] 
        elif '일반과세자' in result:
            rst = '일반'
        else: 
            rst = '미등록'
        result_list.append(rst)
        time.sleep(1)
    driver.close()
    return pd.Series(result_list)


#함수 활용, 결과값 확인 
df['결과'] = confirm_closure(df)
print(df)