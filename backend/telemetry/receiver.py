# telemetry/receiver.py
import socket
import asyncio

class TelemetryReceiver:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        # 비동기 처리를 위해 소켓 블로킹 해제
        self.sock.setblocking(False) 
        self.is_running = False

    async def start_receiving(self, message_queue: asyncio.Queue):
        """UDP 데이터를 수신하여 큐에 전달하는 비동기 루프"""
        self.is_running = True
        print(f"UDP Receiver started on {self.ip}:{self.port}")
        
        loop = asyncio.get_event_loop()
        while self.is_running:
            try:
                # 데이터 수신 대기 (최대 패킷 크기 고려하여 2048 바이트 설정)
                data, addr = await loop.sock_recvfrom(self.sock, 2048)
                await message_queue.put(data)
            except Exception as e:
                print(f"Receive error: {e}")

    def stop(self):
        self.is_running = False
        self.sock.close()
