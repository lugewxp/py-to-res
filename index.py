import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import urljoin
import threading

def fetch_webpage():
    url = url_entry.get()
    if not url:
        return
    
    status_label.config(text="正在加载...")
    
    def load_webpage():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)
            
            text_display.config(state=tk.NORMAL)
            text_display.delete(1.0, tk.END)
            text_display.insert(1.0, clean_text)
            text_display.config(state=tk.DISABLED)
            
            global images_list
            images_list = []
            images = soup.find_all('img')
            
            for img in images:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    if not img_url.startswith(('http://', 'https://')):
                        img_url = urljoin(url, img_url)
                    img_alt = img.get('alt', '无描述')
                    images_list.append((img_url, img_alt))
            
            image_listbox.delete(0, tk.END)
            for i, (img_url, img_alt) in enumerate(images_list, 1):
                image_listbox.insert(tk.END, f"{i}. {img_alt[:30]}{'...' if len(img_alt) > 30 else ''}")
            
            status_label.config(text=f"加载完成。找到 {len(images_list)} 张图片")
            
        except requests.exceptions.RequestException as e:
            status_label.config(text=f"网络请求错误: {e}")
        except Exception as e:
            status_label.config(text=f"发生错误: {e}")
    
    threading.Thread(target=load_webpage).start()

def show_image():
    selection = image_listbox.curselection()
    if not selection:
        return
    
    idx = selection[0]
    if idx >= len(images_list):
        return
    
    img_url, img_alt = images_list[idx]
    status_label.config(text=f"正在加载图片: {img_alt[:30]}...")
    
    def load_and_show():
        try:
            img_response = requests.get(img_url, timeout=10)
            if img_response.status_code == 200:
                img_data = BytesIO(img_response.content)
                img = Image.open(img_data)
                
                img_window = tk.Toplevel(root)
                img_window.title(f"图片预览 - {img_alt[:50]}")
                
                img_width, img_height = img.size
                max_size = 800
                
                if img_width > max_size or img_height > max_size:
                    ratio = min(max_size/img_width, max_size/img_height)
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                
                label = tk.Label(img_window, image=photo)
                label.image = photo
                label.pack()
                
                info_label = tk.Label(img_window, text=f"尺寸: {img_width}x{img_height} | 描述: {img_alt}")
                info_label.pack()
                
                status_label.config(text=f"图片加载完成")
                
        except Exception as e:
            status_label.config(text=f"加载图片失败: {e}")
    
    threading.Thread(target=load_and_show).start()

root = tk.Tk()
root.title("网页内容提取器")
root.geometry("900x700")

images_list = []

frame = ttk.Frame(root, padding="10")
frame.pack(fill=tk.BOTH, expand=True)

url_label = ttk.Label(frame, text="网页URL:")
url_label.pack(anchor=tk.W)

url_entry = ttk.Entry(frame, width=80)
url_entry.pack(pady=5)

fetch_button = ttk.Button(frame, text="获取网页内容", command=fetch_webpage)
fetch_button.pack(pady=5)

notebook = ttk.Notebook(frame)
notebook.pack(fill=tk.BOTH, expand=True, pady=10)

text_frame = ttk.Frame(notebook)
notebook.add(text_frame, text="网页文字")

text_scroll = ttk.Scrollbar(text_frame)
text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

text_display = tk.Text(text_frame, height=20, wrap=tk.WORD, yscrollcommand=text_scroll.set)
text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
text_display.config(state=tk.DISABLED)
text_scroll.config(command=text_display.yview)

image_frame = ttk.Frame(notebook)
notebook.add(image_frame, text="图片列表")

image_list_frame = ttk.Frame(image_frame)
image_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

image_scroll = ttk.Scrollbar(image_list_frame)
image_scroll.pack(side=tk.RIGHT, fill=tk.Y)

image_listbox = tk.Listbox(image_list_frame, height=15, yscrollcommand=image_scroll.set)
image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
image_scroll.config(command=image_listbox.yview)

show_button = ttk.Button(image_frame, text="查看选中图片", command=show_image)
show_button.pack(pady=5)

status_label = ttk.Label(frame, text="就绪")
status_label.pack(pady=5)

root.mainloop()
