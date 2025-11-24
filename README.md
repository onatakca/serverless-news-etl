# Daily News Bot (Email Edition)

This project is a serverless bot that aggregates news from Google News and Twitter (via Nitter) and emails a daily digest to you.

## Setup

### 1. Gmail App Password
To allow the script to send emails via your Gmail account, you need to generate an App Password (since using your real password is less secure and often blocked).

1.  Go to your [Google Account Security settings](https://myaccount.google.com/security).
2.  Enable **2-Step Verification** if it isn't already.
3.  Search for **App Passwords** (or find it under the 2-Step Verification section).
4.  Create a new App Password (name it "Daily News Bot" or similar).
5.  Copy the 16-character password generated.

### 2. GitHub Secrets
To keep your credentials safe, store them as GitHub Secrets:

1.  Go to your repository on GitHub.
2.  Navigate to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  Add the following secrets:
    *   `EMAIL_SENDER`: Your full Gmail address.
    *   `EMAIL_PASSWORD`: The 16-character App Password you just generated.
    *   `EMAIL_RECEIVER`: The email address where you want to receive the digest.

### 3. The Nitter Trick
Twitter (X) does not provide a free, open RSS feed anymore. To get around this, we use **Nitter**, a privacy-focused open-source front-end for Twitter.

*   Nitter instances provide RSS feeds for any Twitter user.
*   The script tries `https://nitter.net/GalatasaraySK/rss` first.
*   Since public Nitter instances can be rate-limited or go down, the script includes a backup URL (`https://nitter.poast.org/GalatasaraySK/rss`) to ensure reliability.

## Usage
The bot runs automatically every day at 8:00 AM UTC. You can also trigger it manually from the **Actions** tab in your GitHub repository.
