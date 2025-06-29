import sys
import csv
import re
import subprocess
import requests
from bs4 import BeautifulSoup
from pathlib import Path

CSV_PATH = Path("./config/channel_list.csv")  # username,channel_id
PUBSUB_URL = "https://pubsubhubbub.appspot.com/subscribe"
CALLBACK_URL = "https://youtubelistener.ngrok.app/notifications"  # 수정 필요
LEASE_SECONDS = 432000

FieldName = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def extract_channel_id_from_handle(handle_url):
    try:
        response = requests.get(handle_url, headers=HEADERS)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        canonical = soup.find("link", rel="canonical")
        if canonical and "channel/" in canonical["href"]:
            return canonical["href"].split("channel/")[-1]

        match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', response.text)
        if match:
            return match.group(1)
        return None
    except:
        return None

def read_csv():
    global FieldName
    data = {}
    if not CSV_PATH.exists():
        return data
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        FieldName = reader.fieldnames

        for row in reader:
            new_row = row.copy()
            del new_row['username']
            data[row['username'].lstrip('@')] = new_row
    return data

def write_csv(data):
    temp_path = CSV_PATH.with_suffix('.tmp')
    try:
        with open(temp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FieldName)
            writer.writeheader()

            for username in data.keys():
                writer.writerow(dict(zip(FieldName, [username] + list(data[username].values()))))
        
        # 임시 파일이 성공적으로 작성된 경우에만 원본 파일을 대체
        temp_path.replace(CSV_PATH)
    except Exception as e:
        print(f"CSV 파일 작성 중 오류 발생: {e}")
        if temp_path.exists():
            temp_path.unlink()  # 임시 파일 삭제
        raise

def get_feed_url(channel_id):
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

def send_curl(channel_id):
    feed_url = get_feed_url(channel_id)
    cmd = [
        "curl", "-X", "POST", PUBSUB_URL,
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-d", f"hub.mode=subscribe",
        "-d", f"hub.topic={feed_url}",
        "-d", f"hub.callback={CALLBACK_URL}",
        "-d", f"hub.lease_seconds={LEASE_SECONDS}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"(구독 요청 성공) {result.stdout}")
    else:
        print(f"구독 요청 실패) {result.stderr}")

def print_help():
    help_text = """
    이름
           ytsub.py - YouTube 채널 ID 관리 및 구독 요청 자동화

    개요
           ytsub.py [username] [-옵션]

    설명
           이 프로그램은 CSV 파일에서 YouTube 채널의 ID를 읽고, 구독 요청을 자동으로 보내는 기능을 제공합니다. 
           옵션이 지정되지 않으면, 주어진 사용자의 피드 URL을 출력합니다.

           -getcsv 
                  사용 예시 : ytsub.py -getcsv
                  이것만 사용하시면 됩니다.
                  CSV 파일에서 채널 ID가 없는 사용자에 대해 YouTube 핸들에서 채널 ID를 추출하여 CSV 파일을 갱신합니다.


        --------------------------------------------------------------------------------------------

           -sendcsv
                  사용 예시 : ytsub.py -getcsv
                  CSV 파일에 있는 모든 채널 ID에 대해 구독 요청을 보냅니다.

           -emptycsv
                  사용 예시 : ytsub.py -getcsv
                  CSV 파일에서 채널 ID가 없는 사용자에 대해 채널 ID를 추출하고, 구독 요청을 보낸 후 CSV 파일을 갱신합니다.

           -curl
                  사용 예시 : ytsub.py @userName -curl
                  특정 사용자의 채널에 대해 구독 요청을 보냅니다.

           [옵션 없음]
                  사용 예시 : ytsub.py @userName
                  특정 사용자의 채널의 채널 아이디어를 가져옵니다.

           -help
                  이 도움말을 출력합니다.
    """
    print(help_text)

def main():
    args = sys.argv[1:]

    if not args:
        print_help()
        return

    csv_data = read_csv()

    if args[0].startswith('-'):  # 옵션만 있는 경우
        option = args[0]

        if option == '-getcsv':
            updated = False
            for username in csv_data.keys():
                channel_id = csv_data[username][FieldName[1]]
                if not channel_id:
                    handle_url = f"https://www.youtube.com/@{username}"
                    new_id = extract_channel_id_from_handle(handle_url)
                    if new_id:
                        csv_data[username][FieldName[1]] = new_id
                        print(f"{username}: 채널 ID 갱신됨 → {new_id}")
                        updated = True
            if updated:
                write_csv(csv_data)
            return

        if option == '-sendcsv':
            for username in csv_data.keys():
                channel_id = csv_data[username][FieldName[1]]
                if channel_id:
                    print(f"{username} → 구독 요청 중...")
                    send_curl(channel_id)
            return

        if option == '-emptycsv':
            updated = False
            for username in csv_data.keys():
                channel_id = csv_data[username][FieldName[1]]
                if not channel_id:
                    handle_url = f"https://www.youtube.com/@{username}"
                    new_id = extract_channel_id_from_handle(handle_url)
                    if new_id:
                        csv_data[username][FieldName[1]] = new_id
                        print(f"{username}: 채널 ID 갱신됨 → {new_id}")
                        send_curl(new_id)
                        updated = True
            if updated:
                write_csv(csv_data)
            return

        if option == '-help':
            print_help()
            return

        print("지원되지 않는 옵션입니다.")
        return

    if args[0].startswith('@'):  # 옵션만 있는 경우
        username = args[0].lstrip('@')
        option = args[1] if len(args) > 1 else None

        channel_id = csv_data.get(username, '')
        if not channel_id:
            print(f"{username}: CSV에 ID 없음, 핸들에서 추출 시도...")
            handle_url = f"https://www.youtube.com/@{username}"
            channel_id = extract_channel_id_from_handle(handle_url)
            if channel_id:
                csv_data[username] = channel_id
                write_csv(csv_data)
            else:
                print(f"{username}: 채널 ID 추출 실패")
                return

        feed_url = get_feed_url(channel_id)

        if option == '-curl':
            send_curl(channel_id)
        else:
            print(f"{username}의 채널 ID: {channel_id}")
    else:
        print("잘못된 명령어입니다.")
        return

if __name__ == "__main__":
    main()
