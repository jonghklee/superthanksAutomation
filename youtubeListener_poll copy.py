import time
import requests
from sendSuperThanks import process_super_thanks
import csv
from pathlib import Path
import concurrent.futures
import atexit
from threading import Event
from bs4 import BeautifulSoup
import re
import logging
import json
import os
import subprocess
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

isTest = 3
Ticket = 100

# 송금 완료된 영상 추적을 위한 파일 경로
COMPLETED_VIDEOS_FILE = "completed_videos.json"

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

# 채널별 타임아웃 실패 횟수 추적
channel_timeout_failures = {}

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
    """완료된 영상 목록 로드"""
    try:
        if os.path.exists(COMPLETED_VIDEOS_FILE):
            with open(COMPLETED_VIDEOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"완료된 영상 목록 로드 실패: {e}")
        return {}

def save_completed_video(channel_id, video_id, video_title=""):
    """완료된 영상 정보 저장"""
    try:
        completed = load_completed_videos()
        if channel_id not in completed:
            completed[channel_id] = {}
        
        completed[channel_id][video_id] = {
            "title": video_title,
            "completed_at": datetime.now().isoformat(),
            "timestamp": int(time.time())
        }
        
        with open(COMPLETED_VIDEOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(completed, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[{channel_id}] 송금 완료 영상 저장: {video_id}")
        
    except Exception as e:
        logger.error(f"완료된 영상 저장 실패: {e}")

def is_video_completed(channel_id, video_id):
    """영상이 이미 송금 완료되었는지 확인"""
    try:
        completed = load_completed_videos()
        return video_id in completed.get(channel_id, {})
    except Exception as e:
        logger.error(f"완료된 영상 확인 실패: {e}")
        return False

def create_fast_session():
    """빠른 요청을 위한 최적화된 세션 생성"""
    session = requests.Session()
    
    # 빠른 재시도 전략 - 실패 시 빠르게 포기
    retry_strategy = Retry(
        total=2,  # 재시도 횟수 감소
        backoff_factor=0.3,  # 빠른 재시도
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 빠른 요청을 위한 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
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

def get_channel_timeout(channel_id):
    """채널별 적응형 타임아웃 계산"""
    base_timeout = 10  # 기본 타임아웃
    failure_count = channel_timeout_failures.get(channel_id, 0)
    
    # 실패 횟수에 따라 타임아웃 증가 (최대 30초)
    adaptive_timeout = min(base_timeout + (failure_count * 5), 30)
    return adaptive_timeout

def fetch_and_process(channel_id, mother_executor, message):
    """빠른 채널 확인 및 처리"""
    global isTest, Ticket
    
    try:
        start_time = time.time()
        
        # 적응형 타임아웃 설정 (실패한 채널은 더 긴 타임아웃)
        timeout = get_channel_timeout(channel_id)
        failure_count = channel_timeout_failures.get(channel_id, 0)
        
        if failure_count > 0:
            logger.info(f"[{channel_id}] 적응형 타임아웃 적용: {timeout}초 (실패횟수: {failure_count})")
        
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        
        response = session.get(channel_url, timeout=timeout)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all("script")
            for script in scripts:
                if 'var ytInitialData' in script.text:
                    initial_data = script.text
                    match = re.search(r'"videoId":"(.*?)"', initial_data)
                    if match:
                        video_id = match.group(1)
                        
                        # 중복 송금 방지 확인
                        if is_video_completed(channel_id, video_id):
                            logger.info(f"[{channel_id}] 이미 송금 완료된 영상: {video_id}")
                            return
                        
                        if (last_video_ids.get(channel_id) != video_id or isTest > 0) and Ticket > 0:
                            if isTest > 0:
                                isTest -= 1         
                            Ticket -= 1
                            logger.info(f"[{channel_id}] 새 영상 발견! {video_id}")
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
                            # logger.info(f"[{channel_id}] 새 영상 없음({video_id})")
                            pass
                    break
        else:
            logger.warning(f"[{channel_id}] 페이지 요청 실패: {response.status_code}")
        
        # 성공하면 실패 횟수 초기화
        if channel_id in channel_timeout_failures:
            del channel_timeout_failures[channel_id]
            logger.info(f"[{channel_id}] 타임아웃 실패 기록 초기화")
            
        elapsed = time.time() - start_time
        logger.debug(f"[{channel_id}] 확인 완료 ({elapsed:.2f}초)")
        
    except requests.exceptions.Timeout as e:
        # 타임아웃 실패 시 실패 횟수 증가
        channel_timeout_failures[channel_id] = channel_timeout_failures.get(channel_id, 0) + 1
        failure_count = channel_timeout_failures[channel_id]
        logger.warning(f"[{channel_id}] 타임아웃 오류 (실패횟수: {failure_count}, 다음 타임아웃: {get_channel_timeout(channel_id)}초)")
        # 타임아웃 오류 시 캡처
        capture_screen_on_error(f"Timeout error for channel {channel_id}: {e}")
        
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"[{channel_id}] 연결 오류: {type(e).__name__}")
        # 연결 오류 시 캡처
        capture_screen_on_error(f"Connection error for channel {channel_id}: {e}")
        
    except Exception as e:
        logger.error(f"[{channel_id}] 예상치 못한 오류 발생", exc_info=True)
        # 예상치 못한 오류 시 캡처
        capture_screen_on_error(f"Unexpected error for channel {channel_id}: {e}")

def initialize_last_video_ids():
    """빠른 초기화"""
    global last_video_ids
    channel_ids = read_channel_ids()
    
    logger.info(f"총 {len(channel_ids)}개 채널 초기화 시작...")
    
    # 병렬로 빠르게 초기화 (최대 20개 동시 처리)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        def init_channel(channel_id):
            try:
                channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
                response = session.get(channel_url, timeout=get_channel_timeout(channel_id))
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    scripts = soup.find_all("script")
                    for script in scripts:
                        if 'var ytInitialData' in script.text:
                            initial_data = script.text
                            match = re.search(r'"videoId":"(.*?)"', initial_data)
                            if match:
                                last_video_ids[channel_id] = match.group(1)
                                logger.info(f"[{channel_id}] 초기화 완료: {match.group(1)}")
                            break
            except Exception as e:
                logger.warning(f"[{channel_id}] 초기화 실패: {e}")
        
        # 모든 채널에 대해 초기화 작업 제출
        for channel_id in channel_ids:
            future = executor.submit(init_channel, channel_id)
            futures.append(future)
        
        # 모든 초기화 작업 완료 대기 (최대 30초)
        concurrent.futures.wait(futures, timeout=30)
    
    logger.info(f"초기화 완료: {len(last_video_ids)}개 채널")

def poll_feed():
    """최적화된 피드 폴링 - 1분 안에 100개 채널 확인"""
    global last_video_ids
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as mother_executor:
        try:
            while not stop_event.is_set() and Ticket > 0:
                try:
                    cycle_start = time.time()
                    logger.info("[=== 피드 체크 사이클 시작 ===]")
                    
                    channel_ids = read_channel_ids()
                    messages = read_message()
                    
                    logger.info(f"확인할 채널 수: {len(channel_ids)}개")
                    
                    # 최대 20개 채널을 동시에 처리 (100개 채널을 50초 안에 처리하기 위해)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                        futures = []
                        
                        for i, channel_id in enumerate(channel_ids):
                            message = messages[i] if i < len(messages) else ""
                            future = executor.submit(fetch_and_process, channel_id, mother_executor, message)
                            futures.append(future)
                        
                        # 모든 작업 완료 대기 (최대 50초)
                        completed_futures = concurrent.futures.wait(futures, timeout=50)
                        
                        # 완료되지 않은 작업 확인
                        not_done = len(completed_futures.not_done)
                        if not_done > 0:
                            logger.warning(f"⚠️ {not_done}개 채널 확인이 시간 초과로 완료되지 않았습니다")
                    
                    cycle_elapsed = time.time() - cycle_start
                    logger.info(f"[=== 피드 체크 사이클 완료: {cycle_elapsed:.2f}초 ===]")
                    
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