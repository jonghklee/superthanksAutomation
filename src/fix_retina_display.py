import pyautogui
import subprocess
import os
from PIL import Image
import cv2
import numpy as np

def fix_retina_display():
    """Retina 디스플레이 문제 해결"""
    print("=== Retina 디스플레이 문제 해결 ===")
    
    # 1. 시스템 해상도 확인
    result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                          capture_output=True, text=True)
    print("시스템 디스플레이 정보:")
    lines = result.stdout.split('\n')
    for line in lines:
        if 'Resolution' in line or 'Pixel Depth' in line:
            print(f"  {line.strip()}")
    
    # 2. PyAutoGUI 해상도 vs 실제 해상도
    pyautogui_size = pyautogui.size()
    print(f"\nPyAutoGUI 인식 해상도: {pyautogui_size}")
    
    # 3. 실제 스크린샷으로 해상도 확인
    screenshot = pyautogui.screenshot()
    print(f"PyAutoGUI 스크린샷 크기: {screenshot.size}")
    
    # 4. macOS screencapture로 해상도 확인
    subprocess.run(["screencapture", "-x", "real_screen.png"], capture_output=True)
    if os.path.exists("real_screen.png"):
        real_img = Image.open("real_screen.png")
        print(f"macOS screencapture 크기: {real_img.size}")
        
        # 해상도 비율 계산
        scale_x = real_img.size[0] / screenshot.size[0]
        scale_y = real_img.size[1] / screenshot.size[1]
        print(f"해상도 배율: x={scale_x}, y={scale_y}")
        
        return scale_x, scale_y
    
    return 1.0, 1.0

def test_with_scale():
    """스케일 적용하여 이미지 찾기 테스트"""
    print("\n=== 스케일 적용 이미지 찾기 테스트 ===")
    
    scale_x, scale_y = fix_retina_display()
    
    # PyAutoGUI로 스크린샷
    screenshot = pyautogui.screenshot()
    
    # 스케일 적용하여 리사이즈
    if scale_x > 1.0 or scale_y > 1.0:
        new_width = int(screenshot.size[0] * scale_x)
        new_height = int(screenshot.size[1] * scale_y)
        screenshot_scaled = screenshot.resize((new_width, new_height), Image.LANCZOS)
        screenshot_scaled.save("screenshot_scaled.png")
        print(f"스케일 적용된 스크린샷 크기: {screenshot_scaled.size}")
        
        # 스케일 적용된 이미지에서 dots.png 찾기
        try:
            screen_np = cv2.cvtColor(np.array(screenshot_scaled), cv2.COLOR_RGB2BGR)
            dots_img = cv2.imread("assets/img/dots.png")
            
            if dots_img is not None:
                result = cv2.matchTemplate(screen_np, dots_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                print(f"스케일 적용 후 매칭 값: {max_val}")
                if max_val > 0.4:
                    # 원래 좌표로 변환
                    original_x = max_loc[0] / scale_x
                    original_y = max_loc[1] / scale_y
                    print(f"✅ dots.png 발견! 원래 좌표: ({original_x}, {original_y})")
                    print(f"   스케일 적용 좌표: {max_loc}")
                else:
                    print(f"❌ 스케일 적용 후에도 찾을 수 없음")
            else:
                print("❌ dots.png 로드 실패")
        except Exception as e:
            print(f"스케일 적용 테스트 오류: {e}")

def create_improved_click_function():
    """개선된 click_with_img 함수 생성"""
    print("\n=== 개선된 함수 생성 ===")
    
    code = '''
def click_with_img_retina(img_path, max_attempts=15):
    """Retina 디스플레이를 고려한 이미지 찾기 함수"""
    import pyautogui
    import subprocess
    import cv2
    import numpy as np
    from PIL import Image
    import os
    
    # 해상도 스케일 계산
    def get_display_scale():
        pyautogui_size = pyautogui.size()
        subprocess.run(["screencapture", "-x", "temp_scale_check.png"], capture_output=True)
        if os.path.exists("temp_scale_check.png"):
            real_img = Image.open("temp_scale_check.png")
            scale_x = real_img.size[0] / pyautogui_size[0]
            scale_y = real_img.size[1] / pyautogui_size[1]
            os.remove("temp_scale_check.png")
            return scale_x, scale_y
        return 1.0, 1.0
    
    scale_x, scale_y = get_display_scale()
    confidence_levels = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
    
    for attempt in range(max_attempts):
        try:
            # macOS screencapture 사용
            subprocess.run(["screencapture", "-x", "temp_screen.png"], capture_output=True)
            if not os.path.exists("temp_screen.png"):
                continue
                
            screen_img = Image.open("temp_screen.png")
            screen_np = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2BGR)
            target_img = cv2.imread(img_path)
            
            if target_img is None:
                print(f"타겟 이미지 {img_path} 로드 실패")
                return False
            
            # 템플릿 매칭
            result = cv2.matchTemplate(screen_np, target_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.4:  # 임계값
                # PyAutoGUI 좌표계로 변환
                click_x = max_loc[0] / scale_x + target_img.shape[1] / (2 * scale_x)
                click_y = max_loc[1] / scale_y + target_img.shape[0] / (2 * scale_y)
                
                print(f"✅ {img_path} 발견! 신뢰도: {max_val:.3f}")
                print(f"   클릭 좌표: ({click_x}, {click_y})")
                
                pyautogui.click(click_x, click_y)
                os.remove("temp_screen.png")
                return True
            
            os.remove("temp_screen.png")
            
        except Exception as e:
            print(f"시도 {attempt + 1} 실패: {e}")
            if os.path.exists("temp_screen.png"):
                os.remove("temp_screen.png")
        
        time.sleep(0.5)
    
    print(f"❌ {img_path} 찾기 실패 ({max_attempts}회 시도)")
    return False
'''
    
    with open("improved_click_retina.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    print("improved_click_retina.py 파일 생성됨")

if __name__ == "__main__":
    test_with_scale()
    create_improved_click_function() 