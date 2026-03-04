import requests
import feedparser
import json
import os
import re
import time
import html
from datetime import datetime, timedelta

BOT_TOKEN = "8563577508:AAGvTSX2NunzroN0vjbvtZ69n6fQjkL5EO4"
CHAT_ID = "-1003502019216"

SEEN_FILE = "seen_links.json"
DIGEST_FILE = "digest_buffer.json"
STATE_FILE = "digest_state.json"

MAX_POSTS_PER_RUN = 300
MIN_ITEMS_FOR_DIGEST = 1  # change to 3 if you want minimum 3 headlines

RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.thehindubusinessline.com/news/feeder/default.rss",
    "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "https://www.livemint.com/rss/markets",
    "https://www.thehansindia.com/sports/feed",
    "https://www.livemint.com/rss/news",
    #--------------------VIDEO--------------------------------------
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCknLrEdhRCp1aegoMqRaCZg",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCUI9vm69ZbAqRK3q3vKLWCQ"
]

# ------------------ Helpers ------------------

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
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

# ------------------ Load State ------------------

if os.path.exists(SEEN_FILE):
    seen_links = set(json.load(open(SEEN_FILE)))
else:
    seen_links = set()

if os.path.exists(DIGEST_FILE):
    digest_data = json.load(open(DIGEST_FILE))
else:
    digest_data = []

if os.path.exists(STATE_FILE):
    state = json.load(open(STATE_FILE))
else:
    state = {"last_sent": ""}

updated_links = set(seen_links)
posts_sent = 0

# ------------------ NEWS POSTING ------------------

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

                digest_data.append({
                    "title": title,
                    "link": link,
                    "time": datetime.utcnow().isoformat()
                })

                time.sleep(0.7)

        except:
            pass

    if posts_sent >= MAX_POSTS_PER_RUN:
        break

# ------------------ DIGEST POSTING ------------------

# Convert UTC to IST
now = datetime.utcnow() + timedelta(hours=5, minutes=30)

current_hour = now.strftime("%H")
current_date = now.strftime("%Y-%m-%d")

digest_hours = ["09", "15", "21", "03"]

digest_id = f"{current_date}-{current_hour}"

if (
    current_hour in digest_hours
    and state["last_sent"] != digest_id
    and len(digest_data) >= MIN_ITEMS_FOR_DIGEST
):

    # Sort newest first
    recent_items = sorted(
        digest_data,
        key=lambda x: x["time"],
        reverse=True
    )

    digest_text = "🌍 <b>WORLD IN LAST FEW HOURS</b>\n\n"

    for item in recent_items:
        digest_text += f"🟦 {item['title']}\n"
        digest_text += f"<a href='{item['link']}'>🔗 News Link</a>\n\n"

    send_message(digest_text)

    state["last_sent"] = digest_id
    digest_data = []

# ------------------ Save State ------------------

json.dump(list(updated_links), open(SEEN_FILE, "w"))
json.dump(digest_data, open(DIGEST_FILE, "w"))
json.dump(state, open(STATE_FILE, "w"))
