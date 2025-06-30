#!/bin/bash
echo "🚀 SuperThank 자동화 프로그램을 시작합니다..."
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
