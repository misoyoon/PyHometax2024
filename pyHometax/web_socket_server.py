import asyncio, os, time
import websockets
import ssl

import config
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

class ClientSession:
    def __init__(self, client_id, websocket, fullpath, auto_manager_id):
        self.client_id = client_id
        self.websocket = websocket
        self.fullpath = fullpath
        self.auto_manager_id = auto_manager_id
        self.last_read_position = 0
        self.initial_request_time = datetime.now()


UNCHANGED_LIMIT_MIN = 1  #(분) 일정 시간 변동이 없을 경우 close 처리  (대략적인 시간으로 정확하지 않음)
PING_TIME_SEC = 5  #(초) client가 실제 연결되었는지 check


# 클라이언트 세션을 관리하는 딕셔너리
client_sessions = {}

#LOG_DIR = "E:/FILESVR/TaxAssist/Log"
#AUTO_STEP_LOG_DIR = "V:\\PyHometax2024\\pyHometax\\LOG"

# 서버의 파일을 클라이언트에게 전송하는 함수
async def send_file_content(session):
    start_time = time.time()

    client_id = session.client_id
    fullpath = session.fullpath
    start_byte = session.last_read_position
    websocket = session.websocket

    if not fullpath or not os.path.exists(fullpath):
        print(f"File Not Fount = {fullpath}")
        return

    try:
        file_size = 0
        with open(fullpath, 'r', encoding='utf8') as f:
            content = ''
            if start_byte == 0:
                f.seek(0, 2)
                file_size = f.tell()

                if file_size > 10000:
                    pos = file_size - 3
                    while pos > 0:
                        try:
                            if pos == 0:
                                start_byte = 0
                                break
                            f.seek(pos, 0)
                            char = f.read(1)
                            if char == '\n':
                                start_byte = pos  + 1
                                break
                        except:
                            ...  #  한글에서 중간에 자를 경우 오류가 발생할 가능성이 있음

                        pos -= 1

            f.seek(start_byte)            
            content = f.read()

            if content:
                await websocket.send(content)
                session.last_read_position = f.tell()
                session.inital_request_time = datetime.now()
            else:
                # 현재 시간과 초기 요청 시간 사이의 차이를 계산
                time_difference = datetime.now() - session.initial_request_time
                # 1분 이상 차이가 나는 경우 세션을 삭제
                if time_difference.total_seconds() >= 60:
                    await websocket.send("\n>>>>> __NO_UPDATE_1MIN__ 60초간 파일에 변경 내용이 없어 해당 세션을 종료합니다!")
                    await websocket.close()
                    print(f"    Removing session! (No changed for 60sec.), client_id={client_id}, size={len(client_sessions)}")
                    if client_id in client_sessions:
                        del client_sessions[client_id]
                
    except websockets.ConnectionClosed:
        if client_id in client_sessions:
            del client_sessions[client_id]
        print(f"    Disconnected (send_file_content()), client_id={client_id}, size={len(client_sessions)}")
    except Exception as e:
        if file_size > 0:
            session.last_read_position = file_size
        await websocket.send(f'File read error : {e}')

# 세션 마다 요청한 파일의 변경 부분을 전달
async def send_content():
    try:
        while True:
            #print(f"    While ==> send_content() Session Size = {len(client_sessions)}")
            for client_id, client_session in client_sessions.copy().items():
                #print(f"    send_content  client_id = {client_id}")
                filename = client_session.fullpath
                if not filename:
                    continue

                await send_file_content(client_session)

            await asyncio.sleep(1)

    except websockets.ConnectionClosed:
        # 클라이언트 세션이 이미 삭제된 경우에는 다시 삭제하지 않도록 확인
        if client_id in client_sessions:
            del client_sessions[client_id]
        print(f"    Disconnected (send_content()), client_id={client_id}, size={len(client_sessions)}")


