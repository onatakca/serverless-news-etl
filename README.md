# Daily News Bot (Email Edition)

This project is a serverless bot that aggregates news from Google News, summarizes it using **Google Gemini AI**, and emails a daily digest to you.

## Setup

### 1. Gmail App Password
To allow the script to send emails via your Gmail account:
1.  Go to [Google Account Security](https://myaccount.google.com/security).
2.  Enable **2-Step Verification**.
3.  Generate an **App Password** (search for it in settings).
4.  Copy the 16-character password.

### 2. Gemini API Key (The Brains)
To generate the smart summary:
1.  Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Click **Create API key**.
3.  Copy the key string.

### 3. GitHub Secrets
Store your credentials securely in your repository:
1.  Go to **Settings** > **Secrets and variables** > **Actions**.
2.  Add the following secrets:
    *   `EMAIL_SENDER`: Your Gmail address.
    *   `EMAIL_PASSWORD`: The App Password.
    *   `EMAIL_RECEIVER`: Where to send the email.
    *   `GEMINI_API_KEY`: The Google AI Studio API key.

## Usage
The bot runs automatically every day at 8:00 AM UTC. You can also trigger it manually from the **Actions** tab.
