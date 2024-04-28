SERVER_TYPE = "DEV"  #개발환경: DEV, 운영환경: PROD

IS_DEBUG = False  # 쿠키로그인
DB_QUERY_PRINT = False
LOG_LEVEL = 'DEBUG'

# 주석처리
# group_id = 'the1'
FILE_ROOT_DIR_BASE = "U:\\TaxAssist\\files\HtTt\\"

# 자동신고(단계별) 로그 생성
AUTO_STEP_LOG_DIR   = "V:/PyHometax_Log_2024/AutoStep"
# 감시watcher로그 (2군데서 사용: 자동신고 watcher, WebSocket watcher)
WATCHER_LOG_DIR     = "V:/PyHometax_Log_2024/Watcher"

# 자동신고 진행사항 LOG 웹소켓
WEBSOCKET_SERVER_IP   = '61.38.105.227'
WEBSOCKET_SERVER_PORT = 18889

# DB 설정
DATABASE_CONFIG = {}
if SERVER_TYPE == 'PROD':
    DATABASE_CONFIG = {
        'db'       : 'taxweb', 
        'user'     : 'taxwebapp', 
        'password' : '!taxweb#', 
        'host'     : '61.38.105.227', 
        'port'     : 3406,
        'charset'  : 'utf8'
    }    
else:
    DATABASE_CONFIG = {
        'db'       : 'taxwebdev',
        'user'     : 'taxwebapp', 
        'password' : '!taxweb#', 
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

BROWSER_SIZE = { 'width' : 1100, 'height': 1150}