# 클라이언트가 요청으로 세션 생성 (주기적으로 ping으로 연결 여부 확인)
async def make_session(websocket, path):
    query = urlparse(path).query
    query_components = parse_qs(query)
    
    auto_manager_id = query_components.get('auto_manager_id', [''])[0]
    filename        = query_components.get('filename', [''])[0]
    
    # 보안을 위한 파일명 변경   
    filename = filename.replace("/", "").replace("\\", "").replace(".", "").replace(":", "")
    fullpath = f'{config.AUTO_STEP_LOG_DIR}/{auto_manager_id}/{filename}.log'


    if not filename or not os.path.exists(fullpath):
        print(f'>>>>> __FILE_NOT_FOUNT__ - 파일이 없어 Socket을 close 합니다. File={filename}\n')
        await websocket.send(f">>>>> __FILE_NOT_FOUNT__ - 파일이 없어 Socket을 close 합니다. File={filename}\n")
        return
        
        max_try = 10
        for i in range(1, max_try+1):
            if not os.path.exists(fullpath): 
                await websocket.send(f'try={i}, Not exists file so waiting ...\n')
                print(f'try={i}, Not exists file so waiting ... Filename={fullpath}')
                await asyncio.sleep(5)
            else:
                break
            
            if max_try == i:
                await websocket.send(f'>>>>> 해당 파일이 생성되지 않아 서비스를 종료합니다!')
                await websocket.close()
                return

    client_id = id(websocket)
    # 클라이언트 세션 관리 및 재사용
    if client_id in client_sessions:
        # 이미 해당 클라이언트의 세션이 존재하는 경우, 기존 세션을 재사용
        session = client_sessions[client_id]
        session.websocket = websocket
        session.fullpath = fullpath
        session.auto_manager_id = auto_manager_id
    else:
        # 해당 클라이언트의 세션이 없는 경우, 새로운 세션 생성
        client_sessions[client_id] = ClientSession(client_id, websocket, fullpath, auto_manager_id)
        print(f"New connected, id={client_id}, size={len(client_sessions)}")

    try:
        while True:
            # 클라이언트의 연결 상태를 주기적으로 확인하여 세션 유지
            await websocket.ping('ping')
            await asyncio.sleep(PING_TIME_SEC)
    except websockets.ConnectionClosed:
        # 클라이언트 세션이 이미 삭제된 경우에는 다시 삭제하지 않도록 확인
        if client_id in client_sessions:
            del client_sessions[client_id]
        print(f"    Disconnected (make_session()), client_id={client_id}, size={len(client_sessions)}")


# 세션 유지를 위한 변경
async def check_client_sessions():
    while True:
        print("Checking client session ... Interval = 60 sec")
        for client_id, client_session in client_sessions.copy().items():
            try:
                # 클라이언트의 연결 상태를 주기적으로 확인하여 세션 유지 또는 종료
                await client_session.websocket.ping('ping')
            except websockets.ConnectionClosed:
                # 클라이언트 세션이 이미 삭제된 경우에는 다시 삭제하지 않도록 확인
                if client_id in client_sessions:
                    del client_sessions[client_id]                
                print(f"    Disconnected (check_client_sessions()), client_id={client_id}, size={len(client_sessions)}")

        await asyncio.sleep(60)


# 서버 실행
async def main():
    if config.SERVER_TYPE == 'PROD':
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile='C:/cert/fullchain.pem', keyfile='C:/cert/taxassist.kr.key')

        start_server = websockets.serve(make_session, config.WEBSOCKET_SERVER_IP, config.WEBSOCKET_SERVER_PORT, ssl=ssl_context)    
    else:
        start_server = websockets.serve(make_session, "localhost", config.WEBSOCKET_SERVER_PORT)

    # 서버 시작
    await start_server

    # 서버가 시작된 후에 실행되어야 할 작업들
    await asyncio.ensure_future(send_content())
    await asyncio.ensure_future(check_client_sessions())

if __name__ == "__main__":
    print("============================================================")
    print(f"[WebSocket Start ...] Server Type - {config.SERVER_TYPE}")
    print("============================================================")
    
    asyncio.run(main())    
    
    print('Exit Program !!')