# YouTube Playlist Downloader

유튜브 플레이리스트를 MP4 형식으로 다운로드하는 Python 스크립트입니다.

## 🚀 주요 기능

### 📊 실시간 진행률 표시

- **전체 개수 표시**: 다운로드할 총 비디오 개수
- **현재 진행 상황**: 완료된 비디오 수와 실패한 비디오 수
- **예상 완료 시간**: 실시간으로 계산되는 예상 완료 시간
- **시각적 진행률 바**: tqdm을 사용한 직관적인 진행률 표시

### 🎬 화질 선택 옵션

- **최고 화질**: bestvideo+bestaudio 조합
- **1080p, 720p, 480p, 360p, 240p, 144p**: 특정 해상도 선택
- **최적 화질**: best 옵션 (자동 선택)
- **자동 선택**: 시스템이 최적의 화질을 자동으로 선택

### ⚡ 다운로드 모드

1. **순차 다운로드**: 안정적이지만 느림
2. **병렬 다운로드**: 빠르지만 일부 실패 가능
3. **🔥 MAX 모드**: 모든 시스템 자원을 활용한 최대 성능

## 📦 설치

### 🍎 macOS 완전 설치 가이드

#### 1. Homebrew 설치 (없는 경우)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. 필수 시스템 도구 설치

```bash
# 시스템 패키지 업데이트
brew update

# Python 3.13 설치 (최신 버전)
brew install python@3.13

# FFmpeg 설치 (비디오/오디오 병합 필수)
brew install ffmpeg

# tkinter 설치 (GUI에 필요)
brew install python-tk

# 추가 유틸리티 (선택사항)
brew install git  # Git이 없는 경우
brew install wget  # wget이 필요한 경우
```

#### 3. PATH 설정 확인

```bash
# Python 경로 확인
which python3

# FFmpeg 경로 확인
which ffmpeg

# PATH에 Homebrew 경로 추가 (필요한 경우)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### 4. 프로젝트 설정

```bash
# 프로젝트 폴더 생성 및 이동
mkdir youtube_downloader_project
cd youtube_downloader_project

# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# Python 라이브러리 설치
pip install -r requirements.txt
```

### 🐧 Linux 설치 가이드

#### Ubuntu/Debian

```bash
# 시스템 패키지 업데이트
sudo apt update

# Python 및 필수 도구 설치
sudo apt install python3 python3-pip python3-venv ffmpeg python3-tk

# 프로젝트 설정
mkdir youtube_downloader_project
cd youtube_downloader_project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Fedora/CentOS

```bash
# Python 및 필수 도구 설치
sudo dnf install python3 python3-pip ffmpeg python3-tkinter

# 프로젝트 설정
mkdir youtube_downloader_project
cd youtube_downloader_project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 🪟 Windows 설치 가이드

#### 1. Python 설치

- [python.org](https://www.python.org/downloads/)에서 Python 3.13 다운로드
- 설치 시 "Add Python to PATH" 옵션 체크

#### 2. FFmpeg 설치

- [ffmpeg.org](https://ffmpeg.org/download.html)에서 Windows 빌드 다운로드
- 압축 해제 후 `bin` 폴더를 시스템 PATH에 추가

#### 3. 프로젝트 설정

```cmd
mkdir youtube_downloader_project
cd youtube_downloader_project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 🔧 빠른 설치 (macOS)

```bash
# Homebrew 업데이트 및 모든 의존성 한 번에 설치
brew update && brew install python@3.13 ffmpeg python-tk git

# PATH 설정 (Apple Silicon Mac의 경우)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 프로젝트 클론 및 설정
git clone <repository-url>
cd youtube_downloader_project
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### ✅ 설치 확인

```bash
# Python 버전 확인
python3 --version

# FFmpeg 설치 확인
ffmpeg -version

# tkinter 설치 확인
python3 -c "import tkinter; print('tkinter 설치 완료')"

# yt-dlp 설치 확인
python3 -c "import yt_dlp; print('yt-dlp 설치 완료')"

