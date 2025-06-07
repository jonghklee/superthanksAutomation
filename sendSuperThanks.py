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


stop_event = Event()
atexit.register(stop_event.set)

# XML 네임스페이스 정의
namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015'
}

executor = ThreadPoolExecutor(max_workers=1)

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

def click_with_img(img_path):
    for attempt in range(15):
        try:
            img = pyautogui.locateOnScreen(img_path, confidence=0.8)
        except Exception as e:
            print(f"이미지 찾기 시도 {attempt + 1} 실패, 다시 시도합니다...")
            continue
        if img:
            click_button(img.left + img.width / 2, img.top + img.height / 2, 0.5)
            return True
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

    # 버튼 클릭 함수 호출

    # img/superthanks1.png 이미지를 직접 찾아 클릭 시도
    time.sleep(2)  # UI가 업데이트될 시간을 줍니다. 필요에 따라 조절하세요.
    if click_with_img("img/dots.png"):
        # img/dots.png 클릭 성공, 잠시 대기 후 img/superthanks2.png 시도
        time.sleep(1)  # UI가 업데이트될 시간을 줍니다. 필요에 따라 조절하세요.
        if click_with_img("img/superthanks2.png"):
            pass
        else:
            return "superthanks를 받지 않는 영상입니다."
    else:
        return "superthanks를 받지 않는 영상입니다."

    time.sleep(1)
    click_with_img("img/3_text.png")
    pyautogui.hotkey('command', 'a')  # cmd + a로 지우기
    pyautogui.press('backspace')
    # 메시지 입력 전 잠시 대기
    time.sleep(0.5)
    # 메시지를 한 글자씩 입력
    pyperclip.copy(message)
    pyautogui.hotkey('command', 'v')
    
    time.sleep(0.1)  # 각 글자 입력 사이에 약간의 딜레이
    time.sleep(1)
    click_with_img("img/4_buyandsend.png")
    time.sleep(5)
    click_with_img("img/5_buy.png")
    time.sleep(2)
    #click_button(312, 476, 0.5)  # Verify_button
    time.sleep(5)

    # 크롬 탭 닫기 AppleScript 명령어 수정
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
    
    # AppleScript 실행하여 특정 URL의 크롬 탭 닫기
    close_result = subprocess.run(["osascript", "-e", close_script], capture_output=True, text=True)

    time.sleep(1)
    
    if close_result.returncode != 0:
        return f"탭 닫기 실패: {close_result.stderr}"

    return "성공적으로 완료되었습니다."

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
    run_in_sequence(sendSuperThanks, "mTJdHpAHKKk", logger, "감사합니다!")