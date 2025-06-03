import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask
from sendSuperThanks import process_super_thanks, run_in_sequence
import csv
from pathlib import Path
import concurrent.futures
import sys
import atexit
from threading import Event
from xml.dom import minidom
from bs4 import BeautifulSoup
import re
import logging

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
POLL_INTERVAL = 1  # 1초 간격
last_video_ids = {}

namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015'
}

def read_channel_ids():
    ids = []
    if not CSV_PATH.exists():
        return ids
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            channel_id = row.get('channel_id')
            username = row.get('username')
            if channel_id:
                ids.append((channel_id, username))
    return ids


def fetch_and_process(channel_id):
    try:
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        response = requests.get(channel_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all("script")
            for script in scripts:
                if 'var ytInitialData' in script.text:
                    initial_data = script.text
                    match = re.search(r'"videoId":"(.*?)"', initial_data)
                    if match:
                        video_id = match.group(1)
                        if last_video_ids.get(channel_id) != video_id:
                            logger.info(f"[{channel_id}] 새 영상 발견! {video_id}")
                            last_video_ids[channel_id] = video_id
                            run_in_sequence(process_super_thanks, video_id, logger)
                        else:
                            logger.info(f"[{channel_id}] 새 영상 없음({video_id})")
                    break
        else:
            logger.error(f"[{channel_id}] 페이지 요청 실패: {response.status_code}")
    except Exception as e:
        logger.error(f"[{channel_id}] 오류 발생", exc_info=True)

def initialize_last_video_ids():
    global last_video_ids
    for channel_id in read_channel_ids():
        try:
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            response = requests.get(channel_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = soup.find_all("script")
                for script in scripts:
                    if 'var ytInitialData' in script.text:
                        initial_data = script.text
                        match = re.search(r'"videoId":"(.*?)"', initial_data)
                        if match:
                            last_video_ids[channel_id] = match.group(1)
                        break
        except Exception as e:
            logger.error(f"[{channel_id}] 초기화 실패", exc_info=True)
    logger.info(last_video_ids)


def poll_feed():
    global last_video_ids
    while not stop_event.is_set():
        try:
            logger.info("[피드 체크 중...]")
            channel_ids = read_channel_ids()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(fetch_and_process, channel_ids)
        except Exception as e:
            logger.error("[피드 전체 오류]", exc_info=True)
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    initialize_last_video_ids()
    poll_feed()
    #fetch_and_process('UCu0elhwDIhuEIEwJa2xs3fw')