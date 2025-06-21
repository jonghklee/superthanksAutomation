
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
