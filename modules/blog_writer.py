import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

INPUT_FILE = "raw_files/processed_Articles.json"
OUTPUT_DIR = "raw_files"


def read_processed_article():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)


def generate_title(article_data):
    topic = article_data.get("topic", "Unknown Topic")
    source_link = article_data.get("source_link", "")
    research = article_data.get("research", "")

    prompt = f"""You are a professional tech blog writer. Generate an attention-grabbing, click-worthy title for a blog post about:

Topic: {topic}
Source: {source_link}
Research Summary: {research[:2000]}

Requirements:
- Create a compelling, specific title that makes people want to click
- Use power words, numbers, or intriguing hooks when appropriate
- Keep it under 80 characters
- Avoid clickbait but make it genuinely compelling
- Output ONLY the title, nothing else"""

    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    if not response.text:
        print(f"Warning: Empty response from Gemini for title generation.")
        return None
    
    return response.text.strip()


def generate_blog(article_data):
    topic = article_data.get("topic", "Unknown Topic")
    source_link = article_data.get("source_link", "")
    research = article_data.get("research", "")

    prompt = f"""You are a professional tech blog writer. Your goal is to write an extremely detailed, engaging, and hook-driven blog post that captures readers from the first sentence.

Topic: {topic}
Source: {source_link}
Research Content:
{research}

Write a professional blog post with:

1. HOOK (First 2-3 sentences) - Start with a shocking fact, provocative question, or bold statement that grabs attention immediately

2. INTRODUCTION (2-3 paragraphs) - Set the context, explain why this matters to readers, establish credibility

3. BODY SECTIONS (Multiple detailed sections):
   - Background and context (what led to this)
   - Key developments and details (the core story)
   - Different perspectives (experts, companies, users)
   - Implications and impact (why this matters)
   - Lesser-known aspects or surprising facts
   - Future outlook and what to watch for

4. COMPREHENSIVE COVERAGE - Each section should be richly detailed with specific examples, data points, and analysis

5. ENGAGING FLOW - Use transitions that pull readers to the next section

6. CONCLUSION - End with a thought-provoking statement about what this means for the future

7. CALL TO ACTION - Encourage readers to engage (comment, share, follow for more)

Guidelines:
- Write in a conversational but professional tone
- Use concrete examples and specific details
- Include relevant statistics or data when available
- Make it scannable with subheadings
- Keep the energy high throughout
- Make it so engaging that readers can't stop reading
- Target 2000-3000 words minimum
- Output ONLY the blog content, no title at the start, no explanations"""

    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    if not response.text:
        print(f"Warning: Empty response from Gemini for blog generation.")
        return None, None
    
    return response.text, article_data.get("generated_at", "")


def save_title(title, topic):
    safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_").strip()[:50]
    if not safe_topic:
        safe_topic = "blog_post"

    title_path = os.path.join(OUTPUT_DIR, f"{safe_topic}_title.md")
    
    with open(title_path, "w", encoding="utf-8") as f:
        f.write(title.strip())
    print(f"Title saved to: {title_path}")
    
    return title_path


def save_blog(blog_content, topic, generated_at):
    safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_").strip()[:50]
    if not safe_topic:
        safe_topic = "blog_post"

    blog_path = os.path.join(OUTPUT_DIR, f"{safe_topic}_blog.md")
    json_path = os.path.join(OUTPUT_DIR, f"{safe_topic}_blog.json")

    with open(blog_path, "w", encoding="utf-8") as f:
        f.write(blog_content)
    print(f"Blog saved to: {blog_path}")

    blog_data = {
        "topic": topic,
        "generated_at": generated_at,
        "title_file": f"{safe_topic}_title.md",
        "blog_file": f"{safe_topic}_blog.md",
        "saved_at": str(blog_path)
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(blog_data, f, indent=2)
    print(f"Blog metadata saved to: {json_path}")

    return blog_path


def main():
    print("=" * 50)
    print("Starting Blog Generation")
    print("=" * 50)

    article_data = read_processed_article()
    topic = article_data.get("topic", "Unknown")
    print(f"\nTopic: {topic}")

    print("\nGenerating title with Gemini...")
    title = generate_title(article_data)
    
    if title:
        title_path = save_title(title, topic)
        print(f"✓ Title saved!")
    else:
        print("✗ Failed to generate title")
        return

    print("\nGenerating blog with Gemini...")
    blog_content, generated_at = generate_blog(article_data)

    if blog_content:
        output_path = save_blog(blog_content, topic, generated_at)
        print(f"\n✓ Blog successfully generated and saved!")
        print(f"  Location: {output_path}")
    else:
        print("\n✗ Failed to generate blog")


if __name__ == "__main__":
    main()