import pymysql
import common

import re
import sys, os
import copy
from collections import OrderedDict

'''
위택스, 홈택스에서 법정동코드 (10자리)를 구하기 위한 코드

[변경이력]
Created 2024-03-01

---------------------------------------------------------
경기도 광주시
---------------------------------------------------------
4161025932	경기도	광주시	연곡리	곤지암읍
4161025934	경기도	광주시	열미리	곤지암읍
4161034024	경기도	광주시	영동리	퇴촌면
4161034026	경기도	광주시	오리	퇴촌면
4161037026	경기도	광주시	오전리	남한산성면
4161025933	경기도	광주시	오향리	곤지암읍
4161025327	경기도	광주시	용수리	초월읍
4161034023	경기도	광주시	우산리	퇴촌면
4161035028	경기도	광주시	우천리	남종면
4161034029	경기도	광주시	원당리	퇴촌면
4161025928	경기도	광주시	유사리	곤지암읍
4161033022	경기도	광주시	유정리	도척면
4161035023	경기도	광주시	이석리	남종면
4161025926	경기도	광주시	이선리	곤지암읍
4161025931	경기도	광주시	장심리	곤지암읍
4161011100	경기도	광주시	장지동	광남1동
4161034030	경기도	광주시	정지리	퇴촌면
4161010800	경기도	광주시	중대동	광남1동
4161025329	경기도	광주시	지월리	초월읍
4161010900	경기도	광주시	직동	광남1동
4161033028	경기도	광주시	진우리	도척면
4161025300	경기도	광주시	초월읍	초월읍
4161033024	경기도	광주시	추곡리	도척면
4161011800	경기도	광주시	추자동	오포1동
4161010500	경기도	광주시	탄벌동	탄벌동
4161011000	경기도	광주시	태전동	광남1동
4161011000	경기도	광주시	태전동	광남2동
4161034000	경기도	광주시	퇴촌면	퇴촌면
4161037025	경기도	광주시	하번천리 남한산성면
4161025325	경기도	광주시	학동리	초월읍
4161010400	경기도	광주시	회덕동	탄벌동
---------------------------------------------------------
'''

