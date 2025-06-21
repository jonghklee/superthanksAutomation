from threading import Thread, Lock, Event
import pyautogui
import time
import subprocess
import random
import xml.etree.ElementTree as ET
import sys
import atexit
import logging
import pyperclip
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
from PIL import Image
import os


stop_event = Event()
atexit.register(stop_event.set)

# XML 네임스페이스 정의
namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015'
}

executor = ThreadPoolExecutor(max_workers=1)

# 딜레이 관련 상수
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

def wait_and_retry(func, max_attempts=5, delay_type='medium'):
    """재시도 로직이 포함된 대기 함수"""
    for attempt in range(max_attempts):
        try:
            result = func()
            if result:
                return True
            smart_delay(delay_type)
        except Exception as e:
            print(f"시도 {attempt + 1} 실패: {e}")
            smart_delay('short')
    return False

# 특정 위치로 이동하여 클릭하는 함수 정의
def click_button(x, y, wait_time):
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

# 열고자 하는 URL

def click_with_img(img_path, max_attempts=15, confidence=0.8):
    """macOS screencapture를 사용한 이미지 찾기 함수 - Retina 디스플레이 지원"""
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
            
            if max_val >= confidence:
                # PyAutoGUI 좌표계로 변환 (중심점 계산)
                click_x = max_loc[0] / scale_x + target_img.shape[1] / (2 * scale_x)
                click_y = max_loc[1] / scale_y + target_img.shape[0] / (2 * scale_y)
                
                print(f"✅ 이미지 {img_path} 발견 (confidence: {max_val:.3f}, 시도: {attempt + 1})")
                print(f"   클릭 좌표: ({click_x:.1f}, {click_y:.1f})")
                
                os.remove("temp_screen.png")
                click_button(click_x, click_y, smart_delay('click'))
                return True
            
            os.remove("temp_screen.png")
            
        except Exception as e:
            print(f"이미지 찾기 시도 {attempt + 1} 실패: {e}")
            if os.path.exists("temp_screen.png"):
                os.remove("temp_screen.png")
        
        # 재시도 전 딜레이
        if attempt < max_attempts - 1:
            smart_delay('short', multiplier=0.5)
    
    print(f"❌ 이미지 {img_path}를 찾을 수 없습니다. ({max_attempts}회 시도, confidence: {confidence})")
    return False


def sendSuperThanks(url, message):
    # 창의 위치 및 크기 설정: {x, y, width, height}
    bounds = "{0, 0, 623, 804}"

    # AppleScript 명령어 구성
    script = f'''
    tell application "Google Chrome"
        activate
        open location "{url}"
        delay 1
        set bounds of front window to {bounds}
    end tell
    '''

    # AppleScript 실행
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"URL 열기 실패: {result.stderr}"

    try:
        # 페이지 로딩 대기
        smart_delay('ui_update')
        
        # dots 버튼 클릭 시도
        if click_with_img("img/dots.png"):
            smart_delay('ui_update')  # 메뉴가 나타날 시간 대기
            
            if click_with_img("img/superthanks2.png"):
                print("Super Thanks 메뉴 클릭 성공")
            else:
                return "superthanks를 받지 않는 영상입니다."
        else:
            return "superthanks를 받지 않는 영상입니다."

        # 텍스트 입력 필드 클릭 및 메시지 입력
        smart_delay('medium')
        if click_with_img("img/3_text.png"):
            smart_delay('click')
            pyautogui.hotkey('command', 'a')  # 기존 텍스트 선택
            smart_delay('type')
            pyautogui.press('backspace')  # 삭제
            smart_delay('click')
            
            # 메시지 입력
            pyperclip.copy(message)
            pyautogui.hotkey('command', 'v')
            smart_delay('medium')
        
        # Buy and Send 버튼 클릭
        if click_with_img("img/4_buyandsend.png"):
            smart_delay('long')  # 결제 페이지 로딩 대기
            
            # Buy 버튼 클릭
            if click_with_img("img/5_buy.png"):
                smart_delay('long', multiplier=2)  # 결제 처리 대기
            else:
                print("Buy 버튼을 찾을 수 없습니다.")
        else:
            print("Buy and Send 버튼을 찾을 수 없습니다.")
        
        # 최종 처리 완료 대기
        smart_delay('long')

        return "성공적으로 완료되었습니다."

    finally:
        # 크롬 탭 닫기 AppleScript 명령어 - 함수가 어떻게 끝나든 항상 실행
        close_script = '''
        tell application "Google Chrome"
            set tabIndex to 0
            repeat with t in (tabs of front window)
                set tabIndex to tabIndex + 1
                if URL of t is equal to "{url}" then
                    close tab tabIndex of front window
                    exit repeat
                end if
            end repeat
        end tell
        '''.format(url=url)
        
        try:
            # AppleScript 실행하여 특정 URL의 크롬 탭 닫기
            close_result = subprocess.run(["osascript", "-e", close_script], capture_output=True, text=True)
            smart_delay('medium')  # 탭 닫기 후 안정화 대기
            
            if close_result.returncode != 0:
                print(f"탭 닫기 실패: {close_result.stderr}")
            else:
                print("탭 닫기 성공")
        except Exception as e:
            print(f"탭 닫기 중 예외 발생: {e}")

def process_super_thanks(video_id, logger, message):
    logger.info(f"[{video_id}] 작업 시작")
    try:
        if not video_id:
            logger.info(f"[{video_id}] video_id가 주어지지 않았습니다.")
            return
        logger.info(f"[{video_id}] 영상ID: {video_id}")
        logger.info(f"[{video_id}] sending super thanks...")
        logger.info(f"[{video_id}] {sendSuperThanks('https://www.youtube.com/watch?v=' + video_id, message)}")
    except Exception as e:
        logger.info(f"[{video_id}] 오류 발생: {e}")
    logger.info(f"[{video_id}] 작업 끝")




if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

    # 파일 핸들러
    file_handler = logging.FileHandler('youtube_listener.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

    # 핸들러 등록
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    #run_in_sequence(sendSuperThanks, "mTJdHpAHKKk", logger, "감사합니다!")