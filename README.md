📬 Gmail Auto-Responder with OpenAI GPT

This project is a Python-based AI-powered Gmail Auto-Responder.
It connects to your Gmail account using the Gmail API, fetches unread emails, generates polite and professional replies using OpenAI GPT-4o, and sends them back automatically.

🚀 Features

✅ Authenticate with Gmail via OAuth2 (credentials.json)

✅ Fetch unread emails (skips auto-replies & no-reply senders)

✅ Extracts email body even from multipart messages

✅ Generates AI-based replies using OpenAI GPT-4o

✅ Sends the reply and marks the email as read

✅ Runs continuously with configurable check intervals

🛠️ Setup Instructions
1. Clone Repository
git clone https://github.com/your-username/email-autoresponder.git
cd email-autoresponder

2. Install Dependencies
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib openai

3. Gmail API Credentials

Go to Google Cloud Console

Enable the Gmail API

Create OAuth 2.0 credentials (download credentials.json)

Place credentials.json in the project folder

4. OpenAI API Key

Get your API key from OpenAI Dashboard

Set it inside the script:

OPENAI_API_KEY = "your_openai_api_key_here"

5. Run the Script
python email_sender_open_AI.py


The script will:

Authenticate Gmail (first run opens a browser for OAuth)

Start checking emails every 30 seconds

Auto-generate and send replies

⚙️ Configuration

Inside email_sender_open_AI.py:

CHECK_INTERVAL = 30 → Interval (seconds) between email checks

MODEL_NAME = "gpt-4o" → OpenAI model used for replies

📂 Project Structure
email-autoresponder/
│── email_sender_open_AI.py   # Main script
│── credentials.json          # Gmail OAuth2 credentials
│── token.pickle              # Generated after first login
│── README.md                 # Documentation

🔐 Security Notes

Do not commit credentials.json, token.pickle, or your API keys to GitHub.

Use environment variables for sensitive keys in production.
