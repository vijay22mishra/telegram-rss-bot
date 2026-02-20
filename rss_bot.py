import requests
import feedparser
import json
import os
import subprocess

BOT_TOKEN = "8563577508:AAGvTSX2NunzroN0vjbvtZ69n6fQjkL5EO4"
CHAT_ID = "-1003502019216"

RSS_FEEDS = [
    "https://khabargaon.com/category/lifestyle/feed",
    "https://khabargaon.com/category/business/feed",
    "https://khabargaon.com/category/sports/feed",
    "https://khabargaon.com/category/entertainment/feed",
    "https://khabargaon.com/category/religion/feed",
    "https://khabargaon.com/category/state/feed",
    "https://khabargaon.com/category/international/feed",
    "https://khabargaon.com/category/national/feed"
]

SEEN_FILE = "seen_links.json"

# Load previous links
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen_links = set(json.load(f))
else:
    seen_links = set()

new_links = set(seen_links)

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:10]:
        link = entry.link

        if link in seen_links:
            continue

        title = entry.title
        message = f"{title}\n{link}"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}

        requests.post(url, data=payload)

        new_links.add(link)

# Save updated links
with open(SEEN_FILE, "w") as f:
    json.dump(list(new_links), f)

# Commit file back to GitHub
subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
subprocess.run(["git", "add", SEEN_FILE])
subprocess.run(["git", "commit", "-m", "Update seen links"])
subprocess.run(["git", "push"])
