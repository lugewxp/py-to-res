# 导入必要的库
import requests  # 用于发送HTTP请求
from bs4 import BeautifulSoup  # 用于解析HTML
import tkinter as tk  # GUI库
from tkinter import ttk  # Tkinter的增强组件
from PIL import Image, ImageTk  # 图像处理库
from io import BytesIO  # 用于内存中处理二进制数据
from urllib.parse import urljoin, urlparse  # 用于处理URL拼接和解析
import threading  # 多线程支持

def validate_and_fix_url(url):
    """验证URL格式，如果没有协议前缀则自动添加https://"""
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

# 定义获取网页内容的函数
def fetch_webpage():
    """从用户输入的URL获取网页内容并提取文字和图片"""
    url = url_entry.get()  # 从输入框获取URL
    if not url:  # 如果URL为空，直接返回
        status_label.config(text="请输入网页URL")
        return
    
    # 验证并修复URL格式
    url = validate_and_fix_url(url)
    
    # 更新输入框显示修复后的URL
    url_entry.delete(0, tk.END)
    url_entry.insert(0, url)
    
    status_label.config(text="正在加载...")  # 更新状态标签

    # 使用多线程加载网页，避免GUI界面卡顿
    def load_webpage():
        try:
            # 发送HTTP GET请求获取网页内容
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 如果请求失败则抛出异常
            response.encoding = response.apparent_encoding  # 自动检测编码
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本、样式和noscript标签，只保留文本内容
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # 提取并清理文本内容
            text = soup.get_text(separator=' ', strip=True)  # 获取文本并用空格分隔
            lines = [line.strip() for line in text.splitlines() if line.strip()]  # 移除空行
            clean_text = '\n'.join(lines)  # 重新组合为字符串
            
            # 在文本显示框中显示清理后的文本
            text_display.config(state=tk.NORMAL)  # 临时启用编辑状态
            text_display.delete(1.0, tk.END)  # 清空现有内容
            text_display.insert(1.0, clean_text)  # 插入新内容
            text_display.config(state=tk.DISABLED)  # 重新禁用编辑
            
            # 提取网页中所有图片
            global images_list  # 声明全局变量
            images_list = []  # 初始化图片列表
            images = soup.find_all('img')  # 查找所有img标签
            
            for img in images:
                # 获取图片URL（支持src和data-src属性）
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    # 处理相对URL（转换为绝对URL）
                    if not img_url.startswith(('http://', 'https://')):
                        img_url = urljoin(url, img_url)
                    img_alt = img.get('alt', '无描述')  # 获取图片描述
                    images_list.append((img_url, img_alt))  # 添加到列表
            
            # 在列表框中显示图片信息
            image_listbox.delete(0, tk.END)  # 清空现有列表
            for i, (img_url, img_alt) in enumerate(images_list, 1):
                # 截取过长的描述文字
                display_text = f"{i}. {img_alt[:30]}{'...' if len(img_alt) > 30 else ''}"
                image_listbox.insert(tk.END, display_text)
            
            # 更新状态标签显示完成信息
            status_label.config(text=f"加载完成。找到 {len(images_list)} 张图片")
            
        except requests.exceptions.RequestException as e:
            # 处理网络请求相关错误
            error_msg = str(e)
            
            # 检查是否是HTTPS连接失败，尝试使用HTTP
            if "https" in url and ("SSLError" in error_msg or "Certificate" in error_msg):
                status_label.config(text="HTTPS连接失败，尝试使用HTTP...")
                try_http_version(url)
            else:
                status_label.config(text=f"网络请求错误: {e}")
        except Exception as e:
            # 处理其他未知错误
            status_label.config(text=f"发生错误: {e}")

    # 启动新线程执行网页加载
    threading.Thread(target=load_webpage, daemon=True).start()

def try_http_version(url):
    """尝试使用HTTP协议访问网站（当HTTPS失败时）"""
    # 将https://替换为http://
    http_url = url.replace('https://', 'http://', 1)
    
    def try_http_request():
        try:
            # 发送HTTP GET请求获取网页内容
            response = requests.get(http_url, timeout=10)
            response.raise_for_status()  # 如果请求失败则抛出异常
            response.encoding = response.apparent_encoding  # 自动检测编码
            
            # 更新输入框显示HTTP版本的URL
            url_entry.delete(0, tk.END)
            url_entry.insert(0, http_url)
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本、样式和noscript标签，只保留文本内容
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # 提取并清理文本内容
            text = soup.get_text(separator=' ', strip=True)  # 获取文本并用空格分隔
            lines = [line.strip() for line in text.splitlines() if line.strip()]  # 移除空行
            clean_text = '\n'.join(lines)  # 重新组合为字符串
            
            # 在文本显示框中显示清理后的文本
            text_display.config(state=tk.NORMAL)  # 临时启用编辑状态
            text_display.delete(1.0, tk.END)  # 清空现有内容
            text_display.insert(1.0, clean_text)  # 插入新内容
            text_display.config(state=tk.DISABLED)  # 重新禁用编辑
            
            # 提取网页中所有图片
            global images_list  # 声明全局变量
            images_list = []  # 初始化图片列表
            images = soup.find_all('img')  # 查找所有img标签
            
            for img in images:
                # 获取图片URL（支持src和data-src属性）
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    # 处理相对URL（转换为绝对URL）
                    if not img_url.startswith(('http://', 'https://')):
                        img_url = urljoin(http_url, img_url)
                    img_alt = img.get('alt', '无描述')  # 获取图片描述
                    images_list.append((img_url, img_alt))  # 添加到列表
            
            # 在列表框中显示图片信息
            image_listbox.delete(0, tk.END)  # 清空现有列表
            for i, (img_url, img_alt) in enumerate(images_list, 1):
                # 截取过长的描述文字
                display_text = f"{i}. {img_alt[:30]}{'...' if len(img_alt) > 30 else ''}"
                image_listbox.insert(tk.END, display_text)
            
            # 更新状态标签显示完成信息
            status_label.config(text=f"HTTP加载完成。找到 {len(images_list)} 张图片")
            
        except requests.exceptions.RequestException as e:
            # 处理网络请求相关错误
            status_label.config(text=f"HTTP请求也失败: {e}")
        except Exception as e:
            # 处理其他未知错误
            status_label.config(text=f"发生错误: {e}")

    # 启动新线程执行HTTP请求
    threading.Thread(target=try_http_request, daemon=True).start()

