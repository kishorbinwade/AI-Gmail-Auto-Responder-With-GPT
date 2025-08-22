from __future__ import print_function
import os
import base64
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import parseaddr
import pickle
import logging

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from openai import OpenAI

# ======================
# CONFIG
# ======================
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
OPENAI_API_KEY = "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"
MODEL_NAME = "gpt-4o"
CHECK_INTERVAL = 30  # seconds between checks

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


# ======================
# AUTHENTICATE GMAIL
# ======================
def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


# ======================
# FETCH UNREAD EMAILS
# ======================
def get_unread_emails(service, limit=5):
    today_str = datetime.utcnow().strftime("%Y/%m/%d")
    query = f"is:unread after:{today_str}"
    results = service.users().messages().list(
        userId='me', labelIds=['UNREAD'], q=query, maxResults=limit
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "")
        clean_sender = parseaddr(sender)[1].lower()

        if any(x in clean_sender for x in ["noreply", "no-reply", "donotreply", "do-not-reply"]):
            logging.info(f"⏩ Skipping auto-generated email from {clean_sender}")
            continue

        auto_submitted = next((h['value'] for h in headers if h['name'].lower() == 'auto-submitted'), "").lower()
        if auto_submitted and auto_submitted != "no":
            logging.info(f"⏩ Skipping auto-submitted email from {clean_sender}")
            continue

        body = extract_email_body(msg_data['payload'])
        emails.append({
            'id': msg['id'],
            'from': clean_sender,
            'subject': subject,
            'body': body
        })

    return emails


def extract_email_body(payload):
    """Extracts plain text body from email payload, even if multipart."""
    if payload.get("mimeType") == "text/plain" and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")

    if "parts" in payload:
        for part in payload["parts"]:
            text = extract_email_body(part)
            if text:
                return text
    return ""


# ======================
# GENERATE AI REPLY (GPT-4o)
# ======================
def generate_ai_reply(email_text):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional email responder. "
                        "Reply briefly, politely, and to the point. "
                        "Do not use placeholders like [Name] or [Your Name]. "
                        "Do not greet by name unless the name appears in the email."
                    )
                },
                {"role": "user", "content": f"Reply to this email:\n\n{email_text}"}
            ],
            temperature=0.5,
            max_tokens=300
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return "Thank you for your email. I will get back to you shortly."


# ======================
# SEND EMAIL
# ======================
def send_email(service, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw_message}).execute()


# ======================
# MARK EMAIL AS READ
# ======================
def mark_as_read(service, msg_id):
    service.users().messages().modify(
        userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
    ).execute()


# ======================
# MAIN LOOP
# ======================
if __name__ == "__main__":
    service = authenticate_gmail()
    logging.info("📬 Gmail Auto-Responder is running. Press CTRL+C to stop.")

    while True:
        try:
            emails = get_unread_emails(service)

            if not emails:
                logging.info("✅ No new emails to reply to.")
            else:
                for email in emails:
                    logging.info(f"📩 Replying to: {email['from']} | Subject: {email['subject']}")
                    reply_text = generate_ai_reply(email['body'])
                    send_email(service, email['from'], f"Re: {email['subject']}", reply_text)
                    mark_as_read(service, email['id'])
                    logging.info(f"✅ Replied to {email['from']}")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logging.info("🛑 Stopped by user.")
            break
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            time.sleep(CHECK_INTERVAL)

