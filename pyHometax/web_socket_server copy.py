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
        self.inital_request_time = datetime.now()


UNCHANGED_LIMIT_MIN = 1  #(분) 일정 시간 변동이 없을 경우 close 처리  (대략적인 시간으로 정확하지 않음)
PING_TIME_SEC = 5  #(초) client가 실제 연결되었는지 check


# 클라이언트 세션을 관리하는 딕셔너리
client_sessions = {}

#LOG_DIR = "E:/FILESVR/TaxAssist/Log"
#AUTO_STEP_LOG_DIR = "V:\\PyHometax2024\\pyHometax\\LOG"

# 서버의 파일을 클라이언트에게 전송하는 함수
async def send_file_content(session):
    start_time = time.time()

    fullpath = session.fullpath
    start_byte = session.last_read_position
    websocket = session.websocket

    #if session.last_read_position == os.path.getsize(session.fullpath):
    #    ...
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
            content  = f.read()

            if content:
                await websocket.send(content)
                session.last_read_position = f.tell()
                session.inital_request_time = datetime.now()
    except Exception as e:
        if file_size > 0:
            session.last_read_position = file_size
        await websocket.send(f'File read error : {e}')

# 세션 마다 요청한 파일의 변경 부분을 전달
async def send_content():
    try:
        while True:
            print(f"While ==> send_content() Session Size = {len(client_sessions)}")
            for client_id, client_session in client_sessions.copy().items():
                #print(f"    send_content  client_id = {client_id}")
                filename = client_session.fullpath
                if not filename:
                    continue

                await send_file_content(client_session)

            await asyncio.sleep(2)

    except websockets.ConnectionClosed:
        del client_sessions[client_id]
        print("Client disconnected")


# 클라이언트가 요청으로 세션 생성 (주기적으로 ping으로 연결 여부 확인)
async def make_session(websocket, path):
    query = urlparse(path).query
    query_components = parse_qs(query)
    
    auto_manager_id = query_components.get('auto_manager_id', [''])[0]
    filename        = query_components.get('filename', [''])[0]
    
    fullpath = f'{config.AUTO_STEP_LOG_DIR}/{auto_manager_id}/{filename}.log'

    if not filename or not os.path.exists(fullpath):
        #print(f'다음의 파일이 없어서 요청 Socket을 close 합니다. File={fullpath}')
        #await websocket.send(f"[{filename}] is not provided !!")
        #return
        max_try = 10
        for i in range(1, max_try+1):
            if not os.path.exists(fullpath): 
                await websocket.send(f'try={i}, Not exists file so waiting ...')
                print(f'try={i}, Not exists file so waiting ... Filename={fullpath}')
                await asyncio.sleep(1)
            else:
                break
            
            if max_try == i:
                await websocket.send(f'해당 파일이 생성되지 않아 서비스를 종료합니다!')
                await websocket.close()
                return
        
    client_id = id(websocket)
    if client_id not in client_sessions:
        print(f"New Client connected, id={client_id}")
        client_sessions[client_id] = ClientSession(client_id, websocket, fullpath, auto_manager_id)

    while True:
        try:
            print(f"    FOR => ping :: session count={len(client_sessions)}, client_id={client_id}")
            await websocket.ping('ping')
            await asyncio.sleep(PING_TIME_SEC)
        except websockets.ConnectionClosed:
            print(f'        except (ping) :: Force disconnected by ping,   DELETEED client_id={client_id},  나머지 session count={len(client_sessions)}')
            #del client_sessions[client_id]
            #for client_id, client_session in client_sessions.copy().items():
            #    print(f"    send_content1 client_id = {client_id}")
            break
        except Exception as e:
            print(f'error pos 2 : {e}')
            for client_id, client_session in client_sessions.copy().items():
                print(f"    send_content2  client_id = {client_id}")
            #del client_sessions[client_id]
            break



# 일정시간 동안 변경이 없는 파일에 대한 세션 close 처리
async def check_client_sessions():

    while True:
        for client_id, client_session in client_sessions.copy().items():
            print(f"FOR : check_client_sessions() :: client_id={client_id}")
            if (datetime.now() - client_session.inital_request_time) > timedelta(minutes=UNCHANGED_LIMIT_MIN):
                print(f'Closing session for client id={client_id}')

                try:
                    await client_session.websocket.send(f"No update file for {UNCHANGED_LIMIT_MIN} min.")
                    del client_sessions[client_id]
                except Exception as e:
                    print(f"check_client_sessions : {client_sessions}")
                    print(f'error pos 1 : {e}')
                    
        await asyncio.sleep(60)


# 서버 실행
async def main():
    if config.SERVER_TYPE == 'PROD':
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile='C:/cert/fullchain.pem', keyfile='C:/cert/taxassist.kr.key')

        start_server = websockets.serve(make_session, config.WEBSOCKET_SERVER_IP, config.WEBSOCKET_SERVER_PORT, ssl=ssl_context)    
        await asyncio.gather(start_server, send_content(), check_client_sessions())
    else:
        start_server = websockets.serve(make_session, "localhost", config.WEBSOCKET_SERVER_PORT)
        await asyncio.gather(start_server, send_content()) #, check_client_sessions())
        

if __name__ == "__main__":
    print("============================================================")
    print(f"[WebSocket Start ...] Server Type - {config.SERVER_TYPE}")
    print("============================================================")
    
    asyncio.run(main())    
    
    print('Exit Program !!')