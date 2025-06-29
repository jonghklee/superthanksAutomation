#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대량 채널 설정 도구
사용자가 여러 YouTube 채널을 한번에 쉽게 등록할 수 있도록 도와주는 도구
"""

import sys
import csv
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

CSV_PATH = Path("./config/channel_list.csv")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# 스레드 안전한 출력을 위한 Lock
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """스레드 안전한 출력"""
    with print_lock:
        print(*args, **kwargs)

def print_banner():
    """프로그램 시작 배너"""
    print("🚀 대량 채널 설정 도구")
    print("=" * 60)
    print("📺 여러 YouTube 채널을 한번에 빠르게 등록하세요!")
    print()

def extract_channel_id_from_handle(handle_url):
    """YouTube 핸들에서 채널 ID 추출"""
    try:
        response = requests.get(handle_url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 방법 1: canonical link에서 추출
        canonical = soup.find("link", rel="canonical")
        if canonical and "channel/" in canonical["href"]:
            return canonical["href"].split("channel/")[-1]

        # 방법 2: 페이지 소스에서 정규식으로 추출
        match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', response.text)
        if match:
            return match.group(1)
            
        return None
    except Exception:
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

def parse_youtube_url(url):
    """다양한 YouTube URL 형식을 파싱"""
    if url.startswith('@'):
        return f"https://www.youtube.com/{url}"
    
    if url.startswith('http'):
        return url
    
    if not url.startswith('youtube.com') and not url.startswith('www.youtube.com'):
        return f"https://www.youtube.com/@{url}"
    
    if not url.startswith('http'):
        return f"https://{url}"
    
    return url

def process_single_channel(channel_input, index, total):
    """단일 채널 처리 (스레드용)"""
    result = {
        'input': channel_input,
        'index': index,
        'success': False,
        'channel_id': None,
        'info': None,
        'error': None
    }
    
    try:
        youtube_url = parse_youtube_url(channel_input.strip())
        safe_print(f"[{index:3}/{total}] 🌐 {youtube_url}")
        
        channel_id = extract_channel_id_from_handle(youtube_url)
        if not channel_id:
            result['error'] = "채널 ID를 찾을 수 없음"
            return result
        
        result['channel_id'] = channel_id
        
        # 채널 정보 가져오기
        channel_info = get_channel_info(channel_id)
        result['info'] = channel_info
        result['success'] = True
        
        if channel_info:
            safe_print(f"[{index:3}/{total}] ✅ {channel_info['name']} ({channel_info['subscribers']})")
        else:
            safe_print(f"[{index:3}/{total}] ✅ {channel_id}")
            
    except Exception as e:
        result['error'] = str(e)
        safe_print(f"[{index:3}/{total}] ❌ 오류: {channel_input}")
    
    return result

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

def save_channels_to_csv(channels_data, append_mode=True):
    """채널 데이터를 CSV에 저장"""
    fieldnames = ['username', 'channel_id', 'message']
    
    # 기존 데이터 읽기
    existing_rows = []
    if append_mode and CSV_PATH.exists():
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)
        except:
            pass
    
    # 새로운 데이터 추가
    for data in channels_data:
        if data['success'] and data['channel_id']:
            username = data['info']['name'] if data['info'] else f"채널_{data['channel_id'][:8]}"
            new_row = {
                'username': username,
                'channel_id': data['channel_id'],
                'message': '좋은 영상 감사합니다'
            }
            existing_rows.append(new_row)
    
    # CSV 파일에 저장
    try:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)
        return True
    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")
        return False

def create_template_file():
    """템플릿 파일 생성"""
    template_content = """# YouTube 채널 대량 등록 템플릿
# 한 줄에 하나씩 채널을 입력하세요
# 
# 입력 가능한 형식:
# @channelname              (핸들)
# channelname               (핸들, @ 없이)
# https://www.youtube.com/@channelname
# https://www.youtube.com/channel/UCxxxxx
#
# 예시:
@youtube
@kbs
@sbs
https://www.youtube.com/@mbc
TeamYouTube
https://www.youtube.com/channel/UCBR8-60-B28hp2BmDPdntcQ

