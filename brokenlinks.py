import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

visited = set()
broken = []

def crawl(url):
    if url in visited:
        return
    visited.add(url)

    try:
        r = requests.get(url, timeout=5)
    except:
        broken.append(url)
        return

    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.find_all("a", href=True):
        full = urljoin(url, link["href"])
        if full.startswith("http"):
            try:
                check = requests.head(full, timeout=5)
                if check.status_code >= 400:
                    broken.append(full)
            except:
                broken.append(full)

crawl("https://www.newyorkspecialed.net")

print("Broken links:")
for b in broken:
    print(b)