import time
import requests
from sendSuperThanks import process_super_thanks
import csv
from pathlib import Path
import concurrent.futures
import atexit
from threading import Event, Lock, RLock
from bs4 import BeautifulSoup
import re
import logging
import json
import os
import subprocess
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import sys
from collections import defaultdict
import multiprocessing

isTest = 3
Ticket = 100

# 송금 완료된 영상 추적을 위한 파일 경로
COMPLETED_VIDEOS_FILE = "completed_videos.json"

# 채널별 타임아웃 실패 횟수 추적 (스레드 안전)
channel_timeout_failures = defaultdict(int)
channel_timeout_lock = RLock()

# 완료된 영상 추적 (스레드 안전)
completed_videos_cache = {}
completed_videos_lock = RLock()

# 마지막 영상 ID 추적 (스레드 안전)
last_video_ids_lock = RLock()

# Free Threading 설정
FREE_THREADING_ENABLED = not hasattr(sys, '_getframe') or getattr(sys, 'flags', None) and hasattr(sys.flags, 'disable_gil')
MAX_WORKERS = min(50, (multiprocessing.cpu_count() * 4)) if FREE_THREADING_ENABLED else min(20, multiprocessing.cpu_count() * 2)

print(f"🚀 Free Threading 상태: {'활성화' if FREE_THREADING_ENABLED else '비활성화'}")
print(f"🔧 최대 워커 수: {MAX_WORKERS}")
print(f"💻 CPU 코어 수: {multiprocessing.cpu_count()}")

# 로거 생성
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

stop_event = Event()
atexit.register(stop_event.set)

CSV_PATH = Path("./channel_list.csv")
POLL_INTERVAL = 1  # 1초 간격으로 다시 변경
last_video_ids = {}

namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015'
}

def capture_screen_on_error(error_info):
    """에러 발생 시 화면 캡처"""
    try:
        # captures 폴더가 없으면 생성
        if not os.path.exists("captures"):
            os.makedirs("captures")
        
        # 현재 시간으로 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_filename = f"captures/error_{timestamp}.png"
        
        # macOS에서 스크린샷 저장
        result = subprocess.run(["screencapture", "-x", capture_filename], capture_output=True)
        
        if result.returncode == 0 and os.path.exists(capture_filename):
            abs_path = os.path.abspath(capture_filename)
            logger.error(f"📸 에러 발생으로 인한 화면 캡처 저장됨: {abs_path}")
            logger.error(f"🔗 파일 링크: file://{abs_path}")
            return abs_path
        else:
            logger.error("❌ 화면 캡처 저장 실패")
            return None
            
    except Exception as e:
        logger.error(f"❌ 화면 캡처 중 오류: {e}")
        return None

