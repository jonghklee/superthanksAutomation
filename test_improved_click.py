import pyautogui
import time
import random
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# sendSuperThanks.py에서 가져온 함수들
DELAYS = {
    'short': (0.5, 1.0),      # 짧은 딜레이
    'medium': (1.0, 2.0),     # 중간 딜레이  
    'long': (2.0, 3.0),       # 긴 딜레이
    'ui_update': (1.0, 1.5),  # UI 업데이트 대기
    'click': (0.1, 0.3),      # 클릭 후 대기
    'type': (0.05, 0.1),      # 타이핑 간격
}

def smart_delay(delay_type='medium', multiplier=1.0):
    """스마트 딜레이 함수 - 랜덤한 딜레이로 봇 탐지 방지"""
    if delay_type in DELAYS:
        min_delay, max_delay = DELAYS[delay_type]
        delay_time = random.uniform(min_delay, max_delay) * multiplier
        time.sleep(delay_time)
        return delay_time
    else:
        time.sleep(1.0)
        return 1.0

def click_button(x, y, wait_time):
    """특정 위치로 이동하여 클릭하는 함수"""
    # 버튼 클릭 전 랜덤 이동
    for _ in range(3):
        x_offset = random.randint(-10, 10)
        y_offset = random.randint(-10, 10)
        duration = random.uniform(0.1, 0.2)
        pyautogui.move(x_offset, y_offset, duration=duration)
        time.sleep(random.uniform(0.05, 0.1))
    # 좌표에 랜덤 오프셋 추가 후 클릭
    random_x = x + random.randint(-3, 3)
    random_y = y + random.randint(-3, 3)
    pyautogui.moveTo(random_x, random_y, duration=0.5)
    time.sleep(random.uniform(0.05, 0.1))
    pyautogui.click()
    time.sleep(wait_time)

def click_with_img(image_path, timeout=10):
    """
    이미지를 찾아서 클릭하는 함수 (confidence 0.8 이상만)
    """
    start_time = time.time()
    logger.info(f"이미지 탐지 시작: {image_path}")
    
    # confidence 레벨 (0.8 이상만)
    confidence_levels = [0.9, 0.8]
    
    while time.time() - start_time < timeout:
        try:
            for confidence in confidence_levels:
                try:
                    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                    if location:
                        center = pyautogui.center(location)
                        logger.info(f"이미지 발견! 위치: {center}, 신뢰도: {confidence}")
                        pyautogui.click(center)
                        return True
                except pyautogui.ImageNotFoundException:
                    continue
                except Exception as e:
                    if "OpenCV" in str(e):
                        logger.warning(f"OpenCV 오류로 confidence 없이 시도: {e}")
                        try:
                            location = pyautogui.locateOnScreen(image_path)
                            if location:
                                center = pyautogui.center(location)
                                logger.info(f"이미지 발견! 위치: {center} (confidence 없음)")
                                pyautogui.click(center)
                                return True
                        except pyautogui.ImageNotFoundException:
                            continue
                    else:
                        logger.error(f"예상치 못한 오류: {e}")
                        continue
            
            # 잠시 대기 후 재시도
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"전체 루프에서 오류 발생: {e}")
            time.sleep(0.5)
    
    logger.warning(f"이미지를 찾을 수 없습니다: {image_path} (timeout: {timeout}초)")
    return False

def test_improved_click():
    """개선된 click_with_img 함수 테스트"""
    print("=== 개선된 click_with_img 함수 테스트 ===")
    
    # 화면 크기 확인
    screen_size = pyautogui.size()
    print(f"화면 크기: {screen_size}")
    
    # 이미지 파일들 테스트
    img_files = ['dots.png', 'superthanks2.png', '3_text.png', '4_buyandsend.png', '5_buy.png']
    
    for img_file in img_files:
        img_path = f"img/{img_file}"
        print(f"\n--- {img_file} 테스트 ---")
        
        # 개선된 함수로 테스트
        result = click_with_img(img_path, timeout=5)  # 빠른 테스트를 위해 5초만
        
        if result:
            print(f"✅ {img_file} 성공!")
        else:
            print(f"❌ {img_file} 실패")
        
        print("-" * 50)

if __name__ == "__main__":
    logger.info("=== 이미지 탐지 테스트 시작 (confidence 0.8 이상만) ===")
    
    test_images = [
        "img/dots.png",
        "img/superthanks1.png", 
        "img/5_buy.png",
        "img/4_buyandsend.png"
    ]
    
    for image in test_images:
        logger.info(f"\n--- {image} 테스트 중 ---")
        result = click_with_img(image, timeout=5)
        if result:
            logger.info(f"✅ {image} 성공!")
        else:
            logger.warning(f"❌ {image} 실패!")
        
        # 다음 테스트를 위한 대기
        time.sleep(2)
    
    logger.info("\n=== 테스트 완료 ===") 