import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import sys
from datetime import datetime, timedelta
import time

# 기존 다운로더 모듈 임포트
from youtube_playlist_downloader import (
    get_system_info, validate_url, get_playlist_videos,
    download_single_video_extreme_max, download_single_video_max, download_single_video,
    download_playlist_extreme_max, download_playlist_max, download_playlist_parallel, download_playlist
)

class ModernYouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # macOS 스타일 설정
        self.setup_macos_style()
        
        # 다운로드 진행 상황 추적
        self.download_progress = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'start_time': None,
            'is_downloading': False,
            'lock': threading.Lock() # 스레드 안전한 진행률 업데이트를 위한 락
        }
        
        # 메시지 큐 (스레드 간 통신)
        self.message_queue = queue.Queue()
        
        # GUI 초기화
        self.setup_gui()
        self.update_gui()
        
    def setup_macos_style(self):
        """macOS 스타일 설정"""
        # 창 스타일
        self.root.configure(bg='#f5f5f7')
        
        # 스타일 설정
        style = ttk.Style()
        style.theme_use('aqua')  # macOS 네이티브 테마
        
        # 커스텀 스타일 정의
        style.configure('Title.TLabel', font=('SF Pro Display', 24, 'bold'), foreground='#1d1d1f')
        style.configure('Subtitle.TLabel', font=('SF Pro Text', 14), foreground='#86868b')
        style.configure('Section.TLabelframe', font=('SF Pro Text', 12, 'bold'), foreground='#1d1d1f')
        style.configure('Section.TLabelframe.Label', font=('SF Pro Text', 12, 'bold'), foreground='#1d1d1f')
        style.configure('Modern.TButton', font=('SF Pro Text', 12), padding=(20, 8))
        style.configure('Primary.TButton', font=('SF Pro Text', 12, 'bold'), padding=(20, 10))
        style.configure('Success.TButton', font=('SF Pro Text', 12), padding=(15, 8))
        style.configure('Info.TLabel', font=('SF Pro Text', 11), foreground='#86868b')
        
        # Radiobutton 스타일 추가
        style.configure('Quality.TRadiobutton', font=('SF Pro Text', 11))
        style.configure('Mode.TRadiobutton', font=('SF Pro Text', 11, 'bold'))
        
    def setup_gui(self):
        """GUI 구성 요소 설정"""
        # 메인 컨테이너
        main_container = ttk.Frame(self.root, padding="20")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 헤더 섹션
        self.setup_header(main_container)
        
        # 메인 콘텐츠 영역
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        
        # 왼쪽 패널 (설정)
        left_panel = ttk.Frame(content_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 오른쪽 패널 (진행률 및 로그)
        right_panel = ttk.Frame(content_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 왼쪽 패널 구성
        self.setup_left_panel(left_panel)
        
        # 오른쪽 패널 구성
        self.setup_right_panel(right_panel)
        
        # 하단 버튼 영역
        self.setup_bottom_buttons(main_container)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
    def setup_header(self, parent):
        """헤더 섹션"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 앱 제목
        title_label = ttk.Label(header_frame, text="YouTube Downloader", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 부제목
        subtitle_label = ttk.Label(header_frame, text="고성능 YouTube 플레이리스트 다운로더", style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 시스템 정보 (우측)
        try:
            system_info = get_system_info()
            info_text = f"CPU {system_info['cpu_count']}코어 • RAM {system_info['memory_gb']}GB"
            system_label = ttk.Label(header_frame, text=info_text, style='Info.TLabel')
            system_label.grid(row=0, column=1, rowspan=2, sticky=(tk.E, tk.N), padx=(20, 0))
        except:
            pass
        
        header_frame.columnconfigure(0, weight=1)
        
    def setup_left_panel(self, parent):
        """왼쪽 패널 (설정)"""
        # URL 입력
        self.setup_url_section(parent)
        
        # 저장 경로
        self.setup_path_section(parent)
        
        # 화질 선택
        self.setup_quality_section(parent)
        
        # 다운로드 모드
        self.setup_mode_section(parent)
        
        # 고급 설정
        self.setup_advanced_section(parent)
        
    def setup_url_section(self, parent):
        """URL 입력 섹션"""
        url_frame = ttk.LabelFrame(parent, text="YouTube URL", style='Section.TLabelframe', padding="15")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # URL 입력 필드
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=40)
        url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 검증 버튼
        validate_btn = ttk.Button(url_frame, text="검증", style='Success.TButton', command=self.validate_url)
        validate_btn.grid(row=0, column=1)
        
        # 도움말 텍스트
        help_text = "플레이리스트 URL 또는 단일 비디오 URL을 입력하세요"
        help_label = ttk.Label(url_frame, text=help_text, style='Info.TLabel')
        help_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        
        url_frame.columnconfigure(0, weight=1)
        
    def setup_path_section(self, parent):
        """저장 경로 섹션"""
        path_frame = ttk.LabelFrame(parent, text="저장 위치", style='Section.TLabelframe', padding="15")
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 경로 입력 필드
        self.path_var = tk.StringVar(value=os.path.abspath("./download"))
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=35)
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 찾아보기 버튼
        browse_btn = ttk.Button(path_frame, text="찾아보기", style='Success.TButton', command=self.browse_path)
        browse_btn.grid(row=0, column=1)
        
        path_frame.columnconfigure(0, weight=1)
        
    def setup_quality_section(self, parent):
        """화질 선택 섹션"""
        quality_frame = ttk.LabelFrame(parent, text="화질 선택", style='Section.TLabelframe', padding="15")
        quality_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.quality_var = tk.StringVar(value="auto")
        
        # 화질 옵션들
        quality_options = [
            ("🎯 자동 선택 (권장)", "auto"),
            ("🏆 최고 화질", "best"),
            ("📺 1080p", "1080p"),
            ("📺 720p", "720p"),
            ("📺 480p", "480p"),
            ("📺 360p", "360p")
        ]
        
        for i, (text, value) in enumerate(quality_options):
            row = i // 2
            col = i % 2
            ttk.Radiobutton(quality_frame, text=text, variable=self.quality_var, 
                           value=value, style='Quality.TRadiobutton').grid(
                row=row, column=col, sticky=tk.W, padx=(0, 20), pady=2)
        
    def setup_mode_section(self, parent):
        """다운로드 모드 섹션"""
        mode_frame = ttk.LabelFrame(parent, text="다운로드 모드", style='Section.TLabelframe', padding="15")
        mode_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.mode_var = tk.StringVar(value="balanced")
        
        # 모드 옵션들
        mode_options = [
            ("⚡ 균형 모드 (권장)", "balanced", "안정적이고 빠른 다운로드"),
            ("🚀 고성능 모드", "performance", "최대 성능으로 빠른 다운로드"),
            ("🔥 극한 모드", "extreme", "모든 자원을 활용한 극한 성능"),
            ("🛡️ 안정 모드", "stable", "안정적인 순차 다운로드")
        ]
        
        for i, (text, value, description) in enumerate(mode_options):
            # 라디오 버튼
            ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var, 
                           value=value, style='Mode.TRadiobutton').grid(
                row=i, column=0, sticky=tk.W, pady=(5, 0))
            
            # 설명 텍스트
            desc_label = ttk.Label(mode_frame, text=description, style='Info.TLabel')
            desc_label.grid(row=i, column=0, sticky=tk.W, padx=(25, 0), pady=(0, 5))
        
    def setup_advanced_section(self, parent):
        """고급 설정 섹션"""
        advanced_frame = ttk.LabelFrame(parent, text="고급 설정", style='Section.TLabelframe', padding="15")
        advanced_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 동시 다운로드 수
        ttk.Label(advanced_frame, text="동시 다운로드 수:", style='Info.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.worker_var = tk.StringVar(value="3")
        worker_entry = ttk.Entry(advanced_frame, textvariable=self.worker_var, width=8)
        worker_entry.grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        
        self.worker_label = ttk.Label(advanced_frame, text="(권장: 3-5)", style='Info.TLabel')
        self.worker_label.grid(row=1, column=1, sticky=tk.W)
        
        # 모드 변경 시 워커 수 업데이트
        self.mode_var.trace_add('write', self.update_worker_count)
        
    def setup_right_panel(self, parent):
        """오른쪽 패널 (진행률 및 로그)"""
        # 진행률 섹션
        self.setup_progress_section(parent)
        
        # 로그 섹션
        self.setup_log_section(parent)
        
    def setup_progress_section(self, parent):
        """진행률 섹션"""
        progress_frame = ttk.LabelFrame(parent, text="다운로드 진행률", style='Section.TLabelframe', padding="15")
        progress_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400, mode='determinate')
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 진행률 퍼센트 표시
        self.progress_percent = tk.StringVar(value="0%")
        percent_label = ttk.Label(progress_frame, textvariable=self.progress_percent, 
                                style='Info.TLabel', font=('SF Pro Text', 12, 'bold'))
        percent_label.grid(row=0, column=2, padx=(10, 0))
        
        # 진행 상황 텍스트
        self.progress_text = tk.StringVar(value="대기 중...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_text, 
                                      style='Info.TLabel')
        self.progress_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # 예상 완료 시간
        self.eta_text = tk.StringVar(value="")
        self.eta_label = ttk.Label(progress_frame, textvariable=self.eta_text, style='Info.TLabel')
        self.eta_label.grid(row=2, column=0, columnspan=3, sticky=tk.W)
        
        # 통계 정보
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_text = tk.StringVar(value="")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_text, style='Info.TLabel')
        stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 속도 정보
        self.speed_text = tk.StringVar(value="")
        speed_label = ttk.Label(stats_frame, textvariable=self.speed_text, style='Info.TLabel')
        speed_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        progress_frame.columnconfigure(0, weight=1)
        
    def setup_log_section(self, parent):
        """로그 섹션"""
        log_frame = ttk.LabelFrame(parent, text="다운로드 로그", style='Section.TLabelframe', padding="15")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 로그 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=12, 
            width=60,
            font=('SF Mono', 10),
            bg='#ffffff',
            fg='#1d1d1f',
            insertbackground='#007aff',
            selectbackground='#007aff',
            selectforeground='#ffffff',
            relief='flat',
            borderwidth=0
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def setup_bottom_buttons(self, parent):
        """하단 버튼 영역"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, pady=(20, 0))
        
        # 시작 버튼
        self.start_btn = ttk.Button(button_frame, text="다운로드 시작", 
                                   style='Primary.TButton', command=self.start_download)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        # 중지 버튼
        self.stop_btn = ttk.Button(button_frame, text="중지", 
                                  style='Modern.TButton', command=self.stop_download, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        # 로그 지우기 버튼
        self.clear_btn = ttk.Button(button_frame, text="로그 지우기", 
                                   style='Modern.TButton', command=self.clear_log)
        self.clear_btn.grid(row=0, column=2)
        
    def validate_url(self):
        """URL 검증"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("오류", "URL을 입력해주세요.")
            return
        
        if not validate_url(url):
            messagebox.showerror("오류", "유효한 YouTube URL이 아닙니다.")
            return
        
        self.log_message("✅ URL 검증 완료")
        messagebox.showinfo("성공", "URL이 유효합니다!")
    
    def browse_path(self):
        """저장 경로 선택"""
        path = filedialog.askdirectory(title="저장할 폴더 선택")
        if path:
            self.path_var.set(path)
    
    def update_worker_count(self, *args):
        """모드 변경 시 워커 수 업데이트"""
        mode = self.mode_var.get()
        try:
            system_info = get_system_info()
            if mode == "balanced":
                self.worker_var.set("3")
                self.worker_label.config(text="(권장: 2-4)")
            elif mode == "performance":
                self.worker_var.set(str(min(system_info['recommended_workers'], 8)))
                self.worker_label.config(text=f"(권장: {system_info['recommended_workers']})")
            elif mode == "extreme":
                self.worker_var.set(str(system_info['max_workers']))
                self.worker_label.config(text=f"(극한: {system_info['max_workers']})")
            else:  # stable
                self.worker_var.set("1")
                self.worker_label.config(text="(순차 다운로드)")
        except:
            pass
    
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 메시지 큐에 추가 (스레드 안전)
        self.message_queue.put(("log", log_entry))
    
    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
    
    def start_download(self):
        """다운로드 시작"""
        if self.download_progress['is_downloading']:
            messagebox.showwarning("경고", "이미 다운로드가 진행 중입니다.")
            return
        
        # 입력 검증
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("오류", "URL을 입력해주세요.")
            return
        
        if not validate_url(url):
            messagebox.showerror("오류", "유효한 YouTube URL이 아닙니다.")
            return
        
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("오류", "저장 경로를 입력해주세요.")
            return
        
        # 워커 수 검증
        try:
            workers = int(self.worker_var.get())
            if workers < 1:
                messagebox.showerror("오류", "워커 수는 1 이상이어야 합니다.")
                return
        except ValueError:
            messagebox.showerror("오류", "올바른 워커 수를 입력해주세요.")
            return
        
        # 화질 선택
        quality_map = {
            'auto': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
            '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
            '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
            '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'
        }
        quality_format = quality_map.get(self.quality_var.get(), quality_map['auto'])
        
        # 진행률 초기화
        self.progress_var.set(0)
        self.progress_percent.set("0%")
        self.progress_text.set("다운로드 준비 중...")
        self.eta_text.set("")
        self.stats_text.set("")
        self.speed_text.set("")
        
        # 다운로드 시작
        self.download_progress['is_downloading'] = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # 다운로드 스레드 시작
        download_thread = threading.Thread(
            target=self.download_worker,
            args=(url, path, quality_format, workers, self.mode_var.get())
        )
        download_thread.daemon = True
        download_thread.start()
        
        self.log_message("🚀 다운로드를 시작합니다...")
    
    def stop_download(self):
        """다운로드 중지"""
        self.download_progress['is_downloading'] = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress_text.set("다운로드 중지됨")
        self.eta_text.set("")
        self.speed_text.set("")
        self.log_message("⏹️ 다운로드가 중지되었습니다.")
    
    def download_worker(self, url, path, quality_format, workers, mode):
        """다운로드 작업 스레드"""
        try:
            # 플레이리스트 정보 가져오기
            self.message_queue.put(("progress_text", "플레이리스트 정보를 가져오는 중..."))
            videos = get_playlist_videos(url)
            
            if not videos:
                self.message_queue.put(("error", "플레이리스트에서 비디오를 찾을 수 없습니다."))
                return
            
            # 진행 상황 초기화
            self.download_progress['total'] = len(videos)
            self.download_progress['completed'] = 0
            self.download_progress['failed'] = 0
            self.download_progress['start_time'] = time.time()
            
            self.message_queue.put(("log", f"총 {len(videos)}개의 비디오를 발견했습니다.\n"))
            
            # 다운로드 경로를 절대 경로로 변환하고 생성
            path = os.path.abspath(path)
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    self.message_queue.put(("log", f"📁 다운로드 경로 생성: {path}\n"))
                except Exception as e:
                    self.message_queue.put(("error", f"다운로드 경로 생성 실패: {e}"))
                    return
            
            # 진행률 콜백 함수 정의
            def progress_callback(current, total, success=True):
                """진행률 업데이트 콜백"""
                with self.download_progress['lock'] if hasattr(self.download_progress, 'lock') else threading.Lock():
                    if success:
                        self.download_progress['completed'] += 1
                    else:
                        self.download_progress['failed'] += 1
                
                # GUI 업데이트를 위한 메시지 전송
                self.message_queue.put(("progress_update", {
                    'current': current,
                    'total': total,
                    'success': success
                }))
                
                # 진행률 텍스트 업데이트
                if success:
                    self.message_queue.put(("progress_text", f"다운로드 중... ({current}/{total})"))
                else:
                    self.message_queue.put(("progress_text", f"실패 처리 중... ({current}/{total})"))
                
                # 통계 업데이트
                completed = self.download_progress['completed']
                failed = self.download_progress['failed']
                stats = f"완료: {completed} | 실패: {failed} | 총: {total}"
                self.message_queue.put(("stats_update", stats))
                
                # 예상 완료 시간 계산
                if self.download_progress['start_time'] and (completed + failed) > 0:
                    elapsed = time.time() - self.download_progress['start_time']
                    avg_time = elapsed / (completed + failed)
                    remaining = total - (completed + failed)
                    eta_seconds = avg_time * remaining
                    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                    self.message_queue.put(("eta", eta_time.strftime('%H:%M:%S')))
            
            # 다운로드 모드에 따른 함수 선택
            if mode == "stable":
                self.message_queue.put(("log", "📋 안정 모드 - 순차 다운로드\n"))
                # 순차 다운로드의 경우 각 비디오마다 진행률 업데이트
                for i, video in enumerate(videos):
                    try:
                        result = download_single_video(video['url'], path, video, quality_format)
                        progress_callback(i + 1, len(videos), result['success'])
                        if result['success']:
                            self.message_queue.put(("log", f"✅ {result['title']}\n"))
                        else:
                            self.message_queue.put(("log", f"❌ {result['title']} - {result['error']}\n"))
                    except Exception as e:
                        progress_callback(i + 1, len(videos), False)
                        self.message_queue.put(("log", f"❌ {video['title']} - 오류: {str(e)}\n"))
                        
            elif mode == "balanced":
                self.message_queue.put(("log", f"⚖️ 균형 모드 - 병렬 다운로드 (최대 {workers}개 동시)\n"))
                download_playlist_parallel(url, path, workers, quality_format, progress_callback)
                
            elif mode == "performance":
                self.message_queue.put(("log", f"🚀 고성능 모드 - MAX 다운로드 (최대 {workers}개 동시)\n"))
                download_playlist_max(url, path, workers, quality_format, progress_callback)
                
            else:  # extreme
                self.message_queue.put(("log", f"🔥 극한 모드 - 극한 MAX 다운로드 (최대 {workers}개 동시)\n"))
                download_playlist_extreme_max(url, path, workers, quality_format, progress_callback)
            
            # 완료 메시지
            elapsed_time = time.time() - self.download_progress['start_time']
            self.message_queue.put(("log", f"✅ 다운로드 완료! 소요 시간: {self.format_duration(elapsed_time)}\n"))
            
        except Exception as e:
            self.message_queue.put(("error", f"다운로드 중 오류 발생: {str(e)}"))
        finally:
            self.download_progress['is_downloading'] = False
            self.message_queue.put(("download_complete", None))
    
    def format_duration(self, seconds):
        """초를 시:분:초 형식으로 변환"""
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
    
    def update_gui(self):
        """GUI 업데이트"""
        try:
            # 메시지 큐 처리
            while True:
                try:
                    msg_type, msg_data = self.message_queue.get_nowait()
                    
                    if msg_type == "log":
                        self.log_text.insert(tk.END, msg_data)
                        self.log_text.see(tk.END)
                    elif msg_type == "progress_text":
                        self.progress_text.set(msg_data)
                    elif msg_type == "progress_update":
                        # 진행률 업데이트
                        current = msg_data['current']
                        total = msg_data['total']
                        progress = (current / total) * 100 if total > 0 else 0
                        self.progress_var.set(progress)
                        self.progress_percent.set(f"{progress:.0f}%")
                    elif msg_type == "stats_update":
                        self.stats_text.set(msg_data)
                    elif msg_type == "eta":
                        self.eta_text.set(f"예상 완료: {msg_data}")
                    elif msg_type == "error":
                        messagebox.showerror("오류", msg_data)
                    elif msg_type == "download_complete":
                        self.start_btn.config(state="normal")
                        self.stop_btn.config(state="disabled")
                        self.progress_text.set("다운로드 완료!")
                        self.progress_percent.set("100%")
                        self.progress_var.set(100)
                        self.eta_text.set("")
                        self.speed_text.set("")
                        
                        # 완료 통계 표시
                        completed = self.download_progress['completed']
                        failed = self.download_progress['failed']
                        total = self.download_progress['total']
                        if total > 0:
                            success_rate = (completed / total) * 100
                            self.stats_text.set(f"완료: {completed} | 실패: {failed} | 성공률: {success_rate:.1f}%")
                        
                except queue.Empty:
                    break
            
            # 진행률 업데이트 (백업 로직)
            if self.download_progress['is_downloading'] and self.download_progress['total'] > 0:
                completed = self.download_progress['completed'] + self.download_progress['failed']
                progress = (completed / self.download_progress['total']) * 100
                self.progress_var.set(progress)
                self.progress_percent.set(f"{progress:.0f}%")
                
                # 통계 업데이트
                stats = f"완료: {self.download_progress['completed']} | 실패: {self.download_progress['failed']} | 총: {self.download_progress['total']}"
                self.stats_text.set(stats)
                
                # 예상 완료 시간 계산
                if self.download_progress['start_time'] and completed > 0:
                    elapsed = time.time() - self.download_progress['start_time']
                    avg_time = elapsed / completed
                    remaining = self.download_progress['total'] - completed
                    eta_seconds = avg_time * remaining
                    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                    self.eta_text.set(f"예상 완료: {eta_time.strftime('%H:%M:%S')}")
                    
                    # 다운로드 속도 계산 (초당 비디오 수)
                    if elapsed > 0:
                        speed = completed / elapsed
                        self.speed_text.set(f"속도: {speed:.1f} 비디오/초")
            
        except Exception as e:
            print(f"GUI 업데이트 오류: {e}")
        
        # 50ms마다 업데이트 (더 빠른 응답성)
        self.root.after(50, self.update_gui)

def main():
    """메인 함수"""
    root = tk.Tk()
    
    # 앱 생성
    app = ModernYouTubeDownloaderGUI(root)
    
    # GUI 실행
    root.mainloop()

if __name__ == "__main__":
    main()
