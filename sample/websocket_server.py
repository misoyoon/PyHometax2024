import asyncio, os, time
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
    start_time = time.time()
    
    filename = session.filename
    start_byte = session.last_read_position
    websocket = session.websocket
    
    if session.last_read_position == os.path.getsize(session.filename):
        ...
        #print('   skipped .. same size')
        #return

    #print(f"time elapsed 1: {int(round((time.time() - start_time) * 1000))}ms")
    
    with open(filename, 'r', encoding='utf8') as f:
        #print(f' size={os.path.getsize(session.filename)}, {session.last_read_position}')
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
            
        #print(f"time elapsed 2: {int(round((time.time() - start_time) * 1000))}ms")
        
        if content:
            await websocket.send(content)
            session.last_read_position = f.tell()


# 클라이언트 세션을 주기적으로 확인하여 파일 변경 여부를 감지하고, 세션 제거
async def check_client_sessions():
    while True:
        for client_id, client_session in client_sessions.items():
            if (datetime.now() - client_session.initial_request_time) > timedelta(minutes=5):
                print(f"Closing session for client {client_id}")
                del client_sessions[client_id]
        await asyncio.sleep(60)  # 60초마다 확인


async def send_content():
    try:
        while True:
            print(f'Session Size = {len(client_sessions)}')
            for client_id, client_session in client_sessions.items():
                filename = client_session.filename
                if not filename: 
                    #del client_sessions[client_id]
                    continue

                await send_file_content(client_session)
                
                #del client_sessions[client_id]
            await asyncio.sleep(2)  # 60초마다 확인
    except websockets.ConnectionClosed:
        del client_sessions[client_id]
        print("Client disconnected")


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
            #print(f"    ping, id={client_id}")
            await websocket.ping('ping')
            await asyncio.sleep(5)
    except websockets.ConnectionClosed:
        del client_sessions[client_id]
        print(f"Client disconnected, id={client_id}")

    print(f'end client_id={client_id}')


# 서버 실행
async def main():
    start_server = websockets.serve(set_session, "localhost", 8765)
    await asyncio.gather(start_server, send_content())
    await asyncio.gather(start_server, check_client_sessions())
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

asyncio.run(main())
print('Exit Program')