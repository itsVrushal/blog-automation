import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

HASHNODE_TOKEN = os.getenv("HASHNODE_TOKEN")
HASHNODE_PUBLICATION_ID = os.getenv("HASHNODE_PUBLICATION_ID")

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
    return list(set(tags))[:4]


def publish_to_hashnode(title, content, tags):
    url = "https://gql.hashnode.com"
    headers = {
        "Authorization": HASHNODE_TOKEN,
        "Content-Type": "application/json"
    }
    
    tag_objects = []
    for tag in tags:
        slug = tag.lower().replace(" ", "-")
        tag_objects.append({"name": tag, "slug": slug})
    
    create_draft_query = """
    mutation CreateDraft($input: CreateDraftInput!) {
        createDraft(input: $input) {
            draft {
                id
                slug
                title
            }
        }
    }
    """
    
    create_variables = {
        "input": {
            "title": title,
            "contentMarkdown": content,
            "publicationId": HASHNODE_PUBLICATION_ID,
            "tags": tag_objects
        }
    }
    
    response = requests.post(url, headers=headers, json={"query": create_draft_query, "variables": create_variables}, timeout=30.0)
    result = response.json()
    
    if "errors" in result:
        print(f"Create draft error: {result['errors']}")
        return None
    
    draft = result.get("data", {}).get("createDraft", {}).get("draft", {})
    draft_id = draft.get("id")
    
    if not draft_id:
        print(f"No draft ID returned: {result}")
        return None
    
    print(f"Draft created: {draft_id}")
    
    publish_draft_query = """
    mutation PublishDraft($input: PublishDraftInput!) {
        publishDraft(input: $input) {
            post {
                id
                slug
                url
            }
        }
    }
    """
    
    publish_variables = {
        "input": {
            "draftId": draft_id
        }
    }
    
    publish_response = requests.post(url, headers=headers, json={"query": publish_draft_query, "variables": publish_variables}, timeout=30.0)
    publish_result = publish_response.json()
    
    if "errors" in publish_result:
        print(f"Publish draft error: {publish_result['errors']}")
        return None
    
    post = publish_result.get("data", {}).get("publishDraft", {}).get("post", {})
    return post

def main():
    print("=" * 50)
    print("Publishing to Hashnode")
    print("=" * 50)
    
    title = read_title_file()
    content = read_blog_file()
    
    if not title or not content:
        print("No blog files found")
        return
    
    print(f"\nFound: {title}")
    
    tags = extract_tags(content)
    
    print(f"\nTitle: {title}")
    print(f"Tags: {tags}")
    print("\nPublishing...")
    
    result = publish_to_hashnode(title, content, tags)
    
    if result:
        print(f"\n[OK] Successfully published!")
        print(f"  URL: {result.get('url')}")
    else:
        print("\n[X] Failed to publish")


if __name__ == "__main__":
    main()