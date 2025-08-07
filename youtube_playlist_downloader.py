import yt_dlp  # yt-dlp 라이브러리 임포트: 유튜브 다운로드를 위한 핵심 도구
import os      # os 라이브러리 임포트: 파일 경로 확인 등에 사용
import concurrent.futures  # 병렬 처리를 위한 라이브러리
import threading  # 스레드 안전성을 위한 라이브러리
from urllib.parse import urlparse  # URL 파싱을 위한 라이브러리
import psutil  # 시스템 리소스 모니터링
import multiprocessing  # CPU 코어 수 확인
import time  # 시간 계산을 위한 라이브러리
from tqdm import tqdm  # 진행률 표시를 위한 라이브러리
from datetime import datetime, timedelta  # 시간 계산을 위한 라이브러리
import socket  # 네트워크 최적화를 위한 라이브러리
import ssl  # SSL 최적화를 위한 라이브러리

# 전역 변수로 진행 상황 추적
download_progress = {
    'total': 0,
    'completed': 0,
    'failed': 0,
    'start_time': None,
    'lock': threading.Lock()
}

def get_system_info():
    """
    시스템 정보를 가져와서 최적의 다운로드 설정을 추천하는 함수
    """
    cpu_count = multiprocessing.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # CPU 코어 수에 따른 최적 워커 수 계산 (극한 성능)
    if cpu_count >= 16:
        recommended_workers = min(cpu_count * 2, 50)  # 16코어 이상: 코어 수 * 2, 최대 50개
    elif cpu_count >= 8:
        recommended_workers = min(cpu_count * 1.5, 30)  # 8코어 이상: 코어 수 * 1.5, 최대 30개
    elif cpu_count >= 4:
        recommended_workers = min(cpu_count * 1.2, 20)  # 4코어 이상: 코어 수 * 1.2, 최대 20개
    else:
        recommended_workers = min(cpu_count + 2, 10)  # 4코어 미만: 코어 수 + 2, 최대 10개
    
    # 메모리 기반 추가 워커 계산
    memory_bonus = int(memory_gb / 4)  # 4GB당 1개 추가 워커
    recommended_workers += memory_bonus
    
    return {
        'cpu_count': cpu_count,
        'memory_gb': round(memory_gb, 1),
        'recommended_workers': recommended_workers,
        'max_workers': min(recommended_workers * 3, 100),  # 극한 MAX 모드용
        'memory_bonus': memory_bonus
    }

def optimize_network_settings():
    """
    네트워크 설정을 극한 성능으로 최적화하는 함수
    """
    # 소켓 버퍼 크기 최적화
    socket.SO_RCVBUF = 1024 * 1024 * 10  # 10MB 수신 버퍼
    socket.SO_SNDBUF = 1024 * 1024 * 10   # 10MB 송신 버퍼
    
    # TCP 설정 최적화
    socket.TCP_NODELAY = 1
    socket.TCP_QUICKACK = 1
    
    print("🌐 네트워크 최적화 완료:")
    print(f"   📡 수신 버퍼: 10MB")
    print(f"   📡 송신 버퍼: 10MB")
    print(f"   📡 TCP 최적화: 활성화")

def get_available_formats(video_url):
    """
    비디오의 사용 가능한 화질 옵션을 가져오는 함수
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            
            # 화질 옵션 정리
            quality_options = []
            seen_qualities = set()
            
            for f in formats:
                if f.get('height') and f.get('ext') == 'mp4':
                    quality = f"{f['height']}p"
                    if quality not in seen_qualities:
                        quality_options.append({
                            'format_id': f['format_id'],
                            'height': f['height'],
                            'quality': quality,
                            'filesize': f.get('filesize', 0)
                        })
                        seen_qualities.add(quality)
            
            # 화질별로 정렬
            quality_options.sort(key=lambda x: x['height'], reverse=True)
            return quality_options
    except Exception as e:
        print(f"화질 정보를 가져올 수 없습니다: {str(e)}")
        return []

def select_quality_format():
    """
    사용자가 화질을 선택할 수 있도록 하는 함수
    """
    print("\n🎬 화질 선택:")
    print("1. 최고 화질 (bestvideo+bestaudio)")
    print("2. 1080p")
    print("3. 720p")
    print("4. 480p")
    print("5. 360p")
    print("6. 240p")
    print("7. 144p")
    print("8. 최적 화질 (best)")
    print("9. 자동 선택 (권장)")
    
    while True:
        choice = input("화질을 선택하세요 (1-9, 기본: 9): ").strip()
        if not choice:
            choice = "9"
        
        if choice in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            quality_map = {
                '1': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '2': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
                '3': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                '4': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
                '5': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best',
                '6': 'bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[height<=240][ext=mp4]/best',
                '7': 'bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/best[height<=144][ext=mp4]/best',
                '8': 'best[ext=mp4]/best',
                '9': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            }
            return quality_map[choice]
        else:
            print("❌ 1-9 사이의 숫자를 입력해주세요.")

def update_progress(success=True):
    """
    진행 상황을 업데이트하는 함수
    """
    with download_progress['lock']:
        if success:
            download_progress['completed'] += 1
        else:
            download_progress['failed'] += 1

def get_eta():
    """
    예상 완료 시간을 계산하는 함수
    """
    if download_progress['start_time'] is None:
        return "계산 중..."
    
    elapsed = time.time() - download_progress['start_time']
    completed = download_progress['completed'] + download_progress['failed']
    
    if completed == 0:
        return "계산 중..."
    
    avg_time_per_video = elapsed / completed
    remaining_videos = download_progress['total'] - completed
    
    if remaining_videos <= 0:
        return "완료!"
    
    eta_seconds = avg_time_per_video * remaining_videos
    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
    
    return eta_time.strftime("%H:%M:%S")

def format_duration(seconds):
    """
    초를 시:분:초 형식으로 변환하는 함수
    """
    if seconds < 60:
        return f"{seconds}초"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}분 {seconds}초"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours}시간 {minutes}분 {seconds}초"

def validate_url(url):
    """
    URL 유효성을 검사하는 함수
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url)
        
        # 기본 URL 형식 검사
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # YouTube 도메인 검사
        if 'youtube.com' not in parsed.netloc and 'youtu.be' not in parsed.netloc:
            return False
        
        # 플레이리스트 URL 검사
        if 'playlist' in url:
            if 'list=' not in url:
                return False
        
        # 단일 비디오 URL 검사
        elif 'watch' in url:
            if 'v=' not in url:
                return False
        
        # youtu.be 링크 검사
        elif 'youtu.be' in url:
            if not parsed.path or len(parsed.path.strip('/')) < 10:
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ URL 검증 오류: {e}")
        return False

