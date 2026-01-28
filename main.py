import feedparser
import smtplib
import ssl
import os
import datetime
from email.message import EmailMessage
import anthropic

import json

HISTORY_FILE = 'history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_history(history_set):
    # Convert set to list and save
    # Keep only last 1000 entries to prevent infinite growth
    history_list = list(history_set)[-1000:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history_list, f)

def fetch_feed_entries(url, topic, history, count=10):
    """Fetches top entries from a Google News or Reddit RSS feed, filtering duplicates."""
    try:
        # Custom User-Agent is often needed for Reddit RSS to work
        feed = feedparser.parse(url, agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        if feed.bozo:
            print(f"Warning: Potential issue parsing feed for {topic}: {feed.bozo_exception}")
        
        entries = feed.entries[:count]
        data = []
        new_links = []
        
        for entry in entries:
            if entry.link in history:
                continue
                
            # RSS feeds usually have 'title', 'link', and sometimes 'description' or 'summary'
            summary = getattr(entry, 'summary', '')
            # Clean up summary HTML if needed, but for now raw is okay for the LLM to parse
            data.append(f"- Title: {entry.title}\n  Link: {entry.link}\n  Snippet: {summary}\n")
            new_links.append(entry.link)
            
        return data, new_links
    except Exception as e:
        print(f"Error fetching {topic}: {e}")
        return [], []

def generate_digest_with_llm(news_data):
    """Uses Claude 3.5 Haiku to generate a cohesive HTML newsletter."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "<h1>Error</h1><p>ANTHROPIC_API_KEY is missing. Please add it to GitHub Secrets.</p>"

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""
    You are an expert investigative journalist and editor. 
    I will provide you with a large set of raw news headlines and snippets for two main topics: **Artificial Intelligence** and **Galatasaray SK**.

    Your task is to write a **comprehensive, in-depth Daily News Report** in HTML format.
    
    **Guidelines for Content (CRITICAL):**
    1. **Length & Depth**: Do NOT write short summaries. I want detailed paragraphs. Analyze the news, explain *why* it matters, and connect the dots between different stories.
    2. **Tone**: Professional, insightful, and engaging. Avoid generic "Here is the news" intros. Dive straight into the most impactful stories.
    3. **Structure**:
       - **Executive Summary**: A 2-3 sentence high-level overview of the day's biggest vibe.
       - **Deep Dive: Artificial Intelligence**: Group stories by themes (e.g., "New Models", "Regulation", "Industry Moves"). Write extensive analysis for the top stories.
       - **Deep Dive: Galatasaray SK**: Cover match results, transfer rumors, and fan sentiment deeply.
       - **Sources**: You MUST embed links naturally in the text (e.g., "according to <a href='...'>TechCrunch</a>").
    
    **Format**: 
    - Return ONLY the HTML body (no ```html``` blocks). 
    - Use modern, clean inline CSS. 
    - Use `<h3>` for sub-themes within the main topics.

    Here is the raw news data:
    {news_data}
    """

    # Using Claude 3.5 Haiku - most cost-effective Claude model
    # Pricing: $0.80/1M input tokens, $4.00/1M output tokens
    # max_tokens=4096 keeps output costs reasonable while allowing comprehensive content
    model_name = 'claude-3-5-haiku-latest'
    
    try:
        message = client.messages.create(
            model=model_name,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text.replace("```html", "").replace("```", "")
    except Exception as e:
        print(f"Error with model {model_name}: {e}")
        return f"<h1>Error Generating Digest</h1><p>Could not generate digest via LLM. Error: {e}</p>"

def send_email(subject, html_content):
    sender = os.environ.get('EMAIL_SENDER')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('EMAIL_RECEIVER')

    if not all([sender, password, receiver]):
        print("Error: Missing environment variables (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER)")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    
    # Mark email as Important / High Priority
    msg['X-Priority'] = '1'
    msg['X-MSMail-Priority'] = 'High'
    msg['Importance'] = 'High'
    
    msg.set_content("This is a HTML email. Please enable HTML viewing.")
    msg.add_alternative(html_content, subtype='html')

    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    # Expanded sources: Google News + Reddit (for community sentiment/breaking news)
    feeds = {
        "Artificial Intelligence (Google News)": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:1d",
        "Artificial Intelligence (Reddit)": "https://www.reddit.com/r/ArtificialIntelligence/top/.rss?t=day",
        "Galatasaray SK (Google News)": "https://news.google.com/rss/search?q=Galatasaray+SK+when:1d",
        "Galatasaray SK (Reddit)": "https://www.reddit.com/r/galatasaray/top/.rss?t=day"
    }

    print("Loading history...")
    history = load_history()
    print(f"Loaded {len(history)} past links.")

    print("Fetching news...")
    all_news_text = ""
    new_links_collected = []
    
    for topic, url in feeds.items():
        print(f"Fetching {topic}...")
        entries, new_links = fetch_feed_entries(url, topic, history)
        if entries:
            all_news_text += f"\n=== SOURCE: {topic} ===\n"
            all_news_text += "\n".join(entries)
            new_links_collected.extend(new_links)
        else:
            # If no *new* news, we don't add anything to the text
            print(f"  No new stories found for {topic}.")

    if not all_news_text:
        print("No new news found today! Skipping email.")
        return

    print("Generating digest with LLM...")
    html_content = generate_digest_with_llm(all_news_text)
    
    print("Sending email...")
    # Dynamic subject line
    send_email(f"Your Daily Briefing: AI & Galatasaray - {datetime.date.today()}", html_content)
    
    print("Updating history...")
    history.update(new_links_collected)
    save_history(history)
    print("History saved.")

if __name__ == "__main__":
    main()
