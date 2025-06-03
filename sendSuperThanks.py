from threading import Thread, Lock, Event
import pyautogui
import time
import subprocess
import random
import xml.etree.ElementTree as ET
import sys
import atexit

stop_event = Event()
atexit.register(stop_event.set)

# XML 네임스페이스 정의
namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015'
}


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
    click_button(566, 575, 0.5)  # dot_button
    click_button(505, 656, 0.5)  # thanks_button
    time.sleep(1)
    click_button(321, 464, 0.5)  # message_input
    pyautogui.write(message)
    time.sleep(1)
    click_button(484, 637, 0.5)  # buy_and_send_button
    time.sleep(5)
    click_button(312, 513, 0.5)  # buy_button
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

def process_super_thanks(video_id, logger):
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



execution_lock = Lock()
current_thread = None

def run_in_sequence(func, video_id, logger):
        logger.info(f"[{video_id}] 작업 시작")
        def runner():
            global current_thread
            with execution_lock:
                if current_thread is not None:
                    logger.info("이전 작업 대기 중...")
                    current_thread.join()
                current_thread = Thread(target=process_super_thanks, args=(video_id, logger))
                current_thread.start()

        Thread(target=runner).start()


if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=yL6P7OR5WOM"
    sendSuperThanks(test_url)