# psutil 설치 확인
python3 -c "import psutil; print('psutil 설치 완료')"
```

### 필요한 라이브러리

- `yt-dlp`: YouTube 다운로드 핵심 라이브러리
- `psutil`: 시스템 리소스 모니터링
- `tqdm`: 진행률 표시
- `tkinter`: GUI 인터페이스 (Python 기본 포함, macOS에서는 별도 설치 필요)

## 🎯 사용법

### 🖥️ GUI 버전 (권장)

```bash
python3 youtube_downloader_gui.py
```

GUI 버전의 특징:

- **직관적인 인터페이스**: 마우스 클릭으로 모든 설정 가능
- **실시간 진행률**: 시각적 진행률 바와 예상 완료 시간
- **로그 표시**: 실시간 다운로드 로그 확인
- **URL 검증**: 버튼 클릭으로 URL 유효성 검사
- **폴더 선택**: 파일 탐색기로 저장 경로 선택

### 💻 콘솔 버전

```bash
python3 youtube_playlist_downloader.py
```

### 2. 플레이리스트 URL 입력

```
다운로드할 유튜브 플레이리스트 URL을 입력하세요:
https://www.youtube.com/playlist?list=PLxxxx
```

### 3. 저장 경로 설정

```
파일을 저장할 폴더 경로를 입력하세요 (기본: ./download):
./download
```

### 4. 화질 선택

```
🎬 화질 선택:
1. 최고 화질 (bestvideo+bestaudio)
2. 1080p
3. 720p
4. 480p
5. 360p
6. 240p
7. 144p
8. 최적 화질 (best)
9. 자동 선택 (권장)
```

### 5. 다운로드 모드 선택

```
다운로드 방식을 선택하세요:
1. 순차 다운로드 (안정적, 느림)
2. 병렬 다운로드 (빠름, 일부 실패 가능)
3. 🔥 MAX 모드 (최대 성능, 모든 자원 활용)
4. 💀🔥 극한 MAX 모드 (극한 성능, 모든 자원 극한 활용)
```

## 📈 진행률 표시 예시

```
다운로드 진행률 (예상 완료: 14:30:25): 45%|████▌     | 9/20 [02:15<02:45, 15.2s/개]
✅ [BTOB] 비투비 - 괜찮아요 (It's Okay) - 뮤직비디오...
```

## 🔧 시스템 최적화

### 자동 시스템 감지

- CPU 코어 수에 따른 최적 워커 수 계산
- 메모리 용량에 따른 버퍼 크기 조정
- 네트워크 상태에 따른 청크 크기 최적화

### MAX 모드 최적화

- 동시 프래그먼트 다운로드 (10개)
- 대용량 버퍼 (1MB)
- 큰 청크 크기 (10MB)
- 재시도 로직 강화

## 📊 결과 요약

다운로드 완료 후 다음과 같은 정보를 제공합니다:

- ✅ 성공한 비디오 개수
- ❌ 실패한 비디오 개수
- 🔄 총 시도 횟수
- ⏱️ 소요 시간
- 📁 저장 경로

## ⚠️ 주의사항

1. **저작권 준수**: 다운로드한 콘텐츠의 저작권을 준수하세요
2. **개인 사용**: 개인적인 용도로만 사용하세요
3. **네트워크 부하**: MAX 모드는 네트워크에 큰 부하를 줄 수 있습니다
4. **저장 공간**: 고화질 다운로드는 많은 저장 공간이 필요합니다

## 🐛 문제 해결

### GUI 실행 오류 시

#### "No module named '\_tkinter'" 오류

```bash
# macOS에서 tkinter 설치
brew install python-tk

# 또는 pip로 설치
python3 -m pip install tk

# Homebrew Python 사용 시 추가 설정
brew link python-tk --force
```

#### "command not found: python3" 오류

```bash
# Homebrew Python 설치 확인
brew list python@3.13

# PATH 설정
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 또는 심볼릭 링크 생성
brew link python@3.13 --force
```

#### "command not found: ffmpeg" 오류

```bash
# FFmpeg 설치 확인
brew list ffmpeg

# PATH 설정 (Apple Silicon Mac)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 또는 심볼릭 링크 생성
brew link ffmpeg --force
```

#### 기타 GUI 오류

- 가상 환경 사용 시: `source venv/bin/activate && python3 youtube_downloader_gui.py`
- 시스템 Python 사용 시: `python3 youtube_downloader_gui.py`
- Python 3.13 이상 사용 시: tkinter trace API 변경으로 인한 오류는 코드에서 수정됨
- Homebrew Python 사용 시: `brew --prefix python@3.13/bin/python3 youtube_downloader_gui.py`

### 다운로드 실패 시

- 인터넷 연결 상태 확인
- URL 유효성 검사
- 저장 경로 권한 확인
- yt-dlp 업데이트: `pip install --upgrade yt-dlp`

### 파일이 다운로드되지 않는 문제

#### 1. 경로 문제 해결

```bash
# 현재 작업 디렉토리 확인
pwd

# 다운로드 폴더 권한 확인
ls -la download/

# 권한 문제 시 권한 수정
chmod 755 download/
```

#### 2. 파일명 문제 해결

- 특수문자가 포함된 파일명으로 인한 저장 실패
- 코드에서 `restrictfilenames: True` 옵션으로 해결됨
- 파일명이 100자로 제한되어 안전하게 저장됨

#### 3. 저장 공간 확인

```bash
# 디스크 사용량 확인
df -h

# 다운로드 폴더 크기 확인
du -sh download/
```

#### 4. 상세한 에러 로그 확인

- GUI 버전: 로그 창에서 상세한 에러 메시지 확인
- 콘솔 버전: 터미널에서 에러 메시지 확인
- 파일 크기가 0인 경우: 네트워크 문제 또는 권한 문제
- 파일이 생성되지 않는 경우: 경로 문제 또는 권한 문제

### 성능 문제 시

- 동시 다운로드 수 줄이기
- 화질 낮추기
- 순차 다운로드 모드 사용

## 📝 업데이트 내역

### v2.1 (현재)

- ✅ GUI 버전 추가 (tkinter 기반)
- ✅ Python 3.13 호환성 개선
- ✅ 극한 MAX 모드 추가
- ✅ 실시간 진행률 표시 추가
- ✅ 화질 선택 옵션 추가
- ✅ 예상 완료 시간 계산
- ✅ 시각적 진행률 바 (tqdm)
- ✅ 시스템 최적화 개선

### v2.0

- 실시간 진행률 표시 추가
- 화질 선택 옵션 추가
- 예상 완료 시간 계산
- 시각적 진행률 바 (tqdm)
- 시스템 최적화 개선

### v1.0

- 기본 플레이리스트 다운로드 기능
- 병렬 처리 지원
- MAX 모드 지원
