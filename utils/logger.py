import logging

def setup_logger():
    """로거 설정"""
    # 로거 생성
    logger = logging.getLogger('pyeongtaekbus')
    logger.setLevel(logging.INFO)
    
    # 핸들러가 이미 있으면 중복 추가 방지
    if logger.handlers:
        return logger
    
    # 콘솔 핸들러 (stdout으로 출력하여 Loki가 수집 가능)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터 설정 (JSON 형식으로 출력)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 전역 로거 인스턴스
log = setup_logger()