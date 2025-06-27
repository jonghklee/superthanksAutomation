#!/bin/bash

# SuperThank 자동화 프로그램 실행 스크립트
# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "🚀 SuperThank 자동화 프로그램 시작"
echo "====================================="

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 확인
if [[ ! -d "venv" ]]; then
    print_error "가상환경이 없습니다. setup.sh를 먼저 실행하세요."
    exit 1
fi

print_info "가상환경 활성화 중..."
source venv/bin/activate

# 필수 파일 확인
if [[ ! -f "channel_list.csv" ]]; then
    print_warning "channel_list.csv 파일이 없습니다."
    echo "기본 파일을 생성합니다..."
    cat > channel_list.csv << EOF
username,channel_id,message
샘플채널,UCu0elhwDIhuEIEwJa2xs3fw,좋은 영상 감사합니다
EOF
fi

if [[ ! -f "completed_videos.json" ]]; then
    print_info "completed_videos.json 파일 생성 중..."
    echo "{}" > completed_videos.json
fi

# 권한 확인 안내
echo ""
print_warning "프로그램 실행 전 확인사항:"
echo "   📱 Chrome에서 YouTube 로그인 완료"
echo "   💸 수동 슈퍼땡스 1회 이상 송금 완료"
echo "   ⚙️  macOS 접근성/화면기록 권한 허용"
echo ""

# 프로그램 실행
print_info "프로그램 실행 중... (Ctrl+C로 중단)"
python "youtubeListener_poll copy.py" 