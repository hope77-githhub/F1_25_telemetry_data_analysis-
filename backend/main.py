# main.py
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from core.config import CONFIG
from core.logger import logger
from telemetry.receiver import TelemetryReceiver
from telemetry import parser
from telemetry.state_manager import state_manager

app = FastAPI()

# 1. 웹소켓 연결 관리자 (여러 명의 사용자가 접속하거나 창을 여러 개 띄울 때 대비)
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Client disconnected.")

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except RuntimeError:
                # 연결이 끊어진 클라이언트 처리
                pass

manager = ConnectionManager()
telemetry_queue = asyncio.Queue()
receiver = TelemetryReceiver(
    ip=CONFIG['f1_telemetry']['udp_ip'], 
    port=CONFIG['f1_telemetry']['udp_port']
)

# 2. 비동기 데이터 처리 워커 (핵심 파이프라인)
async def process_telemetry_queue():
    """큐에서 패킷을 꺼내 파싱하고 분석 후 프론트엔드로 쏘는 메인 루프"""
    logger.info("Telemetry processing worker started.")
    
    while True:
        packet_data = await telemetry_queue.get()
        
        try:
            # 1. 헤더 파싱 및 내 차 인덱스 업데이트
            header = parser.parse_header(packet_data)
            state_manager.update_from_header(header)
            packet_id = header["packetId"]
            
            # 2. 랩 데이터 패킷 (ID 2) 처리 -> 1등 추적
            if packet_id == 2:
                lap_data_list = parser.parse_lap_data_packet(packet_data)
                state_manager.update_from_lap_data(lap_data_list)
            
            # 3. 텔레메트리 패킷 (ID 6) 처리 -> 타겟 차량 분석 및 전송
            elif packet_id == 6:
                target_idx = state_manager.get_current_target_index()
                
                # 타겟 인덱스를 모르면 아직 데이터를 쏘지 않음
                if target_idx is None:
                    continue
                    
                target_telemetry = parser.parse_telemetry_packet(packet_data, target_idx)
                
                # TODO: analysis 폴더의 모듈을 호출해서 브레이킹 포인트/스로틀 연산 추가
                # 분석 결과를 프론트엔드 전송용 페이로드로 구성
                payload = {
                    "type": "telemetry_update",
                    "target_mode": state_manager.target_mode,
                    "target_index": target_idx,
                    "data": target_telemetry
                }
                
                # 웹소켓을 통해 클라이언트들에게 뿌림
                await manager.broadcast_json(payload)
                
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
        finally:
            telemetry_queue.task_done()

# 3. FastAPI 생명주기 (서버 켜고 꺼질 때 동작)
@app.on_event("startup")
async def startup_event():
    # 수신기와 파싱 워커를 백그라운드 태스크로 동시에 실행
    asyncio.create_task(receiver.start_receiving(telemetry_queue))
    asyncio.create_task(process_telemetry_queue())

@app.on_event("shutdown")
def shutdown_event():
    receiver.stop()
    logger.info("Server shutting down.")

# 4. 프론트엔드 통신용 웹소켓 엔드포인트
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 프론트엔드에서 오는 설정 변경 메시지 대기 (예: 타겟 차량 변경)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "set_target":
                new_target = message.get("target")
                state_manager.set_target_mode(new_target)
                # 변경되었음을 프론트엔드에 즉시 회신 (선택사항)
                await websocket.send_json({
                    "type": "system_message", 
                    "message": f"Target changed to {new_target}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