# 아래에 등록하고 싶은 채널들을 입력하세요:
"""
    
    template_path = Path("channels_template.txt")
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"📝 템플릿 파일이 생성되었습니다: {template_path}")
        print("   파일을 편집한 후 다시 실행하세요!")
        return True
    except Exception as e:
        print(f"❌ 템플릿 파일 생성 실패: {e}")
        return False

def read_channels_from_file(file_path):
    """파일에서 채널 목록 읽기"""
    channels = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 주석과 빈 줄 제외
                if line and not line.startswith('#'):
                    channels.append(line)
        return channels
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        return []

def preview_channels(channels, max_show=10):
    """채널 목록 미리보기"""
    print(f"\n📋 발견된 채널 ({len(channels)}개):")
    print("-" * 50)
    
    for i, channel in enumerate(channels[:max_show], 1):
        print(f"  {i:2}. {channel}")
    
    if len(channels) > max_show:
        print(f"  ... (추가 {len(channels) - max_show}개 채널)")
    
    print("-" * 50)
    return True

def bulk_process_channels(channels, max_workers=10):
    """채널들을 병렬로 처리"""
    print(f"\n🚀 {len(channels)}개 채널을 {max_workers}개 스레드로 동시 처리 시작...")
    print("=" * 60)
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 모든 작업 제출
        futures = {
            executor.submit(process_single_channel, channel, i+1, len(channels)): i 
            for i, channel in enumerate(channels)
        }
        
        # 결과 수집
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ 스레드 오류: {e}")
    
    end_time = time.time()
    
    # 결과 정렬 (인덱스 순서대로)
    results.sort(key=lambda x: x['index'])
    
    print("\n" + "=" * 60)
    print(f"⏱️  처리 완료! 소요 시간: {end_time - start_time:.2f}초")
    
    return results

def show_summary(results, existing_channels):
    """처리 결과 요약 출력"""
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    duplicates = [r for r in successful if r['channel_id'] in existing_channels]
    new_channels = [r for r in successful if r['channel_id'] not in existing_channels]
    
    print(f"\n📊 처리 결과 요약:")
    print("=" * 40)
    print(f"✅ 성공:        {len(successful):3}개")
    print(f"❌ 실패:        {len(failed):3}개")
    print(f"🔄 중복:        {len(duplicates):3}개")
    print(f"🆕 새로 추가:   {len(new_channels):3}개")
    print("=" * 40)
    
    if failed:
        print(f"\n❌ 실패한 채널들:")
        for result in failed:
            error = result['error'] or '알 수 없는 오류'
            print(f"   • {result['input']} - {error}")
    
    if duplicates:
        print(f"\n🔄 이미 등록된 채널들:")
        for result in duplicates:
            existing_name = existing_channels[result['channel_id']]
            print(f"   • {result['input']} → {existing_name}")
    
    if new_channels:
        print(f"\n🆕 새로 추가될 채널들:")
        for result in new_channels:
            name = result['info']['name'] if result['info'] else f"채널_{result['channel_id'][:8]}"
            subs = result['info']['subscribers'] if result['info'] else '정보 없음'
            print(f"   • {name} ({subs})")
    
    return new_channels

def interactive_bulk_setup():
    """대화형 대량 설정"""
    print("🎯 대량 채널 설정 모드")
    print()
    
    # 템플릿 파일 확인
    template_path = Path("channels_template.txt")
    if not template_path.exists():
        print("📝 먼저 템플릿 파일을 생성하겠습니다...")
        if create_template_file():
            print("\n✏️  다음 단계:")
            print(f"   1. {template_path} 파일을 편집하세요")
            print("   2. 원하는 채널들을 입력하세요")
            print("   3. 이 프로그램을 다시 실행하세요")
        return
    
    # 템플릿 파일에서 채널 읽기
    channels = read_channels_from_file(template_path)
    if not channels:
        print("❌ 채널 목록이 비어있습니다!")
        print(f"   {template_path} 파일을 편집하고 채널을 추가하세요.")
        return
    
    # 미리보기
    preview_channels(channels)
    
    # 사용자 확인
    response = input(f"\n💫 {len(channels)}개 채널을 처리하시겠습니까? (y/n): ").strip().lower()
    if response not in ['y', 'yes', '예', 'ㅇ']:
        print("❌ 처리를 취소했습니다.")
        return
    
    # 기존 채널 확인
    existing_channels = read_existing_channels()
    print(f"\n📋 현재 등록된 채널: {len(existing_channels)}개")
    
    # 병렬 처리
    results = bulk_process_channels(channels)
    
    # 결과 요약
    new_channels = show_summary(results, existing_channels)
    
    if new_channels:
        save_confirm = input(f"\n💾 {len(new_channels)}개의 새 채널을 저장하시겠습니까? (y/n): ").strip().lower()
        if save_confirm in ['y', 'yes', '예', 'ㅇ']:
            if save_channels_to_csv(new_channels):
                print(f"🎉 {len(new_channels)}개 채널이 성공적으로 저장되었습니다!")
                
                # 최종 통계
                total_channels = len(existing_channels) + len(new_channels)
                print(f"📊 전체 등록 채널: {total_channels}개")
            else:
                print("❌ 저장에 실패했습니다.")
        else:
            print("❌ 저장을 취소했습니다.")
    else:
        print("💡 저장할 새 채널이 없습니다.")

def quick_mode(file_path):
    """빠른 모드 - 파일 지정해서 바로 처리"""
    if not Path(file_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    channels = read_channels_from_file(file_path)
    if not channels:
        print("❌ 유효한 채널이 없습니다!")
        return
    
    print(f"⚡ 빠른 모드: {len(channels)}개 채널 처리")
    
    existing_channels = read_existing_channels()
    results = bulk_process_channels(channels)
    new_channels = show_summary(results, existing_channels)
    
    if new_channels:
        if save_channels_to_csv(new_channels):
            print(f"🎉 {len(new_channels)}개 채널이 자동 저장되었습니다!")
        else:
            print("❌ 저장에 실패했습니다.")

def print_help():
    """도움말 출력"""
    help_text = """
