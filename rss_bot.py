import requests
import feedparser
import json
import os
import re
import time

BOT_TOKEN = "8563577508:AAGvTSX2NunzroN0vjbvtZ69n6fQjkL5EO4"
CHAT_ID = "-1003502019216"

RSS_FEEDS = [
    "https://khabargaon.com/category/business/feed",
    "https://khabargaon.com/category/sports/feed",
    "https://nitter.net/_groww/rss",
    "https://nitter.net/ReutersBiz/rss",
    "https://nitter.net/livemint/rss",
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.thehindubusinessline.com/news/feeder/default.rss",
    "https://www.thehindubusinessline.com/markets/feeder/default.rss",
    "https://khabargaon.com/category/international/feed",
    "https://khabargaon.com/category/national/feed"
]

SEEN_FILE = "seen_links.json"

# -----------------------------
# Utility Functions
# -----------------------------

def clean_html(raw_html):
    clean = re.sub('<.*?>', '', raw_html)
    return clean.strip()

def get_summary(text, word_limit=30):
    words = text.split()
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit]) + "..."

def extract_image(entry):
    # Method 1: media_content
    if hasattr(entry, 'media_content'):
        try:
            return entry.media_content[0]['url']
        except:
            pass

    # Method 2: enclosures
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type') and "image" in link.get('type'):
                return link.get('href')

    # Method 3: image inside summary HTML
    if hasattr(entry, 'summary'):
        match = re.search(r'<img.*?src="(.*?)"', entry.summary)
        if match:
            return match.group(1)

    return None

# -----------------------------
# Load Previously Posted Links
# -----------------------------

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen_links = set(json.load(f))
else:
    seen_links = set()

updated_links = set(seen_links)

# -----------------------------
# Main Logic
# -----------------------------

MAX_POSTS_PER_RUN = 30
posts_sent = 0

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        if posts_sent >= MAX_POSTS_PER_RUN:
            break

        link = entry.link

        if link in seen_links:
            continue

        title = entry.title

        # Generate summary
        summary = ""
        if hasattr(entry, 'summary'):
            clean_text = clean_html(entry.summary)
            summary = get_summary(clean_text, 30)

        # Extract image
        image_url = extract_image(entry)

        # Final formatted message
        message = (
            f"📰 <b>{title}</b>\n\n"
            f"{summary}\n\n"
            f"<a href='{link}'>🔗 News Link</a>"
        )

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

        response = requests.post(url, data=payload)

        # Small delay to avoid Telegram rate limits
        time.sleep(0.7)

        if response.status_code == 200:
            updated_links.add(link)
            posts_sent += 1

    if posts_sent >= MAX_POSTS_PER_RUN:
        break

# -----------------------------
# Save Updated History
# -----------------------------

with open(SEEN_FILE, "w") as f:
    json.dump(list(updated_links), f)