def download_single_video_extreme_max(video_url, download_path, video_info=None, max_retries=5, quality_format=None):
    """
    극한 MAX 모드용 단일 비디오 다운로드 함수 (모든 자원 활용)
    """
    if quality_format is None:
        quality_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    # 다운로드 경로를 절대 경로로 변환
    download_path = os.path.abspath(download_path)
    
    # 다운로드 경로가 존재하는지 확인하고 생성
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return {'success': False, 'url': video_url, 'error': f'경로 생성 실패: {e}', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
    
    # 파일명 안전성을 위한 템플릿 설정
    safe_filename_template = f'{download_path}/%(title).100s.%(ext)s'
    
    # 극한 성능을 위한 yt-dlp 옵션
    ydl_opts = {
        'format': quality_format,
        'merge_output_format': 'mp4',
        'outtmpl': safe_filename_template,
        'quiet': True,
        'ignoreerrors': True,
        'no_warnings': True,
        # 극한 MAX 모드 최적화 옵션들
        'concurrent_fragment_downloads': 50,  # 동시 프래그먼트 다운로드 (극한 증가: 50개)
        'buffersize': 1024 * 1024 * 10,  # 버퍼 크기 극한 증가 (10MB)
        'http_chunk_size': 10485760 * 5,  # 청크 크기 극한 증가 (50MB)
        'retries': max_retries,  # 재시도 횟수 증가
        'fragment_retries': max_retries,  # 프래그먼트 재시도
        'file_access_retries': max_retries,  # 파일 접근 재시도
        'extractor_retries': max_retries,  # 추출기 재시도
        'sleep_interval': 0,  # 대기 시간 최소화
        'max_sleep_interval': 0.1,  # 최대 대기 시간 극한 제한 (0.1초)
        # 네트워크 최적화
        'socket_timeout': 60,  # 소켓 타임아웃 증가
        'http_timeout': 60,  # HTTP 타임아웃 증가
        # 메모리 최적화
        'max_downloads': 1,  # 단일 다운로드에 집중
        'prefer_ffmpeg': True,  # FFmpeg 우선 사용
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        # 극한 성능을 위한 추가 옵션
        'nocheckcertificate': True,  # SSL 인증서 검사 건너뛰기 (속도 향상)
        'prefer_insecure': True,  # 불안전한 연결 선호 (속도 향상)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        # 극한 성능을 위한 추가 설정
        'external_downloader': 'aria2c',  # aria2c 외부 다운로더 사용 (가능한 경우)
        'external_downloader_args': ['--max-connection-per-server=16', '--min-split-size=1M', '--max-concurrent-downloads=16'],
        'concurrent_fragment_downloads': 50,  # 동시 프래그먼트 다운로드 극한 증가
        'buffersize': 1024 * 1024 * 20,  # 버퍼 크기 극한 증가 (20MB)
        'http_chunk_size': 10485760 * 10,  # 청크 크기 극한 증가 (100MB)
        # 파일 저장 안전성 개선
        'restrictfilenames': True,  # 파일명 제한 (특수문자 제거)
        'windowsfilenames': False,  # Windows 파일명 규칙 비활성화
    }
    
    for attempt in range(max_retries + 1):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # 파일이 실제로 저장되었는지 확인 (restrictfilenames 옵션 고려)
            video_title = video_info.get('title', 'Unknown') if video_info else 'Unknown'
            
            # restrictfilenames 옵션으로 인한 파일명 변경을 고려한 검색
            import re
            safe_title = re.sub(r'[^\w\s-]', '', video_title)  # 특수문자 제거
            safe_title = re.sub(r'[-\s]+', '-', safe_title)  # 공백을 하이픈으로 변경
            safe_title = safe_title[:100]  # 100자로 제한
            
            # 가능한 파일명 패턴들
            possible_filenames = [
                f"{video_title}.mp4",
                f"{safe_title}.mp4",
                f"{video_title[:50]}.mp4",
                f"{safe_title[:50]}.mp4"
            ]
            
            # 실제 저장된 파일 찾기
            actual_file_path = None
            for filename in possible_filenames:
                file_path = os.path.join(download_path, filename)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    actual_file_path = file_path
                    break
            
            # 파일을 찾지 못한 경우, 최근 생성된 mp4 파일 검색
            if actual_file_path is None:
                try:
                    mp4_files = []
                    for file in os.listdir(download_path):
                        if file.endswith('.mp4') and os.path.isfile(os.path.join(download_path, file)):
                            file_path = os.path.join(download_path, file)
                            # 최근 30초 내에 생성된 파일만 고려
                            if time.time() - os.path.getctime(file_path) < 30:
                                mp4_files.append((file_path, os.path.getctime(file_path)))
                    
                    if mp4_files:
                        # 가장 최근에 생성된 파일 선택
                        mp4_files.sort(key=lambda x: x[1], reverse=True)
                        actual_file_path = mp4_files[0][0]
                        print(f"🔍 실제 저장된 파일 발견: {os.path.basename(actual_file_path)}")
                except Exception as e:
                    print(f"⚠️ 파일 검색 중 오류: {e}")
            
            if actual_file_path and os.path.exists(actual_file_path):
                file_size = os.path.getsize(actual_file_path)
                if file_size > 0:
                    update_progress(True)
                    return {'success': True, 'url': video_url, 'title': video_title, 'attempts': attempt + 1, 'file_path': actual_file_path, 'file_size': file_size}
                else:
                    print(f"⚠️ 파일이 생성되었지만 크기가 0입니다: {actual_file_path}")
                    if attempt < max_retries:
                        time.sleep(0.1)
                        continue
                    else:
                        update_progress(False)
                        return {'success': False, 'url': video_url, 'error': '파일 크기가 0입니다', 'title': video_title}
            else:
                print(f"⚠️ 예상 파일이 생성되지 않았습니다")
                print(f"🔍 검색한 파일명 패턴: {possible_filenames}")
                print(f"📁 다운로드 경로: {download_path}")
                if attempt < max_retries:
                    time.sleep(0.1)
                    continue
                else:
                    update_progress(False)
                    return {'success': False, 'url': video_url, 'error': '파일이 생성되지 않았습니다', 'title': video_title}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 다운로드 오류 (시도 {attempt + 1}/{max_retries + 1}): {error_msg}")
            
            if 'Video unavailable' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': 'Video unavailable', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif 'Private video' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': 'Private video', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif 'This video is not available' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': 'Video not available', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif 'No such file or directory' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': '파일 시스템 오류', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif attempt < max_retries:
                time.sleep(0.1)  # 극한 모드에서는 최소 대기
                continue  # 재시도
            else:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': error_msg, 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}

def download_single_video_max(video_url, download_path, video_info=None, max_retries=3, quality_format=None):
    """
    MAX 모드용 단일 비디오 다운로드 함수 (재시도 로직 포함)
    """
    if quality_format is None:
        quality_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    # 다운로드 경로를 절대 경로로 변환
    download_path = os.path.abspath(download_path)
    
    # 다운로드 경로가 존재하는지 확인하고 생성
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return {'success': False, 'url': video_url, 'error': f'경로 생성 실패: {e}', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
    
    # 파일명 안전성을 위한 템플릿 설정
    safe_filename_template = f'{download_path}/%(title).100s.%(ext)s'
    
    ydl_opts = {
        'format': quality_format,
        'merge_output_format': 'mp4',
        'outtmpl': safe_filename_template,
        'quiet': True,
        'ignoreerrors': True,
        'no_warnings': True,
        # MAX 모드 최적화 옵션들
        'concurrent_fragment_downloads': 10,  # 동시 프래그먼트 다운로드
        'buffersize': 1024 * 1024,  # 버퍼 크기 증가 (1MB)
        'http_chunk_size': 10485760,  # 청크 크기 증가 (10MB)
        'retries': max_retries,  # 재시도 횟수
        'fragment_retries': max_retries,  # 프래그먼트 재시도
        'file_access_retries': max_retries,  # 파일 접근 재시도
        'extractor_retries': max_retries,  # 추출기 재시도
        'sleep_interval': 0,  # 대기 시간 최소화
        'max_sleep_interval': 1,  # 최대 대기 시간 제한
        # 파일 저장 안전성 개선
        'restrictfilenames': True,  # 파일명 제한 (특수문자 제거)
        'windowsfilenames': False,  # Windows 파일명 규칙 비활성화
    }
    
    for attempt in range(max_retries + 1):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # 파일이 실제로 저장되었는지 확인 (restrictfilenames 옵션 고려)
            video_title = video_info.get('title', 'Unknown') if video_info else 'Unknown'
            
            # restrictfilenames 옵션으로 인한 파일명 변경을 고려한 검색
            import re
            safe_title = re.sub(r'[^\w\s-]', '', video_title)  # 특수문자 제거
            safe_title = re.sub(r'[-\s]+', '-', safe_title)  # 공백을 하이픈으로 변경
            safe_title = safe_title[:100]  # 100자로 제한
            
            # 가능한 파일명 패턴들
            possible_filenames = [
                f"{video_title}.mp4",
                f"{safe_title}.mp4",
                f"{video_title[:50]}.mp4",
                f"{safe_title[:50]}.mp4"
            ]
            
            # 실제 저장된 파일 찾기
            actual_file_path = None
            for filename in possible_filenames:
                file_path = os.path.join(download_path, filename)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    actual_file_path = file_path
                    break
            
            # 파일을 찾지 못한 경우, 최근 생성된 mp4 파일 검색
            if actual_file_path is None:
                try:
                    mp4_files = []
                    for file in os.listdir(download_path):
                        if file.endswith('.mp4') and os.path.isfile(os.path.join(download_path, file)):
                            file_path = os.path.join(download_path, file)
                            # 최근 30초 내에 생성된 파일만 고려
                            if time.time() - os.path.getctime(file_path) < 30:
                                mp4_files.append((file_path, os.path.getctime(file_path)))
                    
                    if mp4_files:
                        # 가장 최근에 생성된 파일 선택
                        mp4_files.sort(key=lambda x: x[1], reverse=True)
                        actual_file_path = mp4_files[0][0]
                        print(f"🔍 실제 저장된 파일 발견: {os.path.basename(actual_file_path)}")
                except Exception as e:
                    print(f"⚠️ 파일 검색 중 오류: {e}")
            
            if actual_file_path and os.path.exists(actual_file_path):
                file_size = os.path.getsize(actual_file_path)
                if file_size > 0:
                    update_progress(True)
                    return {'success': True, 'url': video_url, 'title': video_title, 'attempts': attempt + 1, 'file_path': actual_file_path, 'file_size': file_size}
                else:
                    print(f"⚠️ 파일이 생성되었지만 크기가 0입니다: {actual_file_path}")
                    if attempt < max_retries:
                        continue
                    else:
                        update_progress(False)
                        return {'success': False, 'url': video_url, 'error': '파일 크기가 0입니다', 'title': video_title}
            else:
                print(f"⚠️ 예상 파일이 생성되지 않았습니다: {expected_path}")
                print(f"🔍 검색한 파일명 패턴: {possible_filenames}")
                if attempt < max_retries:
                    continue
                else:
                    update_progress(False)
                    return {'success': False, 'url': video_url, 'error': '파일이 생성되지 않았습니다', 'title': video_title}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 다운로드 오류 (시도 {attempt + 1}/{max_retries + 1}): {error_msg}")
            
            if 'Video unavailable' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': 'Video unavailable', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif 'Private video' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': 'Private video', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif 'This video is not available' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': 'Video not available', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif 'No such file or directory' in error_msg:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': '파일 시스템 오류', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            elif attempt < max_retries:
                continue  # 재시도
            else:
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': error_msg, 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}

def download_single_video(video_url, download_path, video_info=None, quality_format=None):
    """
    단일 비디오를 다운로드하는 함수 (병렬 처리용)
    """
    if quality_format is None:
        quality_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    # 다운로드 경로를 절대 경로로 변환
    download_path = os.path.abspath(download_path)
    
    # 다운로드 경로가 존재하는지 확인하고 생성
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return {'success': False, 'url': video_url, 'error': f'경로 생성 실패: {e}', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
    
    # 파일명 안전성을 위한 템플릿 설정
    safe_filename_template = f'{download_path}/%(title).100s.%(ext)s'
    
    ydl_opts = {
        'format': quality_format,
        'merge_output_format': 'mp4',
        'outtmpl': safe_filename_template,
        'quiet': True,  # 개별 다운로드는 조용히
        'ignoreerrors': True,  # 개별 비디오 오류 무시
        'no_warnings': True,
        # 파일 저장 안전성 개선
        'restrictfilenames': True,  # 파일명 제한 (특수문자 제거)
        'windowsfilenames': False,  # Windows 파일명 규칙 비활성화
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 파일이 실제로 저장되었는지 확인 (restrictfilenames 옵션 고려)
        # video_info가 None인 경우 실제 비디오 정보를 가져오기
        if video_info is None:
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    video_info = ydl.extract_info(video_url, download=False)
            except Exception as e:
                print(f"⚠️ 비디오 정보 가져오기 실패: {e}")
                video_info = {}
        
        video_title = video_info.get('title', 'Unknown') if video_info else 'Unknown'
        
        # restrictfilenames 옵션으로 인한 파일명 변경을 고려한 검색
        import re
        safe_title = re.sub(r'[^\w\s-]', '', video_title)  # 특수문자 제거
        safe_title = re.sub(r'[-\s]+', '-', safe_title)  # 공백을 하이픈으로 변경
        safe_title = safe_title[:100]  # 100자로 제한
        
        # 가능한 파일명 패턴들
        possible_filenames = [
            f"{video_title}.mp4",
            f"{safe_title}.mp4",
            f"{video_title[:50]}.mp4",
            f"{safe_title[:50]}.mp4"
        ]
        
        # restrictfilenames 옵션으로 인한 추가 패턴들
        underscore_title = video_title.replace(' ', '_')
        underscore_safe_title = safe_title.replace(' ', '_')
        possible_filenames.extend([
            f"{underscore_title}.mp4",
            f"{underscore_safe_title}.mp4",
            f"{underscore_title[:50]}.mp4",
            f"{underscore_safe_title[:50]}.mp4"
        ])
        
        # 실제 저장된 파일 찾기
        actual_file_path = None
        for filename in possible_filenames:
            file_path = os.path.join(download_path, filename)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                actual_file_path = file_path
                break
        
        # 파일을 찾지 못한 경우, 최근 생성된 mp4 파일 검색
        if actual_file_path is None:
            try:
                mp4_files = []
                for file in os.listdir(download_path):
                    if file.endswith('.mp4') and os.path.isfile(os.path.join(download_path, file)):
                        file_path = os.path.join(download_path, file)
                        # 최근 30초 내에 생성된 파일만 고려
                        if time.time() - os.path.getctime(file_path) < 30:
                            mp4_files.append((file_path, os.path.getctime(file_path)))
                
                if mp4_files:
                    # 가장 최근에 생성된 파일 선택
                    mp4_files.sort(key=lambda x: x[1], reverse=True)
                    actual_file_path = mp4_files[0][0]
                    print(f"🔍 실제 저장된 파일 발견: {os.path.basename(actual_file_path)}")
            except Exception as e:
                print(f"⚠️ 파일 검색 중 오류: {e}")
        
        if actual_file_path and os.path.exists(actual_file_path):
            file_size = os.path.getsize(actual_file_path)
            if file_size > 0:
                update_progress(True)
                return {'success': True, 'url': video_url, 'title': video_title, 'file_path': actual_file_path, 'file_size': file_size}
            else:
                print(f"⚠️ 파일이 생성되었지만 크기가 0입니다: {actual_file_path}")
                update_progress(False)
                return {'success': False, 'url': video_url, 'error': '파일 크기가 0입니다', 'title': video_title}
        else:
            print(f"⚠️ 예상 파일이 생성되지 않았습니다")
            print(f"🔍 검색한 파일명 패턴: {possible_filenames}")
            print(f"📁 다운로드 경로: {download_path}")
            update_progress(False)
            return {'success': False, 'url': video_url, 'error': '파일이 생성되지 않았습니다', 'title': video_title}
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 다운로드 오류: {error_msg}")
        update_progress(False)
        if 'Video unavailable' in error_msg:
            return {'success': False, 'url': video_url, 'error': 'Video unavailable', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
        elif 'Private video' in error_msg:
            return {'success': False, 'url': video_url, 'error': 'Private video', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
        elif 'This video is not available' in error_msg:
            return {'success': False, 'url': video_url, 'error': 'Video not available', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
        elif 'No such file or directory' in error_msg:
            return {'success': False, 'url': video_url, 'error': '파일 시스템 오류', 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}
        else:
            return {'success': False, 'url': video_url, 'error': error_msg, 'title': video_info.get('title', 'Unknown') if video_info else 'Unknown'}

def get_playlist_videos(playlist_url):
    """
    플레이리스트에서 비디오 URL 목록을 추출하는 함수
    """
    # URL 타입 확인 및 비디오 ID 추출
    video_id = None
    playlist_id = None
    
    if 'watch?v=' in playlist_url:
        video_id = playlist_url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in playlist_url:
        video_id = playlist_url.split('youtu.be/')[1].split('?')[0]
    elif 'playlist?list=' in playlist_url:
        playlist_id = playlist_url.split('list=')[1].split('&')[0]
    
    # 단일 비디오인 경우
    if video_id:
        print(f"✅ 단일 비디오로 처리: {video_id}")
        return [{
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'title': 'Unknown',
            'duration': 0
        }]
    
    # 플레이리스트인 경우
    if playlist_id:
        print(f"✅ 플레이리스트로 처리: {playlist_id}")
        
        # 여러 가지 방법으로 플레이리스트 정보를 가져오기 시도
        methods = [
            # 방법 1: 기본 설정
            {
                'quiet': True,
                'extract_flat': True,
                'ignoreerrors': True,
                'no_warnings': True,
                'socket_timeout': 60,
                'http_timeout': 60,
                'retries': 3,
                'sleep_interval': 1,
                'max_sleep_interval': 3,
            },
            # 방법 2: 더 안정적인 설정
            {
                'quiet': True,
                'extract_flat': True,
                'ignoreerrors': True,
                'no_warnings': True,
                'socket_timeout': 120,
                'http_timeout': 120,
                'retries': 5,
                'sleep_interval': 2,
                'max_sleep_interval': 10,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
            },
            # 방법 3: 최소 설정
            {
                'quiet': True,
                'extract_flat': True,
                'ignoreerrors': True,
                'no_warnings': True,
                'socket_timeout': 30,
                'http_timeout': 30,
                'retries': 1,
            }
        ]
        
        for i, ydl_opts in enumerate(methods, 1):
            try:
                print(f"🔍 방법 {i}로 플레이리스트 정보를 가져오는 중...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    playlist_info = ydl.extract_info(playlist_url, download=False)
                    
                    # playlist_info가 None인 경우 처리
                    if playlist_info is None:
                        print(f"❌ 방법 {i} 실패: 플레이리스트 정보를 가져올 수 없습니다")
                        continue
                    
                    # entries가 없는 경우 처리
                    if 'entries' not in playlist_info:
                        print(f"❌ 방법 {i} 실패: 플레이리스트에 비디오가 없습니다")
                        continue
                    
                    videos = []
                    for entry in playlist_info['entries']:
                        if entry and 'id' in entry:  # None이 아니고 id가 있는 경우만
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            videos.append({
                                'url': video_url,
                                'title': entry.get('title', 'Unknown'),
                                'duration': entry.get('duration', 0)
                            })
                    
                    if videos:
                        print(f"✅ 방법 {i} 성공: 플레이리스트에서 {len(videos)}개의 비디오를 찾았습니다.")
                        return videos
                    else:
                        print(f"❌ 방법 {i} 실패: 비디오를 찾을 수 없습니다")
                        
            except Exception as e:
                print(f"❌ 방법 {i} 실패: {str(e)}")
                continue
        
        # 모든 방법이 실패한 경우, 수동으로 플레이리스트 ID를 사용
        print(f"🔄 모든 방법이 실패했습니다. 플레이리스트 ID를 직접 사용합니다: {playlist_id}")
        return [{
            'url': f"https://www.youtube.com/playlist?list={playlist_id}",
            'title': f'Playlist_{playlist_id}',
            'duration': 0
        }]
    
    print(f"❌ 지원되지 않는 URL 형식: {playlist_url}")
    return []

def download_playlist_extreme_max(playlist_url, download_path, max_workers=None, quality_format=None, progress_callback=None):
    """
    극한 MAX 모드: 모든 성능과 자원을 극한으로 활용한 플레이리스트 다운로드
    """
    system_info = get_system_info()
    
    if max_workers is None:
        max_workers = system_info['max_workers']
    
    print("🚀🔥 극한 MAX 모드 활성화!")
    print("💀 모든 시스템 자원을 극한으로 활용합니다...")
    print(f"💻 시스템 정보: CPU {system_info['cpu_count']}코어, RAM {system_info['memory_gb']}GB")
    print(f"⚡ 극한 워커 수: {system_info['recommended_workers']}개 (MAX: {max_workers}개)")
    print(f"🧠 메모리 보너스: +{system_info['memory_bonus']}개 워커")
    print("🔥 네트워크 대역폭 극한 활용")
    print("💾 메모리 극한 활용")
    print("⚡ CPU 극한 활용")
    
    # 네트워크 최적화
    optimize_network_settings()
    
    print("플레이리스트 정보를 가져오는 중...")
    videos = get_playlist_videos(playlist_url)
    
    if not videos:
        print("플레이리스트에서 비디오를 찾을 수 없습니다.")
        return
    
    # 진행 상황 초기화
    download_progress['total'] = len(videos)
    download_progress['completed'] = 0
    download_progress['failed'] = 0
    download_progress['start_time'] = time.time()
    
    print(f"총 {len(videos)}개의 비디오를 발견했습니다.")
    print(f"🔥💀 극한 MAX 모드 다운로드를 시작합니다 (최대 {max_workers}개 동시 다운로드)...")
    print(f"🎬 선택된 화질: {quality_format}")
    print("⚠️ 경고: 극한 성능으로 인한 시스템 부하가 발생할 수 있습니다!")
    print("💀 모든 자원을 극한으로 활용하여 최대 성능을 발휘합니다!")
    
    # 다운로드 경로를 절대 경로로 변환하고 생성
    download_path = os.path.abspath(download_path)
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return
    
    successful_downloads = 0
    failed_downloads = 0
    total_attempts = 0
    
    # 진행률 표시를 위한 tqdm 설정
    with tqdm(total=len(videos), desc="극한 다운로드 진행률", unit="개") as pbar:
        # ThreadPoolExecutor를 사용한 극한 MAX 모드 병렬 다운로드
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 다운로드 작업 제출 (극한 MAX 모드 함수 사용)
            future_to_video = {
                executor.submit(download_single_video_extreme_max, video['url'], download_path, video, 5, quality_format): video 
                for video in videos
            }
            
            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    if result['success']:
                        successful_downloads += 1
                        attempts = result.get('attempts', 1)
                        total_attempts += attempts
                        if attempts > 1:
                            pbar.set_postfix_str(f"✅ {result['title'][:30]}... (재시도: {attempts}회)")
                        else:
                            pbar.set_postfix_str(f"✅ {result['title'][:30]}...")
                    else:
                        failed_downloads += 1
                        pbar.set_postfix_str(f"❌ {result['title'][:30]}... - {result['error']}")
                    
                    # 진행률 업데이트
                    pbar.update(1)
                    
                    # 진행률 콜백 호출
                    if progress_callback:
                        progress_callback(successful_downloads + failed_downloads, len(videos), result['success'])
                    
                    # 예상 완료 시간 표시
                    eta = get_eta()
                    pbar.set_description(f"극한 다운로드 진행률 (예상 완료: {eta})")
                    
                except Exception as e:
                    failed_downloads += 1
                    pbar.set_postfix_str(f"❌ {video['title'][:30]}... - 오류")
                    pbar.update(1)
    
    # 결과 요약
    elapsed_time = time.time() - download_progress['start_time']
    print(f"\n📊🔥 극한 MAX 모드 다운로드 완료!")
    print(f"✅ 성공: {successful_downloads}개")
    print(f"❌ 실패: {failed_downloads}개")
    print(f"🔄 총 시도: {total_attempts}회")
    print(f"⏱️ 소요 시간: {format_duration(elapsed_time)}")
    print(f"📁 저장 경로: {download_path}")
    print(f"🚀 극한 성능 모드로 {format_duration(elapsed_time)}만에 완료!")
    print(f"💀 모든 자원을 극한으로 활용하여 최대 성능을 달성했습니다!")
    
    if failed_downloads > 0:
        print(f"\n⚠️ {failed_downloads}개의 비디오 다운로드에 실패했습니다.")
        print("실패 원인: 비디오 비공개, 삭제됨, 지역 제한 등")

def download_playlist_max(playlist_url, download_path, max_workers=None, quality_format=None, progress_callback=None):
    """
    MAX 모드: 모든 성능과 자원을 최대한 활용한 플레이리스트 다운로드
    """
    system_info = get_system_info()
    
    if max_workers is None:
        max_workers = system_info['max_workers']
    
    print("🚀 MAX 모드 활성화!")
    print(f"💻 시스템 정보: CPU {system_info['cpu_count']}코어, RAM {system_info['memory_gb']}GB")
    print(f"⚡ 최적 워커 수: {system_info['recommended_workers']}개 (MAX: {max_workers}개)")
    print("🔥 모든 성능과 자원을 최대한 활용합니다...")
    
    print("플레이리스트 정보를 가져오는 중...")
    videos = get_playlist_videos(playlist_url)
    
    if not videos:
        print("플레이리스트에서 비디오를 찾을 수 없습니다.")
        return
    
    # 진행 상황 초기화
    download_progress['total'] = len(videos)
    download_progress['completed'] = 0
    download_progress['failed'] = 0
    download_progress['start_time'] = time.time()
    
    print(f"총 {len(videos)}개의 비디오를 발견했습니다.")
    print(f"🔥 MAX 모드 다운로드를 시작합니다 (최대 {max_workers}개 동시 다운로드)...")
    print(f"🎬 선택된 화질: {quality_format}")
    
    # 다운로드 경로를 절대 경로로 변환하고 생성
    download_path = os.path.abspath(download_path)
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return
    
    successful_downloads = 0
    failed_downloads = 0
    total_attempts = 0
    
    # 진행률 표시를 위한 tqdm 설정
    with tqdm(total=len(videos), desc="다운로드 진행률", unit="개") as pbar:
        # ThreadPoolExecutor를 사용한 MAX 모드 병렬 다운로드
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 다운로드 작업 제출 (MAX 모드 함수 사용)
            future_to_video = {
                executor.submit(download_single_video_max, video['url'], download_path, video, 3, quality_format): video 
                for video in videos
            }
            
            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    if result['success']:
                        successful_downloads += 1
                        attempts = result.get('attempts', 1)
                        total_attempts += attempts
                        if attempts > 1:
                            pbar.set_postfix_str(f"✅ {result['title'][:30]}... (재시도: {attempts}회)")
                        else:
                            pbar.set_postfix_str(f"✅ {result['title'][:30]}...")
                    else:
                        failed_downloads += 1
                        pbar.set_postfix_str(f"❌ {result['title'][:30]}... - {result['error']}")
                    
                    # 진행률 업데이트
                    pbar.update(1)
                    
                    # GUI 진행률 콜백 호출
                    if progress_callback:
                        progress_callback(successful_downloads + failed_downloads, len(videos), result['success'])
                    
                    # 예상 완료 시간 표시
                    eta = get_eta()
                    pbar.set_description(f"다운로드 진행률 (예상 완료: {eta})")
                    
                except Exception as e:
                    failed_downloads += 1
                    pbar.set_postfix_str(f"❌ {video['title'][:30]}... - 오류")
                    pbar.update(1)
                    
                    # GUI 진행률 콜백 호출 (실패)
                    if progress_callback:
                        progress_callback(successful_downloads + failed_downloads, len(videos), False)
    
    # 결과 요약
    elapsed_time = time.time() - download_progress['start_time']
    print(f"\n📊 MAX 모드 다운로드 완료!")
    print(f"✅ 성공: {successful_downloads}개")
    print(f"❌ 실패: {failed_downloads}개")
    print(f"🔄 총 시도: {total_attempts}회")
    print(f"⏱️ 소요 시간: {format_duration(elapsed_time)}")
    print(f"📁 저장 경로: {download_path}")
    
    if failed_downloads > 0:
        print(f"\n⚠️ {failed_downloads}개의 비디오 다운로드에 실패했습니다.")
        print("실패 원인: 비디오 비공개, 삭제됨, 지역 제한 등")

def download_playlist_parallel(playlist_url, download_path, max_workers=3, quality_format=None, progress_callback=None):
    """
    플레이리스트를 병렬로 다운로드하는 함수
    """
    print("플레이리스트 정보를 가져오는 중...")
    videos = get_playlist_videos(playlist_url)
    
    if not videos:
        print("플레이리스트에서 비디오를 찾을 수 없습니다.")
        return
    
    # 진행 상황 초기화
    download_progress['total'] = len(videos)
    download_progress['completed'] = 0
    download_progress['failed'] = 0
    download_progress['start_time'] = time.time()
    
    print(f"총 {len(videos)}개의 비디오를 발견했습니다.")
    print(f"병렬 다운로드를 시작합니다 (최대 {max_workers}개 동시 다운로드)...")
    print(f"🎬 선택된 화질: {quality_format}")
    
    # 다운로드 경로를 절대 경로로 변환하고 생성
    download_path = os.path.abspath(download_path)
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return
    
    successful_downloads = 0
    failed_downloads = 0
    
    # 진행률 표시를 위한 tqdm 설정
    with tqdm(total=len(videos), desc="다운로드 진행률", unit="개") as pbar:
        # ThreadPoolExecutor를 사용한 병렬 다운로드
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 다운로드 작업 제출
            future_to_video = {
                executor.submit(download_single_video, video['url'], download_path, video, quality_format): video 
                for video in videos
            }
            
            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    if result['success']:
                        successful_downloads += 1
                        pbar.set_postfix_str(f"✅ {result['title'][:30]}...")
                    else:
                        failed_downloads += 1
                        pbar.set_postfix_str(f"❌ {result['title'][:30]}... - {result['error']}")
                    
                    # 진행률 업데이트
                    pbar.update(1)
                    
                    # GUI 진행률 콜백 호출
                    if progress_callback:
                        progress_callback(successful_downloads + failed_downloads, len(videos), result['success'])
                    
                    # 예상 완료 시간 표시
                    eta = get_eta()
                    pbar.set_description(f"다운로드 진행률 (예상 완료: {eta})")
                    
                except Exception as e:
                    failed_downloads += 1
                    pbar.set_postfix_str(f"❌ {video['title'][:30]}... - 오류")
                    pbar.update(1)
                    
                    # GUI 진행률 콜백 호출 (실패)
                    if progress_callback:
                        progress_callback(successful_downloads + failed_downloads, len(videos), False)
    
    # 결과 요약
    elapsed_time = time.time() - download_progress['start_time']
    print(f"\n📊 다운로드 완료!")
    print(f"✅ 성공: {successful_downloads}개")
    print(f"❌ 실패: {failed_downloads}개")
    print(f"⏱️ 소요 시간: {format_duration(elapsed_time)}")
    print(f"📁 저장 경로: {download_path}")
    
    if failed_downloads > 0:
        print(f"\n⚠️ {failed_downloads}개의 비디오 다운로드에 실패했습니다.")
        print("실패 원인: 비디오 비공개, 삭제됨, 지역 제한 등")

def download_playlist(playlist_url, download_path, quality_format=None):
    """
    플레이리스트를 MP4 형식으로 다운로드하는 함수 (기존 방식)
    """
    if quality_format is None:
        quality_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    # 다운로드 경로를 절대 경로로 변환하고 생성
    download_path = os.path.abspath(download_path)
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path, exist_ok=True)
            print(f"📁 다운로드 경로 생성: {download_path}")
        except Exception as e:
            print(f"❌ 다운로드 경로 생성 실패: {e}")
            return
    
    # 파일명 안전성을 위한 템플릿 설정
    safe_filename_template = f'{download_path}/%(title).100s.%(ext)s'
    
    # 플레이리스트 ID 추출
    playlist_id = None
    if 'playlist?list=' in playlist_url:
        playlist_id = playlist_url.split('list=')[1].split('&')[0]
    
    # yt-dlp 옵션 설정: 다운로드 방식을 정의
    ydl_opts = {
        'format': quality_format,  # 선택된 화질 사용
        'merge_output_format': 'mp4',  # 최종 출력 형식을 MP4로 강제
        'outtmpl': safe_filename_template,  # 파일 이름 형식: 제목.확장자 (저장 경로 포함)
        'noplaylist': False,  # False로 설정: 플레이리스트 전체 다운로드 (True면 단일 비디오만)
        'quiet': False,  # 다운로드 진행 상황을 콘솔에 표시 (True로 하면 조용히)
        'ignoreerrors': True,  # 개별 비디오 오류 무시
        'no_warnings': False,
        # 파일 저장 안전성 개선
        'restrictfilenames': True,  # 파일명 제한 (특수문자 제거)
        'windowsfilenames': False,  # Windows 파일명 규칙 비활성화
        # 네트워크 안정성 개선
        'socket_timeout': 60,
        'http_timeout': 60,
        'retries': 3,
        'sleep_interval': 1,
        'max_sleep_interval': 5,
    }

    # 다운로드 실행: yt-dlp 객체 생성 후 URL 입력
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🎬 플레이리스트 다운로드 시작: {playlist_url}")
            if playlist_id:
                print(f"📋 플레이리스트 ID: {playlist_id}")
            ydl.download([playlist_url])  # 플레이리스트 URL로 다운로드 시작
        print("✅ 다운로드 완료! 파일은 다음 경로에 저장되었습니다:", download_path)
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")  # 오류 발생 시 메시지 출력 (예: URL 잘못됨, 인터넷 문제)
        if playlist_id:
            print(f"💡 플레이리스트 ID를 확인해보세요: {playlist_id}")

# 메인 부분: 프로그램 실행 시 사용자 입력 받기
if __name__ == "__main__":
    print("유튜브 플레이리스트 다운로더에 오신 것을 환영합니다!")
    print("=" * 50)
    
    # 시스템 정보 표시
    try:
        system_info = get_system_info()
        print(f"💻 시스템: CPU {system_info['cpu_count']}코어, RAM {system_info['memory_gb']}GB")
        print(f"⚡ 권장 동시 다운로드: {system_info['recommended_workers']}개")
    except:
        print("⚠️ 시스템 정보를 가져올 수 없습니다. 기본 설정을 사용합니다.")
    
    # 사용자 입력: 플레이리스트 URL
    while True:
        playlist_url = input("다운로드할 유튜브 플레이리스트 URL을 입력하세요: ").strip()
        
        if not playlist_url:
            print("❌ URL을 입력해주세요.")
            continue
            
        if not validate_url(playlist_url):
            print("❌ 유효한 YouTube URL이 아닙니다.")
            continue
            
        if not playlist_url.startswith("https://www.youtube.com/playlist?"):
            print("⚠️ 플레이리스트 URL이 아닐 수 있습니다. (예: https://www.youtube.com/playlist?list=PLxxxx)")
            confirm = input("계속하시겠습니까? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
        
        break
    
    # 사용자 입력: 저장 경로
    download_path = input("파일을 저장할 폴더 경로를 입력하세요 (기본: ./download): ").strip()
    if not download_path:
        download_path = "./download"
    
    # 화질 선택
    quality_format = select_quality_format()
    
    # 다운로드 방식 선택
    print("\n다운로드 방식을 선택하세요:")
    print("1. 순차 다운로드 (안정적, 느림)")
    print("2. 병렬 다운로드 (빠름, 일부 실패 가능)")
    print("3. 🔥 MAX 모드 (최대 성능, 모든 자원 활용)")
    print("4. 💀🔥 극한 MAX 모드 (극한 성능, 모든 자원 극한 활용)")
    
    while True:
        choice = input("선택 (1, 2, 3, 또는 4): ").strip()
        if choice in ['1', '2', '3', '4']:
            break
        print("❌ 1, 2, 3, 또는 4를 입력해주세요.")
    
    # 워커 수 설정
    max_workers = 3
    if choice == '2':
        try:
            workers_input = input("동시 다운로드 수를 입력하세요 (기본: 3, 권장: 1-5): ").strip()
            if workers_input:
                max_workers = int(workers_input)
                if max_workers < 1:
                    max_workers = 1
                elif max_workers > 10:
                    max_workers = 10
        except ValueError:
            print("잘못된 입력입니다. 기본값 3을 사용합니다.")
    elif choice == '3':
        try:
            system_info = get_system_info()
            print(f"🔥 MAX 모드: 시스템에 최적화된 설정을 사용합니다.")
            print(f"💻 CPU {system_info['cpu_count']}코어, RAM {system_info['memory_gb']}GB")
            print(f"⚡ 권장 워커 수: {system_info['recommended_workers']}개")
            print(f"🚀 MAX 워커 수: {system_info['max_workers']}개")
            
            workers_input = input(f"동시 다운로드 수를 입력하세요 (권장: {system_info['recommended_workers']}, MAX: {system_info['max_workers']}): ").strip()
            if workers_input:
                max_workers = int(workers_input)
                if max_workers < 1:
                    max_workers = 1
                elif max_workers > 20:
                    max_workers = 20
            else:
                max_workers = system_info['max_workers']
        except ValueError:
            print("잘못된 입력입니다. 시스템 최적값을 사용합니다.")
            max_workers = system_info['max_workers']
    elif choice == '4':
        try:
            system_info = get_system_info()
            print(f"💀🔥 극한 MAX 모드: 모든 자원을 극한으로 활용합니다!")
            print(f"💻 CPU {system_info['cpu_count']}코어, RAM {system_info['memory_gb']}GB")
            print(f"⚡ 극한 워커 수: {system_info['recommended_workers']}개")
            print(f"🚀🔥 극한 MAX 워커 수: {system_info['max_workers']}개")
            print(f"🧠 메모리 보너스: +{system_info['memory_bonus']}개 워커")
            print("⚠️ 경고: 극한 성능으로 인한 시스템 부하가 발생할 수 있습니다!")
            print("💀 모든 자원을 극한으로 활용하여 최대 성능을 발휘합니다!")
            
            workers_input = input(f"동시 다운로드 수를 입력하세요 (극한: {system_info['recommended_workers']}, MAX: {system_info['max_workers']}): ").strip()
            if workers_input:
                max_workers = int(workers_input)
                if max_workers < 1:
                    max_workers = 1
                elif max_workers > 100:
                    max_workers = 100
            else:
                max_workers = system_info['max_workers']
        except ValueError:
            print("잘못된 입력입니다. 극한 시스템 최적값을 사용합니다.")
            max_workers = system_info['max_workers']
    
    print(f"\n🚀 다운로드를 시작합니다...")
    print(f"📁 저장 경로: {download_path}")
    print(f"🔗 플레이리스트: {playlist_url}")
    print(f"🎬 선택된 화질: {quality_format}")
    
    if choice == '1':
        print("📋 순차 다운로드 모드")
        download_playlist(playlist_url, download_path, quality_format)
    elif choice == '2':
        print(f"⚡ 병렬 다운로드 모드 (최대 {max_workers}개 동시)")
        download_playlist_parallel(playlist_url, download_path, max_workers, quality_format)
    elif choice == '3':
        print(f"🔥 MAX 모드 (최대 {max_workers}개 동시, 모든 성능 활용)")
        download_playlist_max(playlist_url, download_path, max_workers, quality_format)
    else:
        print(f"💀🔥 극한 MAX 모드 (최대 {max_workers}개 동시, 모든 자원 극한 활용)")
        print("💀 모든 자원을 극한으로 활용하여 최대 성능을 발휘합니다!")
        download_playlist_extreme_max(playlist_url, download_path, max_workers, quality_format)