def show_image():
    """显示选中的图片"""
    selection = image_listbox.curselection()  # 获取列表框中的选中项
    if not selection:  # 如果没有选中项，直接返回
        return

    idx = selection[0]  # 获取选中项的索引
    if idx >= len(images_list):  # 检查索引是否有效
        return

    # 从图片列表中获取图片URL和描述
    img_url, img_alt = images_list[idx]
    status_label.config(text=f"正在加载图片: {img_alt[:30]}...")  # 更新状态

    def load_and_show():
        """加载并显示图片的内部函数"""
        try:
            # 发送请求获取图片数据
            img_response = requests.get(img_url, timeout=10)
            if img_response.status_code == 200:  # 如果请求成功
                # 在内存中打开图片
                img_data = BytesIO(img_response.content)
                img = Image.open(img_data)
                
                # 创建新窗口显示图片
                img_window = tk.Toplevel(root)
                img_window.title(f"图片预览 - {img_alt[:50]}")
                
                # 获取原始图片尺寸
                img_width, img_height = img.size
                max_size = 800  # 最大显示尺寸
                
                # 如果图片尺寸过大，按比例缩小
                if img_width > max_size or img_height > max_size:
                    ratio = min(max_size/img_width, max_size/img_height)
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 转换为Tkinter可用的PhotoImage格式
                photo = ImageTk.PhotoImage(img)
                
                # 创建标签显示图片
                label = tk.Label(img_window, image=photo)
                label.image = photo  # 保持引用，防止被垃圾回收
                label.pack()
                
                # 显示图片信息
                info_label = tk.Label(img_window, text=f"尺寸: {img_width}x{img_height} | 描述: {img_alt}")
                info_label.pack()
                
                status_label.config(text=f"图片加载完成")
                
        except Exception as e:
            # 处理图片加载错误
            status_label.config(text=f"加载图片失败: {e}")

    # 启动新线程执行图片加载
    threading.Thread(target=load_and_show, daemon=True).start()

def on_entry_return(event):
    """当用户在URL输入框中按回车键时触发搜索"""
    fetch_webpage()

# 创建主窗口
root = tk.Tk()
root.title("网页内容提取器")  # 设置窗口标题
root.geometry("900x700")  # 设置窗口尺寸

# 全局变量声明
images_list = []  # 存储图片信息的列表

# 创建主框架
frame = ttk.Frame(root, padding="10")
frame.pack(fill=tk.BOTH, expand=True)

# URL输入部分
url_label = ttk.Label(frame, text="网页URL (支持输入域名如: baidu.com):")
url_label.pack(anchor=tk.W)

url_entry = ttk.Entry(frame, width=80)
url_entry.pack(pady=5)
url_entry.bind('<Return>', on_entry_return)  # 绑定回车键事件

# 获取内容按钮
fetch_button = ttk.Button(frame, text="获取网页内容", command=fetch_webpage)
fetch_button.pack(pady=5)

# 创建选项卡控件
notebook = ttk.Notebook(frame)
notebook.pack(fill=tk.BOTH, expand=True, pady=10)

# 文本显示选项卡
text_frame = ttk.Frame(notebook)
notebook.add(text_frame, text="网页文字")

# 文本显示区域的滚动条
text_scroll = ttk.Scrollbar(text_frame)
text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# 文本显示区域
text_display = tk.Text(text_frame, height=20, wrap=tk.WORD, yscrollcommand=text_scroll.set)
text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
text_display.config(state=tk.DISABLED)  # 初始为只读状态
text_scroll.config(command=text_display.yview)  # 关联滚动条和文本区域

# 图片列表选项卡
image_frame = ttk.Frame(notebook)
notebook.add(image_frame, text="图片列表")

# 图片列表框架
image_list_frame = ttk.Frame(image_frame)
image_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

# 图片列表的滚动条
image_scroll = ttk.Scrollbar(image_list_frame)
image_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# 图片列表框
image_listbox = tk.Listbox(image_list_frame, height=15, yscrollcommand=image_scroll.set)
image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
image_scroll.config(command=image_listbox.yview)  # 关联滚动条和列表框

# 查看图片按钮
show_button = ttk.Button(image_frame, text="查看选中图片", command=show_image)
show_button.pack(pady=5)

# 状态标签
status_label = ttk.Label(frame, text="就绪")
status_label.pack(pady=5)

# 添加说明标签
instructions = """
使用说明:
1. 输入网页URL (支持输入域名如: baidu.com，系统会自动补全https://)
2. 点击"获取网页内容"按钮或按回车键
3. 如果HTTPS连接失败，系统会自动尝试HTTP协议
4. 在"网页文字"选项卡查看提取的文本内容
5. 在"图片列表"选项卡查看并预览图片
"""
instruction_label = ttk.Label(frame, text=instructions, justify=tk.LEFT, foreground="gray")
instruction_label.pack(pady=10)

# 启动GUI主循环
root.mainloop()
