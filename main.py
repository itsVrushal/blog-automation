import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from modules.scrapper import scrape_all
from modules.ranker import rank_articles, get_top_articles,load_previous_articles
from modules.researcher import rank_topics, research_topic, save_processed_topic
from modules.blog_writer import generate_title, save_title, generate_blog, save_blog
from modules.hashnode_write import publish_to_hashnode, extract_tags, read_title_file
from modules.dev_to_write import publish_to_devto, read_blog_file
from datetime import datetime
import json
import os

articles = scrape_all()

print(f"\nTotal articles scraped: {len(articles)}")
print("\n--- JSON Output ---")

output = {
    "scraped_at": datetime.now().isoformat(),
    "total_articles": len(articles),
    "sources": ["Hacker News", "r/technology"],
    "articles": articles
}

print(json.dumps(output,indent=2))
with open("raw_files/tech_news.json","w") as f:
    json.dump(output,f,indent=2)
print("Output saved")
with open("raw_files/tech_news.json", "r") as f:
    data = json.load(f)

existing = load_previous_articles("raw_files/processed_Articles.json")
existing_titles = [a.get("topic", "") for a in existing]
existing_titles = [t for t in existing_titles if t]
ranked = rank_articles(data["articles"],existing_titles) #type: ignore Add a existing articles param


print(f"\nTotal unique articles: {len(ranked)}")
print("\n=== TOP 10 RANKED ARTICLES ===\n")

for i, article in enumerate(ranked[:10], 1):
    print(f"{i}. [{article['rank_score']}] {article['title']}")
    print(f"   Source: {article['source']} | Score: {article.get('score', 'N/A')}")
    print()

top_5 = get_top_articles(data["articles"], 5)

print("\n=== READY FOR GEMINI ANALYSIS ===\n")
for i, article in enumerate(top_5, 1):
    print(f"{i}. {article['title']}")
    print(f"   Link: {article['source_link']}")
    print(f"   Score: {article['rank_score']}")
    print()

output = {
    "generated_at": datetime.now().isoformat(),
    "articles_for_analysis": top_5
}

with open("raw_files/gemini_input.json", "w") as f:
    json.dump(output, f, indent=2)

print("Saved top 5 articles to gemini_input.json")

with open("raw_files/gemini_input.json", "r") as f:
    top_5 =  json.load(f)
top_5_articles = top_5["articles_for_analysis"]
ranked_topics = rank_topics(top_5_articles)
top_topic = ranked_topics[0]

for article in top_5_articles:
    if article["title"] == top_topic:
        top_article = article
        break

research = research_topic(top_topic)

output = {
    "generated_at": top_5["generated_at"],
    "topic": top_topic,
    "source_link": top_article["source_link"], #type: ignore
    "research": research
}
OUTPUT_FILE = "raw_files/processed_Articles.json"

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f, indent=2)

save_processed_topic(top_topic)
print(f"Research completed for topic: {top_topic}")

print("\n" + "="*50)
print("Generating Blog Post...")
print("="*50)

print("\nGenerating title...")
title = generate_title(output)
if title:
    title_path = save_title(title, top_topic)
    print(f"✓ Title generated: {title}")
else:
    print("✗ Failed to generate title")
    exit()

print("\nGenerating blog content...")
blog_content, generated_at = generate_blog(output)
if blog_content:
    output_path = save_blog(blog_content, top_topic, generated_at)
    print(f"\n✓ Blog successfully generated!")
    print(f"  Saved to: {output_path}")
    
    print("\n" + "="*50)
    print("Publishing to Hashnode...")
    print("="*50)
    
    title = read_title_file()
    blog_content = read_blog_file()
    tags = extract_tags(blog_content) if blog_content else []
    
    if title:
        print(f"\nTitle: {title}")
    if tags:
        print(f"Tags: {tags}")
    
    result = publish_to_hashnode(title, blog_content, tags)
    if result:
        print(f"\n[OK] Successfully published to Hashnode!")
        print(f"  URL: {result.get('url')}")
    
    print("\n" + "="*50)
    print("Publishing to Dev.to...")
    print("="*50)
    
    devto_result = publish_to_devto(title, blog_content, tags)
    if devto_result:
        print(f"\n[OK] Successfully published to Dev.to!")
        print(f"  URL: {devto_result.get('url')}")