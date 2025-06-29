#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 채널 찾기 및 추가 도구
사용자가 쉽게 YouTube 채널을 찾아서 channel_list.csv에 추가할 수 있도록 도와주는 프로그램
"""

import sys
import csv
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json

CSV_PATH = Path("./config/channel_list.csv")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

def print_banner():
    """프로그램 시작 배너"""
    print("🔍 YouTube 채널 찾기 도구")
    print("=" * 50)
    print("📺 채널 핸들이나 URL로 채널 ID를 자동으로 찾아드립니다!")
    print()

def extract_channel_id_from_handle(handle_url):
    """YouTube 핸들에서 채널 ID 추출"""
    try:
        print(f"🌐 {handle_url} 접속 중...")
        response = requests.get(handle_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"❌ 접속 실패: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 방법 1: canonical link에서 추출
        canonical = soup.find("link", rel="canonical")
        if canonical and "channel/" in canonical["href"]:
            channel_id = canonical["href"].split("channel/")[-1]
            print(f"✅ 채널 ID 발견 (canonical): {channel_id}")
            return channel_id

        # 방법 2: 페이지 소스에서 정규식으로 추출
        match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', response.text)
        if match:
            channel_id = match.group(1)
            print(f"✅ 채널 ID 발견 (regex): {channel_id}")
            return channel_id
            
        print(f"❌ 채널 ID를 찾을 수 없습니다")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def get_channel_info(channel_id):
    """채널 ID로 채널 정보 가져오기"""
    try:
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        response = requests.get(channel_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 채널명 추출
        title_tag = soup.find("meta", property="og:title")
        channel_name = title_tag["content"] if title_tag else "알 수 없음"
        
        # 구독자 수 추출 시도
        subscriber_match = re.search(r'"subscriberCountText":{"simpleText":"([^"]+)"', response.text)
        subscriber_count = subscriber_match.group(1) if subscriber_match else "비공개"
        
        return {
            "name": channel_name,
            "subscribers": subscriber_count,
            "url": channel_url
        }
    except:
        return None

def read_existing_channels():
    """기존 채널 목록 읽기"""
    existing = {}
    if CSV_PATH.exists():
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing[row['channel_id']] = row['username']
        except:
            pass
    return existing

def add_to_csv(username, channel_id, message="좋은 영상 감사합니다"):
    """채널을 CSV 파일에 추가"""
    # 기존 데이터 읽기
    rows = []
    fieldnames = ['username', 'channel_id', 'message']
    
    if CSV_PATH.exists():
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or fieldnames
                rows = list(reader)
        except:
            pass
    
    # 새 행 추가
    new_row = {
        'username': username,
        'channel_id': channel_id,
        'message': message
    }
    rows.append(new_row)
    
    # CSV 파일에 저장
    try:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")
        return False

def parse_youtube_url(url):
    """다양한 YouTube URL 형식을 파싱"""
    # @핸들 형식
    if url.startswith('@'):
        return f"https://www.youtube.com/{url}"
    
    # 이미 전체 URL인 경우
    if url.startswith('http'):
        return url
    
    # 핸들명만 입력한 경우
    if not url.startswith('youtube.com') and not url.startswith('www.youtube.com'):
        return f"https://www.youtube.com/@{url}"
    
    # youtube.com으로 시작하는 경우
    if not url.startswith('http'):
        return f"https://{url}"
    
    return url

def interactive_mode():
    """대화형 모드"""
    print("🎯 대화형 채널 추가 모드")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요")
    print()
    
    existing = read_existing_channels()
    
    while True:
        print("-" * 50)
        user_input = input("📺 YouTube 채널 입력 (핸들/URL): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 프로그램을 종료합니다")
            break
            
        if not user_input:
            continue
        
        # URL 파싱
        youtube_url = parse_youtube_url(user_input)
        print(f"🔗 처리 URL: {youtube_url}")
        
        # 채널 ID 추출
        channel_id = extract_channel_id_from_handle(youtube_url)
        if not channel_id:
            print("❌ 채널 ID를 찾을 수 없습니다. 다른 URL을 시도해보세요.")
            continue
        
        # 중복 확인
        if channel_id in existing:
            print(f"⚠️  이미 등록된 채널입니다: {existing[channel_id]}")
            continue
        
        # 채널 정보 가져오기
        print("📋 채널 정보 확인 중...")
        channel_info = get_channel_info(channel_id)
        
        if channel_info:
            print(f"✅ 채널 발견!")
            print(f"   📺 이름: {channel_info['name']}")
            print(f"   👥 구독자: {channel_info['subscribers']}")
            print(f"   🆔 ID: {channel_id}")
        else:
            print(f"✅ 채널 ID: {channel_id}")
        
        # 사용자 확인
        confirm = input("💾 이 채널을 추가하시겠습니까? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '예', 'ㅇ']:
            print("❌ 추가를 취소했습니다")
            continue
        
        # 별명 입력
        username = input("📝 채널 별명 입력 (엔터시 채널명 사용): ").strip()
        if not username and channel_info:
            username = channel_info['name']
        elif not username:
            username = f"채널_{channel_id[:8]}"
        
        # 메시지 입력
        message = input("💬 송금 메시지 (엔터시 기본 메시지): ").strip()
        if not message:
            message = "좋은 영상 감사합니다"
        
        # CSV에 추가
        if add_to_csv(username, channel_id, message):
            print(f"🎉 '{username}' 채널이 성공적으로 추가되었습니다!")
            existing[channel_id] = username
        else:
            print("❌ 채널 추가에 실패했습니다")

def batch_mode(input_file):
    """배치 모드 - 파일에서 여러 채널 읽어서 처리"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        return
    
    print(f"📄 {len(lines)}개 채널 처리 시작...")
    existing = read_existing_channels()
    
    for i, line in enumerate(lines, 1):
        print(f"\n[{i}/{len(lines)}] 처리 중: {line}")
        
        youtube_url = parse_youtube_url(line)
        channel_id = extract_channel_id_from_handle(youtube_url)
        
        if not channel_id:
            print(f"❌ 실패: {line}")
            continue
            
        if channel_id in existing:
            print(f"⚠️  이미 등록됨: {existing[channel_id]}")
            continue
        
        channel_info = get_channel_info(channel_id)
        username = channel_info['name'] if channel_info else f"채널_{channel_id[:8]}"
        
        if add_to_csv(username, channel_id):
            print(f"✅ 추가 완료: {username}")
            existing[channel_id] = username
        else:
            print(f"❌ 추가 실패: {line}")

