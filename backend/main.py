# main.py
import asyncio
from fastapi import FastAPI, WebSocket
from core.config import CONFIG
from telemetry.receiver import TelemetryReceiver

app = FastAPI()

# 데이터를 임시 보관할 큐
telemetry_queue = asyncio.Queue()
receiver = TelemetryReceiver(
    ip=CONFIG['f1_telemetry']['udp_ip'], 
    port=CONFIG['f1_telemetry']['udp_port']
)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 UDP 수신기를 백그라운드 태스크로 실행"""
    asyncio.create_task(receiver.start_receiving(telemetry_queue))
    # TODO: 데이터를 큐에서 꺼내 분석(Analysis) 모듈로 넘기는 워커(Worker) 태스크 실행

@app.on_event("shutdown")
def shutdown_event():
    receiver.stop()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """React 프론트엔드와 실시간 데이터를 주고받을 웹소켓 엔드포인트"""
    await websocket.accept()
    try:
        while True:
            # 프론트엔드에서 오는 설정 변경 메시지 수신 (예: 타겟 차량 변경)
            # data = await websocket.receive_json()
            
            # TODO: 분석 모듈을 거친 정제된 데이터를 React로 전송
            # await websocket.send_json({"speed": 300, "gear": 8})
            await asyncio.sleep(0.05) # 임시 딜레이 (1초에 20번 전송)
    except Exception as e:
        print(f"WebSocket Error: {e}")