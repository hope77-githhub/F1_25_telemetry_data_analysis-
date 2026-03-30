# telemetry/state_manager.py
from core.logger import logger

class StateManager:
    def __init__(self):
        # 레이스 참여자 인덱스 (0~21)
        self.player_index = None
        self.leader_index = None
        
        # 프론트엔드에서 선택한 타겟 (기본값: 내 차)
        # "player", "leader", 또는 특정 라이벌의 인덱스 숫자(0~21)가 될 수 있음
        self.target_mode = "player"  

    def update_from_header(self, header_data: dict):
        """
        모든 UDP 패킷의 헤더에서 내 차 인덱스를 추출해 업데이트
        """
        new_player_index = header_data.get("playerCarIndex")
        
        if new_player_index is not None and self.player_index != new_player_index:
            self.player_index = new_player_index
            logger.info(f"Player car index updated to: {self.player_index}")

    def update_from_lap_data(self, lap_data_list: list):
        """
        ID: 2 (Lap Data) 패킷을 받아 1등 차량 인덱스를 업데이트
        lap_data_list는 parser.py에서 만든 22대 차량의 랩 데이터 딕셔너리 리스트
        """
        for lap_data in lap_data_list:
            # m_carPosition이 1인 차가 현재 레이스/세션의 1등
            if lap_data.get("carPosition") == 1:
                new_leader_index = lap_data.get("carIndex")
                
                if self.leader_index != new_leader_index:
                    self.leader_index = new_leader_index
                    logger.debug(f"Race leader changed! New leader index: {self.leader_index}")
                break

    def set_target_mode(self, mode: str):
        """
        프론트엔드(React)에서 버튼을 눌렀을 때 타겟을 변경하는 메서드
        """
        if mode in ["player", "leader"] or (isinstance(mode, int) and 0 <= mode <= 21):
            self.target_mode = mode
            logger.info(f"Target mode changed to: {self.target_mode}")
        else:
            logger.warning(f"Invalid target mode requested: {mode}")

    def get_current_target_index(self) -> int:
        """
        현재 설정된 모드에 따라 텔레메트리를 분석할 '진짜 인덱스 번호'를 반환
        """
        if self.target_mode == "player":
            return self.player_index
        elif self.target_mode == "leader":
            return self.leader_index
        elif isinstance(self.target_mode, int):
            return self.target_mode
            
        # 기본 폴백(Fallback)
        return self.player_index

# 싱글톤처럼 전역에서 하나만 사용할 수 있도록 인스턴스화
state_manager = StateManager()
