import requests
from bs4 import BeautifulSoup

url = input("请输入网页URL: ")
try:
response = requests.get(url)
response.raise_for_status()
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')
text = soup.get_text()
print(text)
except requests.exceptions.RequestException as e:
print("错误: ", e)
