# 🚀 SuperThank 자동화 프로그램

YouTube 채널을 모니터링하여 새로운 영상이 업로드되면 자동으로 슈퍼땡스를 송금하는 완전 자동화 프로그램입니다.

## ✨ 주요 기능

- 📺 **100개+ 채널 동시 모니터링** - 1분마다 모든 채널 확인
- 💸 **자동 슈퍼땡스 송금** - 새 영상 발견 시 즉시 송금
- 🔄 **중복 송금 방지** - 이미 송금한 영상은 자동 건너뛰기
- 📸 **에러 시 자동 캡처** - 문제 발생 시 화면 자동 캡처
- ⚡ **적응형 타임아웃** - 네트워크 상황에 따른 자동 조절
- 🔥 **대량 채널 설정** - 몇백개 채널도 한번에 설정 가능

## 🔧 빠른 시작 (1분 설치)

### 자동 설치 (권장)

```bash
git clone [저장소 주소]
cd superThankAutomation
chmod +x setup.sh
./setup.sh
```

**설치 과정**: Homebrew → Chrome → Python → 가상환경 → 의존성 → 완료! 🎉

## ⚠️ 필수 사전 작업

### 1. macOS 권한 설정

**시스템 환경설정 > 보안 및 개인정보보호**에서:

- ✅ **접근성**: 터미널 앱 허용
- ✅ **화면 기록**: 터미널 앱 허용  
- ✅ **자동화**: 터미널이 다른 앱 제어 허용

### 2. YouTube 사전 설정

**🚨 중요: 매크로 실행 전 반드시 수행하세요!**

1. **Chrome에서 YouTube 로그인** (Chrome 브라우저 필수!)
2. **수동으로 슈퍼땡스 1회 이상 송금**
   - 결제 정보 저장 확인
   - 송금 프로세스 익숙해지기
3. **정상 송금 확인**

## 🎯 사용법

### 1단계: 채널 추가

#### 🔥 대량 등록 (권장) - 한번에 몇십개/몇백개

```bash
source venv/bin/activate
python bulk_channel_setup.py
```

**사용 과정**:
1. 📝 템플릿 파일 자동 생성 (`channels_template.txt`)
2. ✏️ 텍스트 에디터로 채널 목록 입력
3. ⚡ 10개 스레드로 동시 처리 (초고속!)
4. 📊 결과 요약 확인
5. 💾 최종 저장

**예시 화면**:
```
🚀 대량 채널 설정 도구
============================================================

📋 발견된 채널 (50개):
   1. @kbs
   2. @sbs
   3. @mbc
   ...

💫 50개 채널을 처리하시겠습니까? (y/n): y

🚀 50개 채널을 10개 스레드로 동시 처리 시작...
[  1/50] ✅ KBS NEWS (350만명)
[  2/50] ✅ SBS (280만명)
...

⏱️  처리 완료! 소요 시간: 8.32초

📊 처리 결과 요약:
✅ 성공: 45개  ❌ 실패: 2개  🔄 중복: 3개  🆕 새로 추가: 42개

🎉 42개 채널이 성공적으로 저장되었습니다!
```

#### 개별 등록 - 1-2개씩 추가

```bash
python channel_finder.py
```

**입력 가능한 형식**:
- `@kbs` → KBS 공식 채널
- `sbs` → SBS 공식 채널  
- `https://www.youtube.com/@mbc` → 전체 URL
- `https://www.youtube.com/channel/UCxxxxx` → 채널 ID

#### 명령어 모음

```bash
# 현재 등록된 채널 목록 보기
python channel_finder.py -list

# 빠른 모드 (확인 없이 자동 저장)
python bulk_channel_setup.py -quick my_channels.txt

# 템플릿 파일만 생성
python bulk_channel_setup.py -template
```

### 2단계: 프로그램 실행

```bash
./run.sh
```

## 📊 프로그램 작동 방식

### 모니터링 사이클 (1분)
```
├── 50초: 채널 확인 (10개씩 배치 처리)
└── 10초: 슈퍼땡스 송금 처리
```

### 성능 최적화
- **적응형 타임아웃**: 실패 시 10초→15초→20초→25초→30초
- **배치 분산 처리**: 서버 부하 방지
- **스레드 안전성**: Lock으로 데이터 무결성 보장
- **중복 송금 방지**: JSON 파일로 기록 관리

### 안전 장치
- **자동 에러 캡처**: `captures/error_YYYYMMDD_HHMMSS.png`
- **실시간 로그**: `youtube_listener.log`
- **백업 시스템**: 모든 데이터 자동 보존

## 🔍 로그 & 모니터링

```bash
# 실시간 로그 확인
tail -f youtube_listener.log

# 채널 목록 확인
python channel_finder.py -list

# 에러 캡처 확인
ls -la captures/
```

**정상 로그 예시**:
```
2024-01-01 12:00:01 - 배치 1/11 처리 중 (10개 채널)
2024-01-01 12:00:15 - 채널 UCxxxxx에서 새 영상 발견: "영상제목"
2024-01-01 12:00:30 - 슈퍼땡스 송금 완료: UCxxxxx
```

## 🛠️ 문제 해결

### 설치 문제
```bash
# 권한 오류
chmod +x setup.sh run.sh

# 가상환경 재생성
rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

### 채널 찾기 실패
```bash
# 다양한 형식으로 재시도
python channel_finder.py

