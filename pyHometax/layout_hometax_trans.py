import pymysql
import common

import re
import sys, os
import copy
from collections import OrderedDict

'''
홈택스 양도소득세 신고를 위한 전자파일 생성


[기타정보]
  - 납세지 법정동코를 위해 2,3,5 자리를 하나의 필드로 합침

[변경이력]
Created 2024-03-01
'''

class wetax_ele_form :
  CRLF = "\r\n"

  VAR_VALUE = {
        '__세무프로그램코드__'   : '9000' 
    ,   '__the1_법인명__'        : '세무법인더원' 
    ,   '__the1_법인대표명__'    : '김경수'
    ,   '__the1_법인번호__'      : '1101710068286'  
    ,   '__the1_사업자번호__'    : '1208777823' 
    ,   '__the1_대표전화번호__'  : '02-514-0910' 
    # 해외주식 양도소득세 관련 고정값
    ,   '__납세자_구분__'        : '01'  # 01:내국인, 02:외국인, 11:종중,문종, 19:기타단체
    ,   '__신고구분__'           : '11'  # 11:확정신고, 13:예정신고
    ,   '__신고유형__'           : '7'   # 7:해외주식, 2:(예정)국내주식
    ,   '__거주구분__'           : '1'   # 1:거주자, 2:비거주자
    ,   '__거주지국코드__'       : 'KR'  
    ,   '__양도자산종류코드__'   : '11'  
    ,   '__세율__'               : '2000'  
    # 아래의 내용은 매년 변경할 것 !!!
    ,   '__귀속년도__'           : '2023'  
    ,   '__납부기한__'           : '20240531'  
    ,   '__양도소득년월__'       : '202312'  
    ,   '__양도일자__'           : '20231231'  
    
    
    # 테스트를 위해 일부러 중복설정   <=================== 테스트를 위해 임시 변경
    ,   '__신고구분__'           : '13'   # 13:예정신고
    ,   '__신고유형__'           : '2'    # 2:(예정)국내주식
    ,   '__납부기한__'           : '20240430'  
    ,   '__양도소득년월__'       : '202306'  
  }


  # ------------------
  # class 
  # 종류      : FIX, DATE, CODE    
  # 자체 추가 : VAR, DB, PRO[GRAM]


  MAPPING_DB2LAYOUT = [
    { 'record':'02C116300', 'key':'납세자_주민번호',           'dbcol':'holder_ssn'} ,
    { 'record':'02C116300', 'key':'납세자_성명',               'dbcol':'holder_nm'} ,
    { 'record':'02C116300', 'key':'납세자_우편번호(현재주소)', 'dbcol':'holder_zip'} ,
    { 'record':'02C116300', 'key':'납세자_주소(현재주소)',     'dbcol':'holder_full_addr'} ,
    { 'record':'02C116300', 'key':'납세지_법정동코드',         'dbcol':'addr_legal_cd'} ,
    { 'record':'02C116300', 'key':'휴대전화',                  'dbcol':'holder_cellphone'} ,
    { 'record':'02C116300', 'key':'이메일(전자우편)',          'dbcol':'holder_email'} ,
    { 'record':'03C116300', 'key':'양도소득_과세표준',         'dbcol':'result_base_amount'} ,
    { 'record':'03C116300', 'key':'산출세액',                  'dbcol':'result_wetax_tax'} ,
    { 'record':'03C116300', 'key':'납부할_총세액',             'dbcol':'result_wetax_tax_floor'} ,
  ]
  


  def __init__(self, conn=None, ht_series_yyyymm='', group_id='', ht_tt_seq='') -> None:
    # 최종결과 string
    self.result_text = ''
    
    self.conn = conn
    self.ht_series_yyyymm = ht_series_yyyymm
    self.group_id = group_id
    self.ht_tt_seq = ht_tt_seq

    # DB에서 가져와서 차후 설정    
    self.holder_nm = ''

    # FIX  : 레이아웃 자체에서 고정된 값
    # FIX2 : 프로그램 자체적으로 변동없는 고정값
    self.layout_data = {
      '01C116300': {
          '자료구분':                  {'num':1 ,  'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'01'}
        , '서식코드':                  {'num':2,   'val':None,  'len':7,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'C116300'}
        , '납세자ID':                  {'num':3,   'val':None,  'len':13,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'holder_id'}
        , '납세자구분':                {'num':4,   'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__납세자_구분__'}
        , '세목코드':                  {'num':5,   'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'22'}
        , '신고구분코드':              {'num':6,   'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__신고구분__'}
        , '신고유형':                  {'num':7,   'val':None,  'len':1,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__신고유형__'}
        , '과세기간_년월':             {'num':8,   'val':None,  'len':6,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__양도소득년월__'}
        , '신고구분상세코드':          {'num':9,   'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__신고구분__'}
        , '신고서종류코드':            {'num':10,  'val':None,  'len':3,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'001'}
        , '민원종류코드':              {'num':11,  'val':None,  'len':5,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'FD001'}
        , '사용자ID':                  {'num':12,  'val':None,  'len':20,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'user_id'}
        , '제출년월':                  {'num':13,  'val':None,  'len':6,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__귀속년도__'}
        , '성명':                      {'num':14,  'val':None,  'len':30,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'holder_nm'}
        , '은행코드(국세환급금)':      {'num':15,  'val':None,  'len':3,   'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'bank_code'}
        , '계좌번호(국세환급금)':      {'num':16,  'val':None,  'len':20,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'account_number'}
        , '예금종류':                  {'num':17,  'val':None,  'len':20,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'deposit_type'}
        , '세무대리대표자주민등록번호':{'num':18,  'val':None,  'len':13,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'rep_id'}
        , '세무대리대표자성명':        {'num':19,  'val':None,  'len':30,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'rep_name'}
        , '세무대리인전화번호':        {'num':20,  'val':None,  'len':12,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'rep_phone'}
        , '세무대리사업자등록번호':    {'num':21,  'val':None,  'len':10,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'rep_business_id'}
        , '세무대리인관리번호':        {'num':22,  'val':None,  'len':6,   'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'rep_manage_id'}
        , '세무프로그램코드':          {'num':23,  'val':None,  'len':4,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'SW001'}
        , '작성일자':                  {'num':24,  'val':None,  'len':8,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__작성일자__'}
        , '양도일자':                  {'num':25,  'val':None,  'len':8,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__양도일자__'}
        , '세무대리인성명':            {'num':26,  'val':None,  'len':60,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'agent_name'}
        , '세무대리인생년월일':        {'num':27,  'val':None,  'len':8,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__생년월일__'}
        , '공란':                      {'num':28,  'val':None,  'len':47,  'type':'CHAR',   'null':True,  'class':'SPACE', 'fixval':''}
      }                            
      ,'02C116300' : {
            '자료구분':                   {'num':1 ,  'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'02'}
          , '서식코드':                   {'num':2,   'val':None,  'len':7,   'type':'CHAR',   'null':False, 'class':'FIX',   'fixval':'C116300'}
          , '납세자_주민번호':            {'num':3,   'val':None,  'len':13,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'holder_ssn'}
          , '납세자_성명':                {'num':4,   'val':None,  'len':80,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'holder_nm'}
          , '납세자_우편번호(현재주소)':  {'num':5,   'val':None,  'len':6,   'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'holder_zip'}
          , '납세자_주소(현재주소)':      {'num':6,   'val':None,  'len':200, 'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'holder_full_addr'}
          , '납세지_우편번호':            {'num':7,   'val':None,  'len':6,   'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'holder_zip'}
          , '납세지_주소':                {'num':8,   'val':None,  'len':200, 'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'holder_full_addr'}
          #, '납세지_시도코드':            {'num':9,   'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'DB',    'fixval':''}
          #, '납세지_시군구코드':          {'num':10,  'val':None,  'len':3,   'type':'CHAR',   'null':False, 'class':'DB',    'fixval':''}
          #, '납세지_법정동코드':          {'num':11,  'val':None,  'len':5,   'type':'CHAR',   'null':False, 'class':'DB',    'fixval':''}
          , '납세지_법정동코드':          {'num':11,  'val':None,  'len':10,  'type':'CHAR',   'null':False, 'class':'DB',    'fixval':'addr_legal_cd'}
          , '납세자_구분':                {'num':12,  'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__납세자_구분__'}
          , '신고구분':                   {'num':13,  'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__신고구분__'}
          , '신고유형':                   {'num':14,  'val':None,  'len':1,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__신고유형__'}
          , '귀속년도':                   {'num':15,  'val':None,  'len':4,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__귀속년도__'}
          , '양도소득년월':               {'num':16,  'val':None,  'len':6,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__양도소득년월__'}
          , '전화번호':                   {'num':17,  'val':None,  'len':16,  'type':'CHAR',   'null':True,  'class':'VAR',   'fixval':'__the1_대표전화번호__'}
          , '휴대전화':                   {'num':18,  'val':None,  'len':16,  'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'holder_cellphone'}
          , '이메일(전자우편)':           {'num':19,  'val':None,  'len':100, 'type':'CHAR',   'null':True,  'class':'DB',    'fixval':'holder_email'}
          , '거주구분':                   {'num':20,  'val':None,  'len':1,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__거주구분__'}
          , '거주지국코드':               {'num':21,  'val':None,  'len':2,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__거주지국코드__'}
          , '양수인_주민등록번호':        {'num':22,  'val':None,  'len':13,  'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '양수인_성명':                {'num':23,  'val':None,  'len':80,  'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '양수인_분자지분율':          {'num':24,  'val':None,  'len':11.3,'type':'NUMBER', 'null':False, 'class':'FIX2',  'fixval':'0'}
          , '양수인_분모지분율':          {'num':25,  'val':None,  'len':11.3,'type':'NUMBER', 'null':False, 'class':'FIX2',  'fixval':'0'}
          , '양도인_관계코드':            {'num':26,  'val':None,  'len':2,   'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '양도자산종류코드':           {'num':27,  'val':None,  'len':2,   'type':'CHAR',   'null':True,  'class':'VAR',   'fixval':'__양도자산종류코드__'}
          , '양도일자':                   {'num':28,  'val':None,  'len':8,   'type':'CHAR',   'null':False, 'class':'VAR',   'fixval':'__양도일자__'}
          , '양도물건지_우편번호':        {'num':29,  'val':None,  'len':6,   'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '양도물건지_주소':            {'num':30,  'val':None,  'len':130, 'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '은행코드(환급금)':           {'num':31,  'val':None,  'len':3,   'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '계좌번호(환급금)':           {'num':32,  'val':None,  'len':20,  'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
          , '국적코드':                   {'num':33,  'val':None,  'len':2,   'type':'CHAR',   'null':True,  'class':'',      'fixval':''}
      }
      ,'03C116300' : {
            '자료구분':                   {'num':1 ,  'val':None,  'len':2,   'type':'CHAR',   'null':False,  'class':'FIX',  'fixval':'03'}
          , '서식코드':                   {'num':2,   'val':None,  'len':7,   'type':'CHAR',   'null':False,  'class':'FIX',  'fixval':'C116300'}
          , '개별_합계':                  {'num':3,   'val':None,  'len':1,   'type':'CHAR',   'null':False,  'class':'FIX2', 'fixval':'2'} # [1|2]
          , '국내외구분코드':             {'num':4,   'val':None,  'len':1,   'type':'CHAR',   'null':False,  'class':'FIX2', 'fixval':'2'} # [1|2] 
          , '세율구분코드':               {'num':5,   'val':None,  'len':2,   'type':'CHAR',   'null':False,  'class':'FIX2', 'fixval':'61'} # 위의 개는  프로그램을 판단 => 최종 [2261|1200] 둘중하나
          , '양도소득_과세표준':          {'num':6,   'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'DB',   'fixval':'result_base_amount'} # 원단까지 출력
          , '세율':                       {'num':7,   'val':None,  'len':4.3, 'type':'NUMBER', 'null':False,  'class':'VAR',  'fixval':'__세율__'}
          , '산출세액':                   {'num':8,   'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'DB',   'fixval':'result_wetax_tax'} # 원단까지 출력
          , '감면세액':                   {'num':9,   'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '외국납부세액공제':           {'num':10,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '예정신고납부세액공제':       {'num':11,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '특별징수세액공제':           {'num':12,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '신고불성실가산구분':         {'num':13,  'val':None,  'len':2,   'type':'CHAR',   'null':True,   'class':'',     'fixval':''}
          , '부정신고사유':               {'num':14,  'val':None,  'len':2,   'type':'CHAR',   'null':True,   'class':'',     'fixval':''}
          , '신고불성실가산적용세율':     {'num':15,  'val':None,  'len':5.4, 'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '부정신고적용과표':           {'num':16,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '무신고_가산세':              {'num':17,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '기타_가산세':                {'num':18,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '납부지연_가산세':            {'num':19,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '납부지연일수':               {'num':20,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '가산세(합계)':               {'num':21,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '기신고_조정공제':            {'num':22,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
          , '납부할_총세액':              {'num':23,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'DB',   'fixval':'result_wetax_tax_floor'} # 원단 절사
          , '전자신고_세액공제':          {'num':24,  'val':None,  'len':14,  'type':'NUMBER', 'null':False,  'class':'FIX2', 'fixval':'0'}
      }
    }

    # 결과 text 생성
    #self.make_electric_string()
  # // 생성자 끝

  def get_result_text(self):
    return self.result_text

  def set_val(self, type, length, val):
    ret_val = ''
    #val_euc_kr = val.encode("euc-kr")
    
    if type == 'CHAR':
      if not val: 
        val =''

      ret_val = self.padding(length, val, ' ', True)
    elif type == 'NUMBER':
      str_val = str(val)
      ret_val = self.padding(int(length), str_val, '0', False)   # int() -> 소수점 제거
    else:
      sys.exit("ERROR NO=2 : type은 CHAR 혹은 NUMBER 값만 가질 수 있습니다.")
    
    #print(f'@@ len={length} [{ret_val}]')
    
    return ret_val


  # 패딩하기
  def padding(self, length, val, padding_char, is_right=True):
    korLen = self.korlen(val)
    if korLen > length:
      tmpLen = len(val)
      for i in range(tmpLen):
        val = val[0:tmpLen-i]
        korLen = self.korlen(val)
        if korLen <= length: break
    
    if is_right:
      ret_val = val + padding_char * (length-korLen)
    else:
      ret_val = padding_char * (length-korLen) + val
      
    return ret_val

  def check_value_len(self):
    # 최종 val 모양 formatting 하기
    for record in self.layout_data.keys():
      #print('L1 -------', record)
      for field in self.layout_data[record]:
        formated_val = ''
        
        #print('L2 -----------------', field)
        clazz  = self.layout_data[record][field]['class']
        type   = self.layout_data[record][field]['type']
        length = int(self.layout_data[record][field]['len'])  # int() -> 소수점 제거
        fixval = self.layout_data[record][field]['fixval']
        curval = self.layout_data[record][field]['val']
        
        korLen = self.korlen(curval)
        if length != korLen:
          print(f'길이 점검 오류 : field={field}, len={length}, val len={korLen}, val=[{curval}]')

  # 한글 한글자를 2로 계산하는 len() 함수
  def korlen(self, str):
    korP = re.compile('[\u3131-\u3163\uAC00-\uD7A3]+', re.U)
    temp = re.findall(korP, str)    
    temp_len = 0    
    for item in temp:
      temp_len = temp_len + len(item)
    retval = len(str) + temp_len
    
    # print(f"############## {retval} [{str}]")
    return retval

  #def get_data_for_var(self, key): 
  #  return self.FIX2_VALUE_LIST[key]

  def to_amt(self, key):
    ret_val = key
    
    return ret_val
  
  def __str__(self):
    ret_val = ''
    
    for record in self.layout_data.keys():
    
      for field in self.layout_data[record]:
    
        #print('L2 -----------------', field)
        clazz  = self.layout_data[record][field]['class']
        type   = self.layout_data[record][field]['type']
        length = self.layout_data[record][field]['len']
        fixval = self.layout_data[record][field]['fixval']
        val    = self.layout_data[record][field]['val']
        
        ret_val += f'{field} : len={length}, clazz={clazz} val=[{val}]'
        
    return ret_val

  # ======================================================================================================================  
  # DB 연결
  # ======================================================================================================================  
  # 기본정보
  def select_ht_tt_by_key(self):
    param = (self.group_id, self.ht_series_yyyymm, self.ht_tt_seq)
    rs = None
    curs = self.conn.cursor(pymysql.cursors.DictCursor)

    sql = '''
      SELECT *
        , concat(holder_ssn1, holder_ssn2) holder_ssn
        , if(total_income_amount-2500000>=0, total_income_amount-2500000, 0) result_base_amount
        -- , if(total_income_amount-2500000>=0, FLOOR((total_income_amount-2500000) * 0.2 ), 0) result_hometax_tax
        , if(total_income_amount-2500000>=0,    FLOOR((total_income_amount-2500000) * 0.02), 0) result_wetax_tax
        , if(total_income_amount-2500000>=0, TRUNCATE((total_income_amount-2500000) * 0.02, -1), 0) result_wetax_tax_floor
      FROM ht_tt 
      WHERE ifnull(use_yn, 'Y') != 'N'
          AND group_id = %s
          AND ht_series_yyyymm = %s
          -- AND data_type = 'AUTO' AND step_cd = 'REPORT' AND au1='S'
          AND ht_tt_seq = %s
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    row = curs.fetchone()

    return row

  # 계좌정보 (현재 사용안함)
  def select_ht_tt_list_by_key(self):
    param = (self.ht_tt_seq, )
    rs = None
    curs = self.conn.cursor(pymysql.cursors.DictCursor)

    sql = '''
      SELECT *
      FROM ht_tt_list
      WHERE ht_tt_seq = %s
      ORDER BY ht_tt_list_seq ASC
    '''
    common.logqry(sql, param)
    curs.execute(sql, param)
    
    # 데이타 Fetch
    rs = curs.fetchall()

    return rs

  # 개별 생성 내용을 파일로 쓰기
  def make_file_for_one(self):
    if not self.result_text:
      return False

    #print(result_text)
    filename = f'{self.VAR_VALUE["__귀속년도__"]}_양도소득지방세_{self.holder_nm}_{self.ht_tt_seq}.y11'
    euc_kr = self.result_text.encode("euc-kr")
    with open(filename, 'wb') as f:
      f.write(euc_kr)

    file_size = os.path.getsize(filename)
    print(f'file size={file_size} byte')
    return True

  # 복수개의 신고건을 하나의 파일로 생성할 경우 이용
  def make_file_for_many(self, contents, filepath):
    if not contents:
      return False

    #print(result_text)
    euc_kr = contents.encode("euc-kr")
    with open(filepath, 'wb') as f:
      f.write(euc_kr)

    file_size = os.path.getsize(filepath)
    print(f'file size={file_size} byte')
    return True
  
  # 이미  생성된 전자파일을 입력 받아 화면에 출력한다 (점검용)
  def print_file_value_for_debug(self, filepath) :
    f = open(filepath, 'r', encoding='euc-kr')
    for line in f:
      print(line)
      header = line[0:9]
      
      cur_pos = 0
      record = self.layout_data[header]
      for header_key in record.keys():
        #print(header_key)
        field = record[header_key]
        field_len = field['len']
        print(f'{header_key} : {int(field_len)} : [{line[cur_pos:cur_pos+field_len]}]')
        cur_pos += field_len
    f.close()

  def kor_trim(str_msg, int_max_len=80, encoding='euc-kr'):
      try:
          return str_msg.encode(encoding)[:int_max_len].decode(encoding)
      except UnicodeDecodeError:
          try:
              return str_msg.encode(encoding)[:int_max_len-1].decode(encoding)
          except UnicodeDecodeError:        
              return str_msg.encode(encoding)[:int_max_len-2].decode(encoding)    
  # ======================================================================================================================  
  # Main 함수
  # ======================================================================================================================  
  def make_electric_string(self):
    ht_info = self.select_ht_tt_by_key()
    #dbrs  = self.select_ht_tt_list_by_key()
    
    if not ht_info:
      print("DB 조회 결과가 없습니다.")
      return None
    else:
      print(ht_info)
      self.holder_nm = ht_info['holder_nm']
          
    # DB값 넣기
    for field in self.MAPPING_DB2LAYOUT:
      record = field['record']
      key = field['key']
      dbcol = field['dbcol']

      dbval = ht_info[dbcol]
      self.layout_data[record] 
      #print(record, key, dbcol, val)
      
      self.layout_data[record][key]['val'] = dbval
      #print(self.layout_data[record][key]['val'])

    # 고정값 넣기
    for record in self.layout_data.keys():
      #print('L1 -------', record)
      for field in self.layout_data[record]:
        clazz  = self.layout_data[record][field]['class']
        if clazz == 'VAR':
          fixval = self.layout_data[record][field]['fixval']
          self.layout_data[record][field]['val'] = self.VAR_VALUE[fixval]
        elif clazz == 'DB':
          fixval = self.layout_data[record][field]['fixval']
          self.layout_data[record][field]['val'] = ht_info[fixval]

    # 최종 val 모양 formatting 하기
    for record in self.layout_data.keys():
      #print('L1 -------', record)
      for field in self.layout_data[record]:
        formated_val = ''
        
        #print('L2 -----------------', field)
        clazz  = self.layout_data[record][field]['class']
        type   = self.layout_data[record][field]['type']
        length = self.layout_data[record][field]['len']
        fixval = self.layout_data[record][field]['fixval']
        curval = self.layout_data[record][field]['val']
        
        if clazz == 'FIX' or clazz == 'FIX2' or clazz == '':
          formated_val = self.set_val(type, length, fixval)
        elif  clazz == 'DB' or clazz == 'VAR' :
          formated_val = self.set_val(type, length, curval)
          
        self.layout_data[record][field]['val'] = formated_val

    # val에 대한 길이 점검                 
    self.check_value_len()
    
    # 세율내역 합계 정보 추가
    sum_03C116300 = copy.deepcopy(self.layout_data['03C116300'])
    sum_03C116300['개별_합계']['val']      = '1'
    sum_03C116300['국내외구분코드']['val'] = '2'
    sum_03C116300['세율구분코드']['val']   = '00'
    self.layout_data['03C116300_COPY'] = sum_03C116300    
    
    self.result_text = ''
    # 최종 val 모양 formatting 하기
    for record in self.layout_data.keys():
      for field in self.layout_data[record]:
        curval = self.layout_data[record][field]['val']
        
        self.result_text += curval

      self.result_text += self.CRLF
    
    return self.result_text