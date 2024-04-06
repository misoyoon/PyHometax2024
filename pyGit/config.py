IS_DEBUG = False  # 쿠키로그인

DB_QUERY_PRINT = True

LOG_LEVEL = 'DEBUG'

FILE_ROOT_DIR = "E:\\FILESVR\\TaxAssist\\files\git\\wize\\"


DATABASE_CONFIG = {
    #'db'       : 'taxwebdev','user'   : 'taxwebappdev', 
    'db'     : 'taxweb', 'user'   : 'taxwebapp', 
    'password' : '!taxweb#', 
    'host'     : '61.38.105.227', 
    'port'     : 3206,
    'charset'  : 'utf8'
}

HT_SERIES_YYYYMM = '202405'

# 한번에 가와서 처리할 데이터 수
BATCH_BUNDLE_COUNT = 10000

LOGIN_INFO = {
    # 담당자로그인 정보
    'name'      : '와이즈담당자'
    ,'login_id' : 'greatwjb'
    ,'login_pw' : 'dlfdngjs12!'
    ,'group_id' : 'wize'

    # 인증서 비밀번호
    ,'cert_login_pw' : 'trenue3280@@'

    # 세무대리인 (Pxxxxx)
    #,'rep_id' : "P24335"
    #,'rep_pw' : 'kksjns1203!'    
}

#BROWSER_SIZE = { 'width' : 1300, 'height': 1500}
BROWSER_SIZE = { 'width' : 1100, 'height': 1050}

HOST_NAME = 'AUTOSVR'


USER_LIST = {
    # 담당자명 : 로그인ID,  홈택스ID 아님!
    "담당자1" :	"wizeuser1"	,
    "담당자2" :	"wizeuser2"	,
    "담당자3" :	"wizeuser3"	,
    "담당자4" :	"wizeuser4"	,
    "담당자5" :	"wizeuser5"	,
    "담당자6" :	"wizeuser6"	,
}