def show_current_channels():
    """현재 등록된 채널 목록 표시"""
    if not CSV_PATH.exists():
        print("📝 등록된 채널이 없습니다")
        return
    
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            channels = list(reader)
        
        if not channels:
            print("📝 등록된 채널이 없습니다")
            return
        
        print(f"📺 현재 등록된 채널 ({len(channels)}개):")
        print("-" * 80)
        for i, channel in enumerate(channels, 1):
            print(f"{i:3}. {channel['username']:<20} | {channel['channel_id']} | {channel['message']}")
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ 채널 목록 읽기 실패: {e}")

def print_help():
    """도움말 출력"""
    help_text = """
🔍 YouTube 채널 찾기 도구 사용법

사용 방법:
    python channel_finder.py                    # 대화형 모드
    python channel_finder.py -list              # 현재 채널 목록 보기
    python channel_finder.py -batch 파일명      # 파일에서 일괄 추가
    python channel_finder.py -help              # 도움말

대화형 모드:
    - 채널 핸들, URL을 입력하면 자동으로 채널 ID 찾기
    - 채널 정보 확인 후 CSV에 추가
    - 'quit' 입력으로 종료

입력 가능한 형식:
    @channelname                               # 핸들
    channelname                                # 핸들 (@ 없이)
    https://www.youtube.com/@channelname       # 핸들 URL
    https://www.youtube.com/channel/UCxxxxx    # 채널 URL

배치 모드:
    - 텍스트 파일에 한 줄씩 채널 핸들/URL 작성
    - 한번에 여러 채널 추가 가능
    
예시 파일 (channels.txt):
    @kbs
    @sbs
    https://www.youtube.com/@mbc
    """
    print(help_text)

def main():
    print_banner()
    
    args = sys.argv[1:]
    
    if not args:
        # 대화형 모드
        interactive_mode()
    elif args[0] == '-help' or args[0] == '--help':
        print_help()
    elif args[0] == '-list':
        show_current_channels()
    elif args[0] == '-batch' and len(args) > 1:
        batch_mode(args[1])
    else:
        print("❌ 잘못된 옵션입니다. -help로 도움말을 확인하세요.")

if __name__ == "__main__":
    main() 