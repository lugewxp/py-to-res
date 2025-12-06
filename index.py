import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import urljoin
import threading
import os
import re
import webbrowser
import pygame
import tempfile
import time

class WebContentExtractor:
    def __init__(self):
        self.images_list = []
        self.videos_list = []
        self.video_player = None
        self.root = None
        self.setup_ui()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("网页内容提取器 v3.0")
        self.root.geometry("1100x850")
        
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        url_label = ttk.Label(frame, text="网页URL:")
        url_label.pack(anchor=tk.W)
        
        self.url_entry = ttk.Entry(frame, width=80)
        self.url_entry.pack(pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5)
        
        fetch_button = ttk.Button(button_frame, text="获取网页内容", command=self.fetch_webpage)
        fetch_button.pack(side=tk.LEFT, padx=5)
        
        download_video_button = ttk.Button(button_frame, text="下载选中视频", command=self.download_video)
        download_video_button.pack(side=tk.LEFT, padx=5)
        
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        text_frame = self.create_text_tab(notebook)
        notebook.add(text_frame, text="网页文字")
        
        image_frame = self.create_image_tab(notebook)
        notebook.add(image_frame, text="图片列表")
        
        video_frame = self.create_video_tab(notebook)
        notebook.add(video_frame, text="视频列表")
        
        self.status_label = ttk.Label(frame, text="就绪")
        self.status_label.pack(pady=5)
        
        pygame.init()
    
    def create_text_tab(self, notebook):
        text_frame = ttk.Frame(notebook)
        
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_display = tk.Text(text_frame, height=20, wrap=tk.WORD, yscrollcommand=text_scroll.set)
        self.text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_display.config(state=tk.DISABLED)
        text_scroll.config(command=self.text_display.yview)
        
        return text_frame
    
    def create_image_tab(self, notebook):
        image_frame = ttk.Frame(notebook)
        
        image_list_frame = ttk.Frame(image_frame)
        image_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        image_scroll = ttk.Scrollbar(image_list_frame)
        image_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(image_list_frame, height=15, yscrollcommand=image_scroll.set)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        image_scroll.config(command=self.image_listbox.yview)
        
        show_button = ttk.Button(image_frame, text="查看选中图片", command=self.show_image)
        show_button.pack(pady=5)
        
        return image_frame
    
    def create_video_tab(self, notebook):
        video_frame = ttk.Frame(notebook)
        
        video_list_frame = ttk.Frame(video_frame)
        video_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        video_scroll = ttk.Scrollbar(video_list_frame)
        video_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox = tk.Listbox(video_list_frame, height=15, yscrollcommand=video_scroll.set)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        video_scroll.config(command=self.video_listbox.yview)
        
        button_frame = ttk.Frame(video_frame)
        button_frame.pack(pady=5)
        
        preview_button = ttk.Button(button_frame, text="内嵌播放MP4", command=self.play_video_embedded)
        preview_button.pack(side=tk.LEFT, padx=5)
        
        external_button = ttk.Button(button_frame, text="外部播放器", command=self.play_video_external)
        external_button.pack(side=tk.LEFT, padx=5)
        
        return video_frame
    
    def fetch_webpage(self):
        url = self.url_entry.get()
        if not url:
            self.status_label.config(text="错误: 请输入URL")
            return
        
        self.status_label.config(text="正在加载网页...")
        threading.Thread(target=self._load_webpage, args=(url,)).start()
    
    def _load_webpage(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            self._extract_text_content(soup)
            self._extract_image_info(soup, url)
            self._extract_video_info(soup, url)
            
            self.root.after(0, lambda: self.status_label.config(
                text=f"加载完成。找到 {len(self.images_list)} 张图片，{len(self.videos_list)} 个视频"
            ))
            
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: self.status_label.config(text=f"网络请求错误: {e}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"发生错误: {e}"))
    
    def _extract_text_content(self, soup):
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        self.root.after(0, self._update_text_display, clean_text)
    
    def _update_text_display(self, text):
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(1.0, text)
        self.text_display.config(state=tk.DISABLED)
    
    def _extract_image_info(self, soup, base_url):
        self.images_list = []
        images = soup.find_all('img')
        
        for img in images:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urljoin(base_url, img_url)
                img_alt = img.get('alt', '无描述')
                self.images_list.append((img_url, img_alt))
        
        self.root.after(0, self._update_image_listbox)
    
    def _update_image_listbox(self):
        self.image_listbox.delete(0, tk.END)
        for i, (img_url, img_alt) in enumerate(self.images_list, 1):
            display_text = f"{i}. {img_alt[:30]}{'...' if len(img_alt) > 30 else ''}"
            self.image_listbox.insert(tk.END, display_text)
    
    def _extract_video_info(self, soup, base_url):
        self.videos_list = []
        
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src')
            if src:
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                if self._is_video_url(src):
                    title = video.get('title', video.get('alt', '无标题'))
                    self.videos_list.append((src, title, 'direct'))
            
            source_tags = video.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    if not src.startswith(('http://', 'https://')):
                        src = urljoin(base_url, src)
                    if self._is_video_url(src):
                        title = source.get('title', '无标题')
                        self.videos_list.append((src, title, 'direct'))
        
        iframe_tags = soup.find_all('iframe')
        for iframe in iframe_tags:
            src = iframe.get('src')
            if src:
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                title = iframe.get('title', '视频嵌入')
                if 'youtube.com' in src or 'youtu.be' in src:
                    self.videos_list.append((src, title, 'youtube'))
                elif 'bilibili.com' in src:
                    self.videos_list.append((src, title, 'bilibili'))
                elif 'vimeo.com' in src:
                    self.videos_list.append((src, title, 'vimeo'))
        
        a_tags = soup.find_all('a', href=True)
        for a in a_tags:
            href = a['href']
            if self._is_video_url(href):
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                title = a.get_text(strip=True)
                if not title:
                    title = '视频链接'
                self.videos_list.append((href, title, 'direct'))
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_text = script.string
                video_urls = re.findall(r'https?://[^\s<>"]+\.(mp4|webm|avi|mov|flv|wmv|m4v|mkv)', script_text, re.IGNORECASE)
                for url in video_urls:
                    if self._is_video_url(url):
                        self.videos_list.append((url, '脚本中的视频', 'direct'))
        
        self.root.after(0, self._update_video_listbox)
    
    def _is_video_url(self, url):
        video_extensions = ['.mp4', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.mkv']
        for ext in video_extensions:
            if ext in url.lower():
                return True
        return False
    
    def _update_video_listbox(self):
        self.video_listbox.delete(0, tk.END)
        for i, (video_url, title, vtype) in enumerate(self.videos_list, 1):
            type_icon = {
                'direct': '[MP4]',
                'youtube': '[YT]',
                'bilibili': '[B站]',
                'vimeo': '[VM]'
            }.get(vtype, '[VID]')
            display_text = f"{i}. {type_icon} {title[:30]}{'...' if len(title) > 30 else ''}"
            self.video_listbox.insert(tk.END, display_text)
    
    def show_image(self):
        selection = self.image_listbox.curselection()
        if not selection:
            self.status_label.config(text="请先选择一张图片")
            return
        
        idx = selection[0]
        if idx >= len(self.images_list):
            self.status_label.config(text="图片索引错误")
            return
        
        img_url, img_alt = self.images_list[idx]
        self.status_label.config(text=f"正在加载图片: {img_alt[:30]}...")
        threading.Thread(target=self._load_and_show_image, args=(img_url, img_alt)).start()
    
    def _load_and_show_image(self, img_url, img_alt):
        try:
            img_response = requests.get(img_url, timeout=10)
            if img_response.status_code == 200:
                img_data = BytesIO(img_response.content)
                img = Image.open(img_data)
                self.root.after(0, self._create_image_window, img, img_url, img_alt)
                self.root.after(0, lambda: self.status_label.config(
                    text=f"图片加载完成: {img_alt[:30]}"
                ))
            else:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"加载图片失败: HTTP {img_response.status_code}"
                ))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"加载图片失败: {e}"))
    
    def _create_image_window(self, img, img_url, img_alt):
        img_window = tk.Toplevel(self.root)
        img_window.title(f"图片预览 - {img_alt[:50]}")
        
        original_width, original_height = img.size
        max_size = 800
        if original_width > max_size or original_height > max_size:
            ratio = min(max_size / original_width, max_size / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(img_window, image=photo)
        label.image = photo
        label.pack()
        
        info_text = f"原始尺寸: {original_width}x{original_height} | 描述: {img_alt}"
        if len(img_alt) > 50:
            info_text = f"原始尺寸: {original_width}x{original_height} | 描述: {img_alt[:50]}..."
        
        info_label = tk.Label(img_window, text=info_text)
        info_label.pack()
    
    def download_video(self):
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个视频")
            return
        
        idx = selection[0]
        if idx >= len(self.videos_list):
            messagebox.showerror("错误", "视频索引错误")
            return
        
        video_url, title, vtype = self.videos_list[idx]
        
        file_path = filedialog.asksaveasfilename(
            title="保存视频",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 视频", "*.mp4"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.status_label.config(text=f"正在下载视频: {title[:30]}...")
            threading.Thread(target=self._download_video_file, args=(video_url, file_path, title)).start()
    
    def _download_video_file(self, video_url, file_path, title):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.url_entry.get()
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.root.after(0, lambda: self.status_label.config(
                                text=f"下载进度: {progress:.1f}% ({downloaded//1024}KB/{total_size//1024}KB)"
                            ))
            
            self.root.after(0, lambda: self.status_label.config(
                text=f"视频下载完成: {title[:30]}"
            ))
            self.root.after(0, lambda: messagebox.showinfo("成功", f"视频已保存到: {file_path}"))
            
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: self.status_label.config(text=f"视频下载失败: {e}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"下载失败: {e}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"视频下载失败: {e}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"下载失败: {e}"))
    
    def play_video_embedded(self):
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个视频")
            return
        
        idx = selection[0]
        if idx >= len(self.videos_list):
            messagebox.showerror("错误", "视频索引错误")
            return
        
        video_url, title, vtype = self.videos_list[idx]
        
        if vtype in ['youtube', 'bilibili', 'vimeo']:
            choice = messagebox.askyesno("在线视频", "这是在线视频，是否在浏览器中打开？")
            if choice:
                webbrowser.open(video_url)
            return
        
        self.status_label.config(text=f"正在加载视频: {title[:30]}...")
        threading.Thread(target=self._play_video_embedded_thread, args=(video_url, title)).start()
    
    def _play_video_embedded_thread(self, video_url, title):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.url_entry.get()
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(response.content)
                temp_file = tmp.name
            
            self.root.after(0, self._create_video_player_window, temp_file, title)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"视频加载失败: {e}"))
    
    def _create_video_player_window(self, video_file, title):
        if self.video_player and self.video_player.winfo_exists():
            self.video_player.destroy()
        
        self.video_player = tk.Toplevel(self.root)
        self.video_player.title(f"视频播放器 - {title[:50]}")
        self.video_player.geometry("800x600")
        
        control_frame = ttk.Frame(self.video_player)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.play_button = ttk.Button(control_frame, text="播放", command=lambda: self._play_pygame_video(video_file))
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="暂停", command=self._pause_pygame_video)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self._stop_pygame_video)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.volume_scale = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        self.volume_scale.set(50)
        self.volume_scale.pack(side=tk.LEFT, padx=20)
        self.volume_scale.bind("<ButtonRelease-1>", lambda e: self._update_volume())
        
        volume_label = ttk.Label(control_frame, text="音量:")
        volume_label.pack(side=tk.LEFT)
        
        self.video_label = tk.Label(self.video_player, bg='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        self.root.after(0, lambda: self.status_label.config(text=f"视频已加载: {title[:30]}"))
    
    def _play_pygame_video(self, video_file):
        try:
            pygame.mixer.music.load(video_file)
            pygame.mixer.music.play()
            
            info = tk.Label(self.video_player, text="音频播放中 (视频文件)")
            info.pack()
            
        except Exception as e:
            messagebox.showerror("播放错误", f"无法播放视频: {e}")
    
    def _pause_pygame_video(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
    
    def _stop_pygame_video(self):
        pygame.mixer.music.stop()
    
    def _update_volume(self):
        volume = self.volume_scale.get() / 100
        pygame.mixer.music.set_volume(volume)
    
    def play_video_external(self):
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个视频")
            return
        
        idx = selection[0]
        if idx >= len(self.videos_list):
            messagebox.showerror("错误", "视频索引错误")
            return
        
        video_url, title, vtype = self.videos_list[idx]
        
        if vtype in ['youtube', 'bilibili', 'vimeo']:
            webbrowser.open(video_url)
            self.status_label.config(text=f"正在浏览器中打开视频: {title[:30]}")
        else:
            try:
                webbrowser.open(video_url)
                self.status_label.config(text=f"正在尝试播放视频: {title[:30]}")
            except Exception as e:
                self.status_label.config(text=f"无法打开视频: {e}")
    
    def run(self):
        self.root.mainloop()
        pygame.quit()

def main():
    app = WebContentExtractor()
    app.run()

if __name__ == "__main__":
    main()
