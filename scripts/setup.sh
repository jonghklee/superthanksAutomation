#!/bin/bash

echo "🚀 SuperThank 자동화 프로그램 설치를 시작합니다..."
echo "=================================================="

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 진행 단계 함수
print_step() {
    echo -e "${BLUE}[단계 $1/7]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1단계: 시스템 체크
print_step 1 "시스템 환경 확인 중..."
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "이 스크립트는 macOS 전용입니다."
    exit 1
fi
print_success "macOS 환경 확인 완료"

# 2단계: Homebrew 설치
print_step 2 "Homebrew 패키지 매니저 확인 중..."
if ! command -v brew &> /dev/null; then
    echo "📦 Homebrew가 설치되어 있지 않습니다. 설치를 진행합니다..."
    echo "관리자 비밀번호를 입력해주세요:"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # PATH 설정 확인
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    print_success "Homebrew 설치 완료"
else
    print_success "Homebrew가 이미 설치되어 있습니다"
fi

# 3단계: Google Chrome 설치
print_step 3 "Google Chrome 브라우저 확인 중..."
if [[ ! -d "/Applications/Google Chrome.app" ]]; then
    echo "🌐 Google Chrome이 설치되어 있지 않습니다. 설치를 진행합니다..."
    brew install --cask google-chrome
    print_success "Google Chrome 설치 완료"
else
    print_success "Google Chrome이 이미 설치되어 있습니다"
fi

# 4단계: Python 설치
print_step 4 "Python 환경 설정 중..."
if ! command -v python3 &> /dev/null; then
    echo "🐍 Python3를 설치합니다..."
    brew install python
    print_success "Python3 설치 완료"
else
    print_success "Python3가 이미 설치되어 있습니다"
fi

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# 5단계: 가상환경 및 의존성 설치
print_step 5 "프로젝트 의존성 설치 중..."
echo "📁 가상환경을 생성합니다..."
python3 -m venv venv

echo "🔧 가상환경을 활성화합니다..."
source venv/bin/activate

echo "📦 필요한 라이브러리를 설치합니다..."
if [[ -f "config/requirements.txt" ]]; then
    pip install -r config/requirements.txt
    print_success "의존성 설치 완료"
else
    print_error "config/requirements.txt 파일을 찾을 수 없습니다."
    exit 1
fi

# 6단계: 설정 파일 확인
print_step 6 "설정 파일 확인 중..."

# 필수 디렉토리 확인
if [[ ! -d "assets/img" ]]; then
    print_error "assets/img/ 폴더가 없습니다. 매크로 실행에 필요한 이미지 파일들이 누락되었습니다."
    echo "   이 폴더는 프로그램 실행에 필수입니다."
    exit 1
fi

if [[ ! -d "captures" ]]; then
    mkdir -p captures
    print_success "captures/ 폴더 생성 완료"
fi

if [[ ! -f "config/channel_list.csv" ]]; then
    print_warning "config/channel_list.csv 파일이 없습니다."
    echo "📝 기본 설정 파일을 생성합니다..."
    mkdir -p config
    cat > config/channel_list.csv << 'EOF'
username,channel_id,message
예시채널,UCxxxxxxxxxxxxxxxxxxxxxx,좋은 영상 감사합니다
EOF
    echo "✏️  config/channel_list.csv 파일을 편집하여 모니터링할 채널을 추가하세요."
fi

# 실행 스크립트 생성
cat > run.sh << 'EOF'
#!/bin/bash
echo "🚀 SuperThank 자동화 프로그램을 시작합니다..."
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF

chmod +x run.sh
print_success "실행 스크립트 생성 완료"

# 7단계: 권한 설정 안내
print_step 7 "권한 설정 안내"
echo ""
echo "=================================================="
echo -e "${PURPLE}🔐 macOS 권한 설정이 필요합니다${NC}"
echo "=================================================="
echo ""
echo "다음 권한들을 설정해주세요:"
echo ""
echo -e "${YELLOW}1. 접근성 권한:${NC}"
echo "   • 시스템 환경설정 > 보안 및 개인정보보호 > 접근성"
echo "   • 터미널(또는 iTerm) 앱 허용"
echo ""
echo -e "${YELLOW}2. 화면 기록 권한:${NC}"
echo "   • 시스템 환경설정 > 보안 및 개인정보보호 > 화면 기록"  
echo "   • 터미널(또는 iTerm) 앱 허용"
echo ""
echo -e "${YELLOW}3. 자동화 권한:${NC}"
echo "   • 시스템 환경설정 > 보안 및 개인정보보호 > 자동화"
echo "   • 터미널이 다른 앱을 제어할 수 있도록 허용"
echo ""

echo "=================================================="
echo -e "${RED}⚠️  중요한 사전 작업 ⚠️${NC}"
echo "=================================================="
echo ""
echo -e "${RED}매크로를 실행하기 전에 반드시 다음을 수행하세요:${NC}"
echo ""
echo -e "${YELLOW}1. YouTube에 로그인${NC}"
echo "   • Chrome 브라우저에서 YouTube에 로그인"
echo "   • 슈퍼땡스 송금이 가능한 계정인지 확인"
echo ""
echo -e "${YELLOW}2. 수동으로 슈퍼땡스 1회 송금${NC}"
echo "   • 아무 영상에서 수동으로 슈퍼땡스를 1회 이상 송금"
echo "   • 결제 정보가 저장되어 있는지 확인"
echo "   • 송금 프로세스에 익숙해지기"
echo ""
echo -e "${RED}❌ 위 작업을 하지 않으면 매크로가 정상 작동하지 않습니다!${NC}"
echo ""

echo "=================================================="
echo -e "${GREEN}🎉 설치가 완료되었습니다!${NC}"
echo "=================================================="
echo ""
echo "📋 다음 단계:"
echo "1. 권한 설정 완료"
echo "2. YouTube 로그인 및 수동 슈퍼땡스 1회 송금"
echo -e "3. ${YELLOW}채널 추가${NC}:"
echo -e "   ${BLUE}python src/bulk_channel_setup.py${NC}     # 🔥 대량 채널 설정 (권장)"
echo -e "   ${BLUE}python src/channel_finder.py${NC}         # 🔍 개별 채널 찾기"
echo "   또는 config/channel_list.csv 파일 직접 편집"
echo "4. ./run.sh 실행"
echo ""
echo -e "${BLUE}🔥 대량 설정: ${GREEN}python src/bulk_channel_setup.py${NC}"
echo -e "${BLUE}🔍 개별 찾기: ${GREEN}python src/channel_finder.py${NC}"
echo -e "${BLUE}🚀 프로그램 실행: ${GREEN}./run.sh${NC}"
echo ""
echo "🔧 수동 설정: nano config/channel_list.csv"
echo "📖 도움말: cat README.md"
echo ""
print_success "모든 설치가 완료되었습니다!" 