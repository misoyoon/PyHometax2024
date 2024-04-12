import asyncio, os, time
import websockets
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

class ClientSession:
    def __init__(self, client_id, filename, websocket):
        self.client_id = client_id
        self.filename = filename
        self.websocket = websocket
        self.last_read_position = 0
        self.inital_request_time = datetime.now()


# 클라이언트 세션을 관리하는 딕셔너리
client_sessions = {}

LOG_DIR = "E:/FILESVR/TaxAssist/Log"

# 서버의 파일을 클라이언트에게 전송하는 함수
async def send_file_content(session):
    start_time = time.time()

    filename = session.filename
    start_byte = session.last_read_position
    websocket = session.websocket

    #if session.last_read_position == os.path.getsize(session.filename):
    #    ...

    try:
        file_size = 0
        with open(filename, 'r', encoding='utf8') as f:
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
    except Exception() as e:
        if file_size > 0:
            session.last_read_position = file_size
        await websocket.send(f'File read error : {e}')


# 일정시간 동안 변경이 없는 파일에 대한 세션 close 처리
async def check_client_sessions():
    LIMIT_MIN = 3
    while True:
        for client_id, client_session in client_sessions.copy().items():
            if (datetime.now() - client_session.inital_request_time) > timedelta(minutes=LIMIT_MIN):
                print(f'Closing session for client id={client_id}')

                await client_session.websocket.send(f"No update file for {LIMIT_MIN} min.")
                del client_sessions[client_id]
        await asyncio.sleep(60)


# 세션 마다 요청한 파일의 변경 부분을 전달
async def send_content():
    try:
        while True:
            print(f"Session Size = {len(client_sessions)}")
            for client_id, client_session in client_sessions.copy().items():
                filename = client_session.filename
                if not filename:
                    continue

                await send_file_content(client_session)

            await asyncio.sleep(2)

    except websockets.ConnectionClosed:
        del client_sessions[client_id]
        print("Client disconnected")


# 클라이언트가 요청으로 세션 생성 (주기적으로 ping으로 연결 여부 확인)
async def set_session(websocket, path):
    query = urlparse(path).query
    query_components = parse_qs(query)
    filename = query_components.get('filename', [''])[0]
    fullpath = f'{LOG_DIR}/{filename}'

    if not filename or not fullpath:
        await websocket.send(f"[{filename}] is not provided !!")
        return
    
    client_id = id(websocket)
    if client_id not in client_sessions:
        print(f"Client connected, id={client_id}")
        client_sessions[client_id] = ClientSession(client_id, fullpath, websocket)

    try:
        while True:
            await websocket.ping('ping')
            await asyncio.sleep(5)
    except websockets.ConnectionClosed:
        del client_sessions[client_id]
        print(f'Client disconnected by ping test, client_id={client_id}  => session count={len(client_sessions)}')


# 서버 실행
async def main():
    start_server = websockets.serve(set_session, "localhost", 18889)
    await asyncio.gather(start_server, send_content(), check_client_sessions())


asyncio.run(main())    
print('Exit Program !!')