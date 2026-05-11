import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

DEV_TO_API_KEY = os.getenv("DEV_TO_API_KEY")

INPUT_DIR = "raw_files"


def get_latest_files(topic=None):
    md_files = [f for f in os.listdir(INPUT_DIR) if f.endswith("_blog.md")]
    if not md_files:
        return None, None
    md_files.sort(key=lambda f: os.path.getmtime(os.path.join(INPUT_DIR, f)), reverse=True)
    blog_file = md_files[0]
    title_file = blog_file.replace("_blog.md", "_title.md")
    blog_path = os.path.join(INPUT_DIR, blog_file)
    title_path = os.path.join(INPUT_DIR, title_file)
    return title_path, blog_path


def read_title_file(topic=None):
    title_path, _ = get_latest_files(topic)
    if title_path and os.path.exists(title_path):
        with open(title_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def read_blog_file(topic=None):
    _, blog_path = get_latest_files(topic)
    if blog_path and os.path.exists(blog_path):
        with open(blog_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def extract_tags(content):
    tags = ["tech", "ai"]
    content_lower = content.lower()
    if "ai" in content_lower or "gpt" in content_lower or "llm" in content_lower:
        tags.append("artificialintelligence")
    if "google" in content_lower:
        tags.append("google")
    if "openai" in content_lower:
        tags.append("openai")
    if "meta" in content_lower or "facebook" in content_lower:
        tags.append("meta")
    return list(set(tags))[:3]


def publish_to_devto(title, content, tags):
    url = "https://dev.to/api/articles"
    
    headers = {
        "api-key": DEV_TO_API_KEY,
        "Content-Type": "application/json"
    }
    
    article = {
        "article": {
            "title": title,
            "body_markdown": content,
            "tags": tags,
            "published": True
        }
    }
    
    response = requests.post(url, headers=headers, json=article, timeout=30.0)
    result = response.json()
    
    if response.status_code != 201:
        print(f"Error: {response.status_code} - {result}")
        return None
    
    return result

def remove_title(content, title):
    lines = content.split("\n")
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if line_stripped.startswith("# "):
            rest = line_stripped[2:].strip()
            if rest == title or rest == title[:30]:
                continue
        elif line_stripped == title or line_stripped == f"# {title}":
            continue
            
        cleaned_lines.append(line)
    
    result = "\n".join(cleaned_lines)
    lines = result.split("\n")
    
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return "\n".join(lines)

def main():
    print("=" * 50)
    print("Publishing to Dev.to")
    print("=" * 50)
    
    title = read_title_file()
    content = read_blog_file()
    
    if not title or not content:
        print("No blog files found")
        return
    
    print(f"\nFound blog files")
    
    tags = extract_tags(content)
    
    print(f"\nTitle: {title}")
    print(f"Tags: {tags}")
    print("\nPublishing...")
    
    result = publish_to_devto(title, content, tags)
    
    if result:
        print(f"\n[OK] Successfully published!")
        print(f"  URL: {result.get('url')}")
    else:
        print("\n[X] Failed to publish")


if __name__ == "__main__":
    main()