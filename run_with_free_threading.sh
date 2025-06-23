#!/bin/bash

echo "🚀 Python Free Threading 활성화하여 YouTube 리스너 실행"
echo "======================================================"

# Python 3.13+ Free Threading 확인
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
echo "🐍 Python 버전: $python_version"

# Free Threading 빌드 확인
if python3 -c "import sys; print('Free Threading 지원:' if hasattr(sys, 'flags') and hasattr(sys.flags, 'disable_gil') else 'Free Threading 미지원')" 2>/dev/null; then
    echo "✅ Free Threading 지원 확인됨"
else
    echo "⚠️ Free Threading이 지원되지 않는 Python 버전입니다"
    echo "💡 Python 3.13t (free threading build)를 설치해주세요"
    echo "💡 설치 방법: https://docs.python.org/3.13/howto/free-threading.html"
fi

echo ""
echo "📊 시스템 정보:"
echo "   - CPU 코어 수: $(python3 -c "import multiprocessing; print(multiprocessing.cpu_count())")"
echo "   - 최대 워커 수 (예상): $(python3 -c "import multiprocessing; print(min(50, multiprocessing.cpu_count() * 4))")"

echo ""
echo "🔧 가상환경 활성화 중..."
source venv/bin/activate

echo "🎯 프로그램 시작..."
echo "======================================================"

# Free Threading 환경변수 설정
export PYTHON_GIL=0

# 프로그램 실행
python3 "youtubeListener_poll copy.py" 