import json
import os
import time
import requests
import base64
from google import genai
from google.genai import errors
from dotenv import load_dotenv
import config

load_dotenv()

client = genai.Client()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

MAX_RETRIES = 5
INITIAL_DELAY = 15

INPUT_FILE = "raw_files/gemini_input.json"
OUTPUT_FILE = "raw_files/processed_Articles.json"
PROCESSED_TOPICS_FILE = "raw_files/processed_topics.json"

LLM_PROVIDER = config.LLM_PROVIDER


def read_input():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)


def load_processed_topics():
    if os.path.exists(PROCESSED_TOPICS_FILE):
        with open(PROCESSED_TOPICS_FILE, "r") as f:
            return json.load(f)
    return []


def save_processed_topic(topic):
    topics = load_processed_topics()
    topics.append(topic)
    with open(PROCESSED_TOPICS_FILE, "w") as f:
        json.dump(topics, f, indent=2)


def call_nvidia(prompt, max_tokens=512):
    print(f"Calling NVIDIA model: {config.NVIDIA_MODEL}")
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json"
    }
    payload = {
        "model": config.NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 1.0,
        "top_p": 1.0
    }
    response = requests.post(NVIDIA_URL, headers=headers, json=payload, timeout=60)
    print(f"NVIDIA response status: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"Nvidia API error: {response.status_code} - {response.text}")
    result = response.json()
    print(f"NVIDIA raw response: {result}")
    if "choices" not in result or not result["choices"]:
        raise Exception(f"NVIDIA empty response: {result}")
    return result["choices"][0]["message"]["content"]


def call_gemini(prompt, model="gemini-3.1-pro-preview"):
    response = client.models.generate_content(model=model, contents=prompt)
    if response.text:
        return response.text
    return None


def call_llm(prompt, max_tokens=512):
    if LLM_PROVIDER == "nvidia":
        return call_nvidia(prompt, max_tokens)
    else:
        return call_gemini(prompt)


def call_llm_with_retry(prompt, model=None, max_tokens=512):
    for attempt in range(MAX_RETRIES):
        try:
            if LLM_PROVIDER == "nvidia":
                result = call_nvidia(prompt, max_tokens)
                if result:
                    return result
            else:
                model = model or config.GEMINI_MODEL
                response = client.models.generate_content(model=model, contents=prompt)
                if response.text:
                    return response.text
        except errors.ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                delay = INITIAL_DELAY * (2 ** attempt)
                print(f"Rate limit hit. Waiting {delay}s before retry ({attempt + 1}/{MAX_RETRIES})...")
                time.sleep(delay)
                continue
            raise
    raise Exception(f"Failed after {MAX_RETRIES} retries")


def rank_topics(articles):
    titles = [article["title"] for article in articles]
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
    
    processed_topics = load_processed_topics()
    excluded_text = ""
    if processed_topics:
        excluded_text = f"\n\nEXCLUDE these already processed topics:\n" + "\n".join([f"- {t}" for t in processed_topics[:10]])

    prompt = f"""You are a research assistant. Rank the following 5 topics based on their relevancy for a tech blog post.

Topics:
{titles_text}
{excluded_text}

Return a JSON array with just the ranked topic names (from most relevant to least relevant) in this format:
["topic1", "topic2", "topic3", "topic4", "topic5"]

IMPORTANT: Do NOT include any topic from the excluded list above. Choose a NEW topic that has NOT been processed yet.
Consider: current interest, uniqueness, and potential reader engagement."""

    result = call_llm_with_retry(prompt)
    if not result:
        print(f"Warning: Empty response from LLM. Prompt: {prompt[:200]}...")
        return titles
    
    try:
        text = result.strip("```json").strip("```").strip("`").strip()
        ranked = json.loads(text)
        return ranked
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {result[:500]}")
        import re
        matches = re.findall(r'["\']([^"\']+)["\']', result)
        if matches:
            print(f"Extracted topics: {matches[:5]}")
            return matches[:5]
        return titles


def research_topic(topic):
    prompt = f"""Provide in-depth research on the following topic for a comprehensive blog post:

Topic: {topic}

Include:
1. Background and context
2. Key details and recent developments
3. Different perspectives
4. Implications
5. Interesting facts or lesser-known aspects
6. Future outlook

Make it comprehensive and engaging for readers."""

    result = call_llm_with_retry(prompt, max_tokens=1024)
    if not result:
        print(f"Warning: Empty response from LLM for research.")
        return "Research unavailable."
    return result


def save_output(data):
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing = json.load(f)

    existing.append(data)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    
    save_processed_topic(data.get("topic", ""))


def main():
    data = read_input()
    articles = data["articles_for_analysis"]

    print(f"Using LLM provider: {LLM_PROVIDER}")
    print("\nRanking topics...")
    ranked_topics = rank_topics(articles)
    top_topic = ranked_topics[0]

    print(f"\nTop topic: {top_topic}")

    for article in articles:
        if article["title"] == top_topic:
            top_article = article
            break

    print("\nResearching topic...")
    research = research_topic(top_topic)

    output = {
        "generated_at": data["generated_at"],
        "topic": top_topic,
        "source_link": top_article["source_link"],
        "research": research
    }

    save_output(output)
    print(f"Research completed for topic: {top_topic}")


if __name__ == "__main__":
    main()