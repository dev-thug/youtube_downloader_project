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

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Playlist Downloader - 극한 성능")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 다운로드 진행 상황 추적
        self.download_progress = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'start_time': None,
            'is_downloading': False
        }
        
        # 메시지 큐 (스레드 간 통신)
        self.message_queue = queue.Queue()
        
        # GUI 초기화
        self.setup_gui()
        self.update_gui()
        
    def setup_gui(self):
        """GUI 구성 요소 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="YouTube Playlist Downloader", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 시스템 정보
        self.setup_system_info(main_frame)
        
        # URL 입력
        self.setup_url_input(main_frame)
        
        # 저장 경로
        self.setup_save_path(main_frame)
        
        # 화질 선택
        self.setup_quality_selection(main_frame)
        
        # 다운로드 모드 선택
        self.setup_download_mode(main_frame)
        
        # 워커 수 설정
        self.setup_worker_count(main_frame)
        
        # 진행률 표시
        self.setup_progress_display(main_frame)
        
        # 로그 표시
        self.setup_log_display(main_frame)
        
        # 버튼들
        self.setup_buttons(main_frame)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)  # 로그 영역 확장
        
    def setup_system_info(self, parent):
        """시스템 정보 표시"""
        system_frame = ttk.LabelFrame(parent, text="시스템 정보", padding="5")
        system_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        try:
            system_info = get_system_info()
            info_text = f"CPU: {system_info['cpu_count']}코어 | RAM: {system_info['memory_gb']}GB | 권장 워커: {system_info['recommended_workers']}개"
            self.system_label = ttk.Label(system_frame, text=info_text)
            self.system_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        except:
            self.system_label = ttk.Label(system_frame, text="시스템 정보를 가져올 수 없습니다.")
            self.system_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def setup_url_input(self, parent):
        """URL 입력 영역"""
        url_frame = ttk.LabelFrame(parent, text="플레이리스트 URL", padding="5")
        url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # URL 검증 버튼
        self.validate_btn = ttk.Button(url_frame, text="검증", command=self.validate_url)
        self.validate_btn.grid(row=0, column=1)
        
        url_frame.columnconfigure(0, weight=1)
    
    def setup_save_path(self, parent):
        """저장 경로 설정"""
        path_frame = ttk.LabelFrame(parent, text="저장 경로", padding="5")
        path_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.path_var = tk.StringVar(value="./download")
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.browse_btn = ttk.Button(path_frame, text="찾아보기", command=self.browse_path)
        self.browse_btn.grid(row=0, column=1)
        
        path_frame.columnconfigure(0, weight=1)
    
    def setup_quality_selection(self, parent):
        """화질 선택"""
        quality_frame = ttk.LabelFrame(parent, text="화질 선택", padding="5")
        quality_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.quality_var = tk.StringVar(value="9")
        quality_options = [
            ("최고 화질 (bestvideo+bestaudio)", "1"),
            ("1080p", "2"),
            ("720p", "3"),
            ("480p", "4"),
            ("360p", "5"),
            ("240p", "6"),
            ("144p", "7"),
            ("최적 화질 (best)", "8"),
            ("자동 선택 (권장)", "9")
        ]
        
        for i, (text, value) in enumerate(quality_options):
            ttk.Radiobutton(quality_frame, text=text, variable=self.quality_var, 
                           value=value).grid(row=i//3, column=i%3, sticky=tk.W, padx=5)
    
    def setup_download_mode(self, parent):
        """다운로드 모드 선택"""
        mode_frame = ttk.LabelFrame(parent, text="다운로드 모드", padding="5")
        mode_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="3")
        mode_options = [
            ("순차 다운로드 (안정적, 느림)", "1"),
            ("병렬 다운로드 (빠름, 일부 실패 가능)", "2"),
            ("🔥 MAX 모드 (최대 성능, 모든 자원 활용)", "3"),
            ("💀🔥 극한 MAX 모드 (극한 성능, 모든 자원 극한 활용)", "4")
        ]
        
        for i, (text, value) in enumerate(mode_options):
            ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var, 
                           value=value).grid(row=i, column=0, sticky=tk.W, padx=5)
    
    def setup_worker_count(self, parent):
        """워커 수 설정"""
        worker_frame = ttk.LabelFrame(parent, text="동시 다운로드 수", padding="5")
        worker_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.worker_var = tk.StringVar(value="3")
        self.worker_entry = ttk.Entry(worker_frame, textvariable=self.worker_var, width=10)
        self.worker_entry.grid(row=0, column=0, padx=(0, 10))
        
        self.worker_label = ttk.Label(worker_frame, text="(기본값: 3)")
        self.worker_label.grid(row=0, column=1)
        
        # 모드 변경 시 워커 수 업데이트
        self.mode_var.trace('w', self.update_worker_count)
    
    def setup_progress_display(self, parent):
        """진행률 표시"""
        progress_frame = ttk.LabelFrame(parent, text="다운로드 진행률", padding="5")
        progress_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 진행 상황 텍스트
        self.progress_text = tk.StringVar(value="대기 중...")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_text)
        self.progress_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 예상 완료 시간
        self.eta_text = tk.StringVar(value="")
        self.eta_label = ttk.Label(progress_frame, textvariable=self.eta_text)
        self.eta_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        progress_frame.columnconfigure(0, weight=1)
    
    def setup_log_display(self, parent):
        """로그 표시"""
        log_frame = ttk.LabelFrame(parent, text="다운로드 로그", padding="5")
        log_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 로그 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def setup_buttons(self, parent):
        """버튼들"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(10, 0))
        
        self.start_btn = ttk.Button(button_frame, text="다운로드 시작", 
                                   command=self.start_download, style="Accent.TButton")
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="중지", 
                                  command=self.stop_download, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.clear_btn = ttk.Button(button_frame, text="로그 지우기", 
                                   command=self.clear_log)
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
        
        if not url.startswith("https://www.youtube.com/playlist?"):
            result = messagebox.askyesno("경고", 
                                       "플레이리스트 URL이 아닐 수 있습니다.\n계속하시겠습니까?")
            if not result:
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
            if mode == "2":  # 병렬 다운로드
                self.worker_var.set("3")
                self.worker_label.config(text="(권장: 1-5)")
            elif mode == "3":  # MAX 모드
                self.worker_var.set(str(system_info['max_workers']))
                self.worker_label.config(text=f"(권장: {system_info['recommended_workers']}, MAX: {system_info['max_workers']})")
            elif mode == "4":  # 극한 MAX 모드
                self.worker_var.set(str(system_info['max_workers']))
                self.worker_label.config(text=f"(극한: {system_info['recommended_workers']}, MAX: {system_info['max_workers']})")
            else:  # 순차 다운로드
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
        quality_format = quality_map.get(self.quality_var.get(), quality_map['9'])
        
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
            
            # 다운로드 경로 생성
            if not os.path.exists(path):
                os.makedirs(path)
            
            # 다운로드 모드에 따른 함수 선택
            if mode == "1":
                self.message_queue.put(("log", "📋 순차 다운로드 모드\n"))
                download_func = download_playlist
                download_args = (url, path, quality_format)
            elif mode == "2":
                self.message_queue.put(("log", f"⚡ 병렬 다운로드 모드 (최대 {workers}개 동시)\n"))
                download_func = download_playlist_parallel
                download_args = (url, path, workers, quality_format)
            elif mode == "3":
                self.message_queue.put(("log", f"🔥 MAX 모드 (최대 {workers}개 동시, 모든 성능 활용)\n"))
                download_func = download_playlist_max
                download_args = (url, path, workers, quality_format)
            else:  # mode == "4"
                self.message_queue.put(("log", f"💀🔥 극한 MAX 모드 (최대 {workers}개 동시, 모든 자원 극한 활용)\n"))
                download_func = download_playlist_extreme_max
                download_args = (url, path, workers, quality_format)
            
            # 다운로드 실행
            download_func(*download_args)
            
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
                    elif msg_type == "progress":
                        self.progress_var.set(msg_data)
                    elif msg_type == "eta":
                        self.eta_text.set(f"예상 완료: {msg_data}")
                    elif msg_type == "error":
                        messagebox.showerror("오류", msg_data)
                    elif msg_type == "download_complete":
                        self.start_btn.config(state="normal")
                        self.stop_btn.config(state="disabled")
                        self.progress_text.set("완료!")
                        self.eta_text.set("")
                        
                except queue.Empty:
                    break
            
            # 진행률 업데이트
            if self.download_progress['is_downloading'] and self.download_progress['total'] > 0:
                completed = self.download_progress['completed'] + self.download_progress['failed']
                progress = (completed / self.download_progress['total']) * 100
                self.progress_var.set(progress)
                
                # 예상 완료 시간 계산
                if self.download_progress['start_time'] and completed > 0:
                    elapsed = time.time() - self.download_progress['start_time']
                    avg_time = elapsed / completed
                    remaining = self.download_progress['total'] - completed
                    eta_seconds = avg_time * remaining
                    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                    self.eta_text.set(f"예상 완료: {eta_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"GUI 업데이트 오류: {e}")
        
        # 100ms마다 업데이트
        self.root.after(100, self.update_gui)

def main():
    """메인 함수"""
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    # 앱 생성
    app = YouTubeDownloaderGUI(root)
    
    # GUI 실행
    root.mainloop()

if __name__ == "__main__":
    main()
