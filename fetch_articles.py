import feedparser
import json
import openai
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
import opencc

# 初始化简繁转换器
converter = opencc.OpenCC('t2s.json')

# 数据源 (前3个目前为测试可访问源)
RSS_FEEDS = [
    "https://rsshub.app/sspai",  # 模拟 云见 insight
    "https://rsshub.app/36kr/newsflashes",  # 模拟 辉哥奇谭
    "https://rsshub.app/bbc/chinese",  # 模拟 新智元
    "https://www.economist.com/the-world-this-week/rss.xml",  # 经济学人
]

OUTPUT_FILE = "articles.json"

# 从环境变量获取 Key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_summary(text, is_english=False):
    text_simplified = converter.convert(text)
    if not openai.api_key:
        return text_simplified[:100]
    try:
        if is_english:
            prompt = f"请将以下英文新闻翻译成中文，并用不超过100字的简体中文进行总结：{text}"
        else:
            prompt = f"请帮我将以下内容总结为不超过100字的简体中文摘要：{text_simplified}"

        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个中文写作和翻译助手。"},
                {"role": "user", "content": prompt}
            ]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("[AI 摘要生成失败]", e)
        return text_simplified[:100]

def fetch_full_content(url):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")

        if soup.find("article"):
            html = str(soup.find("article"))
        elif soup.find("div", class_="rich_media_content"):
            html = str(soup.find("div", class_="rich_media_content"))
        else:
            html = str(soup.body)
        return converter.convert(html)
    except Exception as e:
        return f"<p>无法加载全文: {e}</p>"

def fetch_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            is_english = "economist.com" in feed_url
            for entry in feed.entries[:3]:
                # 获取全文 HTML
                if 'content' in entry and entry.content:
                    full_html = converter.convert(entry.content[0].value)
                else:
                    full_html = fetch_full_content(entry.link)

                summary = generate_summary(entry.get("summary", entry.get("title", "")), is_english)
                articles.append({
                    "source": converter.convert(feed.feed.get("title", "未知来源")),
                    "author": converter.convert(entry.get("author", feed.feed.get("title", "未知作者"))),
                    "time": entry.get("published", datetime.now().isoformat()),
                    "summary": summary,
                    "content": full_html,
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
