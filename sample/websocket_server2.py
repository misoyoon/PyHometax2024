import asyncio
import websockets
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

class ClientSession:
    def __init__(self, client_id, filename, websocket):
        self.client_id = client_id
        self.filename = filename
        self.websocket = websocket
        self.last_read_position = 0
        self.initial_request_time = datetime.now()

# 클라이언트 세션을 관리하는 딕셔너리
client_sessions = {}

# 서버의 파일을 클라이언트에게 전송하는 함수
async def send_file_content(session):
    filename = session.filename
    start_byte = session.last_read_position
    websocket = session.websocket
    with open(filename, 'r', encoding='utf8') as f:
        if start_byte == 0:
            f.seek(0, 2)  # 파일의 끝으로 이동
            file_size = f.tell()  # 파일 크기 구하기
            
            # 파일 끝에서 한 줄씩 앞으로 이동하여 마지막 줄 찾기
            pos = file_size - 10  # 항상 /n로 끝나기 때문에 임의의 이전 만큼 이동 후 시작
            while pos > 0:
                f.seek(pos, 0)
                if f.read(1) == '\n':
                    break
                pos -= 1          
                
            # 마지막 줄을 읽어와 출력
            content = f.readline()
        else:
            f.seek(start_byte)
            content = f.read()
    
        if content:
            await websocket.send(content)
            session.last_read_position = f.tell()


# 클라이언트가 요청한 파일의 변경 내용을 전달하는 함수
async def set_session(websocket, path):
    query = urlparse(path).query
    query_components = parse_qs(query)
    filename = query_components.get('filename', [''])[0]

    if not filename:
        await websocket.send("Filename not provided")
        return
    
    client_id = id(websocket)
    if client_id not in client_sessions:
        print(f"Client connected, id={client_id}")
        client_sessions[client_id] = ClientSession(client_id, filename, websocket)

    try: 
        while True:
            print(f"    ping, id={client_id}")
            await websocket.ping('ping')
            await asyncio.sleep(60)
    except websockets.ConnectionClosed:
        del client_sessions[client_id]
        print(f"Client disconnected, id={client_id}")

    print('Exit Program')

# 서버 실행
async def main():
    start_server = websockets.serve(set_session, "localhost", 8765)
    await start_server

asyncio.run(main())