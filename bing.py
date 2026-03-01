# File: submit_indexnow.py
import csv
import json
import requests

# Your domain and the API Key you generated and uploaded to your root directory
host = "www.newyorkspecialed.net"
api_key = "8a7b6c5d4e3f2a1b9c8d7e6f5a4b3c2d"
key_location = f"https://{host}/{api_key}.txt"

# The CSV file containing your verified indexable URLs
csv_file = "'ahrefs_indexable_urls.csv"
url_list = []

# Extract URLs from the CSV
try:
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL')
            if url and url.startswith(f"https://{host}"):
                url_list.append(url)
except FileNotFoundError:
    print(f"Error: {csv_file} not found. Please ensure the file is in the same directory.")
    exit()

if not url_list:
    print("No valid URLs found to submit.")
    exit()

print(f"Preparing to submit {len(url_list)} URLs to IndexNow...")

# IndexNow allows up to 10,000 URLs per request. 
# We build the JSON payload per their official documentation.
payload = {
    "host": host,
    "key": api_key,
    "keyLocation": key_location,
    "urlList": url_list
}

headers = {
    "Content-Type": "application/json; charset=utf-8"
}

# The unified IndexNow endpoint automatically routes to Bing, Yandex, etc.
endpoint = "https://api.indexnow.org/indexnow"

# Fire the POST request
response = requests.post(endpoint, data=json.dumps(payload), headers=headers)

if response.status_code == 200:
    print("SUCCESS: 200 OK. URLs successfully submitted to IndexNow.")
elif response.status_code == 202:
    print("SUCCESS: 202 Accepted. IndexNow received the request and is processing it.")
elif response.status_code == 400:
    print("FAILED: 400 Bad Request. Check your payload formatting.")
elif response.status_code == 403:
    print(f"FAILED: 403 Forbidden. The search engine could not verify your key at {key_location}.")
    print("Make sure you uploaded the .txt file to your live server first!")
elif response.status_code == 422:
    print("FAILED: 422 Unprocessable Entity. The URLs don't match the host or key.")
else:
    print(f"UNKNOWN ERROR: Status Code {response.status_code}")
    print(response.text)