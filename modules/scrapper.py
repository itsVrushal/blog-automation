
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

from soupsieve import select_one
from config import MAX_ARTICLES

def scrape_hacker_news(limit = 20):
    url="https://news.ycombinator.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    stories = soup.select(".athing")[:limit]
    for story in stories:
        title = story.select_one(".titleline a").get_text(strip=True)#type: ignore
        link = story.select_one(".titleline")["href"]#type: ignore
        if not link.startswith("http"):#type: ignore
            link = f"https://news.ycombinator.com/{link}"
        subtext = story.find_next_sibling("tr").select_one(".subtext") #type: ignore
        score = subtext.select_one(".score") #type: ignore
        score_text = score.get_text(strip=True) if score else "0 points"
        
        user = subtext.select_one(".hnuser") #type: ignore
        user_text = user.get_text(strip=True) if user else "unknown"
        
        age = subtext.select_one(".age") #type: ignore
        age_text = age.get_text(strip=True) if age else ""
        articles.append({
            "title": title,
            "source_link": link,
            "source": "Hacker News",
            "score": score_text,
            "author": user_text,
            "post_age": age_text,
            "scraped_at": datetime.now().isoformat()
        })
        return articles

def scrape_reddit_news(limit=20):
    """Scrape hot posts from r/technology"""
    url = "https://www.reddit.com/r/technology/hot/.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    articles = []
    posts = data["data"]["children"][:limit]
    
    for post in posts:
        post_data = post["data"]
        title = post_data.get("title", "")
        link = post_data.get("url", "")
        
        if title and link:
            articles.append({
                "title": title,
                "source_link": link,
                "source": "r/technology",
                "score": f"{post_data.get('score', 0)} upvotes",
                "author": post_data.get("author", "unknown"),
                "post_age": "",
                "scraped_at": datetime.now().isoformat()
            })
    
    return articles


def scrape_all():
    all_articles=[]
    print("Starting scraping articles")
    print("Scraping Hackernews")
    try:
        hn_articles = scrape_hacker_news(20)
        all_articles.extend(hn_articles) #type: ignore
        print(f"  Found {len(hn_articles)} articles") #type: ignore
    except Exception as e:
        print(e)

    print("Scraping r/technology")
    try:
        reddit_articles = scrape_reddit_news(20)
        all_articles.extend(reddit_articles) #type: ignore
        print(f"  Found {len(reddit_articles)} articles") #type: ignore
    except Exception as e:
        print(e)
    
    return all_articles
