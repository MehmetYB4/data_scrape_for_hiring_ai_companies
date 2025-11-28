import requests
from bs4 import BeautifulSoup

url = "https://turkiye.ai/portfolio/2pro-danismanlik/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

print("Title tag:", soup.title.string)
h1s = soup.find_all("h1")
for h1 in h1s:
    print("H1:", h1)
    print("Classes:", h1.get("class"))

# Check for other potential name containers
print("Meta title:", soup.find("meta", property="og:title"))
