import requests  # 用于发送HTTP请求
from bs4 import BeautifulSoup  # 用于解析HTML
import tkinter as tk  # GUI库
from tkinter import ttk, filedialog, messagebox  # Tkinter的增强组件和对话框
from PIL import Image, ImageTk  # 图像处理库
from io import BytesIO  # 用于内存中处理二进制数据
from urllib.parse import urljoin, urlparse  # 用于处理URL拼接和解析
import threading  # 多线程支持
import os  # 文件系统操作
import re  # 正则表达式
import webbrowser  # 打开浏览器
import tempfile  # 临时文件处理
import subprocess  # 运行外部程序
import sys  # 系统相关功能
def validate_and_fix_url(url):
    """
    验证URL格式，如果没有协议前缀则自动添加https://
    
    参数:
        url (str): 用户输入的URL
    
    返回:
        str: 修复后的完整URL
    """
    if not url:
        return url
    
    # 移除首尾空格
    url = url.strip()
    
    # 检查是否包含协议前缀
    if not url.startswith(('http://', 'https://')):
        # 如果没有协议前缀，自动添加https://
        url = 'https://' + url
        print(f"URL自动补全为: {url}")
    
    return url

class WebContentExtractor:
    """
    网页内容提取器主类 v5.0
    负责管理GUI界面和所有提取功能，合并了两个版本的所有特性
    """
    
    def __init__(self):
        """
        初始化应用程序 v5.0
        """
        # 初始化数据存储
        self.images_list = []  # 存储图片信息列表，格式: [(url, alt_text), ...]
        self.videos_list = []  # 存储视频信息列表，格式: [(url, title, type), ...]
        self.current_html = ""  # 存储当前网页的HTML源码
        
        # 初始化主窗口
        self.root = None
        
        # 设置用户代理，模拟浏览器访问
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 设置UI界面
        self.setup_ui()
    
    def setup_ui(self):
        """
        设置用户界面 v5.0
        创建所有GUI组件和布局，整合两个版本的所有UI元素
        """
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("网页内容提取器 v5.0 - 完整增强版")
        self.root.geometry("800x600")
        
        # 创建主框架
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== URL输入部分 ==========
        url_label = ttk.Label(frame, text="网页URL (支持输入域名如: baidu.com):")
        url_label.pack(anchor=tk.W)
        
        # URL输入框架
        url_frame = ttk.Frame(frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        # URL输入框
        self.url_entry = ttk.Entry(url_frame, width=80)
        self.url_entry.pack(side=tk.LEFT)
        self.url_entry.bind('<Return>', lambda event: self.fetch_webpage())  # 绑定回车键事件
        
        # 获取内容按钮
        fetch_button = ttk.Button(url_frame, text="获取网页内容", command=self.fetch_webpage)
        fetch_button.pack(side=tk.LEFT, padx=5)
        
        # ========== HTML操作按钮 ==========
        html_buttons_frame = ttk.Frame(frame)
        html_buttons_frame.pack(fill=tk.X, pady=5)
        
        # 保存HTML按钮
        save_html_button = ttk.Button(
            html_buttons_frame, 
            text="保存HTML到html.txt", 
            command=self.save_html_to_file
        )
        save_html_button.pack(side=tk.LEFT, padx=5)
        
        # 打开HTML编辑器按钮
        open_editor_button = ttk.Button(
            html_buttons_frame, 
            text="用html_edit.py打开html.txt", 
            command=self.open_html_in_editor
        )
        open_editor_button.pack(side=tk.LEFT, padx=5)
        
        # ========== 创建选项卡控件 ==========
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建各个选项卡
        text_frame = self.create_text_tab(notebook)
        notebook.add(text_frame, text="网页文字")
        
        html_frame = self.create_html_tab(notebook)
        notebook.add(html_frame, text="HTML源码")
        
        image_frame = self.create_image_tab(notebook)
        notebook.add(image_frame, text="图片列表")
        
        video_frame = self.create_video_tab(notebook)
        notebook.add(video_frame, text="视频列表")
        
        # ========== 状态标签 ==========
        self.status_label = ttk.Label(frame, text="就绪")
        self.status_label.pack(pady=5)
        

        instructions = """
        使用说明 v5.0:
        1. 输入网页URL (支持输入域名如: baidu.com，系统会自动补全https://)
        2. 点击"获取网页内容"按钮或按回车键
        3. 如果HTTPS连接失败，系统会自动尝试HTTP协议
        4. 在"网页文字"选项卡查看提取的文本内容
        5. 在"HTML源码"选项卡查看网页源代码，并可保存或编辑
        6. 在"图片列表"选项卡查看并预览图片
        7. 在"视频列表"选项卡查看、播放或下载视频
        8. 支持提取多种视频格式和视频平台链接
        """
        instruction_label = ttk.Label(frame, text=instructions, justify=tk.LEFT, foreground="gray")
        instruction_label.pack(pady=10)
    
    def create_text_tab(self, notebook):
        """
        创建文本显示选项卡
        
        参数:
            notebook: ttk.Notebook对象
        
        返回:
            ttk.Frame: 文本选项卡的框架
        """
        text_frame = ttk.Frame(notebook)
        
        # 创建滚动条
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建文本显示区域
        self.text_display = tk.Text(text_frame, height=20, wrap=tk.WORD, yscrollcommand=text_scroll.set)
        self.text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_display.config(state=tk.DISABLED)  # 初始为只读状态
        
        # 关联滚动条和文本区域
        text_scroll.config(command=self.text_display.yview)
        
        return text_frame
    
    def create_html_tab(self, notebook):
        """
        创建HTML源码显示选项卡
        
        参数:
            notebook: ttk.Notebook对象
        
        返回:
            ttk.Frame: HTML选项卡的框架
        """
        html_frame = ttk.Frame(notebook)
        
        # 创建滚动条
        html_scroll = ttk.Scrollbar(html_frame)
        html_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建HTML显示区域
        self.html_display = tk.Text(html_frame, height=20, wrap=tk.NONE, yscrollcommand=html_scroll.set)
        self.html_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.html_display.config(state=tk.DISABLED)  # 初始为只读状态
        
        # 关联滚动条和HTML区域
        html_scroll.config(command=self.html_display.yview)
        
        return html_frame
    
    def create_image_tab(self, notebook):
        """
        创建图片列表选项卡
        
        参数:
            notebook: ttk.Notebook对象
        
        返回:
            ttk.Frame: 图片选项卡的框架
        """
        image_frame = ttk.Frame(notebook)
        
        # 创建图片列表框架
        image_list_frame = ttk.Frame(image_frame)
        image_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建滚动条
        image_scroll = ttk.Scrollbar(image_list_frame)
        image_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建图片列表框
        self.image_listbox = tk.Listbox(image_list_frame, height=15, yscrollcommand=image_scroll.set)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 关联滚动条和列表框
        image_scroll.config(command=self.image_listbox.yview)
        
        # 创建查看图片按钮
        show_button = ttk.Button(image_frame, text="查看选中图片", command=self.show_image)
        show_button.pack(pady=5)
        
        return image_frame
    
    def create_video_tab(self, notebook):
        """
        创建视频列表选项卡 v5.0
        包含播放、复制链接和下载功能
        
        参数:
            notebook: ttk.Notebook对象
        
        返回:
            ttk.Frame: 视频选项卡的框架
        """
        video_frame = ttk.Frame(notebook)
        
        # 创建视频列表框架
        video_list_frame = ttk.Frame(video_frame)
        video_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建滚动条
        video_scroll = ttk.Scrollbar(video_list_frame)
        video_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建视频列表框
        self.video_listbox = tk.Listbox(video_list_frame, height=15, yscrollcommand=video_scroll.set)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 关联滚动条和列表框
        video_scroll.config(command=self.video_listbox.yview)
        
        # 创建按钮框架
        button_frame = ttk.Frame(video_frame)
        button_frame.pack(pady=5)
        
        # 播放视频按钮
        preview_button = ttk.Button(button_frame, text="播放MP4视频", command=self.play_video_external)
        preview_button.pack(side=tk.LEFT, padx=5)
        
        # 复制视频链接按钮
        copy_button = ttk.Button(button_frame, text="复制视频链接", command=self.copy_video_url)
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # 下载视频按钮
        download_button = ttk.Button(button_frame, text="下载选中视频", command=self.download_video)
        download_button.pack(side=tk.LEFT, padx=5)
        
        return video_frame
    
    def fetch_webpage(self):
        """
        从用户输入的URL获取网页内容 v5.0
        整合了两个版本的URL处理和错误处理逻辑
        """
        # 获取并验证URL
        url = self.url_entry.get()
        if not url:
            self.status_label.config(text="错误: 请输入URL")
            return
        
        # 验证并修复URL格式
        url = validate_and_fix_url(url)
        
        # 更新输入框显示修复后的URL
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        
        # 更新状态标签
        self.status_label.config(text="正在加载网页...")
        
        # 使用多线程加载网页，避免GUI界面卡顿
        threading.Thread(target=self._load_webpage, args=(url,), daemon=True).start()
    
    def _load_webpage(self, url):
        """
        实际加载网页的内部函数 v5.0
        整合了HTTPS失败时自动尝试HTTP的逻辑
        包含4.0版的请求头和错误处理
        
        参数:
            url (str): 要加载的网页URL
        """
        try:
            # 发送HTTP GET请求获取网页内容（使用4.0版的请求头）
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # 如果请求失败则抛出异常
            response.encoding = response.apparent_encoding  # 自动检测编码
            
            # 保存HTML源码
            self.current_html = response.text
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取文本、图片和视频信息
            self._extract_text_content(soup)
            self._extract_image_info(soup, url)
            self._extract_video_info(soup, url)
            
            # 更新状态标签显示完成信息
            self.root.after(0, lambda: self.status_label.config(
                text=f"加载完成。找到 {len(self.images_list)} 张图片，{len(self.videos_list)} 个视频"
            ))
            
            # 更新HTML显示
            self.root.after(0, self._update_html_display)
            
        except requests.exceptions.RequestException as e:
            # 处理网络请求相关错误
            error_msg = str(e)
            
            # 检查是否是HTTPS连接失败，尝试使用HTTP（2改.py的功能）
            if "https" in url and ("SSLError" in error_msg or "Certificate" in error_msg or "HTTPSConnectionPool" in error_msg):
                self.root.after(0, lambda: self.status_label.config(text="HTTPS连接失败，尝试使用HTTP..."))
                self.try_http_version(url)
            else:
                # 4.0版的错误处理方式
                self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"网络请求错误: {msg}"))
        except Exception as e:
            # 处理其他未知错误
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"发生错误: {msg}"))
    
    def try_http_version(self, url):
        """
        尝试使用HTTP协议访问网站（当HTTPS失败时） v5.0
        来自2改.py的HTTP重试功能
        
        参数:
            url (str): 原始URL（HTTPS版本）
        """
        # 将https://替换为http://
        http_url = url.replace('https://', 'http://', 1)
        
        # 使用多线程执行HTTP请求
        threading.Thread(target=self._try_http_request, args=(http_url,), daemon=True).start()
    
    def _try_http_request(self, http_url):
        """
        实际执行HTTP请求的内部函数 v5.0
        
        参数:
            http_url (str): HTTP版本的URL
        """
        try:
            # 发送HTTP GET请求获取网页内容
            response = requests.get(http_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            # 更新输入框显示HTTP版本的URL
            self.root.after(0, lambda: self.url_entry.delete(0, tk.END))
            self.root.after(0, lambda: self.url_entry.insert(0, http_url))
            
            # 保存HTML源码
            self.current_html = response.text
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取文本、图片和视频信息
            self._extract_text_content(soup)
            self._extract_image_info(soup, http_url)
            self._extract_video_info(soup, http_url)
            
            # 更新状态标签显示完成信息
            self.root.after(0, lambda: self.status_label.config(
                text=f"HTTP加载完成。找到 {len(self.images_list)} 张图片，{len(self.videos_list)} 个视频"
            ))
            
            # 更新HTML显示
            self.root.after(0, self._update_html_display)
            
        except requests.exceptions.RequestException as e:
            # 处理HTTP请求也失败的情况
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"HTTP请求也失败: {msg}"))
        except Exception as e:
            # 处理其他未知错误
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"发生错误: {msg}"))
    
    def _extract_text_content(self, soup):
        """
        从BeautifulSoup对象中提取文本内容
        合并了两个版本的处理方式
        
        参数:
            soup: BeautifulSoup对象
        """
        # 移除脚本、样式和noscript标签，只保留文本内容
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # 提取并清理文本内容
        text = soup.get_text(separator=' ', strip=True)  # 获取文本并用空格分隔
        lines = [line.strip() for line in text.splitlines() if line.strip()]  # 移除空行
        clean_text = '\n'.join(lines)  # 重新组合为字符串
        
        # 在GUI线程中更新文本显示
        self.root.after(0, self._update_text_display, clean_text)
    
    def _update_text_display(self, text):
        """
        更新文本显示区域
        两个版本的处理方式相同
        
        参数:
            text (str): 要显示的文本
        """
        self.text_display.config(state=tk.NORMAL)  # 临时启用编辑状态
        self.text_display.delete(1.0, tk.END)  # 清空现有内容
        self.text_display.insert(1.0, text)  # 插入新内容
        self.text_display.config(state=tk.DISABLED)  # 重新禁用编辑
    
    def _update_html_display(self):
        """
        更新HTML源码显示区域 v5.0
        包含内容截断功能
        """
        self.html_display.config(state=tk.NORMAL)  # 临时启用编辑状态
        self.html_display.delete(1.0, tk.END)  # 清空现有内容
        
        # 如果HTML内容过长，进行截断处理（来自4.0版）
        if len(self.current_html) > 50000:
            self.html_display.insert(1.0, self.current_html[:50000] + "\n\n... (内容过长，已截断)")
        else:
            self.html_display.insert(1.0, self.current_html)
        
        self.html_display.config(state=tk.DISABLED)  # 重新禁用编辑
    
    def save_html_to_file(self):
        """
        将当前HTML源码保存到文件
        两个版本的功能相同
        """
        if not self.current_html:
            messagebox.showwarning("警告", "请先获取网页内容")
            return
        
        try:
            # 将HTML源码保存到html.txt文件
            with open("html.txt", "w", encoding="utf-8") as f:
                f.write(self.current_html)
            
            # 更新状态并显示成功消息
            self.status_label.config(text="HTML已保存到 html.txt")
            messagebox.showinfo("成功", "HTML代码已保存到 html.txt")
        except Exception as e:
            # 处理保存失败的情况
            error_msg = str(e)
            self.status_label.config(text=f"保存失败: {error_msg}")
            messagebox.showerror("错误", f"保存失败: {error_msg}")
    
    def open_html_in_editor(self):
        """
        打开HTML编辑器编辑保存的HTML文件
        两个版本的功能相同
        """
        # 检查文件是否存在
        if not os.path.exists("html.txt"):
            messagebox.showwarning("警告", "未找到 html.txt 文件，请先保存HTML")
            return
        
        # 检查编辑器是否存在
        if not os.path.exists("html_edit.py"):
            messagebox.showwarning("警告", "未找到 html_edit.py 编辑器文件")
            return
        
        try:
            # 使用subprocess打开编辑器
            subprocess.Popen([sys.executable, "html_edit.py", "html.txt"])
            self.status_label.config(text="正在打开HTML编辑器...")
        except Exception as e:
            # 处理打开失败的情况
            error_msg = str(e)
            self.status_label.config(text=f"打开编辑器失败: {error_msg}")
            messagebox.showerror("错误", f"打开编辑器失败: {error_msg}")
    
    def _extract_image_info(self, soup, base_url):
        """
        从BeautifulSoup对象中提取图片信息 v5.0
        支持src和data-src属性
        
        参数:
            soup: BeautifulSoup对象
            base_url (str): 基础URL，用于处理相对URL
        """
        # 初始化图片列表
        self.images_list = []
        
        # 查找所有img标签
        images = soup.find_all('img')
        
        for img in images:
            # 获取图片URL（支持src和data-src属性）
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # 处理相对URL（转换为绝对URL）
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urljoin(base_url, img_url)
                
                # 获取图片描述
                img_alt = img.get('alt', '无描述')
                
                # 添加到图片列表
                self.images_list.append((img_url, img_alt))
        
        # 在GUI线程中更新图片列表框
        self.root.after(0, self._update_image_listbox)
    
    def _update_image_listbox(self):
        """
        更新图片列表框
        两个版本的处理方式相同
        """
        self.image_listbox.delete(0, tk.END)  # 清空现有列表
        
        # 遍历图片列表，添加到列表框中
        for i, (img_url, img_alt) in enumerate(self.images_list, 1):
            # 截取过长的描述文字
            display_text = f"{i}. {img_alt[:30]}{'...' if len(img_alt) > 30 else ''}"
            self.image_listbox.insert(tk.END, display_text)
    
    def _extract_video_info(self, soup, base_url):
        """
        从BeautifulSoup对象中提取视频信息 v5.0
        增强版视频提取功能，支持多种视频格式和平台
        
        参数:
            soup: BeautifulSoup对象
            base_url (str): 基础URL，用于处理相对URL
        """
        # 初始化视频列表
        self.videos_list = []
        
        # ========== 1. 提取video标签中的视频 ==========
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src')
            if src:
                # 处理相对URL
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                
                # 检查是否是视频URL
                if self._is_video_url(src):
                    title = video.get('title', video.get('alt', '无标题'))
                    self.videos_list.append((src, title, 'direct'))
            
            # 提取source标签中的视频
            source_tags = video.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    # 处理相对URL
                    if not src.startswith(('http://', 'https://')):
                        src = urljoin(base_url, src)
                    
                    # 检查是否是视频URL
                    if self._is_video_url(src):
                        title = source.get('title', '无标题')
                        self.videos_list.append((src, title, 'direct'))
        
        # ========== 2. 提取iframe标签中的视频嵌入 ==========
        iframe_tags = soup.find_all('iframe')
        for iframe in iframe_tags:
            src = iframe.get('src')
            if src:
                # 处理相对URL
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                
                title = iframe.get('title', '视频嵌入')
                
                # 识别不同的视频平台
                if 'youtube.com' in src or 'youtu.be' in src:
                    self.videos_list.append((src, title, 'youtube'))
                elif 'bilibili.com' in src:
                    self.videos_list.append((src, title, 'bilibili'))
                elif 'vimeo.com' in src:
                    self.videos_list.append((src, title, 'vimeo'))
        
        # ========== 3. 提取a标签中的视频链接 ==========
        a_tags = soup.find_all('a', href=True)
        for a in a_tags:
            href = a['href']
            
            # 检查是否是视频URL
            if self._is_video_url(href):
                # 处理相对URL
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                
                # 获取链接文本作为标题
                title = a.get_text(strip=True)
                if not title:
                    title = '视频链接'
                
                self.videos_list.append((href, title, 'direct'))
        
        # ========== 4. 提取script标签中的视频链接 ==========
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_text = script.string
                # 使用正则表达式查找视频URL
                video_urls = re.findall(
                    r'https?://[^\s<>"]+\.(mp4|webm|avi|mov|flv|wmv|m4v|mkv)',
                    script_text,
                    re.IGNORECASE
                )
                
                for url in video_urls:
                    if self._is_video_url(url):
                        self.videos_list.append((url, '脚本中的视频', 'direct'))
        
        # 在GUI线程中更新视频列表框
        self.root.after(0, self._update_video_listbox)
    
    def _is_video_url(self, url):
        """
        检查URL是否是视频URL v5.0
        支持多种视频格式
        
        参数:
            url (str): 要检查的URL
        
        返回:
            bool: 如果是视频URL则返回True，否则返回False
        """
        # 视频文件扩展名列表
        video_extensions = ['.mp4', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.mkv']
        
        # 检查URL是否包含视频扩展名
        for ext in video_extensions:
            if ext in url.lower():
                return True
        
        return False
    
    def _update_video_listbox(self):
        """
        更新视频列表框 v5.0
        显示视频类型图标
        """
        self.video_listbox.delete(0, tk.END)  # 清空现有列表
        
        # 遍历视频列表，添加到列表框中
        for i, (video_url, title, vtype) in enumerate(self.videos_list, 1):
            # 根据视频类型设置图标
            type_icon = {
                'direct': '[MP4]',
                'youtube': '[YT]',
                'bilibili': '[B站]',
                'vimeo': '[VM]'
            }.get(vtype, '[VID]')
            
            # 截取过长的标题
            display_text = f"{i}. {type_icon} {title[:30]}{'...' if len(title) > 30 else ''}"
            self.video_listbox.insert(tk.END, display_text)
    
    def show_image(self):
        """
        显示选中的图片 v5.0
        使用多线程加载图片
        """
        # 获取列表框中的选中项
        selection = self.image_listbox.curselection()
        if not selection:
            self.status_label.config(text="请先选择一张图片")
            return
        
        # 获取选中项的索引
        idx = selection[0]
        if idx >= len(self.images_list):
            self.status_label.config(text="图片索引错误")
            return
        
        # 从图片列表中获取图片URL和描述
        img_url, img_alt = self.images_list[idx]
        self.status_label.config(text=f"正在加载图片: {img_alt[:30]}...")
        
        # 使用多线程加载图片，避免GUI界面卡顿
        threading.Thread(target=self._load_and_show_image, args=(img_url, img_alt), daemon=True).start()
    
    def _load_and_show_image(self, img_url, img_alt):
        """
        加载并显示图片的内部函数 v5.0
        整合了两个版本的图片加载逻辑
        
        参数:
            img_url (str): 图片URL
            img_alt (str): 图片描述
        """
        try:
            # 发送请求获取图片数据
            img_response = requests.get(img_url, headers=self.headers, timeout=10)
            
            if img_response.status_code == 200:  # 如果请求成功
                # 在内存中打开图片
                img_data = BytesIO(img_response.content)
                img = Image.open(img_data)
                
                # 在GUI线程中创建图片窗口
                self.root.after(0, self._create_image_window, img, img_url, img_alt)
                
                # 更新状态标签
                self.root.after(0, lambda: self.status_label.config(
                    text=f"图片加载完成: {img_alt[:30]}"
                ))
            else:
                # 处理HTTP错误
                status_code = img_response.status_code
                self.root.after(0, lambda code=status_code: self.status_label.config(
                    text=f"加载图片失败: HTTP {code}"
                ))
                
        except Exception as e:
            # 处理图片加载错误
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"加载图片失败: {msg}"))
    
    def _create_image_window(self, img, img_url, img_alt):
        """
        创建图片预览窗口 v5.0
        包含图片尺寸调整和信息显示
        
        参数:
            img: PIL.Image对象
            img_url (str): 图片URL
            img_alt (str): 图片描述
        """
        # 创建新窗口
        img_window = tk.Toplevel(self.root)
        img_window.title(f"图片预览 - {img_alt[:50]}")
        
        # 获取原始图片尺寸
        original_width, original_height = img.size
        max_size = 800  # 最大显示尺寸
        
        # 如果图片尺寸过大，按比例缩小
        if original_width > max_size or original_height > max_size:
            ratio = min(max_size / original_width, max_size / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 转换为Tkinter可用的PhotoImage格式
        photo = ImageTk.PhotoImage(img)
        
        # 创建标签显示图片
        label = tk.Label(img_window, image=photo)
        label.image = photo  # 保持引用，防止被垃圾回收
        label.pack()
        
        # 显示图片信息（使用4.0版的信息显示方式）
        info_text = f"原始尺寸: {original_width}x{original_height} | 描述: {img_alt}"
        if len(img_alt) > 50:
            info_text = f"原始尺寸: {original_width}x{original_height} | 描述: {img_alt[:50]}..."
        
        info_label = tk.Label(img_window, text=info_text)
        info_label.pack()
    
    def download_video(self):
        """
        下载选中的视频 v5.0
        包含进度显示和错误处理
        """
        # 获取列表框中的选中项
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个视频")
            return
        
        # 获取选中项的索引
        idx = selection[0]
        if idx >= len(self.videos_list):
            messagebox.showerror("错误", "视频索引错误")
            return
        
        # 从视频列表中获取视频信息
        video_url, title, vtype = self.videos_list[idx]
        
        # 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(
            title="保存视频",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 视频", "*.mp4"),
                ("所有文件", "*.*")
            ]
        )
        
        # 如果用户选择了保存路径
        if file_path:
            self.status_label.config(text=f"正在下载视频: {title[:30]}...")
            
            # 使用多线程下载视频，避免GUI界面卡顿
            threading.Thread(
                target=self._download_video_file,
                args=(video_url, file_path, title),
                daemon=True
            ).start()
    
    def _download_video_file(self, video_url, file_path, title):
        """
        下载视频文件的内部函数 v5.0
        整合了4.0版的下载进度显示和错误处理
        
        参数:
            video_url (str): 视频URL
            file_path (str): 保存路径
            title (str): 视频标题
        """
        try:
            # 设置请求头（使用4.0版的headers）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.url_entry.get()  # 添加来源页，防止某些网站拦截
            }
            
            # 发送流式请求下载视频
            response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # 写入文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 如果有文件总大小信息，计算并显示下载进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            downloaded_kb = downloaded // 1024
                            total_kb = total_size // 1024
                            
                            # 在GUI线程中更新状态标签
                            self.root.after(0, lambda p=progress, d=downloaded_kb, t=total_kb: self.status_label.config(
                                text=f"下载进度: {p:.1f}% ({d}KB/{t}KB)"
                            ))
            
            # 下载完成
            self.root.after(0, lambda: self.status_label.config(
                text=f"视频下载完成: {title[:30]}"
            ))
            self.root.after(0, lambda: messagebox.showinfo("成功", f"视频已保存到: {file_path}"))
            
        except requests.exceptions.RequestException as e:
            # 处理网络请求错误
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"视频下载失败: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"下载失败: {msg}"))
        except Exception as e:
            # 处理其他错误
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"视频下载失败: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"下载失败: {msg}"))
    
    def play_video_external(self):
        """
        在外部播放器中播放选中的视频 v5.0
        支持多种视频平台
        
        参数:
            selection: 列表框中选中的项
        """
        # 获取列表框中的选中项
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个视频")
            return
        
        # 获取选中项的索引
        idx = selection[0]
        if idx >= len(self.videos_list):
            messagebox.showerror("错误", "视频索引错误")
            return
        
        # 从视频列表中获取视频信息
        video_url, title, vtype = self.videos_list[idx]
        
        # 根据视频类型处理
        if vtype in ['youtube', 'bilibili', 'vimeo']:
            # 对于在线视频平台，直接在浏览器中打开
            webbrowser.open(video_url)
            self.status_label.config(text=f"正在浏览器中打开视频: {title[:30]}")
        else:
            # 对于直接视频链接，尝试在浏览器中打开
            try:
                webbrowser.open(video_url)
                self.status_label.config(text=f"正在尝试播放视频: {title[:30]}")
            except Exception as e:
                # 处理打开失败的情况
                error_msg = str(e)
                self.status_label.config(text=f"无法打开视频: {error_msg}")
    
    def copy_video_url(self):
        """
        复制视频链接到剪贴板 v5.0
        
        参数:
            selection: 列表框中选中的项
        """
        # 获取列表框中的选中项
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个视频")
            return
        
        # 获取选中项的索引
        idx = selection[0]
        if idx >= len(self.videos_list):
            messagebox.showerror("错误", "视频索引错误")
            return
        
        # 从视频列表中获取视频信息
        video_url, title, vtype = self.videos_list[idx]
        
        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(video_url)
        
        # 更新状态标签并显示成功消息
        self.status_label.config(text=f"已复制视频链接: {title[:30]}")
        messagebox.showinfo("成功", "视频链接已复制到剪贴板")
    
    def run(self):
        """
        运行应用程序
        启动Tkinter主循环
        """
        self.root.mainloop()


# ============================ 主函数 ============================
def main():
    """
    程序入口函数
    创建并运行WebContentExtractor实例 v5.0
    """
    # 创建应用程序实例
    app = WebContentExtractor()
    
    # 运行应用程序
    app.run()


# ============================ 程序入口 ============================
if __name__ == "__main__":
    main()
