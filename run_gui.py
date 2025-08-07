#!/usr/bin/env python3
"""
YouTube Playlist Downloader GUI 실행 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from youtube_downloader_gui import main
    print("🚀 YouTube Playlist Downloader GUI를 시작합니다...")
    main()
except ImportError as e:
    print(f"❌ 오류: {e}")
    print("필요한 라이브러리가 설치되어 있는지 확인해주세요.")
    print("설치 명령어: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    print("콘솔 버전을 사용해보세요: python youtube_playlist_downloader.py")
