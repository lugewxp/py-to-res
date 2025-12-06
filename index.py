import requests
from bs4 import BeautifulSoup

url = input("请输入网页URL: ")

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
    
    print(clean_text)
    
except requests.exceptions.RequestException as e:
    print(f"网络请求错误: {e}")
except Exception as e:
    print(f"发生错误: {e}")