class addr_legal :
    
    def __init__(self, conn=None, addr='') -> None:
        self.conn = conn
        self.addr = addr
        self.addr_legal_cd = ''
        
        
        (si_do, si_gun_gu, dong_li) = self.fn_주소분석()
        if not  si_gun_gu:
            addrs = self.addr.split()
            si_gun_gu = addrs[1]
        
        # 세종시는 시군구값이 없음
        if si_do == '세종특별자치시':
            si_gun_gu = ''
        
        
        if not dong_li:
            print(f"ERROR dong_li=null : addr={self.addr}")
        else:
            #print(f"{self.addr}  ===> si_do:{si_do} si_gun_gu:{si_gun_gu} dong_li:{dong_li}")
            rs = self.select_addr_legal(dong_li, si_do, si_gun_gu)
            
            if not rs:
                #print("######################## select_addr_legal_2")
                rs = self.select_addr_legal_2(dong_li, si_do, si_gun_gu)
            
            if not rs:
                print(f"결과없음 : {self.addr}  ===> si_do:{si_do} si_gun_gu:{si_gun_gu} dong_li:{dong_li}")
            #for row in rs:
            #    print(row)
    
    def get_addr_legal_cd(self):
        return self.addr_legal_cd
    
    
    def fn_주소분석(self):
        si_do = ''
        si_gun_gu = ''
        dong_li = ''
        eubmyeon = ''  # 읍면
        
        addrs = self.addr.split()  # split()는 기본적으로 white space에 대해서 분리해 줌
        si_do = self.fn_시도명_표준화(addrs[0])
        #si_gun_gu = addrs[1]
        
        tmp = addrs[1][-1]
        tmpl = tmp[-1]
        if addrs[1][-1] == '동' or addrs[1][-1] == '읍' or addrs[1][-1] == '면' or addrs[1][-1] == '리':
            dong_li = addrs[1]
        elif addrs[2][-1] == '동' or addrs[2][-1] == '읍' or addrs[2][-1] == '면' or addrs[2][-1] == '리':
            si_gun_gu = addrs[1]
            dong_li = addrs[2]
        elif len(addrs)>3 and (addrs[3][-1] == '동' or addrs[3][-1] == '읍' or addrs[3][-1] == '면' or addrs[3][-1] == '리'):
            si_gun_gu = addrs[1]
            dong_li = addrs[3]
        
        #dong_li 검사 후 계속 진행 여부 판단하기
        if dong_li:
            # 숫자 제거 후 '동'만 있으면 실패로 간주하여 계속 진행
            dong_li_tmp = re.sub(r'\d', '', dong_li)
            if dong_li_tmp != '동':
                return (si_do, si_gun_gu, dong_li) 
        
        # 주소에 포함된 괄호 내부 내용만 추출
        if self.addr.find('(') >=0 and self.addr.find(')') >=0:
            p = re.compile('\(([^)]+)')
            addr_etc = p.findall(self.addr)
            if addr_etc:
                dong_li_tmp = addr_etc[0]
                # 괄호안에 2개 이상의 정보가 있을 경우 (반포동,반포자이아파트)
                if dong_li_tmp.find(',') >= 0:
                    dong_li = dong_li_tmp.split(',')[0]
                else:
                    dong_li = dong_li_tmp
                
                if dong_li.find(' '):
                    dong_li = dong_li.split()[0]
        
            if not dong_li:
                print(f'CASE1, 동리없음 : 주소={self.addr}, 시도={si_do}, 시군구={si_gun_gu}, 동리={dong_li} ')
            elif dong_li[-1] != '동' and dong_li[-1] != '리' and dong_li[-1] != '가':
                print(f'CASE1, 동명이 [동][리][가]로 끝나지 않음 : {self.addr}, 시도={si_do}, 시군구={si_gun_gu}, 동리={dong_li} ')
            else:
                si_gun_gu = '' # 알수 있는 방법이 있나???
                pass  # 정상처리로 판단
        else:
            # 괄호가 없는 경우 처리
            dong_li = addrs[2]
            if dong_li[-1] == '구':
                dong_li = addrs[3]
                if dong_li[-1] != '동' and dong_li[-1] != '리' and dong_li[-1] != '가':
                    msg = 'CASE2-1, 동명이 [동][리][가]로 끝나지 않음 : {0:<100}, 시도={1}, 시군구={2}, 동리={3}'.format(self.addr, si_do, si_gun_gu, dong_li)
                    print(msg)
                else:
                    si_gun_gu = addrs[2]
                    pass # 정상처리로 판단
                    #print(f'CASE2-1 로 정상처리 : {self.addr} 동리={dong_li}')
            if dong_li[-1] == '면':
                dong_li = addrs[3]
                si_gun_gu = addrs[2]
                # 정상처리
            elif dong_li[-1] != '동' and dong_li[-1] != '리' and dong_li[-1] != '가':
                msg = 'CASE2, 동명이 [동][리][가]로 끝나지 않음 : {0:<100}, 시도={1}, 시군구={2}, 동리={3}'.format(self.addr, si_do, si_gun_gu, dong_li)
                print(msg)

        return (si_do, si_gun_gu, dong_li)


    def fn_시도명_표준화(self, si_do):
        ret = si_do
        if si_do.find('서울') >=0: 
            ret = '서울특별시'
        elif si_do.find('경기') >=0: 
            ret = '경기도'
        elif si_do.find('부산') >=0: 
            ret = '부산광역시'
        elif si_do.find('인천') >=0: 
            ret = '인천광역시'
        elif si_do.find('대전') >=0: 
            ret = '대전광역시'
        elif si_do.find('울산') >=0: 
            ret = '울산광역시'
        elif si_do.find('광주') >=0: 
            ret = '광주광역시'
        elif si_do.find('대구') >=0: 
            ret = '대구광역시'
        elif si_do.find('세종') >=0: 
            ret = '세종특별자치시'
        elif si_do.find('전남') >=0 or si_do.find('전라남도') >=0: 
            ret = '전라남도'
        elif si_do.find('전북') >=0 or si_do.find('전라북도') >=0: 
            ret = '전북특별자치도'
        elif si_do.find('충남') >=0 or si_do.find('충청남도') >=0: 
            ret = '충청남도'
        elif si_do.find('충북') >=0 or si_do.find('충청북도') >=0: 
            ret = '충청북도'
        elif si_do.find('경남') >=0 or si_do.find('경상남도') >=0: 
            ret = '경상남도'
        elif si_do.find('경북') >=0 or si_do.find('경상북도') >=0: 
            ret = '경상북도'
        elif si_do.find('강원') >=0: 
            ret = '강원특별자치도'
        elif si_do.find('제주') >=0: 
            ret = '제주특별자치도'
        
        return ret
            

    # 기본정보
    def select_addr_legal(self, dong_li, si_do='', si_gun_gu=''):
        param = (dong_li, )
        rs = None
        curs = self.conn.cursor(pymysql.cursors.DictCursor)

        sql = '''
            SELECT *
            FROM addr_legal_dong 
            WHERE dong_li = %s
        '''
        
        if si_do :
            sql += f' AND si_do = %s'
            param = (dong_li, si_do)
        if si_gun_gu:
            sql += f" AND si_gun_gu LIKE CONCAT(%s, '%%')"
            param = (dong_li, si_do, si_gun_gu)
            
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        return rs

    def select_addr_legal_2(self, dong_li, si_do='', si_gun_gu=''):
        param = (dong_li, )
        rs = None
        curs = self.conn.cursor(pymysql.cursors.DictCursor)

        sql = '''
            SELECT *
            FROM addr_legal_dong 
            WHERE dong = %s
        '''
        
        if si_do :
            sql += f' AND si_do = %s'
            param = (dong_li, si_do)
        if si_gun_gu:
            sql += f' AND si_gun_gu = %s'
            param = (dong_li, si_do, si_gun_gu)
            
        common.logqry(sql, param)
        curs.execute(sql, param)
        
        # 데이타 Fetch
        rs = curs.fetchall()
        return rs    