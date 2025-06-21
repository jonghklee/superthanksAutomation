import pyautogui
import time
import os
import traceback

def test_image_detection():
    """이미지 탐지 기능을 테스트하는 함수"""
    print("=== PyAutoGUI 이미지 탐지 테스트 ===")
    
    # 화면 크기 확인
    screen_size = pyautogui.size()
    print(f"화면 크기: {screen_size}")
    
    # 스크린샷 저장 테스트
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("test_screenshot.png")
        print("✅ 스크린샷 저장 성공")
    except Exception as e:
        print(f"❌ 스크린샷 저장 실패: {e}")
        traceback.print_exc()
        return
    
    # PyAutoGUI 설정 확인
    print(f"PyAutoGUI failsafe: {pyautogui.FAILSAFE}")
    print(f"PyAutoGUI pause: {pyautogui.PAUSE}")
    
    # 이미지 파일들 확인
    img_files = ['dots.png', 'superthanks2.png', '3_text.png', '4_buyandsend.png', '5_buy.png']
    
    for img_file in img_files:
        img_path = f"img/{img_file}"
        if os.path.exists(img_path):
            print(f"✅ {img_file} 파일 존재")
            
            # 파일 크기 확인
            file_size = os.path.getsize(img_path)
            print(f"   파일 크기: {file_size} bytes")
            
            # 이미지 찾기 테스트 (confidence 없이)
            try:
                print(f"   {img_file} 검색 중...")
                location = pyautogui.locateOnScreen(img_path)
                if location:
                    print(f"✅ {img_file} 화면에서 발견: {location}")
                else:
                    print(f"⚠️  {img_file} 화면에서 찾을 수 없음")
            except Exception as e:
                print(f"❌ {img_file} 검색 중 오류: {type(e).__name__}: {e}")
                traceback.print_exc()
                
            # OpenCV가 있다면 confidence로도 테스트
            try:
                print(f"   {img_file} confidence 검색 중...")
                location_conf = pyautogui.locateOnScreen(img_path, confidence=0.8)
                if location_conf:
                    print(f"✅ {img_file} confidence로 발견: {location_conf}")
                else:
                    print(f"⚠️  {img_file} confidence로 찾을 수 없음")
            except TypeError as e:
                print(f"⚠️  OpenCV 없음 - confidence 사용 불가: {e}")
            except Exception as e:
                print(f"❌ {img_file} confidence 검색 중 오류: {type(e).__name__}: {e}")
                traceback.print_exc()
                
        else:
            print(f"❌ {img_file} 파일 없음")
        
        print("-" * 50)

if __name__ == "__main__":
    test_image_detection() 