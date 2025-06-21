import pyautogui
import subprocess
import os
from PIL import Image
import time

def test_screenshot_methods():
    """다양한 스크린샷 방법 테스트"""
    print("=== 스크린샷 방법 테스트 ===")
    
    # 방법 1: PyAutoGUI 기본
    try:
        print("1. PyAutoGUI 기본 방법...")
        screenshot1 = pyautogui.screenshot()
        screenshot1.save("test_pyautogui.png")
        print("✅ PyAutoGUI 기본 방법 성공")
    except Exception as e:
        print(f"❌ PyAutoGUI 기본 방법 실패: {e}")
    
    # 방법 2: macOS screencapture 명령어
    try:
        print("2. macOS screencapture 명령어...")
        result = subprocess.run(["screencapture", "-x", "test_screencapture.png"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ macOS screencapture 성공")
        else:
            print(f"❌ macOS screencapture 실패: {result.stderr}")
    except Exception as e:
        print(f"❌ macOS screencapture 오류: {e}")
    
    # 방법 3: PyAutoGUI 설정 변경 후
    try:
        print("3. PyAutoGUI 설정 변경 후...")
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        screenshot3 = pyautogui.screenshot()
        screenshot3.save("test_pyautogui_modified.png")
        print("✅ PyAutoGUI 설정 변경 후 성공")
    except Exception as e:
        print(f"❌ PyAutoGUI 설정 변경 후 실패: {e}")
    
    # 파일 크기 확인
    print("\n=== 생성된 파일 확인 ===")
    for filename in ["test_pyautogui.png", "test_screencapture.png", "test_pyautogui_modified.png"]:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename}: {size} bytes")
        else:
            print(f"❌ {filename}: 파일 없음")

def test_image_detection_with_screencapture():
    """screencapture로 찍은 이미지로 탐지 테스트"""
    print("\n=== screencapture로 이미지 탐지 테스트 ===")
    
    # screencapture로 스크린샷
    result = subprocess.run(["screencapture", "-x", "screen_for_test.png"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("screencapture 실패")
        return
    
    # PIL로 이미지 열기
    try:
        screen_img = Image.open("screen_for_test.png")
        print(f"스크린샷 크기: {screen_img.size}")
        
        # dots.png 찾기 테스트
        import cv2
        import numpy as np
        
        # 이미지를 numpy 배열로 변환
        screen_np = np.array(screen_img)
        dots_img = cv2.imread("img/dots.png")
        
        if dots_img is not None:
            # 템플릿 매칭
            result = cv2.matchTemplate(screen_np, dots_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            print(f"최대 매칭 값: {max_val}")
            if max_val > 0.4:
                print(f"✅ dots.png 발견! 위치: {max_loc}, 신뢰도: {max_val}")
            else:
                print(f"❌ dots.png 찾을 수 없음 (최대 신뢰도: {max_val})")
        else:
            print("❌ dots.png 로드 실패")
            
    except Exception as e:
        print(f"이미지 처리 오류: {e}")

if __name__ == "__main__":
    test_screenshot_methods()
    test_image_detection_with_screencapture() 