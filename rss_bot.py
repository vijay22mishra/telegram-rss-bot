import requests
import feedparser

BOT_TOKEN = "8563577508:AAGvTSX2NunzroN0vjbvtZ69n6fQjkL5EO4"
CHAT_ID = "-1003502019216"
RSS_URL = "https://khabargaon.com/category/business/feed"

feed = feedparser.parse(RSS_URL)

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
