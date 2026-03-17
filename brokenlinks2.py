import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time

domain = "https://www.newyorkspecialed.net"

visited = set()
to_visit = [domain]

broken_links = []
internal_links = []

while to_visit:

    url = to_visit.pop()

    if url in visited:
        continue

    visited.add(url)

    try:
        r = requests.get(url, timeout=10)
        status = r.status_code
    except:
        broken_links.append((url,"connection_error"))
        continue

    print("Crawling:",url)

    if status >= 400:
        broken_links.append((url,status))
        continue

    soup = BeautifulSoup(r.text,"html.parser")

    for link in soup.find_all("a",href=True):

        full = urljoin(url,link["href"])

        parsed = urlparse(full)

        if domain in full:

            internal_links.append((url,full))

            if full not in visited:
                to_visit.append(full)

    time.sleep(0.5)

df_broken = pd.DataFrame(broken_links,columns=["URL","Status"])
df_links = pd.DataFrame(internal_links,columns=["Source Page","Link"])

df_broken.to_csv("broken_pages.csv",index=False)
df_links.to_csv("internal_links.csv",index=False)

print("Crawl complete")
print("Broken pages:",len(df_broken))