import feedparser
import json
import openai
from datetime import datetime
import os

# 真实可用的RSS地址（先测试一下用国外可访问的公共源，例如 BBC 中文）
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/zhongwen/simp/rss.xml",  # BBC 中文
    "https://36kr.com/feed"  # 36氪
]

OUTPUT_FILE = "articles.json"
openai.api_key = os.getenv("OPENAI_API_KEY")  # 从Secrets读取

def generate_summary(text):
    # 如果没配置OPENAI_API_KEY，则直接取前100字
    if not openai.api_key:
        return text[:100]

    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个中文写作助手。"},
                {"role": "user", "content": f"请帮我将以下内容总结为不超过100字的中文摘要：{text}"}
            ]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("[AI 摘要生成失败]", e)
        return text[:100]

def fetch_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                summary = generate_summary(entry.get("summary", entry.get("title", "")))
                articles.append({
                    "source": feed.feed.get("title", "未知来源"),
                    "author": entry.get("author", feed.feed.get("title", "未知作者")),
                    "time": entry.get("published", datetime.now().isoformat()),
                    "summary": summary,
                    "content": entry.get("summary", ""),
                    "url": entry.link,
                    "favorite": False
                })
        except Exception as e:
            print(f"[抓取失败] {feed_url} - {e}")
    return articles

if __name__ == "__main__":
    data = fetch_articles()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已更新 {len(data)} 篇文章到 {OUTPUT_FILE}")
