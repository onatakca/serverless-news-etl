import feedparser
import smtplib
import ssl
import os
import datetime
from email.message import EmailMessage

def fetch_feed(url, retries=1):
    """Fetches a feed, with a simple retry mechanism for Nitter instances."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            raise Exception(f"Error parsing feed: {feed.bozo_exception}")
        return feed
    except Exception as e:
        if retries > 0:
            print(f"Failed to fetch {url}, retrying... ({e})")
            return fetch_feed(url, retries - 1)
        print(f"Failed to fetch {url} after retries.")
        return None

def get_top_entries(feed_url, count=5):
    feed = fetch_feed(feed_url)
    if not feed or not feed.entries:
        return []
    return feed.entries[:count]

def generate_html_content(feeds):
    html_parts = ["<html><body>"]
    html_parts.append(f"<h1>Daily News Digest - {datetime.date.today()}</h1>")
    
    for topic, url in feeds.items():
        entries = []
        # Special handling for Nitter backups
        if isinstance(url, list):
            for u in url:
                entries = get_top_entries(u)
                if entries:
                    break
        else:
            entries = get_top_entries(url)
            
        html_parts.append(f"<h2>{topic}</h2>")
        if not entries:
            html_parts.append("<p>No news found or error fetching feed.</p>")
            continue
            
        html_parts.append("<ul>")
        for entry in entries:
            title = entry.title
            link = entry.link
            # Nitter feeds sometimes have empty titles or just text, let's ensure we have something
            if not title:
                title = "No Title"
            html_parts.append(f"<li><a href='{link}'>{title}</a></li>")
        html_parts.append("</ul>")
        
    html_parts.append("</body></html>")
    return "".join(html_parts)

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
    feeds = {
        "Artificial Intelligence": "https://news.google.com/rss/search?q=Artificial+Intelligence",
        "Data Engineering": "https://news.google.com/rss/search?q=Data+Engineering",
        "Galatasaray SK (Twitter/Nitter)": [
            "https://nitter.net/GalatasaraySK/rss",
            "https://nitter.poast.org/GalatasaraySK/rss"
        ]
    }

    print("Fetching news...")
    html_content = generate_html_content(feeds)
    
    print("Sending email...")
    send_email(f"Daily News Digest - {datetime.date.today()}", html_content)

if __name__ == "__main__":
    main()
