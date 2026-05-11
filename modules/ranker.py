import json
from difflib import SequenceMatcher
from datetime import datetime

def load_previous_articles(filepath="tech_news.json"):
    """Load previously processed articles to avoid duplicates"""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            return data.get("articles", [])
    except:
        return []

def is_duplicate(new_title, existing_titles, threshold=0.7):
    """Check if article is duplicate using similarity ratio"""
    new_title_lower = new_title.lower()
    for existing in existing_titles:
        similarity = SequenceMatcher(None, new_title_lower, existing.lower()).ratio()
        if similarity > threshold:
            return True
    return False

def rank_articles(articles, existing_titles=None):
    """Rank articles by multiple factors"""
    if existing_titles is None:
        existing_titles = []
    
    ranked = []
    
    for article in articles:
        score = 0
        
        article_score = article.get("score", "0")
        if "points" in article_score:
            try:
                score += int(article_score.split()[0]) * 1.0
            except:
                pass
        elif "upvotes" in article_score:
            try:
                score += int(article_score.split()[0]) * 1.0
            except:
                pass
        
        if article.get("source") == "Hacker News":
            score += 50
        elif article.get("source") == "r/technology":
            score += 30
        
        title = article.get("title", "")
        if any(kw in title.lower() for kw in ["ai", "gpt", "llm", "openai", "google", "meta", "anthropic"]):
            score += 100
        if any(kw in title.lower() for kw in ["launch", "release", "new", "announce"]):
            score += 30
        
        if is_duplicate(title, existing_titles):
            continue
        
        ranked.append({
            **article,
            "rank_score": int(score)
        })
    
    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    return ranked

def get_top_articles(articles, top_n=5):
    """Get top N articles for Gemini analysis"""
    ranked = rank_articles(articles)
    return ranked[:top_n]