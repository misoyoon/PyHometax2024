IS_DEBUG = False  # 쿠키로그인

DB_QUERY_PRINT = False

LOG_LEVEL = 'DEBUG'

# 주석처리
# group_id = 'the1'
FILE_ROOT_DIR_BASE = "E:\\FILESVR\\TaxAssist\\files\HtTt\\"


DATABASE_CONFIG = {
    'db'       : 'taxwebdev','user'   : 'taxwebapp', 
    #'db'     : 'taxweb', 'user'   : 'taxwebapp', 
    'password' : '!taxweb#', 
    #'host'     : '61.38.105.227', 
    'host'     : 'localhost', 
    'port'     : 3406,
    'charset'  : 'utf8'
}

HT_SERIES_YYYYMM = '202405'

# 한번에 가와서 처리할 데이터 수
BATCH_BUNDLE_COUNT = 10000

LOGIN_INFO = {
    # 담당자로그인 정보
    'name'      : None
    ,'login_id' : None
    ,'login_pw' : None
    ,'group_id' : None

    # 인증서 비밀번호
    ,'cert_login_pw' : 'kksjns1203!'

    # 세무대리인 (Pxxxxx)
    ,'rep_id' : "P24335"
    ,'rep_pw' : 'kksjns1203!'    
}

#BROWSER_SIZE = { 'width' : 1300, 'height': 1500}
BROWSER_SIZE = { 'width' : 1100, 'height': 1150}

# 주석처리
#HOST_NAME = 'AUTOSVR'


# USER_LIST = {
#     # 담당자명 : 로그인ID,  홈택스ID 아님!
#     "관리자"  : "MANAGER_ID"

# ,     "강솔이" :	"the1tax_1"	
# ,     "강솔이2":	"the1tax_1a"
# ,     "김미송" :	"the1tax_2"
# ,     "김미송2":	"the1tax_2a"
# ,     "장지헌" : 	"the1tax_3"
# ,     "이의정" :	"the1tax_4"	
# ,     "이현진" :	"the1tax_5"	
# ,     "최재원" :	"the1tax_6"	
# ,     "최우영" :	"the1tax_7"	
# ,     "김민재" :	"the1tax_8"
# ,     "이문현" :	"the1tax_9"
# ,     "김재욱" :	"the1tax_10"
# ,     "김재욱2":	"the1tax_10a"
# ,     "백종환" :	"the1tax_11"
# ,     "이태림" :	"the1tax_12"
# }

