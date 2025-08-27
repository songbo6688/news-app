import feedparser
import json
import openai
from datetime import datetime
import os

# 公众号 RSS 地址（占位，后续替换成真实地址）
RSS_FEEDS = [
    "https://rsshub.app/wechat/xxx1",  # 云见 insight
    "https://rsshub.app/wechat/xxx2",  # 辉哥奇谭
    "https://rsshub.app/wechat/xxx3"   # 新智元
]

OUTPUT_FILE = "articles.json"
openai.api_key = os.getenv("OPENAI_API_KEY")  # 从 GitHub Secrets 读取

# 调用 AI 生成 100 字摘要
def generate_summary(text):
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
        print("AI 摘要生成失败：", e)
        return text[:100]

# 抓取 RSS 数据
def fetch_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:  # 每个源取最近 3 篇
            summary = generate_summary(entry.get("summary", entry.get("title", "")))
            articles.append({
                "source": feed.feed.title,
                "author": entry.get("author", feed.feed.title),
                "time": entry.get("published", datetime.now().isoformat()),
                "summary": summary,
                "content": entry.get("summary", ""),
                "url": entry.link,
                "favorite": False
            })
    return articles

if __name__ == "__main__":
    data = fetch_articles()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已更新 {len(data)} 篇文章到 {OUTPUT_FILE}")
