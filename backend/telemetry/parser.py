# telemetry/parser.py
import struct
from telemetry.structures import HEADER_FORMAT, CAR_TELEMETRY_FORMAT, CAR_TELEMETRY_SIZE, MAX_CARS
from telemetry.structures import LAP_DATA_FORMAT, LAP_DATA_SIZE, MAX_CARS

def parse_header(packet_data: bytes) -> dict:
    """29바이트 헤더를 파싱하여 딕셔너리로 반환"""
    unpacked = struct.unpack(HEADER_FORMAT, packet_data[:29])
    
    return {
        "packetFormat": unpacked[0],
        "gameYear": unpacked[1],
        "gameMajorVersion": unpacked[2],
        "gameMinorVersion": unpacked[3],
        "packetVersion": unpacked[4],
        "packetId": unpacked[5],           # 핵심: 패킷 종류 식별 [cite: 16]
        "sessionUID": unpacked[6],
        "sessionTime": unpacked[7],
        "frameIdentifier": unpacked[8],
        "overallFrameIdentifier": unpacked[9],
        "playerCarIndex": unpacked[10],    # 핵심: 내 차 인덱스 [cite: 21]
        "secondaryPlayerCarIndex": unpacked[11]
    }

def parse_telemetry_packet(packet_data: bytes, target_index: int) -> dict:
    """
    ePacketIdCarTelemetry (ID: 6) 패킷 해독.
    전체 22대 중 target_index(내 차 또는 1등)의 데이터만 추출해서 반환.
    """
    # 헤더 이후부터 텔레메트리 데이터 시작 (29바이트 지점)
    offset = 29 
    
    # 22대 데이터를 모두 파싱할 수도 있지만, 타겟 차량 데이터만 쏙 빼오면 효율적이야.
    target_offset = offset + (target_index * CAR_TELEMETRY_SIZE)
    target_data = packet_data[target_offset : target_offset + CAR_TELEMETRY_SIZE]
    
    unpacked = struct.unpack(CAR_TELEMETRY_FORMAT, target_data)
    
    return {
        "speed": unpacked[0],          # km/h [cite: 290]
        "throttle": unpacked[1],       # 0.0 ~ 1.0 [cite: 291]
        "steer": unpacked[2],          # -1.0 ~ 1.0 [cite: 292]
        "brake": unpacked[3],          # 0.0 ~ 1.0 [cite: 293]
        "gear": unpacked[5],           # 1-8, N=0, R=-1 [cite: 295]
        "engineRPM": unpacked[6],      # [cite: 296]
        "drs": unpacked[7]             # 0 = off, 1 = on [cite: 297]
    }

def parse_lap_data_packet(packet_data: bytes) -> list:
    """
    ePacketIdLapData (ID: 2) 패킷 해독.
    22대 차량의 랩 데이터를 모두 파싱해서 리스트로 반환해. 
    여기서 순위를 확인해 1등 타겟팅이나 마이크로 섹터 구간을 연산할 수 있어.
    """
    offset = 29 # 공통 헤더 29바이트 이후부터 랩 데이터 시작 [cite: 170]
    lap_data_list = []
    
    for i in range(MAX_CARS):
        target_data = packet_data[offset : offset + LAP_DATA_SIZE]
        unpacked = struct.unpack(LAP_DATA_FORMAT, target_data)
        
        # 우리가 분석 기능과 상태 추적에 쓸 핵심 데이터만 딕셔너리로 추출 [cite: 136, 137, 146, 149, 150, 153]
        lap_data_list.append({
            "carIndex": i,
            "lastLapTimeInMS": unpacked[0],     # 마지막 랩 타임 [cite: 136]
            "currentLapTimeInMS": unpacked[1],  # 현재 랩 타임 [cite: 137]
            "lapDistance": unpacked[10],        # 이번 랩 주행 거리 (코너 위치 파악용) [cite: 146]
            "carPosition": unpacked[13],        # 현재 순위 (1등 찾기 핵심) [cite: 149]
            "currentLapNum": unpacked[14],      # 현재 랩 수 [cite: 150]
            "sector": unpacked[17]              # 현재 섹터 (0, 1, 2) [cite: 153]
        })
        
        # 다음 차량 데이터로 오프셋 이동
        offset += LAP_DATA_SIZE 
        
    return lap_data_list