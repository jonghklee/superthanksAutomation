import pyautogui
import time
import random
import subprocess
import cv2
import numpy as np
from PIL import Image
import os

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
    print(f"   클릭 실행: ({x:.1f}, {y:.1f})")
    # 실제 클릭은 하지 않고 테스트만
    # pyautogui.click(x, y)
    time.sleep(wait_time)

def click_with_img_strict(img_path, max_attempts=2, min_confidence=0.6):
    """엄격한 confidence로 이미지 찾기 함수"""
    # 해상도 스케일 계산 (한 번만)
    def get_display_scale():
        pyautogui_size = pyautogui.size()
        subprocess.run(["screencapture", "-x", "temp_scale_check.png"], capture_output=True)
        if os.path.exists("temp_scale_check.png"):
            real_img = Image.open("temp_scale_check.png")
            scale_x = real_img.size[0] / pyautogui_size[0]
            scale_y = real_img.size[1] / pyautogui_size[1]
            os.remove("temp_scale_check.png")
            return scale_x, scale_y
        return 2.0, 2.0  # Retina 기본값

    scale_x, scale_y = get_display_scale()
    print(f"   해상도 스케일: x={scale_x:.2f}, y={scale_y:.2f}")
    
    # 더 엄격한 confidence 레벨들 (높은 정확도만 사용)
    confidence_levels = [0.9, 0.8, 0.7, 0.6]
    
    best_match = None
    best_confidence = 0.0
    best_coords = None
    
    for attempt in range(max_attempts):
        try:
            # macOS screencapture로 고해상도 스크린샷
            subprocess.run(["screencapture", "-x", "temp_screen.png"], capture_output=True)
            if not os.path.exists("temp_screen.png"):
                continue
                
            screen_img = Image.open("temp_screen.png")
            screen_np = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2BGR)
            target_img = cv2.imread(img_path)
            
            if target_img is None:
                print(f"타겟 이미지 {img_path} 로드 실패")
                os.remove("temp_screen.png")
                return False
            
            # 템플릿 매칭
            result = cv2.matchTemplate(screen_np, target_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            print(f"   최대 매칭 값: {max_val:.3f} (임계값: {min_confidence})")
            
            if max_val > best_confidence:
                best_confidence = max_val
                if max_val >= min_confidence:
                    # PyAutoGUI 좌표계로 변환 (중심점 계산)
                    click_x = max_loc[0] / scale_x + target_img.shape[1] / (2 * scale_x)
                    click_y = max_loc[1] / scale_y + target_img.shape[0] / (2 * scale_y)
                    best_coords = (click_x, click_y)
            
            os.remove("temp_screen.png")
            
        except Exception as e:
            print(f"시도 {attempt + 1} 실패: {e}")
            if os.path.exists("temp_screen.png"):
                os.remove("temp_screen.png")
        
        if attempt < max_attempts - 1:
            time.sleep(0.2)
    
    if best_confidence >= min_confidence and best_coords:
        print(f"✅ 이미지 {img_path} 발견 (confidence: {best_confidence:.3f})")
        print(f"   클릭 좌표: ({best_coords[0]:.1f}, {best_coords[1]:.1f})")
        click_button(best_coords[0], best_coords[1], smart_delay('click'))
        return True
    else:
        print(f"❌ 이미지 {img_path} 찾기 실패 (최고 신뢰도: {best_confidence:.3f}, 필요: {min_confidence})")
        return False

def test_strict_click():
    """엄격한 confidence로 테스트 - dots만 인식되어야 함"""
    print("=== 엄격한 confidence 테스트 (dots만 인식되어야 함) ===")
    
    # 화면 크기 확인
    screen_size = pyautogui.size()
    print(f"PyAutoGUI 인식 해상도: {screen_size}")
    
    # 이미지 파일들 테스트 - dots는 낮은 임계값, 나머지는 높은 임계값
    test_cases = [
        ('dots.png', 0.5),           # dots는 0.5 이상이면 인식
        ('superthanks2.png', 0.7),   # 나머지는 0.7 이상이어야 인식
        ('3_text.png', 0.7),
        ('4_buyandsend.png', 0.7),
        ('5_buy.png', 0.7)
    ]
    
    for img_file, min_conf in test_cases:
        img_path = f"img/{img_file}"
        print(f"\n--- {img_file} 테스트 (최소 신뢰도: {min_conf}) ---")
        
        result = click_with_img_strict(img_path, max_attempts=2, min_confidence=min_conf)
        
        if result:
            print(f"✅ {img_file} 성공!")
        else:
            print(f"❌ {img_file} 실패 (예상된 결과일 수 있음)")
        
        print("-" * 50)

if __name__ == "__main__":
    test_strict_click() 