# 대량 처리에서 실패한 채널 개별 처리
python bulk_channel_setup.py -template
# 실패한 채널만 템플릿에 추가 후 재실행
```

### 매크로 오류
1. **YouTube 로그인 확인** (Chrome에서)
2. **수동 슈퍼땡스 1회 송금** 필수
3. **macOS 권한 재설정**
4. **에러 캡처 확인** (`captures/` 폴더)

## ⚙️ 고급 설정

### 테스트 모드
```python
# youtubeListener_poll copy.py 파일에서
isTest = 3      # 테스트용 송금 횟수
Ticket = 100    # 총 송금 가능 횟수
```

### 성능 조절
```python
# 모니터링 간격 (권장하지 않음)
check_duration = 50  # 채널 확인 시간

# 동시 처리 스레드 수
max_workers = 10     # 채널 찾기 도구에서
```

## 📈 성능 벤치마크

### 채널 설정 속도
| 채널 수 | 소요 시간 | 비고 |
|---------|-----------|------|
| 10개 | 2-3초 | 개별 처리 |
| 50개 | 8-12초 | 대량 처리 |
| 100개 | 15-25초 | 최적화된 병렬 처리 |

### 모니터링 성능
- **100개 채널**: 1분 사이클 완료
- **200개 채널**: 1.2분 사이클
- **실시간 송금**: 새 영상 발견 후 10초 내

## 📁 파일 구조

```
superThankAutomation/
├── setup.sh                      # 자동 설치 스크립트
├── run.sh                         # 실행 스크립트
├── bulk_channel_setup.py          # 🔥 대량 채널 설정 (권장)
├── channel_finder.py              # 개별 채널 찾기
├── youtubeListener_poll copy.py   # 메인 프로그램
├── sendSuperThanks.py            # 송금 처리 모듈
├── channel_list.csv              # 모니터링 채널 목록
├── completed_videos.json         # 송금 완료 기록
├── requirements.txt              # Python 의존성
├── captures/                     # 에러 시 캡처 이미지
├── img/                          # 매크로용 이미지
└── logs/                         # 로그 파일
```

## 🚀 실전 사용 예시

### 시나리오 1: 신규 사용자 (50개 채널 설정)

```bash
# 1. 설치
./setup.sh

# 2. 대량 채널 설정
python bulk_channel_setup.py
# → channels_template.txt 파일이 생성됨

# 3. 텍스트 에디터로 채널 목록 입력
# @kbs
# @sbs
# @mbc
# ... (50개 채널)

# 4. 재실행하여 일괄 처리
python bulk_channel_setup.py
# → 8-12초만에 50개 채널 자동 등록 완료!

# 5. 프로그램 시작
./run.sh
```

### 시나리오 2: 기존 사용자 (추가 채널 등록)

```bash
# 빠른 추가 (개별)
python channel_finder.py
# → @newchannel 입력

# 빠른 추가 (여러개)
echo "@newchannel1
@newchannel2
@newchannel3" > new_channels.txt
python bulk_channel_setup.py -quick new_channels.txt
```

### 시나리오 3: 대규모 관리 (200개+ 채널)

```bash
# 100개씩 나누어 처리
python bulk_channel_setup.py  # 첫 100개
python bulk_channel_setup.py  # 나머지 100개

# 최종 확인
python channel_finder.py -list | wc -l
# → 총 채널 수 확인
```

## 🎯 빠른 참조

### 필수 명령어
```bash
./setup.sh                          # 설치
python bulk_channel_setup.py        # 대량 채널 설정 ⭐
./run.sh                             # 프로그램 실행
```

### 관리 명령어  
```bash
python channel_finder.py -list      # 채널 목록
python bulk_channel_setup.py -help  # 도움말
tail -f youtube_listener.log        # 실시간 로그
```

### 중요 파일
- **채널 목록**: `channel_list.csv`
- **송금 기록**: `completed_videos.json`  
- **에러 캡처**: `captures/`
- **실시간 로그**: `youtube_listener.log`

## 💡 Pro Tips

### 효율적인 채널 관리
1. **대량 설정을 우선 활용** - 10배 빠름
2. **실패한 채널은 다른 형식으로 재시도**
3. **정기적으로 로그 확인** - 문제 조기 발견
4. **백업 습관** - `cp channel_list.csv backup/`

### 성능 최적화
1. **안정적인 인터넷 연결** 필수
2. **Chrome 브라우저 최적화** - 불필요한 탭 정리
3. **시스템 리소스 확보** - 메모리 4GB+ 권장

### 안전한 사용
1. **테스트 모드로 먼저 확인**
2. **수동 송금 1회는 필수**
3. **권한 설정 정확히**
4. **에러 캡처 주기적 확인**

## 📞 지원

문제 발생 시 확인 순서:
1. **로그 파일**: `youtube_listener.log`
2. **에러 캡처**: `captures/` 폴더
3. **권한 설정**: macOS 시스템 환경설정
4. **수동 테스트**: 직접 슈퍼땡스 송금 시도

## ⚖️ 면책 조항

이 프로그램은 교육 목적으로 제작되었습니다. 사용으로 인한 모든 결과는 사용자의 책임입니다.

---

**🎉 행복한 자동화 라이프 되세요!** 🚀

### 🔗 Quick Links
- [설치](#-빠른-시작-1분-설치) | [사용법](#-사용법) | [문제해결](#-문제-해결) | [성능](#-성능-벤치마크) 