def load_completed_videos():
    """완료된 영상 목록 로드 (스레드 안전)"""
    with completed_videos_lock:
        # 캐시된 데이터가 있으면 반환
        if completed_videos_cache:
            return completed_videos_cache.copy()
        
        try:
            if os.path.exists(COMPLETED_VIDEOS_FILE):
                with open(COMPLETED_VIDEOS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    completed_videos_cache.update(data)
                    return data
            return {}
        except Exception as e:
            logger.error(f"완료된 영상 목록 로드 실패: {e}")
            return {}

def save_completed_video(channel_id, video_id, video_title=""):
    """완료된 영상 정보 저장 (스레드 안전)"""
    with completed_videos_lock:
        try:
            # 캐시 업데이트
            if channel_id not in completed_videos_cache:
                completed_videos_cache[channel_id] = {}
            
            completed_videos_cache[channel_id][video_id] = {
                "title": video_title,
                "completed_at": datetime.now().isoformat(),
                "timestamp": int(time.time())
            }
            
            # 파일 저장
            with open(COMPLETED_VIDEOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(completed_videos_cache, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[{channel_id}] 송금 완료 영상 저장: {video_id}")
            
        except Exception as e:
            logger.error(f"완료된 영상 저장 실패: {e}")

def is_video_completed(channel_id, video_id):
    """영상이 이미 송금 완료되었는지 확인 (스레드 안전)"""
    with completed_videos_lock:
        try:
            # 캐시에서 먼저 확인
            if channel_id in completed_videos_cache:
                return video_id in completed_videos_cache[channel_id]
            
            # 캐시에 없으면 파일에서 로드
            completed = load_completed_videos()
            return video_id in completed.get(channel_id, {})
        except Exception as e:
            logger.error(f"완료된 영상 확인 실패: {e}")
            return False

def create_fast_session():
    """Free Threading 최적화된 세션 생성"""
    session = requests.Session()
    
    # Free Threading 환경에서 더 공격적인 설정
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.2,  # 더 빠른 재시도
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    # Free Threading에서는 더 많은 연결 풀 사용 가능
    pool_size = 100 if FREE_THREADING_ENABLED else 50
    adapter = HTTPAdapter(
        max_retries=retry_strategy, 
        pool_connections=pool_size, 
        pool_maxsize=pool_size,
        socket_options=[(41, 1, 1)]  # TCP_NODELAY 설정
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'DNT': '1'
    })
    
    return session

# 전역 세션 생성
session = create_fast_session()

def read_channel_ids():
    ids = []
    if not CSV_PATH.exists():
        return ids
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            channel_id = row.get('channel_id')
            if channel_id:
                ids.append(channel_id)
    return ids

def read_message():
    message = []
    if not CSV_PATH.exists():
        return message
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            message.append(row.get('message'))
    return message

def parse_html_content(html_content, channel_id):
    """HTML 파싱을 별도 함수로 분리 (CPU 집약적 작업)"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all("script")
        for script in scripts:
            if 'var ytInitialData' in script.text:
                initial_data = script.text
                match = re.search(r'"videoId":"(.*?)"', initial_data)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        logger.warning(f"[{channel_id}] HTML 파싱 오류: {e}")
        return None

def fetch_and_process(channel_id, mother_executor, message):
    """Free Threading 최적화된 채널 확인 및 처리"""
    global isTest, Ticket
    
    try:
        start_time = time.time()
        thread_id = threading.get_ident()
        
        # 스레드 안전한 타임아웃 설정
        with channel_timeout_lock:
            failure_count = channel_timeout_failures[channel_id]
            timeout = min(10 + (failure_count * 5), 25)
        
        if failure_count > 0:
            logger.info(f"[{channel_id}] 적응형 타임아웃: {timeout}초 (실패 횟수: {failure_count}) [Thread-{thread_id}]")
        
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        
        response = session.get(channel_url, timeout=timeout)
        
        if response.status_code == 200:
            # 성공 시 타임아웃 실패 카운터 리셋 (스레드 안전)
            with channel_timeout_lock:
                if channel_timeout_failures[channel_id] > 0:
                    logger.info(f"[{channel_id}] 요청 성공 - 타임아웃 카운터 리셋 [Thread-{thread_id}]")
                    channel_timeout_failures[channel_id] = 0
            
            # HTML 파싱을 별도 함수로 분리 (CPU 집약적 작업을 병렬화)
            video_id = parse_html_content(response.text, channel_id)
            
            if video_id:
                # 중복 송금 방지 확인
                if is_video_completed(channel_id, video_id):
                    logger.info(f"[{channel_id}] 이미 송금 완료된 영상: {video_id} [Thread-{thread_id}]")
                    return
                
                # 스레드 안전한 last_video_ids 접근
                with last_video_ids_lock:
                    is_new_video = last_video_ids.get(channel_id) != video_id or isTest > 0
                    if is_new_video and Ticket > 0:
                        if isTest > 0:
                            isTest -= 1
                        Ticket -= 1
                        logger.info(f"[{channel_id}] 새 영상 발견! {video_id} [Thread-{thread_id}]")
                        last_video_ids[channel_id] = video_id
                        
                        # 송금 작업 제출
                        future = mother_executor.submit(process_super_thanks, video_id, logger, message)
                        
                        # 송금 완료 후 기록 (비동기로 처리하기 위해 콜백 추가)
                        def mark_completed(fut):
                            try:
                                save_completed_video(channel_id, video_id)
                            except Exception as e:
                                logger.error(f"송금 완료 기록 실패: {e}")
                        
                        future.add_done_callback(mark_completed)
        else:
            logger.warning(f"[{channel_id}] 페이지 요청 실패: {response.status_code}")
            
        elapsed = time.time() - start_time
        logger.debug(f"[{channel_id}] 확인 완료 ({elapsed:.2f}초)")
        
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # 스레드 안전한 타임아웃 실패 카운터 증가
        if isinstance(e, requests.exceptions.Timeout):
            with channel_timeout_lock:
                channel_timeout_failures[channel_id] += 1
                failure_count = channel_timeout_failures[channel_id]
            logger.warning(f"[{channel_id}] 타임아웃 오류 (실패 횟수: {failure_count}) - 다음 시도에서 타임아웃 증가 [Thread-{thread_id}]")
        else:
            logger.warning(f"[{channel_id}] 네트워크 오류: {type(e).__name__} [Thread-{thread_id}]")
        
        # 네트워크 오류 시 캡처 (타임아웃은 너무 자주 발생할 수 있으므로 제외)
        if not isinstance(e, requests.exceptions.Timeout):
            capture_screen_on_error(f"Network error for channel {channel_id}: {e}")
        
    except Exception as e:
        logger.error(f"[{channel_id}] 예상치 못한 오류 발생 [Thread-{thread_id}]", exc_info=True)
        # 예상치 못한 오류 시 캡처
        capture_screen_on_error(f"Unexpected error for channel {channel_id}: {e}")

def initialize_last_video_ids():
    """Free Threading 최적화된 초기화"""
    global last_video_ids
    channel_ids = read_channel_ids()
    
    logger.info(f"총 {len(channel_ids)}개 채널 초기화 시작... (Free Threading: {'활성화' if FREE_THREADING_ENABLED else '비활성화'})")
    
    # Free Threading에서는 더 많은 워커 사용 가능
    init_workers = min(MAX_WORKERS, len(channel_ids))
    logger.info(f"초기화 워커 수: {init_workers}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=init_workers) as executor:
        futures = []
        
        def init_channel(channel_id):
            try:
                thread_id = threading.get_ident()
                channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
                response = session.get(channel_url, timeout=10)
                
                if response.status_code == 200:
                    # HTML 파싱을 별도 함수 사용 (CPU 집약적 작업)
                    video_id = parse_html_content(response.text, channel_id)
                    if video_id:
                        # 스레드 안전한 last_video_ids 업데이트
                        with last_video_ids_lock:
                            last_video_ids[channel_id] = video_id
                        logger.info(f"[{channel_id}] 초기화 완료: {video_id} [Thread-{thread_id}]")
            except Exception as e:
                logger.warning(f"[{channel_id}] 초기화 실패: {e} [Thread-{threading.get_ident()}]")
        
        # 모든 채널에 대해 초기화 작업 제출
        for channel_id in channel_ids:
            future = executor.submit(init_channel, channel_id)
            futures.append(future)
        
        # 모든 초기화 작업 완료 대기 (최대 30초)
        concurrent.futures.wait(futures, timeout=30)
    
    logger.info(f"초기화 완료: {len(last_video_ids)}개 채널")

def poll_feed():
    """Free Threading 최적화된 피드 폴링 - 1분 안에 100개 채널 확인"""
    global last_video_ids
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as mother_executor:
        try:
            cycle_count = 0
            while not stop_event.is_set() and Ticket > 0:
                try:
                    cycle_count += 1
                    cycle_start = time.time()
                    logger.info(f"[=== 피드 체크 사이클 #{cycle_count} 시작 ===]")
                    logger.info(f"Free Threading: {'활성화' if FREE_THREADING_ENABLED else '비활성화'}, 최대 워커: {MAX_WORKERS}")
                    
                    channel_ids = read_channel_ids()
                    messages = read_message()
                    
                    logger.info(f"확인할 채널 수: {len(channel_ids)}개, 남은 티켓: {Ticket}")
                    
                    # Free Threading에서는 더 많은 워커 사용
                    poll_workers = min(MAX_WORKERS, len(channel_ids))
                    with concurrent.futures.ThreadPoolExecutor(max_workers=poll_workers) as executor:
                        futures = []
                        
                        for i, channel_id in enumerate(channel_ids):
                            message = messages[i] if i < len(messages) else ""
                            future = executor.submit(fetch_and_process, channel_id, mother_executor, message)
                            futures.append(future)
                        
                        # 모든 작업 완료 대기 (최대 50초)
                        completed_futures = concurrent.futures.wait(futures, timeout=50)
                        
                        # 완료되지 않은 작업 확인
                        not_done = len(completed_futures.not_done)
                        done = len(completed_futures.done)
                        if not_done > 0:
                            logger.warning(f"⚠️ {not_done}개 채널 확인이 시간 초과로 완료되지 않았습니다 (완료: {done}개)")
                    
                    cycle_elapsed = time.time() - cycle_start
                    channels_per_second = len(channel_ids) / cycle_elapsed if cycle_elapsed > 0 else 0
                    logger.info(f"[=== 사이클 #{cycle_count} 완료: {cycle_elapsed:.2f}초, {channels_per_second:.1f} 채널/초 ===]")
                    
                    # 1분 사이클 맞추기 위한 대기
                    if cycle_elapsed < 60:
                        wait_time = 60 - cycle_elapsed
                        logger.info(f"다음 사이클까지 {wait_time:.1f}초 대기...")
                        time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error("[피드 전체 오류]", exc_info=True)
                    # 전체 오류 시 캡처
                    capture_screen_on_error(f"Feed polling error: {e}")
                    time.sleep(5)  # 오류 시 5초 대기
                    
        except KeyboardInterrupt:
            logger.warning("사용자 인터럽트 - 작업 취소 시도")
            mother_executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            # 세션 종료
            session.close()

if __name__ == '__main__':
    logger.info("")
    logger.info("=" * 50)
    logger.info("------- 프로그램 시작 -------")
    logger.info("=" * 50)
    logger.info(f"isTest: {isTest}, Ticket: {Ticket}")
    logger.info("빠른 초기화 중...")
    
    try:
        initialize_last_video_ids()
        logger.info("초기화 완료 - 피드 폴링 시작")
        poll_feed()
    except Exception as e:
        logger.error("프로그램 실행 중 오류 발생", exc_info=True)
        capture_screen_on_error(f"Program startup error: {e}")