🚀 대량 채널 설정 도구 사용법

사용 방법:
    python bulk_channel_setup.py                   # 대화형 모드 (권장)
    python bulk_channel_setup.py -quick 파일명     # 빠른 모드
    python bulk_channel_setup.py -template         # 템플릿 파일만 생성
    python bulk_channel_setup.py -help             # 도움말

대화형 모드 (권장):
    1. 템플릿 파일 자동 생성 (channels_template.txt)
    2. 파일 편집으로 채널 목록 입력
    3. 미리보기 및 확인 후 일괄 처리
    4. 결과 확인 및 저장

빠른 모드:
    - 기존 파일을 바로 처리
    - 확인 없이 자동 저장
    - 배치 처리에 적합

특징:
    ⚡ 동시 처리: 10개 스레드로 빠른 처리
    🔍 스마트 감지: 다양한 URL 형식 지원
    🔄 중복 방지: 기존 채널과 자동 비교
    📊 상세 보고: 성공/실패/중복 통계
    💾 안전 저장: 기존 데이터 보존

입력 예시 파일:
    @youtube
    @kbs  
    sbs
    https://www.youtube.com/@mbc
    https://www.youtube.com/channel/UCxxxxx
    """
    print(help_text)

def main():
    print_banner()
    
    args = sys.argv[1:]
    
    if not args:
        # 대화형 모드
        interactive_bulk_setup()
    elif args[0] == '-help' or args[0] == '--help':
        print_help()
    elif args[0] == '-template':
        create_template_file()
    elif args[0] == '-quick' and len(args) > 1:
        quick_mode(args[1])
    else:
        print("❌ 잘못된 옵션입니다. -help로 도움말을 확인하세요.")

if __name__ == "__main__":
    main() 