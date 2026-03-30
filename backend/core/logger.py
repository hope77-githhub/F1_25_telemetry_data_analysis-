# core/logger.py
import logging
import sys

def setup_logger():
    # 로거 이름 설정
    logger = logging.getLogger("F1_Telemetry")
    logger.setLevel(logging.INFO)

    # 핸들러가 중복으로 추가되는 것을 방지
    if not logger.handlers:
        # 출력 포맷 설정: [시간] [레벨] 메시지
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # 터미널 창(콘솔)에 출력하는 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# 전역으로 사용할 logger 인스턴스 생성
logger = setup_logger()
