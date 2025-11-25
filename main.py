import feedparser
import smtplib
import ssl
import os
import datetime
from email.message import EmailMessage
import google.generativeai as genai

def fetch_feed_entries(url, topic, count=5):
    """Fetches top entries from a Google News RSS feed."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            print(f"Warning: Potential issue parsing feed for {topic}: {feed.bozo_exception}")
        
        entries = feed.entries[:count]
        data = []
        for entry in entries:
            # RSS feeds usually have 'title', 'link', and sometimes 'description' or 'summary'
            summary = getattr(entry, 'summary', '')
            # Clean up summary HTML if needed, but for now raw is okay for the LLM to parse
            data.append(f"- Title: {entry.title}\n  Link: {entry.link}\n  Snippet: {summary}\n")
        return data
    except Exception as e:
        print(f"Error fetching {topic}: {e}")
        return []

def generate_digest_with_llm(news_data):
    """Uses Gemini to generate a cohesive HTML newsletter."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "<h1>Error</h1><p>GEMINI_API_KEY is missing. Please add it to GitHub Secrets.</p>"

    genai.configure(api_key=api_key)

    prompt = f"""
    You are a professional news anchor and editor. 
    I will provide you with the latest raw news headlines and snippets for three topics: Artificial Intelligence, Data Engineering, and Galatasaray SK.

    Your task is to write a "Daily Personal News Digest" email in HTML format.
    
    Guidelines:
    1. **Style**: engaging, concise, and "newsletter-style" (not just a list of links). Write like a human summarizing the day's events.
    2. **Structure**:
       - A welcoming intro.
       - A section for each topic (use <h2>).
       - For each topic, synthesize the headlines into a narrative. If a story is big, highlight it. 
       - Embed the links naturally in the text (e.g., "Read more") or as a clean list of sources at the end of the section.
       - A brief conclusion.
    3. **Format**: Return ONLY the HTML body (no ```html``` blocks). Use inline CSS for basic styling (clean font, readable).

    Here is the raw news data:
    {news_data}
    """

    # Use Gemini 3.0 Pro as requested
    model_name = 'gemini-3.0-pro' 
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.replace("```html", "").replace("```", "")
    except Exception as e:
        print(f"Error with model {model_name}: {e}")
        print("Listing available models to help debug:")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"- {m.name}")
        except Exception as list_e:
            print(f"Could not list models: {list_e}")
            
        return f"<h1>Error Generating Digest</h1><p>Could not generate digest via LLM. Check GitHub Action logs for available models. Error: {e}</p>"

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
    # Switched Galatasaray to Google News for reliability
    feeds = {
        "Artificial Intelligence": "https://news.google.com/rss/search?q=Artificial+Intelligence",
        "Data Engineering": "https://news.google.com/rss/search?q=Data+Engineering",
        "Galatasaray SK": "https://news.google.com/rss/search?q=Galatasaray+SK" 
    }

    print("Fetching news...")
    all_news_text = ""
    for topic, url in feeds.items():
        print(f"Fetching {topic}...")
        entries = fetch_feed_entries(url, topic)
        if entries:
            all_news_text += f"\n=== TOPIC: {topic} ===\n"
            all_news_text += "\n".join(entries)
        else:
            all_news_text += f"\n=== TOPIC: {topic} ===\nNo news found today.\n"

    print("Generating digest with LLM...")
    html_content = generate_digest_with_llm(all_news_text)
    
    print("Sending email...")
    send_email(f"Daily Digest - {datetime.date.today()}", html_content)

if __name__ == "__main__":
    main()
