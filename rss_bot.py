import requests
import feedparser
import json
import os
import re
import time
import html
from datetime import datetime

BOT_TOKEN = "8563577508:AAGvTSX2NunzroN0vjbvtZ69n6fQjkL5EO4"
CHAT_ID = "-1003502019216"

SEEN_FILE = "seen_links.json"
DIGEST_FILE = "digest_buffer.json"

DIGEST_TIMES = ["09:00", "15:00", "21:00", "03:00"]
MAX_POSTS_PER_RUN = 30

RSS_FEEDS = [
     "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.thehindubusinessline.com/news/feeder/default.rss",
    "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "https://www.livemint.com/rss/markets",
    "https://www.livemint.com/rss/news",
    "https://www.livemint.com/rss/companies"
]

# ---------- Helpers ----------

def clean_html(raw_html):
    return re.sub('<.*?>', '', raw_html).strip()

def get_summary(text, word_limit=30):
    words = text.split()
    return " ".join(words[:word_limit]) + "..." if words else ""

def extract_image(entry):
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media:
                return media['url']

    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type') and "image" in link.get('type'):
                return link.get('href')

    if hasattr(entry, 'summary'):
        match = re.search(r'<img.*?src="(.*?)"', entry.summary)
        if match:
            return match.group(1)

    return None

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload)

# ---------- Load files ----------

if os.path.exists(SEEN_FILE):
    seen_links = set(json.load(open(SEEN_FILE)))
else:
    seen_links = set()

if os.path.exists(DIGEST_FILE):
    digest_data = json.load(open(DIGEST_FILE))
else:
    digest_data = []

updated_links = set(seen_links)

# ---------- NEWS POSTING ----------

posts_sent = 0

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        if posts_sent >= MAX_POSTS_PER_RUN:
            break

        link = entry.get("link")
        if not link or link in seen_links:
            continue

        title = html.escape(entry.get("title", "No Title"))

        summary = ""
        if hasattr(entry, "summary"):
            summary = html.escape(get_summary(clean_html(entry.summary)))

        image_url = extract_image(entry)

        message = (
            f"🟦 <b><a href='{link}'>{title}</a></b>\n\n"
            f"{summary}\n\n"
            f"<a href='{link}'>🔗 News Link</a>"
        )

        try:
            if image_url:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                payload = {
                    "chat_id": CHAT_ID,
                    "photo": image_url,
                    "caption": message,
                    "parse_mode": "HTML"
                }
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }

            r = requests.post(url, data=payload)

            if r.status_code == 200:
                updated_links.add(link)
                posts_sent += 1

                # Save to digest buffer
                digest_data.append({
                    "title": title,
                    "link": link,
                    "time": datetime.utcnow().isoformat()
                })

                time.sleep(0.7)

        except:
            pass

# ---------- DIGEST POSTING ----------

current_time = datetime.now().strftime("%H:%M")

if current_time in DIGEST_TIMES and digest_data:

    digest_text = "🌍 <b>WORLD IN LAST FEW HOURS</b>\n\n"

    for item in digest_data[-20:]:
        digest_text += f"🟦 {item['title']}\n"
        digest_text += f"<a href='{item['link']}'>🔗 News Link</a>\n\n"

    send_message(digest_text)

    digest_data = []  # clear after sending

# ---------- SAVE FILES ----------

json.dump(list(updated_links), open(SEEN_FILE, "w"))
json.dump(digest_data, open(DIGEST_FILE, "w"))
