import requests
import feedparser

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

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:5]:
        title = entry.title
        link = entry.link

        message = f"{title}\n{link}"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        requests.post(url, data=payload)
